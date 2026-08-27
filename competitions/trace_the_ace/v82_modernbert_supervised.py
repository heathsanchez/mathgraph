#!/usr/bin/env python3
"""V82: supervised ModernBERT on V81 multi-resolution mastery evidence.

Primary question: does task-supervised language understanding materially improve
objective-cold log loss once the input representation exposes target segment,
instructional phase, assistance/state trajectory, and whole-session context?

For CPU feasibility this experiment unfreezes the classifier/pooler plus the top
N transformer blocks. This is deliberately different from frozen embeddings:
task labels update the language model's upper representation layers.
"""
from __future__ import annotations
import argparse, json, random
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, trajectory_views, SEED
from v81_target_segment_phase import choose_target_segment, phase_views

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)


def clip_chars(s: str, n: int) -> str:
    s=str(s)
    if len(s)<=n: return s
    # Preserve both start and terminal evidence.
    a=n//2; return s[:a] + " [..CUT..] " + s[-(n-a):]


def make_text(df: pd.DataFrame, objective: str, max_chars: int=18000) -> tuple[str, dict]:
    whole, whole_num, _ = trajectory_views(df, objective)
    seg, meta = choose_target_segment(df, objective)
    target, target_num, _ = trajectory_views(seg, objective)
    phases, phase_num = phase_views(seg, objective)

    # Multi-resolution evidence. Whole context is compacted; target/independent/
    # application and canonical states get preferential budget.
    parts = [
        f"[OBJECTIVE] {objective}",
        f"[TARGET_SEGMENT] {clip_chars(target['raw'], 4200)}",
        f"[TARGET_STUDENT] {clip_chars(target['student'], 2600)}",
        f"[TARGET_CANONICAL] {clip_chars(target['canonical'], 2400)}",
        f"[TARGET_TERMINAL] {clip_chars(target['terminal'], 2200)}",
        f"[PRIOR] {clip_chars(phases.get('phase_prior',''), 1200)}",
        f"[GUIDED] {clip_chars(phases.get('phase_guided',''), 1600)}",
        f"[INDEPENDENT] {clip_chars(phases.get('phase_independent',''), 2200)}",
        f"[APPLICATION] {clip_chars(phases.get('phase_application',''), 1800)}",
        f"[PHASE_STATES] {clip_chars(phases.get('phase_states',''), 1800)}",
        f"[WHOLE_CONTEXT] {clip_chars(whole['raw'], 3200)}",
        f"[WHOLE_TERMINAL] {clip_chars(whole['terminal'], 1200)}",
    ]
    text="\n".join(parts)
    if len(text)>max_chars: text=clip_chars(text,max_chars)
    return text, meta


class TextDS(Dataset):
    def __init__(self, texts, labels, tok, max_len): self.texts=texts; self.labels=labels; self.tok=tok; self.max_len=max_len
    def __len__(self): return len(self.texts)
    def __getitem__(self,i):
        enc=self.tok(self.texts[i], truncation=True, max_length=self.max_len, padding=False)
        enc={k:torch.tensor(v,dtype=torch.long) for k,v in enc.items()}
        enc['labels']=torch.tensor(float(self.labels[i]),dtype=torch.float32)
        return enc


def collate(tok):
    def fn(rows):
        labels=torch.stack([r.pop('labels') for r in rows])
        b=tok.pad(rows,padding=True,return_tensors='pt'); b['labels']=labels
        return b
    return fn


def unfreeze_top(model, top_blocks: int):
    for p in model.parameters(): p.requires_grad=False
    # Always train classification head / pooler-like named modules.
    for n,p in model.named_parameters():
        ln=n.lower()
        if any(x in ln for x in ['classifier','score','pooler']): p.requires_grad=True
    # ModernBERT/HF encoder layer naming varies; discover indexed layer names.
    layer_names=[]
    for n,_ in model.named_parameters():
        bits=n.split('.')
        for j,b in enumerate(bits[:-1]):
            if b.isdigit() and any(x in '.'.join(bits[:j]).lower() for x in ['layer','layers','encoder']):
                try: layer_names.append(int(b))
                except: pass
    if layer_names:
        mx=max(layer_names); cutoff=max(0,mx-top_blocks+1)
        for n,p in model.named_parameters():
            bits=n.split('.')
            idx=None
            for j,b in enumerate(bits):
                if b.isdigit() and any(x in '.'.join(bits[:j]).lower() for x in ['layer','layers','encoder']): idx=int(b); break
            if idx is not None and idx>=cutoff: p.requires_grad=True
    trainable=sum(p.numel() for p in model.parameters() if p.requires_grad)
    total=sum(p.numel() for p in model.parameters())
    print('trainable_parameters',trainable,'total_parameters',total,'fraction',trainable/total)
    return trainable,total


def predict(model, loader, device):
    model.eval(); out=[]; ys=[]
    with torch.no_grad():
        for b in loader:
            y=b.pop('labels').numpy(); ys.extend(y.tolist())
            b={k:v.to(device) for k,v in b.items()}
            z=model(**b).logits.squeeze(-1); out.extend(torch.sigmoid(z).cpu().numpy().tolist())
    return np.asarray(out),np.asarray(ys)


def run(a):
    frame=load_training(a.features,a.labels).reset_index(drop=True)
    if a.limit: frame=frame.iloc[:a.limit].copy().reset_index(drop=True)
    cache={}; texts=[]; metas=[]
    for i,r in frame.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
        t,m=make_text(cache[sid],str(r.learning_objective),a.max_chars); texts.append(t); metas.append(m)
        if (i+1)%1000==0: print('built_texts',i+1)
    y=frame.target.to_numpy(np.float32)
    grp=(frame.learning_objective_id if 'learning_objective_id' in frame else frame.learning_objective).astype(str).to_numpy()
    folds=list(GroupKFold(5).split(np.zeros(len(y)),y,grp))
    selected=list(range(min(a.folds,len(folds))))
    tok=AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); print('device',device)
    results=[]; all_p=[]; all_y=[]
    for fi in selected:
        tr,va=folds[fi]
        model=AutoModelForSequenceClassification.from_pretrained(a.model,num_labels=1,problem_type='regression',trust_remote_code=True)
        unfreeze_top(model,a.top_blocks); model.to(device)
        train_ds=TextDS([texts[i] for i in tr],y[tr],tok,a.max_len); val_ds=TextDS([texts[i] for i in va],y[va],tok,a.max_len)
        train_dl=DataLoader(train_ds,batch_size=a.batch,shuffle=True,collate_fn=collate(tok),num_workers=0)
        val_dl=DataLoader(val_ds,batch_size=a.eval_batch,shuffle=False,collate_fn=collate(tok),num_workers=0)
        params=[p for p in model.parameters() if p.requires_grad]
        opt=torch.optim.AdamW(params,lr=a.lr,weight_decay=.01)
        steps=max(1,len(train_dl)*a.epochs); sched=get_linear_schedule_with_warmup(opt,max(1,int(.06*steps)),steps)
        model.train(); seen=0
        for ep in range(a.epochs):
            for b in train_dl:
                labels=b.pop('labels').to(device)
                b={k:v.to(device) for k,v in b.items()}
                logits=model(**b).logits.squeeze(-1)
                loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,labels)
                loss.backward(); torch.nn.utils.clip_grad_norm_(params,1.0); opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
                seen+=1
                if seen%50==0: print('fold',fi+1,'step',seen,'loss',float(loss.detach().cpu()))
        p,yy=predict(model,val_dl,device); p=np.clip(p,1e-5,1-1e-5)
        row={'fold':fi+1,'rows':len(va),'logloss':float(log_loss(yy,p)),'auc':float(roc_auc_score(yy,p))}; print('RESULT',row); results.append(row); all_p.extend(p.tolist()); all_y.extend(yy.tolist())
        del model; 
        if torch.cuda.is_available(): torch.cuda.empty_cache()
    result={'model':a.model,'mode':'supervised_top_blocks','top_blocks':a.top_blocks,'epochs':a.epochs,'lr':a.lr,'max_len':a.max_len,'folds_run':len(selected),'fold_results':results,'pooled_logloss':float(log_loss(all_y,all_p)) if all_p else None,'pooled_auc':float(roc_auc_score(all_y,all_p)) if all_p else None,'segmentation':{'mean_fraction':float(np.mean([m['segment_fraction'] for m in metas])),'mean_segments':float(np.mean([m['segments'] for m in metas]))}}
    Path(a.out).write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v82_modernbert_supervised.json'); p.add_argument('--model',default='answerdotai/ModernBERT-large'); p.add_argument('--folds',type=int,default=1); p.add_argument('--epochs',type=int,default=1); p.add_argument('--top-blocks',type=int,default=2); p.add_argument('--lr',type=float,default=2e-5); p.add_argument('--max-len',type=int,default=768); p.add_argument('--max-chars',type=int,default=18000); p.add_argument('--batch',type=int,default=2); p.add_argument('--eval-batch',type=int,default=4); p.add_argument('--limit',type=int,default=0); run(p.parse_args())

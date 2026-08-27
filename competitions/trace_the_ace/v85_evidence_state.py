#!/usr/bin/env python3
"""V85: RGRS EvidenceEvent -> knowledge-state separator.

Compares three objective-cold arms:
A0: V75 whole-session representation baseline.
A1: explicit objective-conditioned EvidenceEvent IR with assistance/independence tags.
A2: same EvidenceEvent IR with assistance/independence tags ablated.

Primary decision: A1 must beat A0 by >=0.003 log loss and materially beat A2 to count
as a representation-level breakthrough. Otherwise retain as negative/conditional law.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript, tokens, jaccard, char_ngram_overlap
from v75_canonical_trajectory import load_training, trajectory_views, SEED
from v81_target_segment_phase import choose_target_segment, phase_for

QUESTION_RE=re.compile(r"\?|\b(?:what|how|why|which|calculate|solve|find|show|explain|tell me|your turn|try|have a go)\b",re.I)
POS_RE=re.compile(r"\b(?:correct|right|yes|exactly|great|brilliant|well done|good job|nice|perfect)\b",re.I)
NEG_RE=re.compile(r"\b(?:not quite|incorrect|wrong|try again|check|remember|almost|no[, .])\b",re.I)
HINT_RE=re.compile(r"\b(?:remember|think about|hint|try|look at|first|start by|let's|lets|together|we can|I'll|i will|let me)\b",re.I)
SUPPLY_RE=re.compile(r"\b(?:the answer is|it is|equals|so .* is|that gives|we get|you should)\b",re.I)
ACK_RE=re.compile(r"^(?:ok(?:ay)?|yes|yeah|yep|no|nope|thanks?|thank you|got it|sure|right|mhm|uh huh|great|cool)[.! ]*$",re.I)

PHASE_WEIGHT={'OTHER':.45,'GOAL':.25,'PRIOR':.35,'GUIDED':.55,'INDEPENDENT':1.0,'APPLICATION':1.1}


def rel(text,obj):
    return float(max(jaccard(tokens(str(text)),tokens(str(obj))),.5*char_ngram_overlap(str(text),str(obj))))


def substantive(s):
    s=str(s).strip()
    if not s or ACK_RE.match(s): return False
    # preserve short numeric/math answers
    if re.search(r"\d|[=+\-*/%]",s): return True
    return len(tokens(s))>=2


def phase_replay(df):
    ph='OTHER'; out=[]
    for t in df.content.fillna('').astype(str):
        ph=phase_for(t,ph); out.append(ph)
    return out


def evidence_events(df,obj):
    d=df.reset_index(drop=True).copy(); phases=phase_replay(d)
    events=[]
    n=len(d)
    for i,row in d.iterrows():
        if str(row.role).lower()!='student' or not substantive(row.content): continue
        # nearest preceding tutor question/prompt within 4 turns
        qidx=None
        for j in range(i-1,max(-1,i-5),-1):
            if str(d.iloc[j].role).lower()=='tutor' and QUESTION_RE.search(str(d.iloc[j].content)):
                qidx=j; break
        if qidx is None: continue
        q=str(d.iloc[qidx].content); ans=str(row.content)
        # immediate/near tutor feedback after response
        feedback=''; fbidx=None
        for j in range(i+1,min(n,i+4)):
            if str(d.iloc[j].role).lower()=='tutor': feedback=str(d.iloc[j].content); fbidx=j; break
        rq=rel(q,obj); ra=rel(ans,obj); relevance=max(rq,.4*ra)
        # Assistance is derived only from tutor turns after previous student response and before this answer.
        window=' '.join(str(d.iloc[j].content) for j in range(max(0,qidx-2),i) if str(d.iloc[j].role).lower()=='tutor')
        supplied=bool(SUPPLY_RE.search(window)); hinted=bool(HINT_RE.search(window))
        assistance=1.0 if supplied else (.6 if hinted else 0.0)
        independent=(phases[i] in ('INDEPENDENT','APPLICATION') and assistance<.3)
        pos=bool(POS_RE.search(feedback)); neg=bool(NEG_RE.search(feedback))
        # canonical state; tutor feedback is auxiliary, not ground truth
        if neg: state='UNRESOLVED_ERROR'
        elif pos and assistance>=.6: state='CORRECT_AFTER_GUIDANCE'
        elif pos and independent: state='INDEPENDENT_CORRECT'
        elif pos: state='SUPPORTED_CORRECT'
        else: state='UNJUDGED_RESPONSE'
        events.append({'i':i,'phase':phases[i],'q':q,'a':ans,'feedback':feedback,'rel':relevance,
                       'assistance':assistance,'independent':independent,'state':state,
                       'position':i/max(1,n-1),'pos':pos,'neg':neg})
    return events


def render(events,obj,ablate=False):
    keep=sorted(events,key=lambda e:(e['rel']*(.4+.6*e['position'])*PHASE_WEIGHT.get(e['phase'],.4)),reverse=True)[:16]
    keep=sorted(keep,key=lambda e:e['i'])
    rows=[]
    for e in keep:
        tags=[f"PHASE={e['phase']}",f"STATE={e['state']}",f"REL={e['rel']:.2f}",f"POS={int(e['pos'])}",f"NEG={int(e['neg'])}"]
        if not ablate: tags += [f"ASSIST={e['assistance']:.1f}",f"INDEP={int(e['independent'])}"]
        rows.append('['+' '.join(tags)+'] [Q] '+e['q']+' [STUDENT] '+e['a'])
    return f"[OBJECTIVE] {obj}\n"+'\n'.join(rows)


def nums(events,ablate=False):
    if not events: return np.zeros(22 if not ablate else 16,float)
    E=events; rels=np.array([e['rel'] for e in E]); pos=np.array([e['pos'] for e in E],float); neg=np.array([e['neg'] for e in E],float)
    ind=np.array([e['independent'] for e in E],float); ass=np.array([e['assistance'] for e in E],float); positions=np.array([e['position'] for e in E])
    app=np.array([e['phase']=='APPLICATION' for e in E],float); late=positions>=.6
    base=[len(E),rels.mean(),rels.max(),pos.mean(),neg.mean(),positions[pos>0].max() if pos.any() else 0,
          positions[neg>0].max() if neg.any() else 0,pos[late].mean() if late.any() else 0,neg[late].mean() if late.any() else 0,
          app.mean(),(pos*rels).sum()/(rels.sum()+1e-6),(neg*rels).sum()/(rels.sum()+1e-6),
          float(any(e['state']=='UNRESOLVED_ERROR' for e in E[-3:])),float(any(e['state']=='INDEPENDENT_CORRECT' for e in E[-3:])),
          sum(e['state']=='INDEPENDENT_CORRECT' for e in E),sum(e['state']=='CORRECT_AFTER_GUIDANCE' for e in E)]
    if ablate: return np.asarray(base,float)
    extra=[ass.mean(),ass[-3:].mean() if len(ass)>=3 else ass.mean(),ind.mean(),ind[late].mean() if late.any() else 0,
           (pos*ind*rels).sum()/(rels.sum()+1e-6),(neg*(1-ass)*rels).sum()/(rels.sum()+1e-6)]
    return np.asarray(base+extra,float)


def build_sparse(texts,Z,prefix):
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    X=hv.transform([f'[{prefix}] '+x for x in texts]); Z=np.vstack(Z); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6)
    return hstack([X,csr_matrix(Z)],format='csr')


def build_v75(frame,transcripts):
    rows=[]; ns=[]
    for _,r in frame.iterrows():
        v,n,_=trajectory_views(transcripts[str(r.session_id)],str(r.learning_objective)); rows.append(v); ns.append(n)
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    parts=[hv.transform([f'[OBJECTIVE] {x}' for x in frame.learning_objective])]
    for k in rows[0].keys(): parts.append(hv.transform([f'[{k.upper()}] '+r[k] for r in rows]))
    Z=np.vstack(ns); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6); parts.append(csr_matrix(Z))
    return hstack(parts,format='csr')


def oof(X,y,splits,name):
    p=np.zeros(len(y)); fs=[]
    for k,(tr,va) in enumerate(splits,1):
        m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
        q=np.clip(m.predict_proba(X[va])[:,1],1e-5,1-1e-5); p[va]=q
        row={'fold':k,'logloss':float(log_loss(y[va],q)),'auc':float(roc_auc_score(y[va],q))}; print(name,row); fs.append(row)
    return p,fs


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    if a.limit: f=f.iloc[:a.limit].copy().reset_index(drop=True)
    cache={}
    for sid in f.session_id.astype(str).unique(): cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
    full_text=[]; abl_text=[]; full_num=[]; abl_num=[]; meta=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; seg,m=choose_target_segment(d,str(r.learning_objective)); ev=evidence_events(seg,str(r.learning_objective))
        full_text.append(render(ev,str(r.learning_objective),False)); abl_text.append(render(ev,str(r.learning_objective),True))
        full_num.append(nums(ev,False)); abl_num.append(nums(ev,True)); meta.append({'events':len(ev),**m})
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sp=list(GroupKFold(5).split(np.zeros(len(y)),y,groups))
    X0=build_v75(f,cache); X1=build_sparse(full_text,full_num,'EVIDENCE'); X2=build_sparse(abl_text,abl_num,'EVIDENCE_ABL')
    p0,f0=oof(X0,y,sp,'A0_v75'); p1,f1=oof(X1,y,sp,'A1_evidence'); p2,f2=oof(X2,y,sp,'A2_ablation')
    ll0=float(log_loss(y,p0)); ll1=float(log_loss(y,p1)); ll2=float(log_loss(y,p2))
    # Also test whether evidence is orthogonal to V75; fixed transparent grid only.
    blends=[]; best=None
    for w in np.linspace(0,1,21):
        q=np.clip((1-w)*p0+w*p1,1e-5,1-1e-5); ll=float(log_loss(y,q)); row={'evidence_weight':float(w),'logloss':ll}; blends.append(row)
        if best is None or ll<best['logloss']: best=row
    gain=ll0-ll1; causal=ll2-ll1
    if gain>=.003 and causal>=.001: decision='REPRESENTATION_BREAKTHROUGH'
    elif gain>=.001 and causal>0: decision='PROMISING_PARTIAL'
    elif best['logloss']<=ll0-.001: decision='ORTHOGONAL_SIGNAL_ONLY'
    else: decision='REJECT_OR_REFINE_R5'
    out={'primary':'objective-cold','A0_v75':ll0,'A1_evidence':ll1,'A2_ablation':ll2,'gain_vs_A0':gain,'causal_assistance_gain':causal,
         'best_blend':best,'decision':decision,'folds':{'A0':f0,'A1':f1,'A2':f2},
         'event_stats':{'mean_events':float(np.mean([m['events'] for m in meta])),'zero_event_fraction':float(np.mean([m['events']==0 for m in meta]))}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v85_evidence_state.json'); p.add_argument('--limit',type=int,default=0); run(p.parse_args())

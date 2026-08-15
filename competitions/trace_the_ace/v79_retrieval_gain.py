#!/usr/bin/env python3
"""V79: objective-conditioned semantic retrieval + learning-gain state + V75 blend.

This is deliberately different from whole-transcript embedding. It embeds tutoring
Q/A/feedback episodes once per session, retrieves the episodes most semantically
aligned with each learning objective, explicitly summarizes early->late mastery
change, and tests an OOF blend with the sparse V75 trajectory champion.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer

from v71_mastery_events import load_transcript, extract_episodes
from v75_canonical_trajectory import load_training, trajectory_views, SEED


def folds(groups, n=5):
    g=np.asarray(groups.astype(str)); z=np.zeros(len(g)); return list(GroupKFold(n_splits=n).split(z,z,g))

def episode_text(e):
    return f"Tutor question: {e.question} Student answer: {e.answer} Tutor feedback: {e.feedback}"

def build_session_episodes(frame, transcript_dir):
    sessions={}
    for i,sid in enumerate(frame.session_id.astype(str).unique()):
        df=load_transcript(transcript_dir/f'{sid}.csv')
        eps=extract_episodes(df, '')
        # cap at 32 episodes; keep both early and late coverage if exceptionally long
        if len(eps)>32:
            idx=np.unique(np.r_[np.arange(8),np.linspace(8,len(eps)-9,16,dtype=int),np.arange(len(eps)-8,len(eps))])
            eps=[eps[j] for j in idx]
        sessions[sid]=eps
        if (i+1)%2500==0: print('sessions',i+1)
    return sessions

def encode_episode_bank(model, sessions, batch):
    flat=[]; spans={}; start=0
    for sid,eps in sessions.items():
        texts=[episode_text(e) for e in eps]
        flat.extend(texts); spans[sid]=(start,start+len(texts)); start+=len(texts)
    E=model.encode(flat or [' '],batch_size=batch,show_progress_bar=True,normalize_embeddings=True,convert_to_numpy=True).astype(np.float32)
    return E,spans

def retrieval_features(frame, sessions, Ebank, spans, Eobj, k=6):
    rows=[]; agg=[]
    for i,r in enumerate(frame.itertuples(index=False)):
        sid=str(r.session_id); eps=sessions[sid]; a,b=spans[sid]
        if not eps:
            rows.append(np.zeros(24,np.float32)); agg.append(np.zeros(Eobj.shape[1],np.float32)); continue
        E=Ebank[a:b]; sims=E@Eobj[i]
        top=np.argsort(sims)[-min(k,len(eps)):][::-1]
        st=sims[top]; w=np.exp(5*(st-st.max())); w=w/(w.sum()+1e-12)
        agg.append((E[top]*w[:,None]).sum(0))
        pos=np.array([eps[j].feedback_pos for j in top],float); neg=np.array([eps[j].feedback_neg for j in top],float)
        hint=np.array([eps[j].hinted for j in top],float); sub=np.array([eps[j].answer_substantive for j in top],float)
        rec=np.array([eps[j].recency for j in top],float); independent=pos*sub*(1-hint)
        # explicit early/final mastery among objective-relevant evidence
        early=rec<=np.median(rec); late=~early
        score=independent-neg-.35*hint
        early_score=float(score[early].mean()) if early.any() else 0.; late_score=float(score[late].mean()) if late.any() else 0.
        gain=late_score-early_score
        feats=np.array([
            len(eps),len(top),st[0],st.mean(),st.min(),st.std() if len(st)>1 else 0.,
            pos.mean(),neg.mean(),hint.mean(),sub.mean(),independent.mean(),
            float((w*pos).sum()),float((w*neg).sum()),float((w*independent).sum()),
            early_score,late_score,gain,float(rec.mean()),float(rec[np.argmax(st)]),
            float(score[-1]),float(score.max()),float(score.min()),
            float(np.mean(st[rec>=.66])) if np.any(rec>=.66) else 0.,
            float(np.mean(st[rec<=.33])) if np.any(rec<=.33) else 0.,
        ],np.float32)
        rows.append(feats)
    return np.vstack(rows),np.vstack(agg)

def build_v75(frame, transcript_dir):
    cache={}; views=[]; nums=[]
    for i,r in frame.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(transcript_dir/f'{sid}.csv')
        v,n,_=trajectory_views(cache[sid],str(r.learning_objective)); views.append(v); nums.append(n)
        if (i+1)%2500==0: print('v75 views',i+1)
    nums=np.vstack(nums).astype(np.float64); z=(nums-nums.mean(0))/(nums.std(0)+1e-6)
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    parts=[
      hv.transform(['[OBJECTIVE] '+str(x) for x in frame.learning_objective]),
      hv.transform(['[RAW] '+v['raw'] for v in views]),
      hv.transform(['[STUDENT] '+v['student'] for v in views]),
      hv.transform(['[LOCAL] '+v['local'] for v in views]),
      hv.transform(['[STATE] '+v['canonical'] for v in views]),
      hv.transform(['[TERMINAL] '+v['terminal'] for v in views]), csr_matrix(z)]
    return hstack(parts,format='csr')

def eval_regime(X75,Xr,y,split,name):
    p75=np.zeros(len(y)); pr=np.zeros(len(y)); fr=[]
    for f,(tr,va) in enumerate(split,1):
        m75=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr])
        p75[va]=np.clip(m75.predict_proba(X75[va])[:,1],1e-5,1-1e-5)
        sc=StandardScaler().fit(Xr[tr]); A=sc.transform(Xr[tr]); B=sc.transform(Xr[va])
        mr=LogisticRegression(C=.03,max_iter=500,solver='liblinear',random_state=SEED).fit(A,y[tr])
        pr[va]=np.clip(mr.predict_proba(B)[:,1],1e-5,1-1e-5)
        fr.append({'fold':f,'v75':float(log_loss(y[va],p75[va])),'retrieval_gain':float(log_loss(y[va],pr[va]))}); print(name,fr[-1])
    grid=[]; best=None
    for w in np.linspace(0,1,41):
        p=(1-w)*p75+w*pr; ll=float(log_loss(y,p)); row={'retrieval_weight':float(w),'logloss':ll}; grid.append(row)
        if best is None or ll<best['logloss']: best=row
    p=(1-best['retrieval_weight'])*p75+best['retrieval_weight']*pr
    return {'v75':float(log_loss(y,p75)),'retrieval_gain':float(log_loss(y,pr)),'best_blend':best,'blend_auc':float(roc_auc_score(y,p)),'folds':fr,'grid':grid}

def run(a):
    frame=load_training(a.features,a.labels).reset_index(drop=True)
    if a.limit: frame=frame.iloc[:a.limit].copy().reset_index(drop=True)
    model=SentenceTransformer(a.model)
    sessions=build_session_episodes(frame,a.transcripts)
    Ebank,spans=encode_episode_bank(model,sessions,a.batch)
    # unique objective embedding cache
    uniq=frame.learning_objective.astype(str).unique().tolist(); Eu=model.encode(uniq,batch_size=a.batch,show_progress_bar=True,normalize_embeddings=True,convert_to_numpy=True).astype(np.float32); omap={o:Eu[i] for i,o in enumerate(uniq)}
    Eobj=np.vstack([omap[str(x)] for x in frame.learning_objective])
    F,Agg=retrieval_features(frame,sessions,Ebank,spans,Eobj,a.topk)
    # interactions: objective, retrieved evidence, product, delta-style scalar state features
    Xr=np.hstack([Eobj,Agg,Eobj*Agg,F]).astype(np.float32)
    X75=build_v75(frame,a.transcripts); y=frame.target.to_numpy(int)
    objgrp=frame.learning_objective_id if 'learning_objective_id' in frame else frame.learning_objective
    out={'diagnostics':{'rows':len(frame),'sessions':len(sessions),'model':a.model,'embedding_dim':Eobj.shape[1],'retrieval_features':Xr.shape[1],'topk':a.topk},'session':eval_regime(X75,Xr,y,folds(frame.session_id),'session'),'objective':eval_regime(X75,Xr,y,folds(objgrp),'objective')}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
def parse():
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--model',default='sentence-transformers/all-MiniLM-L6-v2'); p.add_argument('--batch',type=int,default=128); p.add_argument('--topk',type=int,default=6); p.add_argument('--limit',type=int,default=0); p.add_argument('--out',default='v79_retrieval_gain.json'); return p.parse_args()
if __name__=='__main__': run(parse())

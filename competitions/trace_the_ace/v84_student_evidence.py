#!/usr/bin/env python3
"""V84: student-evidence representation with tutor-language confound removed.

Builds objective-cold OOF predictions from question + student answer + canonical
state/assistance tokens, but excludes raw tutor praise/feedback wording from the
student-evidence view. Compares against whole-session V75 and reports blend gain.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, trajectory_views, extract_canonical_events, SEED
from v81_target_segment_phase import choose_target_segment


def folds(g):
    z=np.zeros(len(g)); return list(GroupKFold(5).split(z,z,g.astype(str).to_numpy()))

def evidence_view(df,obj):
    ev=extract_canonical_events(df,obj)
    chunks=[]
    nums=[]
    for e in ev:
        rb='HIGH' if e.relevance>=.15 else 'MID' if e.relevance>=.05 else 'LOW'
        ab='NONE' if e.assistance<=.1 else 'LOW' if e.assistance<=.5 else 'HIGH'
        chunks.append(f'[STATE={e.state}] [REL={rb}] [ASSIST={ab}] [Q] {e.question} [STUDENT] {e.answer}')
        nums.append([e.relevance,e.recency,e.assistance,e.substantive,e.explanation])
    if nums:
        A=np.asarray(nums,float)
        feat=np.concatenate([A.mean(0),A.max(0),A[-1],np.array([len(ev)],float)])
    else: feat=np.zeros(16,float)
    return ' '.join(chunks),feat

def build_v75(frame,rows,nums):
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    parts=[hv.transform(['[OBJECTIVE] '+str(x) for x in frame.learning_objective])]
    for k in ['raw','student','local','canonical','terminal']:
        parts.append(hv.transform([f'[{k.upper()}] '+r[k] for r in rows]))
    Z=np.vstack(nums); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6); parts.append(csr_matrix(Z))
    return hstack(parts,format='csr')
def build_evidence(frame,whole_text,seg_text,nums):
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    parts=[hv.transform(['[OBJECTIVE] '+str(x) for x in frame.learning_objective]),hv.transform(['[WHOLE_EVIDENCE] '+x for x in whole_text]),hv.transform(['[TARGET_EVIDENCE] '+x for x in seg_text])]
    Z=np.vstack(nums); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6); parts.append(csr_matrix(Z))
    return hstack(parts,format='csr')
def oof(X,y,sp,name):
    p=np.zeros(len(y)); fr=[]
    for k,(tr,va) in enumerate(sp,1):
        m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
        q=np.clip(m.predict_proba(X[va])[:,1],1e-5,1-1e-5); p[va]=q
        row={'fold':k,'rows':len(va),'logloss':float(log_loss(y[va],q)),'auc':float(roc_auc_score(y[va],q))}; print(name,row); fr.append(row)
    return p,fr

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True); cache={}; vr=[]; vn=[]; wt=[]; st=[]; en=[]
    for i,r in f.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
        d=cache[sid]; v,n,_=trajectory_views(d,str(r.learning_objective)); vr.append(v); vn.append(n)
        seg,_=choose_target_segment(d,str(r.learning_objective)); w,wn=evidence_view(d,str(r.learning_objective)); s,sn=evidence_view(seg,str(r.learning_objective)); wt.append(w); st.append(s); en.append(np.concatenate([wn,sn]))
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); grp=f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective; sp=folds(grp)
    Xv=build_v75(f,vr,vn); Xe=build_evidence(f,wt,st,en); pv,fv=oof(Xv,y,sp,'v75'); pe,fe=oof(Xe,y,sp,'evidence')
    grid=[]; best=None
    for w in np.linspace(0,1,41):
        q=np.clip((1-w)*pv+w*pe,1e-5,1-1e-5); ll=float(log_loss(y,q)); row={'evidence_weight':float(w),'logloss':ll}; grid.append(row); best=row if best is None or ll<best['logloss'] else best
    out={'v75_logloss':float(log_loss(y,pv)),'evidence_logloss':float(log_loss(y,pe)),'best_blend':best,'folds':{'v75':fv,'evidence':fe},'blend_grid':grid}; Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v84_student_evidence.json'); run(p.parse_args())

#!/usr/bin/env python3
"""V112 FAST RAW-OBSERVABLE SCREEN.
Frozen screen only: one shared transcript/V97 pass, deterministic 2500-row discovery sample,
objective-grouped OOF. Tests whether information discarded by V71 exists in raw transcripts.
Escalate only >= .003 V97 gain; >= .010 is phase-change candidate.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from v111_fast_residual_screen import h
from v110_residual_collider_state_discovery import hb, ll, logit, p97_predict
from v71_mastery_events import load_transcript, normalize_roles
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
EPS=1e-5
MATH=re.compile(r"\d|[+\-*/=×÷<>%]|\b(?:half|quarter|third|decimal|fraction|percent|times|divide|multiply)\b",re.I)

def texts(df,obj):
 d=normalize_roles(df).reset_index(drop=True); role=d.role_repaired.astype(str).tolist(); c=d.content.fillna('').astype(str).tolist()
 student=' '.join(x for r,x in zip(role,c) if r=='student'); tutor=' '.join(x for r,x in zip(role,c) if r=='tutor'); full=' '.join(f'[{r}] {x}' for r,x in zip(role,c))
 seg,_=choose_target_segment(df,obj); sr=normalize_roles(seg).reset_index(drop=True); local=' '.join(f'[{r}] {x}' for r,x in zip(sr.role_repaired.astype(str),sr.content.fillna('').astype(str)))
 last=' '.join(f'[{r}] {x}' for r,x in list(zip(role,c))[-8:])
 return student,tutor,full,local,last

def numvec(df):
 d=normalize_roles(df).reset_index(drop=True); role=d.role_repaired.astype(str).to_numpy(); c=d.content.fillna('').astype(str).tolist(); n=max(1,len(c)); stu=[x for r,x in zip(role,c) if r=='student']; tut=[x for r,x in zip(role,c) if r=='tutor']
 lens=np.array([len(x) for x in stu],float) if stu else np.zeros(1); words=np.array([len(x.split()) for x in stu],float) if stu else np.zeros(1)
 return np.array([len(c),len(stu),len(tut),lens.mean(),lens.max(),words.mean(),np.mean([bool(MATH.search(x)) for x in stu]) if stu else 0,np.mean(d.role_changed),len(stu)/n,len(tut)/n],float)

def sparse_oof(P,X,y,g):
 q=np.zeros(len(y)); folds=GroupKFold(min(4,len(np.unique(g))))
 for tr,va in folds.split(np.zeros(len(y)),y,g):
  m=LogisticRegression(C=.08,max_iter=180,solver='liblinear',random_state=SEED).fit(hstack([csr_matrix(logit(P[tr])[:,None]),X[tr]],format='csr'),y[tr]); q[va]=m.predict_proba(hstack([csr_matrix(logit(P[va])[:,None]),X[va]],format='csr'))[:,1]
 return np.clip(q,EPS,1-EPS)
def dense_oof(P,X,y,g):
 q=np.zeros(len(y)); folds=GroupKFold(min(4,len(np.unique(g))))
 for tr,va in folds.split(X,y,g):
  sc=StandardScaler().fit(X[tr]); m=LogisticRegression(C=.15,max_iter=180,solver='liblinear',random_state=SEED).fit(np.c_[logit(P[tr]),sc.transform(X[tr])],y[tr]); q[va]=m.predict_proba(np.c_[logit(P[va]),sc.transform(X[va])])[:,1]
 return np.clip(q,EPS,1-EPS)
def main(a):
 f=load_training(a.features,a.labels).reset_index(drop=True); print('features columns',list(f.columns),flush=True)
 obj0=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); cand=np.where(np.array([hb(x,5)!=0 for x in obj0]))[0]; ix=np.array(sorted(cand,key=lambda i:h(f.response_id.iloc[i]))[:a.rows]); f=f.iloc[ix].reset_index(drop=True)
 y=f.target.to_numpy(int); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); support=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy(); cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}
 rt=[];rz=[]; T={k:[] for k in ['STUDENT','TUTOR','FULL','LOCAL','LAST8']}; N=[]
 for _,r in f.iterrows():
  d=cache[str(r.session_id)]; t,z=segmented_control(d,str(r.learning_objective),'related');rt.append(t);rz.append(z); vals=texts(d,str(r.learning_objective));
  for k,v in zip(T,vals): T[k].append(v)
  N.append(numvec(d))
 X75=build_v75(f,cache);Xr=build_control(rt,rz);P=np.zeros(len(f));splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(f)),y,obj))
 for tr,va in splits:P[va],_=p97_predict(X75,Xr,y,tr,va,support)
 base=ll(y,P);out={'rows':len(f),'objectives':len(np.unique(obj)),'v97':base,'tests':{}}
 hv=HashingVectorizer(n_features=2**16,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
 for k,txt in T.items():
  X=hv.transform(txt);q=sparse_oof(P,X,y,obj);out['tests'][k]={'ll':ll(y,q),'gain':base-ll(y,q)}
 Xn=np.vstack(N);q=dense_oof(P,Xn,y,obj);out['tests']['STRUCTURE']={'ll':ll(y,q),'gain':base-ll(y,q)}
 # Combined raw views: cheap union, tests whether complementary raw observables jointly matter.
 X=hstack([hv.transform(T['STUDENT']),hv.transform(T['TUTOR']),hv.transform(T['LOCAL']),csr_matrix(StandardScaler().fit_transform(Xn))],format='csr');q=sparse_oof(P,X,y,obj);out['tests']['COMBINED']={'ll':ll(y,q),'gain':base-ll(y,q)}
 # Tight collision geometry from the same frozen predictions.
 ds=[]
 for o in np.unique(obj):
  z=np.where(obj==o)[0];a0=z[y[z]==0];a1=z[y[z]==1]
  if len(a0) and len(a1):
   p1=np.sort(P[a1]);ds.extend(float(np.min(np.abs(p1-P[i]))) for i in a0)
 out['tight_collisions']={'basis':len(ds),'median_dp':float(np.median(ds)) if ds else None,'p10_dp':float(np.quantile(ds,.1)) if ds else None}
 gains={k:v['gain'] for k,v in out['tests'].items()};win=max(gains,key=gains.get);g=gains[win];out['decision']={'winner':win,'winner_gain':g,'verdict':'PHASE_CHANGE_CANDIDATE' if g>=.01 else 'ESCALATE_RAW_OBSERVABLE' if g>=.003 else 'RAW_TRANSCRIPT_NOT_SEPARATING','rule':'Escalate >=.003; phase-change candidate >=.010; otherwise audit non-text metadata/test-regime/applicability.'}
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v112_fast_raw_observable_screen.json');main(p.parse_args())

#!/usr/bin/env python3
"""V100 Phase A: leakage-safe calibrated meta-stacker.

V99 asks which expert wins. V100 preserves probability/loss magnitude by learning
P(correct) directly from INNER-OOF V75/RELATED predictions plus runtime-visible
support/disagreement context. Outer objective-cold folds remain untouched.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from v71_mastery_events import load_transcript,tokens
from v75_canonical_trajectory import load_training,SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups,obj_family
from v94_related_control import segmented_control,build_control

EPS=1e-5

def expert(X,y,tr,va):
 m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
 return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)

def counts(tr,va,v):
 u,n=np.unique(v[tr],return_counts=True); d=dict(zip(u,n)); return np.asarray([d.get(v[i],0) for i in va],float)

def meta(p0,pr,ec,fc,sc,turns,olen):
 p0=np.asarray(p0); pr=np.asarray(pr); d=pr-p0
 return np.column_stack([p0,pr,d,np.abs(d),p0*pr,p0*p0,pr*pr,
  np.abs(p0-.5),np.abs(pr-.5),np.log1p(ec),np.log1p(fc),np.log1p(sc),np.log1p(turns),np.log1p(olen)])

def run(a):
 f=load_training(a.features,a.labels).reset_index(drop=True)
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in f.session_id.astype(str).unique()}
 rt=[];rz=[]
 for i,r in f.iterrows():
  t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t);rz.append(z)
  if (i+1)%2500==0: print('rows',i+1)
 X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
 obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
 key=f.learning_objective.astype(str).to_numpy(); fam=f.learning_objective.astype(str).map(obj_family).astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
 turns=np.asarray([len(cache[str(s)]) for s in sess],float); olen=np.asarray([len(tokens(x)) for x in key],float)
 outer=folds_from_groups(obj); P0=np.zeros(len(y)); PR=np.zeros(len(y)); PS=np.zeros(len(y)); P97=np.zeros(len(y)); folds=[]
 for k,(tr,va) in enumerate(outer,1):
  print('OUTER',k,len(tr),len(va)); p0=expert(X0,y,tr,va); pr=expert(Xr,y,tr,va); P0[va]=p0;PR[va]=pr
  inner=list(GroupKFold(3).split(np.zeros(len(tr)),y[tr],obj[tr])); M=np.zeros((len(tr),14))
  for j,(itl,ivl) in enumerate(inner,1):
   it=tr[itl]; iv=tr[ivl]; q0=expert(X0,y,it,iv); qr=expert(Xr,y,it,iv)
   M[ivl]=meta(q0,qr,counts(it,iv,key),counts(it,iv,fam),counts(it,iv,sess),turns[iv],olen[iv]); print(' inner',j,len(iv))
  stack=HistGradientBoostingClassifier(loss='log_loss',max_depth=2,max_iter=100,learning_rate=.04,min_samples_leaf=120,l2_regularization=2.0,random_state=SEED)
  stack.fit(M,y[tr])
  MV=meta(p0,pr,counts(tr,va,key),counts(tr,va,fam),counts(tr,va,sess),turns[va],olen[va]); ps=np.clip(stack.predict_proba(MV)[:,1],EPS,1-EPS); PS[va]=ps
  ec=counts(tr,va,key); w=np.where(ec==0,.35,0.0); p97=np.clip((1-w)*p0+w*pr,EPS,1-EPS);P97[va]=p97
  r={'fold':k,'v75':float(log_loss(y[va],p0)),'related':float(log_loss(y[va],pr)),'v97':float(log_loss(y[va],p97)),'v100':float(log_loss(y[va],ps))};folds.append(r);print(r)
 ll0=float(log_loss(y,P0)); llr=float(log_loss(y,PR)); ll97=float(log_loss(y,P97)); lls=float(log_loss(y,PS)); gain=ll97-lls
 verdict='PROMOTE_TO_FOUR_WORLD_V100' if gain>=.002 else ('REFINE_STACKER' if gain>=.0005 else 'SUPPRESS_THIS_STACKER')
 out={'primary':'objective-cold nested calibrated stacker','v75':ll0,'related':llr,'v97':ll97,'v100_stacker':lls,'gain_vs_v97':gain,'folds':folds,'decision':{'verdict':verdict,'precommit':'promote only if nested objective-cold gain vs V97 >= 0.002'}}
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',default='v100_nested_stacker.json');run(p.parse_args())

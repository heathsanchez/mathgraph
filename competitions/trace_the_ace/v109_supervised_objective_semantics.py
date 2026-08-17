#!/usr/bin/env python3
"""V109: supervised semantic objective-difficulty model composed with frozen V97."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
EPS=1e-5

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))
def bucket(x,n=5): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)%n
def folds(g,n=5):
 g=np.asarray(g).astype(str); i=np.arange(len(g)); b=np.array([bucket(x,n) for x in g]); return [(i[b!=k],i[b==k]) for k in range(n) if np.any(b==k) and np.any(b!=k)]
def mixed(obj,sess,n=5):
 i=np.arange(len(obj)); ob=np.array([bucket(x,n) for x in obj]); sb=np.array([bucket(x,n) for x in sess]); out=[]
 for k in range(n):
  m=(ob==k)|((ob!=k)&(sb==k));
  if np.any(m) and np.any(~m): out.append((i[~m],i[m]))
 return out
def unseen(keys,tr,va):
 s=set(keys[tr]); return np.array([keys[i] not in s for i in va],bool)
def fitp(X,y,tr,va):
 m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr]); return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)
def semantic_predict(text,y,tr,va):
 trtxt=[text[i] for i in tr]; vatxt=[text[i] for i in va]; cw=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=120000,sublinear_tf=True); ww=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=50000,sublinear_tf=True); A=hstack([cw.fit_transform(trtxt),ww.fit_transform(trtxt)],format='csr'); B=hstack([cw.transform(vatxt),ww.transform(vatxt)],format='csr'); m=LogisticRegression(C=.8,max_iter=300,solver='liblinear',random_state=SEED).fit(A,y[tr]); return np.clip(m.predict_proba(B)[:,1],EPS,1-EPS)
def run(a):
 f=load_training(a.features,a.labels).reset_index(drop=True); cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in f.session_id.astype(str).unique()}; rt=[]; rz=[]
 for j,r in f.iterrows():
  t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
  if (j+1)%2500==0: print('rows',j+1,flush=True)
 X75=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int); text=f.learning_objective.fillna('').astype(str).tolist(); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); sup=f.learning_objective.astype(str).to_numpy(); ses=f.session_id.astype(str).to_numpy(); worlds={'objective_cold':folds(obj),'session_cold':folds(ses),'mixed_support':mixed(obj,ses)}; out={'law':'seen=.75 V75+.25 SEM; unseen=.85 V97+.15 SEM','worlds':{}}; gains=[]
 for name,sp in worlds.items():
  a0=np.zeros(len(y)); a1=np.zeros(len(y)); cov=np.zeros(len(y),bool); fs=[]
  for k,(tr,va) in enumerate(sp,1):
   p75=fitp(X75,y,tr,va); pr=fitp(Xr,y,tr,va); ps=semantic_predict(text,y,tr,va); u=unseen(sup,tr,va); q0=np.where(u,.65*p75+.35*pr,p75); q1=np.where(u,.85*q0+.15*ps,.75*p75+.25*ps); a0[va]=q0; a1[va]=q1; cov[va]=1; rec={'fold':k,'v97':ll(y[va],q0),'v109':ll(y[va],q1),'semantic':ll(y[va],ps),'gain':ll(y[va],q0)-ll(y[va],q1)}; fs.append(rec); print(name,rec,flush=True)
  rec={'v97':ll(y[cov],a0[cov]),'v109':ll(y[cov],a1[cov]),'gain_vs_v97':ll(y[cov],a0[cov])-ll(y[cov],a1[cov]),'folds':fs}; out['worlds'][name]=rec; gains.append(rec['gain_vs_v97'])
 g=np.array(gains); out['decision']={'mean_gain':float(g.mean()),'verdict':'STRUCTURAL_PROMOTE_V109' if g.mean()>=.003 and g.min()>=0 and out['worlds']['mixed_support']['gain_vs_v97']>=.002 else 'SUPPRESS_V109','precommit':'mean>=.003, mixed>=.002, no negative world'}; Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v109.json'); run(p.parse_args())

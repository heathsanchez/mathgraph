#!/usr/bin/env python3
"""V108: explicit objective x transcript interactions dropped into frozen V97."""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from v71_mastery_events import load_transcript, tokens
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
def role_terms(df,role,cap):
 c=Counter(); [c.update(tokens(x)) for x in df.loc[df.role.astype(str).str.lower()==role,'content'].fillna('').astype(str)]; return [w for w,_ in c.most_common(cap)]
def cross_doc(df,obj):
 ot=sorted(tokens(obj))[:16] or ['_objective_']; st=role_terms(df,'student',72); tt=role_terms(df,'tutor',48); p=[]
 for o in ot: p += [f'O={o}|S={x}' for x in st]+[f'O={o}|T={x}' for x in tt]
 return ' '.join(p)
def run(a):
 f=load_training(a.features,a.labels).reset_index(drop=True); cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in f.session_id.astype(str).unique()}; rt=[]; rz=[]; docs=[]
 for j,r in f.iterrows():
  s=str(r.session_id); o=str(r.learning_objective); t,z=segmented_control(cache[s],o,'related'); rt.append(t); rz.append(z); docs.append(cross_doc(cache[s],o));
  if (j+1)%2500==0: print('rows',j+1,flush=True)
 X75=build_v75(f,cache); Xr=build_control(rt,rz); Xi=HashingVectorizer(n_features=2**20,alternate_sign=False,norm='l2',analyzer=str.split,lowercase=False).transform(docs); X=hstack([X75,Xi],format='csr')
 y=f.target.to_numpy(int); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); sup=f.learning_objective.astype(str).to_numpy(); ses=f.session_id.astype(str).to_numpy(); worlds={'objective_cold':folds(obj),'session_cold':folds(ses),'mixed_support':mixed(obj,ses)}; out={'worlds':{}}; gains=[]
 for name,sp in worlds.items():
  a0=np.zeros(len(y)); a1=np.zeros(len(y)); cov=np.zeros(len(y),bool); fs=[]
  for k,(tr,va) in enumerate(sp,1):
   p75=fitp(X75,y,tr,va); p108=fitp(X,y,tr,va); pr=fitp(Xr,y,tr,va); u=unseen(sup,tr,va); q0=np.where(u,.65*p75+.35*pr,p75); q1=np.where(u,.65*p108+.35*pr,p108); a0[va]=q0; a1[va]=q1; cov[va]=1; rec={'fold':k,'v97':ll(y[va],q0),'v108':ll(y[va],q1),'gain':ll(y[va],q0)-ll(y[va],q1)}; fs.append(rec); print(name,rec,flush=True)
  rec={'v97':ll(y[cov],a0[cov]),'v108':ll(y[cov],a1[cov]),'gain_vs_v97':ll(y[cov],a0[cov])-ll(y[cov],a1[cov]),'folds':fs}; out['worlds'][name]=rec; gains.append(rec['gain_vs_v97'])
 g=np.array(gains); out['decision']={'mean_gain':float(g.mean()),'verdict':'STRUCTURAL_PROMOTE_V108' if g.mean()>=.003 and g.min()>=0 and out['worlds']['mixed_support']['gain_vs_v97']>=.002 else 'SUPPRESS_V108','precommit':'mean>=.003, mixed>=.002, no negative world'}; Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v108.json'); run(p.parse_args())

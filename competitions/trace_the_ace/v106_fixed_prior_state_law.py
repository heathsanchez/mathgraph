#!/usr/bin/env python3
"""V106: independent confirmation of a fixed V105-derived runtime law.

Precommitted after V105, before inspecting these fresh hash-fold results:
  seen objective:   0.80 V75 + 0.20 V74
  unseen objective: 0.50 V75 + 0.20 V74 + 0.30 RELATED

Comparator is frozen V97:
  seen objective:   1.00 V75
  unseen objective: 0.65 V75 + 0.35 RELATED

V106 deliberately changes validation geometry from V105's GroupKFold ordering to
stable SHA256 hash partitions. No weights are selected from V106 labels.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

from v71_mastery_events import load_transcript
from v74_semantic_objective_prior import semantic_prior_predict
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import obj_family, style_matrix
from v94_related_control import segmented_control, build_control

EPS=1e-5
W74=0.20
WR=0.30
V97_WR=0.35
N=5

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))
def hfold(x,salt='v106'):
    b=(salt+'|'+str(x)).encode('utf-8')
    return int(hashlib.sha256(b).hexdigest()[:12],16)%N

def folds_hash(groups,salt):
    g=np.asarray(groups).astype(str); idx=np.arange(len(g)); a=np.asarray([hfold(x,salt) for x in g])
    return [(idx[a!=k],idx[a==k]) for k in range(N)]

def mixed_hash(obj,sess):
    obj=np.asarray(obj).astype(str); sess=np.asarray(sess).astype(str); idx=np.arange(len(obj))
    of=np.asarray([hfold(x,'v106-mixed-obj') for x in obj]); sf=np.asarray([hfold(x,'v106-mixed-sess') for x in sess])
    out=[]
    for k in range(N):
        cold=of==k
        session_seen=(of!=k)&(sf==k)
        va=idx[cold|session_seen]; tr=idx[~(cold|session_seen)]
        out.append((tr,va))
    return out

def fit_lr(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)
def unseen_mask(keys,tr,va):
    seen=set(keys[tr].tolist()); return np.asarray([keys[i] not in seen for i in va],bool)
def v97(p75,pr,u):
    w=np.where(u,V97_WR,0.0); return np.clip((1-w)*p75+w*pr,EPS,1-EPS)
def v106(p75,p74,pr,u):
    rw=np.where(u,WR,0.0); return np.clip((1-W74-rw)*p75+W74*p74+rw*pr,EPS,1-EPS)

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1,flush=True)
    X75=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    support=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
    fam=f.learning_objective.astype(str).map(obj_family).astype(str).to_numpy()
    style=KMeans(n_clusters=5,random_state=137,n_init=10).fit(style_matrix(f,cache)).labels_.astype(str)
    worlds={
      'objective_cold':folds_hash(obj,'v106-obj'),
      'session_cold':folds_hash(sess,'v106-sess'),
      'objective_family_cold':folds_hash(fam,'v106-fam'),
      'style_cold':folds_hash(style,'v106-style'),
      'mixed_support':mixed_hash(obj,sess),
    }
    out={'primary':'fixed V105-derived law on fresh hash folds','law':{'w74_all':W74,'wr_unseen':WR},'comparator':{'v97_wr_unseen':V97_WR},'worlds':{}}
    gains=[]
    for name,sp in worlds.items():
        P75=np.zeros(len(y)); P97=np.zeros(len(y)); P106=np.zeros(len(y)); U=np.zeros(len(y),bool); folds=[]
        for k,(tr,va) in enumerate(sp,1):
            if not len(va): continue
            p75=fit_lr(X75,y,tr,va); pr=fit_lr(Xr,y,tr,va); p74,_=semantic_prior_predict(f.iloc[tr],f.iloc[va])
            u=unseen_mask(support,tr,va); q97=v97(p75,pr,u); q106=v106(p75,p74,pr,u)
            P75[va]=p75; P97[va]=q97; P106[va]=q106; U[va]=u
            row={'fold':k,'rows':int(len(va)),'unseen_fraction':float(u.mean()),'v75':ll(y[va],p75),'v97':ll(y[va],q97),'v106':ll(y[va],q106),'gain_vs_v97':ll(y[va],q97)-ll(y[va],q106)}
            folds.append(row); print(name,row,flush=True)
        used=P106>0
        rec={'rows':int(used.sum()),'unseen_fraction':float(U[used].mean()),'v75':ll(y[used],P75[used]),'v97':ll(y[used],P97[used]),'v106':ll(y[used],P106[used]),'gain_vs_v97':ll(y[used],P97[used])-ll(y[used],P106[used]),'folds':folds}
        out['worlds'][name]=rec; gains.append(rec['gain_vs_v97']); print(name,'SUMMARY',rec,flush=True)
    g=np.asarray(gains); mixed=out['worlds']['mixed_support']['gain_vs_v97']; session=out['worlds']['session_cold']['gain_vs_v97']; objg=out['worlds']['objective_cold']['gain_vs_v97']
    promote=(g.mean()>=.0005 and mixed>=.0005 and session>=0 and g.min()>=-.0005)
    out['decision']={'mean_gain_vs_v97':float(g.mean()),'mixed_gain_vs_v97':float(mixed),'session_gain_vs_v97':float(session),'objective_gain_vs_v97':float(objg),'worst_gain_vs_v97':float(g.min()),'verdict':'BUILD_V106_RUNTIME' if promote else 'KEEP_V97','precommit':'build iff mean gain vs V97 >= .0005, mixed >= .0005, session >= 0, worst world >= -.0005'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v106_fixed_prior_state_law.json'); run(p.parse_args())

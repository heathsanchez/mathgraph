#!/usr/bin/env python3
"""V107: support-conditioned V74 prior on top of frozen V97.

Hypothesis from V106: V74 helps supported/seen-objective regimes but hurts exact-unseen
objectives. Preserve V97 exactly on unseen objectives and add a small fixed V74 prior
only when the exact objective has fold-local training support.

This is a fixed-law confirmation: no labels select weights.
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
W_V97_UNSEEN=0.35
W74_SEEN=0.20


def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))
def fit_lr(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)
def bucket(x,n=5):
    h=int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
    return h % n
def hash_folds(groups,n=5):
    g=np.asarray(groups).astype(str); idx=np.arange(len(g)); out=[]
    gb=np.asarray([bucket(x,n) for x in g])
    for k in range(n):
        va=idx[gb==k]; tr=idx[gb!=k]; out.append((tr,va))
    return out
def mixed_support_folds(obj,sess,n=5):
    idx=np.arange(len(obj)); ob=np.asarray([bucket(x,n) for x in obj]); sb=np.asarray([bucket(x,n) for x in sess]); out=[]
    for k in range(n):
        cold=ob==k
        seen_session=(ob!=k)&(sb==k)
        va=idx[cold|seen_session]; tr=idx[~(cold|seen_session)]; out.append((tr,va))
    return out
def unseen_mask(keys,tr,va):
    seen=set(keys[tr].tolist()); return np.asarray([keys[i] not in seen for i in va],bool)

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
      'objective_cold':hash_folds(obj),
      'session_cold':hash_folds(sess),
      'objective_family_cold':hash_folds(fam),
      'style_cold':hash_folds(style),
      'mixed_support':mixed_support_folds(obj,sess),
    }
    out={'law':{'unseen':'V97 = .65 V75 + .35 RELATED','seen':'0.80 V75 + 0.20 V74'},'worlds':{}}
    gains=[]
    for name,sp in worlds.items():
        p97=np.zeros(len(y)); p107=np.zeros(len(y)); U=np.zeros(len(y),bool); folds=[]
        for k,(tr,va) in enumerate(sp,1):
            p75=fit_lr(X75,y,tr,va); pr=fit_lr(Xr,y,tr,va); p74,_=semantic_prior_predict(f.iloc[tr],f.iloc[va])
            uns=unseen_mask(support,tr,va); U[va]=uns
            q97=np.where(uns,.65*p75+.35*pr,p75)
            q107=np.where(uns,q97,.80*p75+.20*p74)
            q97=np.clip(q97,EPS,1-EPS); q107=np.clip(q107,EPS,1-EPS)
            p97[va]=q97; p107[va]=q107
            folds.append({'fold':k,'rows':int(len(va)),'unseen_fraction':float(uns.mean()),'v97':ll(y[va],q97),'v107':ll(y[va],q107),'gain':ll(y[va],q97)-ll(y[va],q107)})
            print(name,folds[-1],flush=True)
        rec={'v97':ll(y,p97),'v107':ll(y,p107),'gain_vs_v97':ll(y,p97)-ll(y,p107),'unseen_fraction':float(U.mean()),'folds':folds}
        out['worlds'][name]=rec; gains.append(rec['gain_vs_v97']); print(name,'SUMMARY',rec,flush=True)
    g=np.asarray(gains,float); mixed=out['worlds']['mixed_support']['gain_vs_v97']; session=out['worlds']['session_cold']['gain_vs_v97']; objg=out['worlds']['objective_cold']['gain_vs_v97']
    promote=(g.mean()>=.0005 and mixed>=.0003 and session>=.0003 and objg>=-.0002 and g.min()>=-.0003)
    out['decision']={'mean_gain_vs_v97':float(g.mean()),'mixed_support_gain':float(mixed),'session_cold_gain':float(session),'objective_cold_gain':float(objg),'worst_gain':float(g.min()),'verdict':'PROMOTE_V107_RUNTIME' if promote else 'KEEP_V97','precommit':'promote iff mean >= .0005, mixed >= .0003, session >= .0003, objective >= -.0002, worst >= -.0003'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v107_support_conditioned_prior.json'); run(p.parse_args())

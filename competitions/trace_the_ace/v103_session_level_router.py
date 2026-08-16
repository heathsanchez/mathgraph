#!/usr/bin/env python3
"""V103: nested session-level applicability router.

V102 showed applicability gain appears primarily at session resolution. This test learns
one RELATED blend weight per session from runtime-visible unlabeled session evidence and
aggregate V75/RELATED disagreement. Outer objective-cold folds remain untouched.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript, tokens
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups
from v94_related_control import segmented_control, build_control

EPS=1e-5
GRID=np.array([0.,.15,.25,.35,.45,.60,1.0])


def fit_expert(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)


def best_weight(y,p0,pr,idx):
    best=(1e99,.35)
    for w in GRID:
        q=np.clip((1-w)*p0[idx]+w*pr[idx],EPS,1-EPS)
        v=float(log_loss(y[idx],q,labels=[0,1]))
        if v<best[0]: best=(v,float(w))
    return best[1]


def session_features(p0,pr,idx,turns,obj_len,n_objectives):
    a=p0[idx]; b=pr[idx]; d=b-a
    return np.array([
        len(idx), np.mean(a), np.mean(b), np.mean(np.abs(d)), np.std(d),
        np.mean(d), np.mean(np.abs(d)>.03), np.mean(np.abs(d)>.06), np.mean(np.abs(d)>.10),
        np.mean(np.abs(a-.5)), np.mean(np.abs(b-.5)),
        np.mean(turns[idx]), np.mean(obj_len[idx]), float(n_objectives)
    ],float)


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1,flush=True)
    X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy(); text=f.learning_objective.astype(str).to_numpy()
    turns=np.asarray([len(cache[str(s)]) for s in sess],float)
    obj_len=np.asarray([len(tokens(x)) for x in text],float)

    p0_all=np.zeros(len(y)); pr_all=np.zeros(len(y)); p97_all=np.zeros(len(y)); p103_all=np.zeros(len(y))
    folds=[]
    for k,(tr,va) in enumerate(folds_from_groups(obj),1):
        p0=fit_expert(X0,y,tr,va); pr=fit_expert(Xr,y,tr,va)
        p0_all[va]=p0; pr_all[va]=pr

        # Inner objective-grouped OOF predictions on outer-train only.
        ip0=np.zeros(len(tr)); ipr=np.zeros(len(tr))
        inner=GroupKFold(min(3,len(np.unique(obj[tr])))).split(np.zeros(len(tr)),y[tr],obj[tr])
        for itr_l,iva_l in inner:
            itr=tr[itr_l]; iva=tr[iva_l]
            ip0[iva_l]=fit_expert(X0,y,itr,iva); ipr[iva_l]=fit_expert(Xr,y,itr,iva)

        train_sessions=np.unique(sess[tr]); Z=[]; target=[]
        for s in train_sessions:
            loc=np.where(sess[tr]==s)[0]
            nobj=len(np.unique(obj[tr][loc]))
            Z.append(session_features(ip0,ipr,loc,turns[tr],obj_len[tr],nobj))
            target.append(best_weight(y[tr],ip0,ipr,loc))
        Z=np.vstack(Z); target=np.asarray(target)
        mu=Z.mean(0); sd=Z.std(0)+1e-6
        reg=HistGradientBoostingRegressor(max_depth=2,max_iter=120,learning_rate=.04,min_samples_leaf=40,
                l2_regularization=2.0,random_state=SEED).fit((Z-mu)/sd,target)

        w=np.zeros(len(va))
        for s in np.unique(sess[va]):
            loc=np.where(sess[va]==s)[0]
            nobj=len(np.unique(obj[va][loc]))
            z=session_features(p0,pr,loc,turns[va],obj_len[va],nobj).reshape(1,-1)
            ws=float(np.clip(reg.predict((z-mu)/sd)[0],0,.60))
            w[loc]=ws
        q103=np.clip((1-w)*p0+w*pr,EPS,1-EPS); p103_all[va]=q103
        q97=np.clip(.65*p0+.35*pr,EPS,1-EPS); p97_all[va]=q97
        folds.append({'fold':k,'v97':float(log_loss(y[va],q97)),'v103':float(log_loss(y[va],q103)),
                      'gain':float(log_loss(y[va],q97)-log_loss(y[va],q103)),'mean_weight':float(w.mean())})
        print(folds[-1],flush=True)

    ll97=float(log_loss(y,p97_all)); ll103=float(log_loss(y,p103_all)); gain=ll97-ll103
    l0=-(y*np.log(p0_all)+(1-y)*np.log(1-p0_all)); lr=-(y*np.log(pr_all)+(1-y)*np.log(1-pr_all))
    oracle=float(np.mean(np.minimum(l0,lr)))
    verdict='PROMOTE_TO_FOUR_WORLD_V103' if gain>=.002 else ('REFINE_SESSION_ROUTER' if gain>=.0005 else 'SUPPRESS_SESSION_ROUTER')
    out={'primary':'nested session-level applicability router','v97':ll97,'v103':ll103,'gain_vs_v97':gain,
         'row_endpoint_oracle':oracle,'folds':folds,
         'decision':{'verdict':verdict,'precommit':'promote only if objective-cold gain vs frozen V97 >= 0.002'}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v103_session_level_router.json'); run(p.parse_args())

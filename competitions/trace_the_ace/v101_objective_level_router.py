#!/usr/bin/env python3
"""V101: nested objective-level applicability router.

Residual from V99/V100: row-level gates failed while the endpoint oracle remains huge.
Hypothesis: applicability lives at the objective level, not the individual row.

Outer objective-cold folds are untouched evaluation. Inner OOF expert predictions on
outer-train objectives are aggregated by objective. A small objective-level regressor
predicts a single RELATED blend weight for each unseen outer objective using only
runtime-visible objective text and unlabeled aggregate expert behavior.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript, tokens
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups
from v94_related_control import segmented_control, build_control

EPS=1e-5
GRID=np.array([0.0,0.15,0.25,0.35,0.45,0.60])


def fit_expert(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)


def obj_numeric(p0,pr,idx,turns,obj_len):
    a=p0[idx]; b=pr[idx]; d=b-a
    return np.array([
        len(idx), a.mean(), b.mean(), np.mean(np.abs(d)), np.std(d),
        np.mean(np.abs(a-.5)), np.mean(np.abs(b-.5)),
        np.mean(d>0), np.mean(np.abs(d)>.05), np.mean(np.abs(d)>.10),
        np.mean(turns[idx]), np.mean(obj_len[idx])
    ],float)


def best_weight(y,p0,pr,idx):
    best=(1e9,0.35)
    for w in GRID:
        q=np.clip((1-w)*p0[idx]+w*pr[idx],EPS,1-EPS)
        ll=float(log_loss(y[idx],q,labels=[0,1]))
        if ll<best[0]: best=(ll,float(w))
    return best[1]


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related')
        rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1)
    X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    text=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
    turns=np.asarray([len(cache[str(s)]) for s in sess],float)
    obj_len=np.asarray([len(tokens(x)) for x in text],float)
    outer=folds_from_groups(obj)
    hv=HashingVectorizer(n_features=2**12,alternate_sign=False,norm='l2',analyzer='char_wb',ngram_range=(3,5),lowercase=True)

    p0_all=np.zeros(len(y)); pr_all=np.zeros(len(y)); pv97_all=np.zeros(len(y)); pv101_all=np.zeros(len(y))
    rows=[]
    for k,(tr,va) in enumerate(outer,1):
        p0=fit_expert(X0,y,tr,va); pr=fit_expert(Xr,y,tr,va); p0_all[va]=p0; pr_all[va]=pr

        # Inner OOF expert predictions for training objective-level router.
        inner=GroupKFold(min(3,len(np.unique(obj[tr])))).split(np.zeros(len(tr)),y[tr],obj[tr])
        ip0=np.zeros(len(tr)); ipr=np.zeros(len(tr))
        for itr_l,iva_l in inner:
            itr=tr[itr_l]; iva=tr[iva_l]
            ip0[iva_l]=fit_expert(X0,y,itr,iva); ipr[iva_l]=fit_expert(Xr,y,itr,iva)

        train_objs=np.unique(obj[tr]); tr_text=[]; tr_num=[]; target=[]
        for g in train_objs:
            loc=np.where(obj[tr]==g)[0]
            idx_global=tr[loc]
            tr_text.append(str(text[idx_global[0]]))
            tr_num.append(obj_numeric(ip0,ipr,loc,turns[tr],obj_len[tr]))
            target.append(best_weight(y[tr],ip0,ipr,loc))
        T=hv.transform(tr_text); Z=np.vstack(tr_num); mu=Z.mean(0); sd=Z.std(0)+1e-6
        XR=hstack([T,csr_matrix((Z-mu)/sd)],format='csr')
        reg=Ridge(alpha=10.0,random_state=SEED).fit(XR,np.asarray(target))

        pred_w=np.zeros(len(va)); objective_weights={}
        for g in np.unique(obj[va]):
            loc=np.where(obj[va]==g)[0]; idx_global=va[loc]
            z=obj_numeric(p0,pr,loc,turns[va],obj_len[va]).reshape(1,-1)
            xx=hstack([hv.transform([str(text[idx_global[0]])]),csr_matrix((z-mu)/sd)],format='csr')
            w=float(np.clip(reg.predict(xx)[0],0,.60)); pred_w[loc]=w; objective_weights[str(g)]=w
        q=np.clip((1-pred_w)*p0+pred_w*pr,EPS,1-EPS); pv101_all[va]=q
        q97=np.clip(.65*p0+.35*pr,EPS,1-EPS); pv97_all[va]=q97
        rows.append({'fold':k,'v75':float(log_loss(y[va],p0)),'v97':float(log_loss(y[va],q97)),
                     'v101':float(log_loss(y[va],q)),'mean_weight':float(pred_w.mean()),
                     'objective_weight_min':float(min(objective_weights.values())),'objective_weight_max':float(max(objective_weights.values()))})
        print(rows[-1])

    ll0=float(log_loss(y,p0_all)); ll97=float(log_loss(y,pv97_all)); ll101=float(log_loss(y,pv101_all))
    l0=-(y*np.log(p0_all)+(1-y)*np.log(1-p0_all)); lr=-(y*np.log(pr_all)+(1-y)*np.log(1-pr_all))
    oracle=float(log_loss(y,np.where(lr<l0,pr_all,p0_all)))
    gain=ll97-ll101
    verdict='PROMOTE_TO_FOUR_WORLD_V101' if gain>=.002 else ('REFINE_OBJECTIVE_ROUTER' if gain>=.0005 else 'SUPPRESS_OBJECTIVE_ROUTER')
    out={'primary':'nested objective-level applicability router','v75':ll0,'v97':ll97,'v101':ll101,
         'gain_vs_v97':gain,'diagnostic_endpoint_oracle':oracle,'folds':rows,
         'decision':{'verdict':verdict,'precommit':'promote only if objective-cold gain vs frozen V97 >= 0.002'}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v101_objective_level_router.json'); run(p.parse_args())

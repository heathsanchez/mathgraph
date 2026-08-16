#!/usr/bin/env python3
"""V99 Phase A: leakage-safe learned expert applicability gate.

Question: can runtime-visible evidence predict when RELATED beats V75 on objective-cold
rows, recovering material V91 oracle complementarity beyond frozen V97?

Discipline:
- Outer objective-cold folds are untouched evaluation.
- Gate training features use INNER out-of-fold expert predictions only.
- Outer expert predictions are produced by models fit only on outer-train rows.
- No leaderboard/test labels or outer-validation labels enter fitting or tuning.
- One fixed conservative gate architecture and blend law; no sweep.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript, tokens
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups, obj_family
from v94_related_control import segmented_control, build_control

EPS=1e-5
GATE_SCALE=.65


def fit_expert(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)


def counts_for(train_idx, eval_idx, values):
    u,n=np.unique(values[train_idx],return_counts=True); d=dict(zip(u,n))
    return np.asarray([d.get(values[i],0) for i in eval_idx],float)


def gate_features(p0,pr,exact_count,family_count,session_count,turns,obj_len):
    p0=np.asarray(p0); pr=np.asarray(pr)
    # Every feature is available at runtime before observing the target label.
    return np.column_stack([
        p0,pr,np.abs(pr-p0),pr-p0,
        np.abs(p0-.5),np.abs(pr-.5),
        np.log1p(exact_count),np.log1p(family_count),np.log1p(session_count),
        np.log1p(turns),np.log1p(obj_len),
    ])


def row_loss(y,p):
    return -(y*np.log(p)+(1-y)*np.log(1-p))


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
    key=f.learning_objective.astype(str).to_numpy()
    fam=f.learning_objective.astype(str).map(obj_family).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy()
    turns=np.asarray([len(cache[str(s)]) for s in sess],float)
    obj_len=np.asarray([len(tokens(x)) for x in key],float)
    outer=folds_from_groups(obj)

    p0_all=np.zeros(len(y)); pr_all=np.zeros(len(y)); pg_all=np.zeros(len(y)); pv97_all=np.zeros(len(y))
    fold_rows=[]
    for k,(tr,va) in enumerate(outer,1):
        print('OUTER',k,'train',len(tr),'val',len(va))
        p0=fit_expert(X0,y,tr,va); pr=fit_expert(Xr,y,tr,va)
        p0_all[va]=p0; pr_all[va]=pr

        # Inner OOF expert predictions on outer-train only.
        inner_groups=obj[tr]; n_inner=min(3,len(np.unique(inner_groups)))
        inner=GroupKFold(n_inner).split(np.zeros(len(tr)),y[tr],inner_groups)
        ip0=np.zeros(len(tr)); ipr=np.zeros(len(tr)); G=np.zeros((len(tr),11))
        for j,(itr_local,iva_local) in enumerate(inner,1):
            itr=tr[itr_local]; iva=tr[iva_local]
            q0=fit_expert(X0,y,itr,iva); qr=fit_expert(Xr,y,itr,iva)
            ip0[iva_local]=q0; ipr[iva_local]=qr
            ec=counts_for(itr,iva,key); fc=counts_for(itr,iva,fam); sc=counts_for(itr,iva,sess)
            G[iva_local]=gate_features(q0,qr,ec,fc,sc,turns[iva],obj_len[iva])
            print(' inner',j,'n',len(iva))

        l0=row_loss(y[tr],ip0); lr=row_loss(y[tr],ipr)
        gy=(lr<l0).astype(int); sw=np.abs(l0-lr)+.01
        if len(np.unique(gy))<2:
            gate_prob=np.full(len(va),float(gy[0]))
        else:
            gate=HistGradientBoostingClassifier(max_depth=2,max_iter=80,learning_rate=.05,
                    min_samples_leaf=100,l2_regularization=1.0,random_state=SEED)
            gate.fit(G,gy,sample_weight=sw)
            ec=counts_for(tr,va,key); fc=counts_for(tr,va,fam); sc=counts_for(tr,va,sess)
            GV=gate_features(p0,pr,ec,fc,sc,turns[va],obj_len[va])
            gate_prob=gate.predict_proba(GV)[:,1]

        w=np.clip(GATE_SCALE*gate_prob,0,GATE_SCALE)
        pg=np.clip((1-w)*p0+w*pr,EPS,1-EPS); pg_all[va]=pg
        ec_outer=counts_for(tr,va,key)
        w97=np.where(ec_outer==0,.35,0.0)
        pv97=np.clip((1-w97)*p0+w97*pr,EPS,1-EPS); pv97_all[va]=pv97
        fold_rows.append({'fold':k,'v75':float(log_loss(y[va],p0)),'related':float(log_loss(y[va],pr)),
                          'v97':float(log_loss(y[va],pv97)),'v99_gate':float(log_loss(y[va],pg)),
                          'mean_gate_weight':float(w.mean()),'ability_win_rate_inner':float(gy.mean())})
        print(fold_rows[-1])

    ll0=float(log_loss(y,p0_all)); llr=float(log_loss(y,pr_all)); ll97=float(log_loss(y,pv97_all)); llg=float(log_loss(y,pg_all))
    l0=row_loss(y,p0_all); lr=row_loss(y,pr_all)
    oracle=np.where(lr<l0,pr_all,p0_all); llor=float(log_loss(y,oracle))
    gain=ll97-llg; oracle_gap=ll97-llor; recovery=gain/oracle_gap if oracle_gap>0 else 0.0
    verdict='PROMOTE_TO_FOUR_WORLD_V99' if gain>=.002 else ('REFINE_GATE' if gain>=.0005 else 'SUPPRESS_THIS_GATE')
    out={'primary':'objective-cold nested applicability gate','v75':ll0,'related':llr,'v97':ll97,'v99_gate':llg,
         'gain_vs_v97':gain,'diagnostic_endpoint_oracle':llor,'oracle_gap_from_v97':oracle_gap,
         'oracle_gap_recovered_fraction':recovery,'gate_scale':GATE_SCALE,'folds':fold_rows,
         'decision':{'verdict':verdict,'precommit':'promote to four-world only if nested objective-cold gain vs V97 >= 0.002'}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v99_oof_expert_gate.json'); run(p.parse_args())

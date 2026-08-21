#!/usr/bin/env python3
"""V132: leakage-safe learned applicability gate for V129 tutor uptake.

This is derived from the Residual Constraint Graph, not a feature sweep.
V129 shows control-separated uptake signal only in a label-defined ambiguity regime;
V131 shows prediction density alone is too broad. V132 asks whether the missing
activation predicate is itself learnable from runtime-visible state.

For each OUTER fold:
1. Produce INNER-OOF V97 predictions on the outer-training rows.
2. Produce INNER-OOF uptake and rotated-control corrections on those rows.
3. Define correction-benefit targets only on outer-training rows from per-row logloss.
4. Fit one frozen logistic applicability gate from runtime-visible features.
5. Fit the correction model on all outer-training INNER-OOF base predictions.
6. Apply both correction and gate to untouched outer validation rows.

No validation labels enter feature construction, correction fitting, or gating.
No threshold/C/feature sweep. The identical procedure is run for the rotated-reply
control so an apparent benefit from generic second-stage selection is not enough.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from v110_residual_collider_state_discovery import ll,logit,p97_predict
from v129_tutor_uptake import feats,pairs
from v75_canonical_trajectory import SEED

EPS=1e-5
GATE_C=.10
CORR_C=.05


def row_loss(y,p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS); y=np.asarray(y,int)
    return -(y*np.log(p)+(1-y)*np.log(1-p))


def crowd_features(P,obj):
    """Runtime-visible geometry, no labels."""
    P=np.asarray(P,float); obj=np.asarray(obj,str)
    nearest=np.ones(len(P),float); count=np.ones(len(P),float)
    for o in np.unique(obj):
        z=np.where(obj==o)[0]; count[z]=len(z)
        if len(z)>1:
            d=np.abs(P[z,None]-P[None,z]); np.fill_diagonal(d,np.inf)
            nearest[z]=np.min(d,axis=1)
    return np.c_[np.log1p(count),nearest,(nearest<=.01).astype(float)]


def gate_features(P,Q,R,obj):
    P=np.asarray(P,float); Q=np.asarray(Q,float); R=np.asarray(R,float)
    d=Q-P
    # Every field is available at inference time once V97 and the frozen uptake
    # correction have produced their probabilities.
    return np.c_[P,Q,d,np.abs(d),np.abs(P-.5),logit(P),crowd_features(P,obj),R]


def residual_fit(P,R,y):
    mu=R.mean(0); sd=R.std(0)+1e-6
    X=np.c_[logit(P),(R-mu)/sd]
    m=LogisticRegression(C=CORR_C,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y)
    return mu,sd,m


def residual_apply(model,P,R):
    mu,sd,m=model
    X=np.c_[logit(P),(R-mu)/sd]
    return np.clip(m.predict_proba(X)[:,1],EPS,1-EPS)


def inner_oof(X75,Xr,y,groups,support,R):
    nsp=min(3,len(np.unique(groups)))
    splits=list(GroupKFold(nsp).split(np.zeros(len(y)),y,groups))
    P=np.zeros(len(y)); Q=np.zeros(len(y))
    # First get base OOF for all rows.
    for tr,va in splits:
        P[va],_=p97_predict(X75,Xr,y,tr,va,support)
    # Then fit each residual correction on OOF base probabilities of its training
    # rows and validate on the same untouched inner validation block.
    for tr,va in splits:
        mod=residual_fit(P[tr],R[tr],y[tr])
        Q[va]=residual_apply(mod,P[va],R[va])
    return np.clip(P,EPS,1-EPS),np.clip(Q,EPS,1-EPS)


def fit_gate(P,Q,R,obj,y):
    X=gate_features(P,Q,R,obj)
    target=(row_loss(y,Q)<row_loss(y,P)).astype(int)
    # If degenerate, use a constant decision rather than manufacturing a model.
    if len(np.unique(target))<2:
        return {'constant':int(target[0]),'mu':None,'sd':None,'model':None,'rate':float(target.mean())}
    mu=X.mean(0); sd=X.std(0)+1e-6
    m=LogisticRegression(C=GATE_C,max_iter=300,solver='liblinear',class_weight='balanced',random_state=SEED).fit((X-mu)/sd,target)
    return {'constant':None,'mu':mu,'sd':sd,'model':m,'rate':float(target.mean())}


def apply_gate(g,P,Q,R,obj):
    if g['constant'] is not None:
        take=np.full(len(P),bool(g['constant']))
    else:
        X=gate_features(P,Q,R,obj); pr=g['model'].predict_proba((X-g['mu'])/g['sd'])[:,1]
        take=pr>=.5
    out=np.asarray(P,float).copy(); out[take]=Q[take]
    return np.clip(out,EPS,1-EPS),take


def eval_geometry(name,groups,X75,Xr,y,support,obj,R,C):
    groups=np.asarray(groups); nsp=min(4,len(np.unique(groups)))
    outer=list(GroupKFold(nsp).split(np.zeros(len(y)),y,groups))
    PB=np.zeros(len(y)); GR=np.zeros(len(y)); GC=np.zeros(len(y));
    takeR=np.zeros(len(y),bool); takeC=np.zeros(len(y),bool); foldrows=[]
    for k,(tr,va) in enumerate(outer,1):
        # Clean outer validation base prediction.
        pva,_=p97_predict(X75,Xr,y,tr,va,support)
        # Training state for gate/correction is itself OOF.
        pin,qin=inner_oof(X75[tr],Xr[tr],y[tr],groups[tr],support[tr],R[tr])
        _pin_c,qin_c=inner_oof(X75[tr],Xr[tr],y[tr],groups[tr],support[tr],C[tr])
        # pin and _pin_c are deterministically identical; do not use labels from va.
        gateR=fit_gate(pin,qin,R[tr],obj[tr],y[tr]); gateC=fit_gate(pin,qin_c,C[tr],obj[tr],y[tr])
        corrR=residual_fit(pin,R[tr],y[tr]); corrC=residual_fit(pin,C[tr],y[tr])
        qva=residual_apply(corrR,pva,R[va]); qva_c=residual_apply(corrC,pva,C[va])
        gr,tR=apply_gate(gateR,pva,qva,R[va],obj[va]); gc,tC=apply_gate(gateC,pva,qva_c,C[va],obj[va])
        PB[va]=pva; GR[va]=gr; GC[va]=gc; takeR[va]=tR; takeC[va]=tC
        foldrows.append({'fold':k,'rows':int(len(va)),'base_ll':ll(y[va],pva),'gate_ll':ll(y[va],gr),'control_gate_ll':ll(y[va],gc),'train_benefit_rate':gateR['rate'],'take_rate':float(tR.mean())})
    b=ll(y,PB); r=ll(y,GR); c=ll(y,GC)
    return {
        'geometry':name,'baseline_v97_ll':b,
        'nested_gate':{'ll':r,'gain':b-r,'take_rate':float(takeR.mean())},
        'nested_rotated_control_gate':{'ll':c,'gain':b-c,'take_rate':float(takeC.mean())},
        'real_minus_control_gain':c-r,
        'folds':foldrows,
    }


def main(a):
    d=Path(a.dir); z=np.load(d/'arrays.npz',allow_pickle=True)
    y=z['y']; obj=z['objectives']; support=z['support']; sessions=z['sessions']
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz'); cache={}
    with zipfile.ZipFile(a.archive) as za:
        names=set(za.namelist())
        for sid in np.unique(sessions):
            name=f'{sid}.csv'
            if name not in names: raise RuntimeError('missing '+name)
            with za.open(name) as f: rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            P=pairs(rows); shift=1+(int(hashlib.sha256(str(sid).encode()).hexdigest()[:8],16)%max(1,len(P)-1)) if len(P)>1 else 0
            cache[str(sid)]=(feats(P,0),feats(P,shift))
    R=np.vstack([cache[str(s)][0] for s in sessions]); C=np.vstack([cache[str(s)][1] for s in sessions])
    out={'protocol':'V132_NESTED_APPLICABILITY_GATE','rows':int(len(y)),
         'hypothesis':'V129 contains local relational information but requires a learned runtime-visible ambiguity/applicability predicate',
         'precommit':{'outer_folds':4,'inner_folds':3,'gate_C':GATE_C,'correction_C':CORR_C,'gate_threshold':.5,'no_sweep':True,
                      'promote_gain_each_geometry':.0005,'real_minus_control_each_geometry':.0005}}
    out['objective_grouped']=eval_geometry('objective_grouped',obj,X75,Xr,y,support,obj,R,C)
    out['session_grouped']=eval_geometry('session_grouped',sessions,X75,Xr,y,support,obj,R,C)
    def ok(r): return r['nested_gate']['gain']>=.0005 and r['real_minus_control_gain']>=.0005
    po,ps=ok(out['objective_grouped']),ok(out['session_grouped'])
    out['decision']={'objective_pass':bool(po),'session_pass':bool(ps),'verdict':'PROMOTE_LEARNED_APPLICABILITY_GATE' if po and ps else 'SUPPRESS_LEARNED_UPTAKE_APPLICABILITY_FAMILY'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--dir',required=True); p.add_argument('--out',required=True); main(p.parse_args())

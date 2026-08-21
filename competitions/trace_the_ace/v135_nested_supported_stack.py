#!/usr/bin/env python3
"""V135: deployable nested stack for supported objectives.

Constraint-derived from V105/V106/V97 lineage:
- V97 changes only unsupported objectives; public gain over V75 is tiny.
- V105 showed V74+V75+RELATED complementarity but selected weights on held-out folds.
- V125 closed pure calibration.

V135 learns composition only from inner-OOF predictions on outer-training rows.
For any outer row whose objective has no support in outer training, prediction is EXACTLY
V97. Thus objective-cold cannot regress by construction. For supported rows, compare:
A0 V97
A1 nested stack from V75+RELATED only
A2 nested stack from V75+RELATED+smoothed objective-difficulty prior.
No sweep. Objective prior smoothing alpha fixed at 10.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from v110_residual_collider_state_discovery import EPS,ll,logit,fit_base,p97_predict
from v75_canonical_trajectory import SEED
ALPHA=10.0; C=.10

def prior_apply(y,tr,va,support):
    g=float(np.mean(y[tr])); sums={}; counts={}
    for i in tr:
        k=str(support[i]); sums[k]=sums.get(k,0.)+float(y[i]); counts[k]=counts.get(k,0)+1
    p=np.empty(len(va)); c=np.empty(len(va)); seen=np.empty(len(va),bool)
    for j,i in enumerate(va):
        k=str(support[i]); n=counts.get(k,0); s=sums.get(k,0.); seen[j]=n>0; c[j]=n
        p[j]=(s+ALPHA*g)/(n+ALPHA)
    return np.clip(p,EPS,1-EPS),c,seen

def components(X75,Xr,y,tr,va,support):
    p75=fit_base(X75,y,tr,va); pr=fit_base(Xr,y,tr,va); pp,c,seen=prior_apply(y,tr,va,support)
    p97=np.where(seen,p75,.65*p75+.35*pr)
    return np.clip(p97,EPS,1-EPS),p75,pr,pp,c,seen

def feats(p75,pr,pp,c,full=True):
    xs=[logit(p75),logit(pr),logit(p75)-logit(pr)]
    if full: xs += [logit(pp),np.log1p(c)]
    return np.column_stack(xs)

def fit_stack(X,y):
    return LogisticRegression(C=C,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y)

def nested_geom(name,groups,X75,Xr,y,support):
    groups=np.asarray(groups); n=len(y); p0=np.zeros(n); p1=np.zeros(n); p2=np.zeros(n); folds=[]
    outer=list(GroupKFold(min(4,len(np.unique(groups)))).split(np.zeros(n),y,groups))
    for k,(tr,va) in enumerate(outer,1):
        # Outer predictions/components are untouched.
        q0,o75,orr,opp,oc,oseen=components(X75,Xr,y,tr,va,support)
        # Inner-OOF components for stack training only.
        ig=groups[tr]; inner=list(GroupKFold(min(3,len(np.unique(ig)))).split(np.zeros(len(tr)),y[tr],ig))
        ip75=np.zeros(len(tr)); ipr=np.zeros(len(tr)); ipp=np.zeros(len(tr)); ic=np.zeros(len(tr)); iseen=np.zeros(len(tr),bool)
        for ltr,lva in inner:
            atr=tr[ltr]; ava=tr[lva]
            _,a75,ar,ap,ac,aseen=components(X75,Xr,y,atr,ava,support)
            ip75[lva]=a75;ipr[lva]=ar;ipp[lva]=ap;ic[lva]=ac;iseen[lva]=aseen
        # Learn only from examples where the objective was actually supported.
        fitmask=iseen
        if fitmask.sum()<50 or len(np.unique(y[tr][fitmask]))<2:
            q1=q0.copy();q2=q0.copy()
        else:
            m1=fit_stack(feats(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask],False),y[tr][fitmask])
            m2=fit_stack(feats(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask],True),y[tr][fitmask])
            q1=q0.copy();q2=q0.copy()
            if oseen.any():
                q1[oseen]=np.clip(m1.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],False))[:,1],EPS,1-EPS)
                q2[oseen]=np.clip(m2.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)
        p0[va]=q0;p1[va]=q1;p2[va]=q2
        folds.append({'fold':k,'rows':int(len(va)),'supported_fraction':float(oseen.mean()),'v97_ll':ll(y[va],q0),'composition_ll':ll(y[va],q1),'full_stack_ll':ll(y[va],q2)})
    b,a1,a2=ll(y,p0),ll(y,p1),ll(y,p2)
    return {'geometry':name,'v97_ll':b,'composition_only':{'ll':a1,'gain':b-a1},'full_stack':{'ll':a2,'gain':b-a2},'prior_incremental_gain':a1-a2,'folds':folds}

def main(a):
    d=Path(a.dir);z=np.load(d/'arrays.npz',allow_pickle=True);y=z['y'];obj=z['objectives'];support=z['support'];sessions=z['sessions'];X75=load_npz(d/'X75.npz');Xr=load_npz(d/'Xr.npz')
    out={'protocol':'V135_NESTED_SUPPORTED_STACK','rows':int(len(y)),'hypothesis':'deployable inner-OOF composition of V75, RELATED, and objective difficulty improves supported-objective regime while exact-fallback preserves unsupported V97','precommit':{'outer_folds':4,'inner_folds':3,'stack_C':C,'prior_alpha':ALPHA,'no_sweep':True,'supported_session_gain':.001,'objective_noninferiority':.0001,'prior_incremental_gain':.0003}}
    out['objective_grouped']=nested_geom('objective_grouped',obj,X75,Xr,y,support)
    out['session_grouped']=nested_geom('session_grouped',sessions,X75,Xr,y,support)
    O=out['objective_grouped'];S=out['session_grouped']
    comp=(S['composition_only']['gain']>=.001 and O['composition_only']['gain']>=-.0001)
    full=(S['full_stack']['gain']>=.001 and O['full_stack']['gain']>=-.0001)
    prior=full and S['prior_incremental_gain']>=.0003
    best='FULL_STACK' if full and S['full_stack']['gain']>=S['composition_only']['gain'] else 'COMPOSITION_ONLY' if comp else 'NONE'
    out['decision']={'composition_pass':bool(comp),'full_stack_pass':bool(full),'objective_prior_causal':bool(prior),'preferred':best,'verdict':'PROMOTE_NESTED_SUPPORTED_'+best if best!='NONE' else 'SUPPRESS_NESTED_SUPPORTED_STACK'}
    Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dir',required=True);p.add_argument('--out',required=True);main(p.parse_args())

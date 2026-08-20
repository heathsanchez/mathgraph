#!/usr/bin/env python3
"""V125: nested calibration residual over frozen V97.

Question: is V97 leaving lawful log-loss improvement in probability calibration,
without adding new information or exploiting a particular validation geometry?

Frozen protocol:
- deterministic 2500-row response-id sample;
- exact V97 endpoint (V75 when objective supported; .65 V75 + .35 RELATED when unsupported);
- 4-fold outer objective-grouped and session-grouped OOF;
- calibration parameters fit only to inner-OOF V97 predictions inside each outer training fold;
- intervention = one global Platt map sigmoid(a + b*logit(p97));
- control = same map fit after deterministic shuffle of inner-OOF probabilities;
- no hyperparameter sweep.

Promote only if calibration gains >= .001 log loss in BOTH geometries and beats
the shuffled calibration by >= .001 in BOTH. Otherwise retain as a negative law.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control

EPS=1e-5

def hh(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS)))
def logit(p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS); return np.log(p/(1-p))

def endpoint(X75,Xr,y,key,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr])
    p75=m.predict_proba(X75[va])[:,1]
    r=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr])
    pr=r.predict_proba(Xr[va])[:,1]
    vals,cts=np.unique(key[tr],return_counts=True); d=dict(zip(vals,cts))
    seen=np.array([d.get(x,0)>0 for x in key[va]])
    return np.clip(np.where(seen,p75,.65*p75+.35*pr),EPS,1-EPS)

def fit_cal(p,y):
    return LogisticRegression(C=1000.,max_iter=300,solver='liblinear',random_state=SEED).fit(logit(p)[:,None],y)

def geometry(name,groups,X75,Xr,y,key):
    outer=list(GroupKFold(4).split(np.zeros(len(y)),y,groups))
    pb=np.zeros(len(y)); pc=np.zeros(len(y)); ps=np.zeros(len(y)); folds=[]
    for k,(tr,va) in enumerate(outer):
        inner_groups=groups[tr]
        inn=list(GroupKFold(min(4,len(np.unique(inner_groups)))).split(np.zeros(len(tr)),y[tr],inner_groups))
        pi=np.zeros(len(tr))
        for itr,iva in inn:
            pi[iva]=endpoint(X75,Xr,y,key,tr[itr],tr[iva])
        cal=fit_cal(pi,y[tr])
        rng=np.random.default_rng(SEED+125+k)
        sh=fit_cal(pi[rng.permutation(len(pi))],y[tr])
        raw=endpoint(X75,Xr,y,key,tr,va)
        q=cal.predict_proba(logit(raw)[:,None])[:,1]
        qs=sh.predict_proba(logit(raw)[:,None])[:,1]
        pb[va]=raw;pc[va]=q;ps[va]=qs
        folds.append({'fold':k+1,'rows':int(len(va)),'baseline':ll(y[va],raw),'calibrated':ll(y[va],q),
                      'gain':ll(y[va],raw)-ll(y[va],q),'slope':float(cal.coef_[0,0]),
                      'intercept':float(cal.intercept_[0])})
    base=ll(y,pb); cal=ll(y,pc); shuf=ll(y,ps)
    return {'geometry':name,'baseline_v97_ll':base,'calibrated_ll':cal,'gain':base-cal,
            'shuffled_calibration_ll':shuf,'calibration_minus_shuffle_gain':shuf-cal,'folds':folds}

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    print('features columns',list(f.columns),flush=True)
    ix=sorted(range(len(f)),key=lambda i:hh(f.response_id.iloc[i]))[:a.rows]
    f=f.iloc[ix].reset_index(drop=True)
    y=f.target.to_numpy(int); key=f.learning_objective.astype(str).to_numpy()
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy()
    cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}
    rt=[];rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related');rt.append(t);rz.append(z)
        if (i+1)%500==0: print('prepared rows',i+1,flush=True)
    X75=build_v75(f,cache);Xr=build_control(rt,rz)
    ro=geometry('objective_grouped',obj,X75,Xr,y,key);rs=geometry('session_grouped',sess,X75,Xr,y,key)
    def ok(r): return r['gain']>=.001 and r['calibration_minus_shuffle_gain']>=.001
    verdict='PROMOTE_CALIBRATION_LAW' if ok(ro) and ok(rs) else 'KEEP_V97_CALIBRATION'
    out={'protocol':'V125_NESTED_CALIBRATION','rows':len(f),'precommit':{'gain_each_geometry':.001,'margin_vs_shuffle_each':.001,'no_sweep':True},
         'objective_grouped':ro,'session_grouped':rs,'decision':{'objective_pass':ok(ro),'session_pass':ok(rs),'verdict':verdict}}
    Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v125_nested_calibration.json');run(p.parse_args())

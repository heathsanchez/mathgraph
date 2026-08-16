#!/usr/bin/env python3
"""V102: locate the resolution at which RELATED applicability actually lives.

Diagnostic only. Uses untouched outer objective-cold folds to generate V75/RELATED
predictions once, then measures label-informed oracle blend ceilings at progressively
finer groupings. This does NOT define a deployable router; it decides what unit V103
should model.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from v71_mastery_events import load_transcript, tokens
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups
from v94_related_control import segmented_control, build_control

EPS=1e-5
GRID=np.array([0.,.15,.25,.35,.45,.60,1.0])

def fit(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))

def oracle_group(y,p0,pr,groups):
    q=np.empty(len(y)); ws=[]
    for g in np.unique(groups):
        ix=np.where(groups==g)[0]; best=(1e99,0.,None)
        for w in GRID:
            z=(1-w)*p0[ix]+w*pr[ix]; v=ll(y[ix],z)
            if v<best[0]: best=(v,float(w),z)
        q[ix]=best[2]; ws.append(best[1])
    return ll(y,q), float(np.mean(ws)), len(ws)

def family(s):
    # tokens() returns a set; sort to make this deterministic and sliceable.
    t=sorted(tokens(str(s)))
    return ' '.join(t[:3]) if t else ''

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1,flush=True)
    X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy(); fam=np.asarray([family(x) for x in f.learning_objective.astype(str)])
    p0=np.zeros(len(y)); pr=np.zeros(len(y))
    # Generate expert predictions exactly once; every resolution audit below reuses them.
    for k,(tr,va) in enumerate(folds_from_groups(obj),1):
        p0[va]=fit(X0,y,tr,va); pr[va]=fit(Xr,y,tr,va); print('fold',k,flush=True)
    v75=ll(y,p0); v97=ll(y,.65*p0+.35*pr)
    row_loss=np.minimum(-(y*np.log(p0)+(1-y)*np.log(1-p0)),-(y*np.log(pr)+(1-y)*np.log(1-pr)))
    row_oracle=float(np.mean(row_loss))
    levels={}
    for name,g in [('family',fam),('objective',obj),('session',sess),('session_objective',np.char.add(np.char.add(sess,'|'),obj))]:
        val,mw,n=oracle_group(y,p0,pr,g); levels[name]={'oracle_ll':val,'gain_vs_v97':v97-val,'mean_best_weight':mw,'groups':n}
        print(name,levels[name],flush=True)
    best=min((ll(y,(1-w)*p0+w*pr),float(w)) for w in GRID)
    out={'v75':v75,'v97':v97,'global_grid_oracle':{'ll':best[0],'weight':best[1],'gain_vs_v97':v97-best[0]},
         'levels':levels,'row_endpoint_oracle':{'ll':row_oracle,'gain_vs_v97':v97-row_oracle},
         'decision_rule':'Choose the coarsest grouping whose oracle recovers a material fraction of the row endpoint oracle; V103 must model that unit using runtime-visible unlabeled features only.'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v102_applicability_resolution.json'); run(p.parse_args())

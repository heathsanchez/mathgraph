#!/usr/bin/env python3
"""V136: full-data untouched verification of promoted V135.

This is verification, not discovery. V135's operator and hyperparameters are frozen:
- V75 + RELATED + smoothed exact-objective difficulty prior (alpha=10)
- logistic stack C=.10
- stack fit only from inner-OOF support-seen rows
- exact V97 fallback whenever target objective is unsupported by outer training
- 4 outer / 3 inner folds, no sweep

V136 rebuilds V75 and RELATED from the full competition training corpus and evaluates
that exact operator on all training rows. Primary gate is session-grouped transfer;
objective-grouped is a structural non-regression audit and must remain exactly V97.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from v75_canonical_trajectory import load_training
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control
from v135_nested_supported_stack import nested_geom,ALPHA,C

def main(a):
    t0=time.time()
    f=load_training(a.features,a.labels).reset_index(drop=True)
    print('FULL_ROWS',len(f),'COLUMNS',list(f.columns),flush=True)
    y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    support=f.learning_objective.astype(str).to_numpy()
    sessions=f.session_id.astype(str).to_numpy()
    cache={}
    us=np.unique(sessions)
    for j,sid in enumerate(us,1):
        cache[str(sid)]=load_transcript(a.transcripts/f'{sid}.csv')
        if j%2500==0: print('TRANSCRIPTS',j,'/',len(us),'elapsed',round(time.time()-t0,1),flush=True)
    print('BUILD_V75',flush=True)
    X75=build_v75(f,cache)
    print('V75_SHAPE',X75.shape,'nnz',X75.nnz,'elapsed',round(time.time()-t0,1),flush=True)
    rt=[];rz=[]
    for i,r in f.iterrows():
        text,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related')
        rt.append(text);rz.append(z)
        if (i+1)%5000==0: print('RELATED_ROWS',i+1,'elapsed',round(time.time()-t0,1),flush=True)
    Xr=build_control(rt,rz)
    print('RELATED_SHAPE',Xr.shape,'nnz',Xr.nnz,'elapsed',round(time.time()-t0,1),flush=True)

    # Primary untouched verification world: unseen sessions, mostly support-seen objectives.
    S=nested_geom('session_grouped_full',sessions,X75,Xr,y,support)
    print('SESSION_RESULT',json.dumps(S,indent=2),flush=True)
    # Structural safety audit: objective-held-out rows must use exact V97 fallback.
    O=nested_geom('objective_grouped_full',obj,X75,Xr,y,support)
    print('OBJECTIVE_RESULT',json.dumps(O,indent=2),flush=True)

    sg=S['full_stack']['gain']; og=O['full_stack']['gain']; inc=S['prior_incremental_gain']
    all_session_folds=all(x['full_stack_ll'] < x['v97_ll'] for x in S['folds'])
    obj_exact=abs(og)<=1e-12 and all(abs(x['full_stack_ll']-x['v97_ll'])<=1e-12 for x in O['folds'])
    verdict=('PROMOTE_V135_TO_RUNTIME' if sg>=.005 and inc>=.003 and all_session_folds and obj_exact
             else 'RETAIN_V135_PARTIAL' if sg>=.002 and obj_exact
             else 'SUPPRESS_V135_FULL_TRANSFER')
    out={
      'protocol':'V136_FULL_V135_VERIFICATION',
      'rows':int(len(f)),'sessions':int(len(np.unique(sessions))),'objectives':int(len(np.unique(obj))),
      'frozen_operator':{'stack_C':C,'prior_alpha':ALPHA,'outer_folds':4,'inner_folds':3,'unsupported_fallback':'exact_v97'},
      'precommit':{'primary_session_gain':.005,'prior_incremental_gain':.003,'all_session_folds_improve':True,'objective_exact_nonregression':True},
      'session_grouped':S,'objective_grouped':O,
      'decision':{'session_gain':float(sg),'prior_incremental_gain':float(inc),'all_session_folds_improve':bool(all_session_folds),'objective_exact_nonregression':bool(obj_exact),'verdict':verdict},
      'elapsed_seconds':float(time.time()-t0)
    }
    Path(a.out).write_text(json.dumps(out,indent=2));print('FINAL',json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',default='v136_full_v135_verification.json');main(p.parse_args())

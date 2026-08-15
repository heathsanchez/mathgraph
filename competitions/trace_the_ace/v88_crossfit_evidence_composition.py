#!/usr/bin/env python3
"""V88: cross-fitted V75 + ablated EvidenceEvent composition.

RGRS response to V85:
- assistance/independence tags were not causal (A1 ~= A2), so remove them;
- EvidenceEvents were weak standalone but strongly complementary to V75.

This test asks whether that composition survives leakage-resistant weight selection.
For each held-out objective-cold fold, choose the blend weight using only OOF
predictions from the other four folds, then score the untouched fold.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import evidence_events, render, nums, build_sparse, build_v75, oof


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={}
    for sid in f.session_id.astype(str).unique():
        cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')

    texts=[]; z=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]
        seg,_=choose_target_segment(d,str(r.learning_objective))
        ev=evidence_events(seg,str(r.learning_objective))
        texts.append(render(ev,str(r.learning_objective),ablate=True))
        z.append(nums(ev,ablate=True))
        if (i+1)%2500==0: print('rows',i+1)

    y=f.target.to_numpy(int)
    groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    splits=list(GroupKFold(5).split(np.zeros(len(y)),y,groups))

    X0=build_v75(f,cache)
    X2=build_sparse(texts,z,'EVIDENCE_ABL')
    p0,_=oof(X0,y,splits,'V75')
    pe,_=oof(X2,y,splits,'EVIDENCE_ABL')

    fold_id=np.empty(len(y),int)
    for k,(_,va) in enumerate(splits): fold_id[va]=k

    grid=np.linspace(0,0.8,33)
    q=np.zeros(len(y)); selected=[]
    for k,(_,va) in enumerate(splits):
        tune=np.where(fold_id!=k)[0]
        best=None
        for w in grid:
            pt=np.clip((1-w)*p0[tune]+w*pe[tune],1e-5,1-1e-5)
            ll=float(log_loss(y[tune],pt))
            if best is None or ll<best['tune_logloss']:
                best={'evidence_weight':float(w),'tune_logloss':ll}
        w=best['evidence_weight']
        q[va]=np.clip((1-w)*p0[va]+w*pe[va],1e-5,1-1e-5)
        best['fold']=k+1
        best['heldout_logloss']=float(log_loss(y[va],q[va]))
        selected.append(best)
        print('fold',best)

    ll0=float(log_loss(y,p0)); lle=float(log_loss(y,pe)); llq=float(log_loss(y,q))
    gain=ll0-llq
    decision='R7_COMPOSITION_CONFIRMED' if gain>=.003 else ('R7_PARTIAL' if gain>=.001 else 'REJECT_GLOBAL_BLEND_GAIN')
    out={'primary':'objective-cold-crossfitted','v75_logloss':ll0,'evidence_ablation_logloss':lle,
         'crossfit_blend_logloss':llq,'crossfit_gain_vs_v75':gain,'decision':decision,
         'selected_by_fold':selected,'mean_evidence_weight':float(np.mean([x['evidence_weight'] for x in selected]))}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v88_crossfit_evidence_composition.json'); run(p.parse_args())

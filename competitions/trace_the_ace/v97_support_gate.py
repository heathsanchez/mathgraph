#!/usr/bin/env python3
"""V97: submission-sprint exact-support gate.

Frozen law from V93-V96: RELATED ability is a specialist for objectives with no
training support; V75 dominates when exact objective support is present.
This test does not tune the law. It evaluates the precommitted runtime rule:
    count_train(objective) == 0 -> 0.35 RELATED + 0.65 V75
    otherwise                   -> V75
across four shift worlds using fold-local training counts only.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v85_evidence_state import build_v75, oof
from v93_shift_robust_validation import folds_from_groups, obj_family, style_matrix
from v94_related_control import segmented_control, build_control
from sklearn.cluster import KMeans

W_UNSEEN = 0.35
EPS = 1e-5


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
    support_key=f.learning_objective.astype(str).to_numpy()  # always runtime-visible
    sess=f.session_id.astype(str).to_numpy(); fam=f.learning_objective.astype(str).map(obj_family).to_numpy()
    SX=style_matrix(f,cache); style=KMeans(n_clusters=5,random_state=137,n_init=10).fit(SX).labels_.astype(str)
    worlds={'objective_cold':folds_from_groups(obj),'session_cold':folds_from_groups(sess),
            'objective_family_cold':folds_from_groups(fam),'style_cold':folds_from_groups(style)}
    out={'primary':'fixed-exact-support-runtime-gate','law':{'unseen_weight':W_UNSEEN,'seen_weight':0.0,'predicate':'fold-local exact learning_objective text training count == 0'},'worlds':{}}
    gains=[]; regress=[]
    for name,sp in worlds.items():
        p0,_=oof(X0,y,sp,name+':V75'); pr,_=oof(Xr,y,sp,name+':RELATED')
        q=np.zeros(len(y)); unseen=np.zeros(len(y),bool)
        for tr,va in sp:
            counts={g:int(n) for g,n in zip(*np.unique(support_key[tr],return_counts=True))}
            m=np.array([counts.get(str(support_key[i]),0)==0 for i in va],bool); unseen[va]=m
            w=np.where(m,W_UNSEEN,0.0)
            q[va]=np.clip((1-w)*p0[va]+w*pr[va],EPS,1-EPS)
        ll0=float(log_loss(y,p0)); llq=float(log_loss(y,q)); gain=ll0-llq
        rec={'v75':ll0,'support_gate':llq,'gain_vs_v75':gain,'ability_fraction':float(unseen.mean()),
             'unseen_rows':int(unseen.sum()),'seen_rows':int((~unseen).sum())}
        out['worlds'][name]=rec; gains.append(gain); regress.append(max(0.0,-gain)); print(name,rec)
    mean_gain=float(np.mean(gains)); worst_reg=float(max(regress)); obj_gain=out['worlds']['objective_cold']['gain_vs_v75']
    promote=obj_gain>=0.0025 and mean_gain>=0.0007 and worst_reg<=0.0005
    out['decision']={'objective_gain':obj_gain,'mean_gain_four_worlds':mean_gain,'worst_world_regression':worst_reg,
                     'verdict':'BUILD_SUBMISSION_NOW' if promote else 'STOP_DO_NOT_SUBMIT',
                     'precommit':'build iff objective gain >=.0025, four-world mean gain >=.0007, worst regression <=.0005'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
    if a.require_promote and not promote: raise SystemExit(42)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v97_support_gate.json'); p.add_argument('--require-promote',action='store_true'); run(p.parse_args())

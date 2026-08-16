#!/usr/bin/env python3
"""Train V75 + V94 RELATED assets for the fixed V97 support gate."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control


def pack_model(m): return m.coef_.ravel().astype(np.float64), np.asarray(m.intercept_,dtype=np.float64)

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[];rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t);rz.append(z)
        if (i+1)%2500==0: print('rows',i+1)
    X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X0,y)
    mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr,y)
    Z=np.vstack(rz).astype(float); rmean=Z.mean(0); rstd=Z.std(0)+1e-6
    from v75_canonical_trajectory import trajectory_views
    nums=[]
    for _,r in f.iterrows(): nums.append(trajectory_views(cache[str(r.session_id)],str(r.learning_objective))[1])
    N=np.vstack(nums).astype(float); vmean=N.mean(0); vstd=N.std(0)+1e-6
    c0,b0=pack_model(m0); cr,br=pack_model(mr)
    a.out_dir.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.out_dir/'v97_assets.npz',v75_coef=c0,v75_intercept=b0,v75_num_mean=vmean,v75_num_std=vstd,
                        related_coef=cr,related_intercept=br,related_num_mean=rmean,related_num_std=rstd)
    counts=f.groupby('learning_objective').size().astype(int).to_dict()
    manifest={'candidate':'V97_FIXED_EXACT_SUPPORT_GATE','unseen_weight':0.35,'seen_weight':0.0,'objective_key':'learning_objective',
              'objective_counts':{str(k):int(v) for k,v in counts.items()},'rows':int(len(f))}
    (a.out_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({k:v for k,v in manifest.items() if 'counts' not in k},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);run(p.parse_args())

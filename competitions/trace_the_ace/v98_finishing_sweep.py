#!/usr/bin/env python3
"""V98: tiny support/ability finishing sweep against frozen V97.

No new representation is fit. V75 and RELATED are computed once per frozen shift
world, then a small predeclared family of runtime-visible exact-support laws is
scored. V97 (count==0 -> 0.35 RELATED) is the immutable baseline.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import log_loss

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v85_evidence_state import build_v75, oof
from v93_shift_robust_validation import folds_from_groups, obj_family, style_matrix
from v94_related_control import segmented_control, build_control

EPS=1e-5
V97=(0.35, 0, 0.0)  # unseen weight, low-support threshold, low-support weight
# Deliberately tiny family. Each tuple = (w0, low_threshold, wlow).
CANDIDATES=[
 (0.35,0,0.0),
 (0.45,0,0.0),(0.50,0,0.0),(0.60,0,0.0),
 (0.45,1,0.15),(0.50,1,0.15),(0.60,1,0.15),
 (0.45,2,0.15),(0.50,2,0.25),(0.60,2,0.25),
 (0.50,4,0.15),(0.60,4,0.25),(0.60,4,0.35),
]

def name(c):
    w0,t,wl=c
    return f'w0={w0:.2f}|n1to{t}={wl:.2f}' if t else f'w0={w0:.2f}|seen=0'

def weights_for_counts(counts,c):
    w0,t,wl=c
    counts=np.asarray(counts)
    w=np.zeros(len(counts),float)
    w[counts==0]=w0
    if t:
        w[(counts>=1)&(counts<=t)]=wl
    return w

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
    sess=f.session_id.astype(str).to_numpy(); fam=f.learning_objective.astype(str).map(obj_family).to_numpy()
    SX=style_matrix(f,cache); style=KMeans(n_clusters=5,random_state=137,n_init=10).fit(SX).labels_.astype(str)
    worlds={'objective_cold':folds_from_groups(obj),'session_cold':folds_from_groups(sess),
            'objective_family_cold':folds_from_groups(fam),'style_cold':folds_from_groups(style)}
    out={'primary':'V98 tiny finishing sweep','v97_baseline':name(V97),'candidates':[name(c) for c in CANDIDATES],'worlds':{}}
    by_candidate={name(c):[] for c in CANDIDATES}
    for wn,sp in worlds.items():
        p0,_=oof(X0,y,sp,wn+':V75'); pr,_=oof(Xr,y,sp,wn+':RELATED')
        fold_counts=np.zeros(len(y),int)
        for tr,va in sp:
            vals,ns=np.unique(key[tr],return_counts=True); d=dict(zip(vals,ns))
            fold_counts[va]=[int(d.get(str(key[i]),0)) for i in va]
        rec={'v75':float(log_loss(y,p0)),'laws':{}}
        for c in CANDIDATES:
            w=weights_for_counts(fold_counts,c)
            q=np.clip((1-w)*p0+w*pr,EPS,1-EPS)
            ll=float(log_loss(y,q)); gain=rec['v75']-ll
            rec['laws'][name(c)]={'logloss':ll,'gain_vs_v75':gain,'mean_weight':float(w.mean())}
            by_candidate[name(c)].append((wn,ll,gain))
        out['worlds'][wn]=rec
        print(wn,'V75',rec['v75'],'V97',rec['laws'][name(V97)])
    v97_world={wn:out['worlds'][wn]['laws'][name(V97)]['logloss'] for wn in worlds}
    ranking=[]
    for c in CANDIDATES:
        n=name(c); vals=by_candidate[n]
        deltas=[v97_world[wn]-ll for wn,ll,_ in vals]
        gains=[g for _,_,g in vals]
        ranking.append({'law':n,'mean_gain_vs_v97':float(np.mean(deltas)),
                        'objective_gain_vs_v97':float(deltas[0]),
                        'worst_world_delta_vs_v97':float(min(deltas)),
                        'mean_gain_vs_v75':float(np.mean(gains))})
    eligible=[r for r in ranking if r['objective_gain_vs_v97']>=0 and r['worst_world_delta_vs_v97']>=-0.0005]
    best=max(eligible,key=lambda r:r['mean_gain_vs_v97']) if eligible else next(r for r in ranking if r['law']==name(V97))
    promote=(best['law']!=name(V97) and best['mean_gain_vs_v97']>=0.0005 and best['worst_world_delta_vs_v97']>=-0.0005)
    out['ranking']=sorted(ranking,key=lambda r:r['mean_gain_vs_v97'],reverse=True)
    out['decision']={'best':best,'verdict':'PROMOTE_V98_FINISHER' if promote else 'KEEP_V97',
      'precommit':'promote only if mean gain vs frozen V97 >=0.0005, objective nonnegative, worst-world delta >=-0.0005'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out['decision'],indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v98_finishing_sweep.json'); run(p.parse_args())

#!/usr/bin/env python3
"""V93: distribution-shift validation + robust blend selection.

Goal: objective-cold CV materially over-predicts V75 public performance. Rather
than tune to leaderboard scores, construct several lawful train-only stress
worlds and choose V75/relative-ability blend weights that remain good across
all of them.

Worlds:
  * objective-cold        -- unseen learning objectives
  * session-cold          -- unseen tutoring sessions
  * objective-family-cold -- related objective wording held together
  * style-cold            -- transcript structural regimes held together

The public leaderboard is NOT used to fit predictions or weights.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from sklearn.cluster import KMeans

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v85_evidence_state import build_v75, oof
from v89_relative_ability_composition import non_target_ability, build_ability

STOP={"the","a","an","to","of","and","with","using","in","on","for","by","from","within","up","simple"}

def obj_family(s:str)->str:
    toks=[x for x in re.findall(r"[a-z]+",str(s).lower()) if x not in STOP]
    # intentionally coarse: hold semantically similar surface families together
    return "|".join(toks[:3]) if toks else "EMPTY"

def style_matrix(f,cache):
    rows=[]
    for _,r in f.iterrows():
        d=cache[str(r.session_id)]
        roles=d.role.astype(str).str.lower() if 'role' in d else np.array([])
        contents=d.content.fillna('').astype(str).tolist() if 'content' in d else []
        n=max(1,len(d)); st=sum(x=='student' for x in roles); tu=sum(x=='tutor' for x in roles)
        words=sum(len(x.split()) for x in contents); chars=sum(len(x) for x in contents)
        math=sum(bool(re.search(r"\d|[=+\-*/%]",x)) for x in contents)
        questions=sum('?' in x for x in contents)
        rows.append([len(d),st/n,tu/n,words/n,chars/n,math/n,questions/n])
    X=np.asarray(rows,float); return (X-X.mean(0))/(X.std(0)+1e-6)

def folds_from_groups(groups,n=5):
    g=np.asarray(groups).astype(str)
    k=min(n,len(np.unique(g)))
    if k<2: raise ValueError('need at least two groups')
    return list(GroupKFold(k).split(np.zeros(len(g)),np.zeros(len(g)),g))

def eval_world(name,X0,Xa,y,splits,grid):
    p0,_=oof(X0,y,splits,f'{name}:V75')
    pa,_=oof(Xa,y,splits,f'{name}:ABILITY')
    ll0=float(log_loss(y,p0)); lla=float(log_loss(y,pa))
    scores=[]
    for w in grid:
        p=np.clip((1-w)*p0+w*pa,1e-5,1-1e-5)
        scores.append({'w':float(w),'ll':float(log_loss(y,p))})
    best=min(scores,key=lambda z:z['ll'])
    return {'name':name,'v75':ll0,'ability':lla,'best':best,'curve':scores},p0,pa

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    at=[]; az=[]
    for i,r in f.iterrows():
        t,z=non_target_ability(cache[str(r.session_id)],str(r.learning_objective)); at.append(t); az.append(z)
        if (i+1)%2500==0: print('rows',i+1)
    X0=build_v75(f,cache); Xa=build_ability(at,az); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy(); fam=f.learning_objective.astype(str).map(obj_family).to_numpy()
    SX=style_matrix(f,cache); km=KMeans(n_clusters=5,random_state=137,n_init=10).fit(SX); style=km.labels_.astype(str)
    worlds={
      'objective_cold':folds_from_groups(obj),
      'session_cold':folds_from_groups(sess),
      'objective_family_cold':folds_from_groups(fam),
      'style_cold':folds_from_groups(style),
    }
    grid=np.linspace(0,0.7,29); results={}; curves={}
    for name,sp in worlds.items():
        r,_,_=eval_world(name,X0,Xa,y,sp,grid); results[name]=r; curves[name]={x['w']:x['ll'] for x in r['curve']}
        print(name,'V75',r['v75'],'ABILITY',r['ability'],'BEST',r['best'])
    # Robust weight: minimize worst excess loss relative to each world's own best.
    robust=[]
    for w in grid:
        exc=[]; raw=[]
        for name,r in results.items():
            ll=curves[name][float(w)]; raw.append(ll); exc.append(ll-r['best']['ll'])
        robust.append({'w':float(w),'worst_excess':float(max(exc)),'mean_excess':float(np.mean(exc)),
                       'worst_logloss':float(max(raw)),'mean_logloss':float(np.mean(raw))})
    choice=min(robust,key=lambda z:(z['worst_excess'],z['mean_excess'],z['mean_logloss']))
    out={'primary':'shift-robust-validation','worlds':results,'robust_choice':choice,
         'objective_cold_best_weight':results['objective_cold']['best']['w'],
         'note':'No leaderboard score used in model fitting, split construction, or weight selection.'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v93_shift_robust.json'); run(p.parse_args())

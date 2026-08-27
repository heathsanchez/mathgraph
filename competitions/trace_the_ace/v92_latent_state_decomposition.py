#!/usr/bin/env python3
"""V92: latent student-state decomposition.

Hypothesis: the transcript is a noisy measurement instrument. Predict post-test
correctness from (a) whole-session V75, (b) non-target local ability, (c) target
EvidenceEvents, and (d) objective difficulty, with explicit latent contrasts.
All base predictions are objective-cold OOF; the meta-combiner is cross-fitted
across the same held-out objective folds. Ablations test which latent components
actually pay rent.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import evidence_events, render, nums, build_sparse, build_v75, oof
from v89_relative_ability_composition import non_target_ability, build_ability

EPS=1e-5

def logit(p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS)
    return np.log(p/(1-p))

def objective_matrix(texts):
    w=HashingVectorizer(n_features=2**16,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    c=HashingVectorizer(n_features=2**16,alternate_sign=False,norm='l2',analyzer='char_wb',ngram_range=(3,5),lowercase=True)
    return hstack([w.transform(texts),c.transform(texts)],format='csr')

def base_meta(p0,pa,pe,pd):
    l0,la,le,ld=map(logit,[p0,pa,pe,pd])
    return np.c_[
        l0,la,le,ld,
        la-ld,            # ability relative to objective difficulty
        le-la,            # target-specific deviation from general ability
        le-ld,            # target evidence relative to difficulty
        np.abs(le-la),
        np.abs(la-ld),
        l0-la,
        l0-le,
        la*ld,
        le*la,
    ]

def crossfit_meta(y,splits,p0,pa,pe,pd,cols=None,C=0.1):
    X=base_meta(p0,pa,pe,pd)
    if cols is not None: X=X[:,cols]
    q=np.zeros(len(y)); fold_rows=[]
    for k,(tr,va) in enumerate(splits):
        # The base inputs are themselves OOF predictions. Meta fit is restricted
        # to other objective-cold folds and scored on untouched held-out objectives.
        m=LogisticRegression(C=C,max_iter=1000,solver='lbfgs',random_state=SEED)
        m.fit(X[tr],y[tr]); q[va]=m.predict_proba(X[va])[:,1]
        fold_rows.append({'fold':k+1,'logloss':float(log_loss(y[va],np.clip(q[va],EPS,1-EPS)))})
    return np.clip(q,EPS,1-EPS),fold_rows

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    et=[]; ez=[]; at=[]; az=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; obj=str(r.learning_objective)
        seg,_=choose_target_segment(d,obj); ev=evidence_events(seg,obj)
        et.append(render(ev,obj,ablate=True)); ez.append(nums(ev,ablate=True))
        t,z=non_target_ability(d,obj); at.append(t); az.append(z)
        if (i+1)%2500==0: print('rows',i+1)

    y=f.target.to_numpy(int)
    groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    splits=list(GroupKFold(5).split(np.zeros(len(y)),y,groups))

    X0=build_v75(f,cache)
    Xa=build_ability(at,az)
    Xe=build_sparse(et,ez,'EVIDENCE_ABL')
    Xd=objective_matrix(f.learning_objective.fillna('').astype(str).tolist())
    p0,_=oof(X0,y,splits,'V75')
    pa,_=oof(Xa,y,splits,'ABILITY')
    pe,_=oof(Xe,y,splits,'TARGET')
    pd,_=oof(Xd,y,splits,'DIFFICULTY')

    # Full latent comparison and causal component ablations.
    full,folds=crossfit_meta(y,splits,p0,pa,pe,pd)
    # Column definitions from base_meta: 0 V75,1 ability,2 target,3 difficulty,
    # 4 ability-difficulty,5 target-ability,6 target-difficulty,...
    no_ability,_=crossfit_meta(y,splits,p0,pa,pe,pd,cols=[0,2,3,6,10])
    no_difficulty,_=crossfit_meta(y,splits,p0,pa,pe,pd,cols=[0,1,2,5,7,9,10,12])
    no_target,_=crossfit_meta(y,splits,p0,pa,pe,pd,cols=[0,1,3,4,8,9,11])
    linear_only,_=crossfit_meta(y,splits,p0,pa,pe,pd,cols=[0,1,2,3])

    # Reproduce V89-style cross-fitted convex composition as a strong control.
    fold=np.empty(len(y),int)
    for k,(_,va) in enumerate(splits): fold[va]=k
    blend=np.zeros(len(y)); selected=[]
    grid=np.arange(0,0.61,0.1)
    for k,(_,va) in enumerate(splits):
        tune=np.where(fold!=k)[0]; best=None
        for we in grid:
            for wa in grid:
                if we+wa>.8: continue
                p=np.clip((1-we-wa)*p0[tune]+we*pe[tune]+wa*pa[tune],EPS,1-EPS)
                ll=float(log_loss(y[tune],p))
                if best is None or ll<best['ll']: best={'we':float(we),'wa':float(wa),'ll':ll}
        we,wa=best['we'],best['wa']
        blend[va]=np.clip((1-we-wa)*p0[va]+we*pe[va]+wa*pa[va],EPS,1-EPS)
        selected.append({'fold':k+1,**best})

    scores={
      'v75':float(log_loss(y,p0)),
      'ability':float(log_loss(y,pa)),
      'target':float(log_loss(y,pe)),
      'difficulty':float(log_loss(y,pd)),
      'v89_control':float(log_loss(y,blend)),
      'latent_full':float(log_loss(y,full)),
      'no_ability':float(log_loss(y,no_ability)),
      'no_difficulty':float(log_loss(y,no_difficulty)),
      'no_target':float(log_loss(y,no_target)),
      'linear_only':float(log_loss(y,linear_only)),
    }
    scores['gain_vs_v89']=scores['v89_control']-scores['latent_full']
    scores['gain_vs_v75']=scores['v75']-scores['latent_full']
    # Require a meaningful improvement and positive ablation support.
    causal={
      'ability_value':scores['no_ability']-scores['latent_full'],
      'difficulty_value':scores['no_difficulty']-scores['latent_full'],
      'target_value':scores['no_target']-scores['latent_full'],
      'contrast_value':scores['linear_only']-scores['latent_full'],
    }
    decision='PROMOTE_LATENT_DECOMPOSITION' if scores['gain_vs_v89']>=.002 and sum(v>0 for v in causal.values())>=2 else ('PARTIAL' if scores['gain_vs_v89']>0 else 'REJECT')
    out={'primary':'objective-cold-crossfitted','scores':scores,'causal_ablation_values':causal,'folds':folds,'v89_selected':selected,'decision':decision}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v92_latent_state_decomposition.json'); run(p.parse_args())

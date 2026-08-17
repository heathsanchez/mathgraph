#!/usr/bin/env python3
"""V105: restore the missing V74 objective-prior + V75 student-state composition.

Repo reset hypothesis: V74 was promoted as a mandatory independent objective-difficulty
prior, but the V75->V104 lineage largely rebuilt V75 without it. Test the smallest
lawful composition before further routing work.

For each outer validation world:
  * V74 is fit only on outer-train and predicts outer-valid.
  * V75 and RELATED are fit only on outer-train and predict outer-valid.
  * Inner grouped OOF predictions on outer-train select a tiny convex grid.
  * RELATED weight is permitted only where the exact objective has zero support in the
    corresponding training fold. No test-batch aggregation or cross-response features.

A deterministic mixed-support world combines unseen-objective rows with held-out-session
rows on otherwise seen objectives, so the gate is not judged only in pure objective-cold.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v74_semantic_objective_prior import semantic_prior_predict
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups, obj_family, style_matrix
from v94_related_control import segmented_control, build_control

EPS=1e-5
W74=np.array([0.,.10,.20,.30,.40,.50])
WR=np.array([0.,.10,.20,.30,.40])


def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))

def fit_lr(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)

def unseen_mask(keys,tr,va):
    seen=set(keys[tr].tolist())
    return np.asarray([keys[i] not in seen for i in va],bool)

def compose(p75,p74,pr,unseen,w74,wr):
    # RELATED is unavailable on supported objectives. Preserve convexity per row.
    rw=np.where(unseen,wr,0.0)
    base=np.maximum(0.0,1.0-w74-rw)
    return np.clip(base*p75+w74*p74+rw*pr,EPS,1-EPS)

def mixed_support_folds(obj,sess,n=5):
    """Each fold has cold objectives plus session-held-out rows from remaining objectives."""
    uo=np.unique(obj); us=np.unique(sess)
    of={x:i % n for i,x in enumerate(sorted(uo))}
    sf={x:i % n for i,x in enumerate(sorted(us))}
    out=[]
    idx=np.arange(len(obj))
    for k in range(n):
        cold=np.asarray([of[x]==k for x in obj])
        seen_session=np.asarray([(of[o]!=k and sf[s]==k) for o,s in zip(obj,sess)])
        va=idx[cold|seen_session]; tr=idx[~(cold|seen_session)]
        out.append((tr,va))
    return out

def inner_oof(f,X75,Xr,y,outer_tr,groups,support_key):
    n=len(outer_tr); p75=np.zeros(n); p74=np.zeros(n); pr=np.zeros(n); uns=np.zeros(n,bool)
    g=groups[outer_tr]
    ns=min(3,len(np.unique(g)))
    for itr_l,iva_l in GroupKFold(ns).split(np.zeros(n),y[outer_tr],g):
        itr=outer_tr[itr_l]; iva=outer_tr[iva_l]
        p75[iva_l]=fit_lr(X75,y,itr,iva)
        pr[iva_l]=fit_lr(Xr,y,itr,iva)
        p74[iva_l],_=semantic_prior_predict(f.iloc[itr],f.iloc[iva])
        uns[iva_l]=unseen_mask(support_key,itr,iva)
    return p75,p74,pr,uns

def select_weights(y,p75,p74,pr,uns):
    best_base=(1e99,None); best_gate=(1e99,None)
    for a in W74:
        q=compose(p75,p74,pr,uns,a,0.0); v=ll(y,q)
        if v<best_base[0]: best_base=(v,{'w74':float(a),'wr':0.0})
        for r in WR:
            if a+r>.80: continue
            q=compose(p75,p74,pr,uns,a,r); v=ll(y,q)
            if v<best_gate[0]: best_gate=(v,{'w74':float(a),'wr':float(r)})
    return best_base,best_gate

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1,flush=True)
    X75=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    support=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
    fam=f.learning_objective.astype(str).map(obj_family).astype(str).to_numpy()
    style=KMeans(n_clusters=5,random_state=137,n_init=10).fit(style_matrix(f,cache)).labels_.astype(str)
    worlds={
      'objective_cold':(folds_from_groups(obj),obj),
      'session_cold':(folds_from_groups(sess),sess),
      'objective_family_cold':(folds_from_groups(fam),fam),
      'style_cold':(folds_from_groups(style),style),
      'mixed_support':(mixed_support_folds(obj,sess),obj),
    }
    out={'primary':'restore V74 objective prior + V75 state + lawful unsupported RELATED','worlds':{}}
    gains=[]; gate_gains=[]
    for name,(sp,inner_groups) in worlds.items():
        P75=np.zeros(len(y)); P74=np.zeros(len(y)); PG=np.zeros(len(y)); PB=np.zeros(len(y)); PR=np.zeros(len(y)); U=np.zeros(len(y),bool)
        folds=[]
        for k,(tr,va) in enumerate(sp,1):
            p75=fit_lr(X75,y,tr,va); pr=fit_lr(Xr,y,tr,va); p74,_=semantic_prior_predict(f.iloc[tr],f.iloc[va])
            uns=unseen_mask(support,tr,va)
            i75,i74,ir,iu=inner_oof(f,X75,Xr,y,tr,inner_groups,support)
            base,gate=select_weights(y[tr],i75,i74,ir,iu)
            qb=compose(p75,p74,pr,uns,base[1]['w74'],0.0)
            qg=compose(p75,p74,pr,uns,gate[1]['w74'],gate[1]['wr'])
            P75[va]=p75; P74[va]=p74; PR[va]=pr; PB[va]=qb; PG[va]=qg; U[va]=uns
            folds.append({'fold':k,'rows':int(len(va)),'unseen_fraction':float(uns.mean()),
              'v75':ll(y[va],p75),'v74':ll(y[va],p74),'prior_state':ll(y[va],qb),'prior_state_related':ll(y[va],qg),
              'selected_prior':base[1],'selected_gate':gate[1]})
            print(name,folds[-1],flush=True)
        rec={'v75':ll(y,P75),'v74':ll(y,P74),'related':ll(y,PR),'prior_state':ll(y,PB),'prior_state_related':ll(y,PG),
             'gain_prior_state_vs_v75':ll(y,P75)-ll(y,PB),'gain_gate_vs_v75':ll(y,P75)-ll(y,PG),
             'gain_gate_vs_prior_state':ll(y,PB)-ll(y,PG),'unseen_fraction':float(U.mean()),'folds':folds}
        out['worlds'][name]=rec; gains.append(rec['gain_prior_state_vs_v75']); gate_gains.append(rec['gain_gate_vs_v75'])
        print(name,'SUMMARY',rec,flush=True)
    # Promotion is based on broad lawful transfer, not objective-cold alone.
    key=['session_cold','objective_cold','objective_family_cold','style_cold','mixed_support']
    g=np.asarray([out['worlds'][x]['gain_gate_vs_v75'] for x in key])
    gp=np.asarray([out['worlds'][x]['gain_prior_state_vs_v75'] for x in key])
    mixed=out['worlds']['mixed_support']['gain_gate_vs_v75']; session=out['worlds']['session_cold']['gain_gate_vs_v75']
    promote=(g.mean()>=.0015 and mixed>=.0010 and session>=-.0005 and g.min()>=-.0010)
    out['decision']={'mean_gate_gain':float(g.mean()),'mean_prior_state_gain':float(gp.mean()),'mixed_support_gain':float(mixed),
      'worst_gate_gain':float(g.min()),'verdict':'PROMOTE_V105_COMPOSITION' if promote else 'DO_NOT_PROMOTE_V105',
      'precommit':'promote iff mean five-world gate gain >= .0015, mixed-support >= .0010, session-cold >= -.0005, no world worse than -.0010'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v105_prior_state_composition.json'); run(p.parse_args())

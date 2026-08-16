#!/usr/bin/env python3
"""V104: single-separator test for session-level applicability.

V102 localized most oracle headroom to session resolution, while V103's multivariate
session regressor overfit/regressed. This test asks the cheapest next question: does one
runtime-visible session statistic lawfully separate sessions that want MORE vs LESS
RELATED than frozen V97's 0.35 blend?

Selection is nested. Outer objective-cold folds are untouched. Inside each outer-train,
objective-grouped OOF expert predictions are used to choose exactly one feature,
threshold, direction, and two blend weights. The chosen rule is then applied unchanged
to the outer validation fold.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from v71_mastery_events import load_transcript, tokens
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups
from v94_related_control import segmented_control, build_control

EPS=1e-5
WEIGHTS=np.array([0.0,0.15,0.25,0.35,0.45,0.60])
FEATURE_NAMES=['n_rows','p0_mean','pr_mean','abs_disagree_mean','disagree_std','signed_disagree_mean',
               'frac_abs_gt_03','frac_abs_gt_06','frac_abs_gt_10','p0_conf','pr_conf','turns','obj_len','n_objectives']


def fit_expert(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))

def sf(p0,pr,idx,turns,obj_len,nobj):
    a=p0[idx]; b=pr[idx]; d=b-a
    return np.array([len(idx),a.mean(),b.mean(),np.mean(np.abs(d)),np.std(d),np.mean(d),
        np.mean(np.abs(d)>.03),np.mean(np.abs(d)>.06),np.mean(np.abs(d)>.10),
        np.mean(np.abs(a-.5)),np.mean(np.abs(b-.5)),np.mean(turns[idx]),np.mean(obj_len[idx]),float(nobj)],float)

def session_table(y,p0,pr,sess,obj,turns,obj_len,indices):
    rows=[]
    for s in np.unique(sess[indices]):
        loc_global=indices[np.where(sess[indices]==s)[0]]
        z=sf(p0,pr,loc_global,turns,obj_len,len(np.unique(obj[loc_global])))
        rows.append((s,loc_global,z))
    return rows

def choose_rule(y,p0,pr,rows):
    # Predeclared quantile thresholds; choose one feature + threshold + direction + two weights.
    Z=np.vstack([r[2] for r in rows])
    best=(1e99,None)
    for j,name in enumerate(FEATURE_NAMES):
        vals=Z[:,j]
        for q in (0.2,0.35,0.5,0.65,0.8):
            t=float(np.quantile(vals,q))
            for direction in ('low_more','high_more'):
                for w_more in (0.45,0.60):
                    for w_less in (0.0,0.15,0.25,0.35):
                        pred=np.empty(len(y)); mask=np.zeros(len(y),bool)
                        for _,ix,z in rows:
                            more=(z[j] <= t) if direction=='low_more' else (z[j] > t)
                            w=w_more if more else w_less
                            pred[ix]=(1-w)*p0[ix]+w*pr[ix]; mask[ix]=True
                        v=ll(y[mask],pred[mask])
                        if v<best[0]: best=(v,{'feature':name,'feature_index':j,'threshold':t,'direction':direction,'w_more':w_more,'w_less':w_less})
    return best

def apply_rule(p0,pr,rows,rule,n):
    q=np.empty(n)
    j=rule['feature_index']; t=rule['threshold']; direction=rule['direction']
    weights=[]
    for _,ix,z in rows:
        more=(z[j] <= t) if direction=='low_more' else (z[j] > t)
        w=rule['w_more'] if more else rule['w_less']; q[ix]=(1-w)*p0[ix]+w*pr[ix]; weights.extend([w]*len(ix))
    return q,np.asarray(weights)

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1,flush=True)
    X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy(); text=f.learning_objective.astype(str).to_numpy()
    turns=np.asarray([len(cache[str(s)]) for s in sess],float); obj_len=np.asarray([len(tokens(x)) for x in text],float)
    p97_all=np.zeros(len(y)); p104_all=np.zeros(len(y)); folds=[]
    for k,(tr,va) in enumerate(folds_from_groups(obj),1):
        p0=np.zeros(len(y)); pr=np.zeros(len(y))
        p0[va]=fit_expert(X0,y,tr,va); pr[va]=fit_expert(Xr,y,tr,va)
        ip0=np.zeros(len(y)); ipr=np.zeros(len(y))
        inner=GroupKFold(min(3,len(np.unique(obj[tr])))).split(np.zeros(len(tr)),y[tr],obj[tr])
        for itr_l,iva_l in inner:
            itr=tr[itr_l]; iva=tr[iva_l]
            ip0[iva]=fit_expert(X0,y,itr,iva); ipr[iva]=fit_expert(Xr,y,itr,iva)
        train_rows=session_table(y,ip0,ipr,sess,obj,turns,obj_len,tr)
        _,rule=choose_rule(y,ip0,ipr,train_rows)
        va_rows=session_table(y,p0,pr,sess,obj,turns,obj_len,va)
        q=np.empty(len(y)); qva,w=apply_rule(p0,pr,va_rows,rule,len(y)); q[va]=qva[va]
        q97=np.clip(.65*p0[va]+.35*pr[va],EPS,1-EPS); q104=np.clip(q[va],EPS,1-EPS)
        p97_all[va]=q97; p104_all[va]=q104
        folds.append({'fold':k,'v97':ll(y[va],q97),'v104':ll(y[va],q104),'gain':ll(y[va],q97)-ll(y[va],q104),
                      'rule':rule,'mean_weight':float(np.mean(w))})
        print(folds[-1],flush=True)
    l97=ll(y,p97_all); l104=ll(y,p104_all); gain=l97-l104
    verdict='PROMOTE_TO_FOUR_WORLD_V104' if gain>=.002 else ('REFINE_SINGLE_SEPARATOR' if gain>=.0005 else 'SUPPRESS_SINGLE_SEPARATOR')
    out={'primary':'nested single session separator','v97':l97,'v104':l104,'gain_vs_v97':gain,'folds':folds,
         'decision':{'verdict':verdict,'precommit':'promote only if objective-cold gain vs frozen V97 >= 0.002'}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v104_single_session_separator.json'); run(p.parse_args())

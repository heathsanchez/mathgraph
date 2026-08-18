#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from v74_semantic_objective_prior import load_training, semantic_prior_predict
EPS=1e-5

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS)))

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    print('columns',list(f.columns),flush=True)
    y=f.target.to_numpy(int); sess=f.session_id.astype(str).to_numpy(); key=f.learning_objective.astype(str).to_numpy()
    grp=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    p=np.zeros(len(f)); support=np.zeros(len(f)); folds=[]
    for k,(tr,va) in enumerate(GroupKFold(5).split(np.zeros(len(y)),y,sess),1):
        ph,_=semantic_prior_predict(f.iloc[tr],f.iloc[va],k=16,smooth=2.0);p[va]=ph
        vals,cts=np.unique(key[tr],return_counts=True);d=dict(zip(vals,cts));support[va]=np.array([d.get(x,0) for x in key[va]],float)
        folds.append({'fold':k,'rows':len(va),'v74_ll':ll(y[va],ph),'support_rate':float(np.mean(support[va]>0))})
    session_ll=ll(y,p); support_rate=float(np.mean(support>0))
    bins=[('ZERO',support==0),('1_2',(support>=1)&(support<=2)),('3_9',(support>=3)&(support<=9)),('10_29',(support>=10)&(support<=29)),('30_PLUS',support>=30)]
    strat={}
    rowloss=-(y*np.log(np.clip(p,EPS,1))+(1-y)*np.log(np.clip(1-p,EPS,1)));tot=rowloss.sum()
    for n,m in bins:
        if m.any(): strat[n]={'rows':int(m.sum()),'share':float(m.mean()),'v74_ll':ll(y[m],p[m]),'loss_share':float(rowloss[m].sum()/tot),'mean_support':float(support[m].mean())}
    po=np.zeros(len(f))
    for tr,va in GroupKFold(5).split(np.zeros(len(y)),y,grp): po[va],_=semantic_prior_predict(f.iloc[tr],f.iloc[va],k=16,smooth=2.0)
    obj_ll=ll(y,po)
    out={'rows':len(f),'sessions':int(f.session_id.nunique()),'objectives':int(f.learning_objective.nunique()),'positive_rate':float(y.mean()),'session_cold_v74':session_ll,'session_exact_objective_support_rate':support_rate,'session_folds':folds,'support_strata':strat,'objective_cold_v74_stress':obj_ll,'session_minus_objective_advantage':obj_ll-session_ll,'decision':{'verdict':'V74_SESSION_GEOMETRY_CONFIRMED' if session_ll<=.56 and support_rate>=.60 else 'V74_SESSION_GEOMETRY_NOT_CONFIRMED','rule':'Confirm if session-cold V74 <=.560 and fold-local exact objective support >=60%. Runtime promotion still requires comparison to verified incumbent/public test.'}}
    Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--out',default='v115b_pure_v74_reality_audit.json');run(p.parse_args())

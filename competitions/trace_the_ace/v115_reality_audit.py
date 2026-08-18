#!/usr/bin/env python3
"""V115 Reality Audit.

Primary question: did we over-optimize objective-cold validation and underweight the
competition's natural new-session / same-objective regime?

Frozen outputs:
- full 35,072-row 5-fold session-grouped OOF for pure V74, V75 and V97;
- pure V74 support/frequency stratification using fold-local objective support;
- per-fold gains and objective-frequency contribution to log loss;
- deterministic provider-proxy stratification from transcript structure only;
- objective-grouped stress results are reported as a secondary contrast, not a gate.

No test labels, no cross-validation leakage, no cross-test aggregation.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript, normalize_roles
from v74_semantic_objective_prior import semantic_prior_predict
from v75_canonical_trajectory import load_training, build_v75 if False else trajectory_views, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control

EPS=1e-5

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS)))

def provider_proxy(df):
    """Deterministic structural proxy only; deliberately not claimed as true provider ID."""
    d=normalize_roles(df).reset_index(drop=True)
    roles=d.role_repaired.astype(str).str.lower().to_numpy()
    txt=d.content.fillna('').astype(str).tolist()
    n=len(d); stu=int(np.sum(roles=='student')); tut=int(np.sum(roles=='tutor'))
    mean_words=float(np.mean([len(x.split()) for x in txt])) if txt else 0.0
    markers=sum(bool(re.search(r'\b(?:learning objective|learning goal|prior learning|i do|we do|you do|application|slide|lesson)\b',x,re.I)) for x in txt)
    # Long lesson / curriculum-marker sessions are TSL-like; compact chats Eedi-like.
    tsl_like=(n>=24) or (markers>=2) or (tut>=12 and mean_words>=8)
    return 'TSL_LIKE' if tsl_like else 'EEDI_LIKE'

def fit_logit(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)

def p97_endpoint(X75,Xr,y,key,tr,va):
    p75=fit_logit(X75,y,tr,va); pr=fit_logit(Xr,y,tr,va)
    support={x:0 for x in []}
    vals,cts=np.unique(key[tr],return_counts=True); d=dict(zip(vals,cts))
    seen=np.array([d.get(x,0)>0 for x in key[va]])
    p=np.where(seen,p75,.65*p75+.35*pr)
    return np.clip(p,EPS,1-EPS),p75,pr,np.array([d.get(x,0) for x in key[va]],float)

def eval_session(frame,cache):
    y=frame.target.to_numpy(int); key=frame.learning_objective.astype(str).to_numpy(); sess=frame.session_id.astype(str).to_numpy()
    X75=build_v75(frame,cache)
    rt=[];rz=[]
    for _,r in frame.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t);rz.append(z)
    Xr=build_control(rt,rz)
    splits=list(GroupKFold(5).split(np.zeros(len(y)),y,sess))
    p74=np.zeros(len(y));p75=np.zeros(len(y));p97=np.zeros(len(y));support=np.zeros(len(y));fold=np.zeros(len(y),int)
    folds=[]
    for k,(tr,va) in enumerate(splits):
        ph,_=semantic_prior_predict(frame.iloc[tr],frame.iloc[va],k=16,smooth=2.0);p74[va]=ph
        q,q75,qr,s=p97_endpoint(X75,Xr,y,key,tr,va);p97[va]=q;p75[va]=q75;support[va]=s;fold[va]=k
        folds.append({'fold':k+1,'rows':len(va),'v74':ll(y[va],p74[va]),'v75':ll(y[va],p75[va]),'v97':ll(y[va],p97[va])})
    # support bins frozen before seeing results
    bins=[('ZERO',lambda s:s==0),('1_2',lambda s:(s>=1)&(s<=2)),('3_9',lambda s:(s>=3)&(s<=9)),('10_29',lambda s:(s>=10)&(s<=29)),('30_PLUS',lambda s:s>=30)]
    strat={}
    rowloss=-(y*np.log(np.clip(p74,EPS,1))+(1-y)*np.log(np.clip(1-p74,EPS,1)))
    total=float(rowloss.sum())
    for name,fn in bins:
        m=fn(support)
        if m.any(): strat[name]={'rows':int(m.sum()),'share':float(m.mean()),'mean_support':float(support[m].mean()),'v74_ll':ll(y[m],p74[m]),'v75_ll':ll(y[m],p75[m]),'v97_ll':ll(y[m],p97[m]),'v74_loss_share':float(rowloss[m].sum()/total)}
    return {'v74':ll(y,p74),'v75':ll(y,p75),'v97':ll(y,p97),'folds':folds,'support_strata':strat},(p74,p75,p97,support)

def objective_stress(frame):
    y=frame.target.to_numpy(int); grp=(frame.learning_objective_id if 'learning_objective_id' in frame else frame.learning_objective).astype(str).to_numpy();p=np.zeros(len(y))
    for tr,va in GroupKFold(5).split(np.zeros(len(y)),y,grp): p[va],_=semantic_prior_predict(frame.iloc[tr],frame.iloc[va],k=16,smooth=2.0)
    return ll(y,p)

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    print('features columns',list(f.columns),flush=True)
    print('rows',len(f),'sessions',f.session_id.nunique(),'objectives',f.learning_objective.nunique(),flush=True)
    cache={}
    proxy={}
    for i,sid in enumerate(f.session_id.astype(str).unique()):
        d=load_transcript(a.transcripts/f'{sid}.csv');cache[sid]=d;proxy[sid]=provider_proxy(d)
        if (i+1)%5000==0: print('loaded sessions',i+1,flush=True)
    session,(p74,p75,p97,support)=eval_session(f,cache)
    y=f.target.to_numpy(int);reg=np.array([proxy[str(s)] for s in f.session_id.astype(str)])
    regimes={}
    for r in ['EEDI_LIKE','TSL_LIKE']:
        m=reg==r
        regimes[r]={'rows':int(m.sum()),'sessions':int(f.loc[m,'session_id'].nunique()),'share':float(m.mean()),'v74':ll(y[m],p74[m]),'v75':ll(y[m],p75[m]),'v97':ll(y[m],p97[m]),'v74_gain_vs_v75':ll(y[m],p75[m])-ll(y[m],p74[m])}
    objstress=objective_stress(f)
    delta=session['v75']-session['v74']
    # Frozen interpretation. V74 is a leaderboard-priority candidate if it beats V75 by >= .010 session-cold and >=60% rows have exact support.
    supported=float(np.mean(support>0))
    verdict='PRIORITIZE_PURE_V74_RUNTIME' if delta>=.010 and supported>=.60 else ('V74_REAL_BUT_MIXED' if delta>=.003 else 'V74_NOT_PRIMARY')
    out={'diagnostics':{'rows':len(f),'sessions':int(f.session_id.nunique()),'objectives':int(f.learning_objective.nunique()),'positive_rate':float(y.mean()),'session_exact_objective_support_rate':supported,'provider_proxy_is_heuristic':True},'session_cold':session,'objective_cold_v74_stress':objstress,'provider_proxy':regimes,'decision':{'verdict':verdict,'v74_gain_vs_v75_session':delta,'rule':'PRIORITIZE pure V74 if session-cold gain vs V75 >=.010 and >=60% validation rows have fold-local exact-objective support; objective-cold is secondary stress only.'}}
    Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',default='v115_reality_audit.json');run(p.parse_args())

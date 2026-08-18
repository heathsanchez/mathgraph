#!/usr/bin/env python3
"""V111 FAST SCREEN — decision-changing residual tests in one shared pass.
Screen only; winners require untouched full verification before promotion.
Frozen before results: deterministic hash sample, V97 baseline, grouped OOF, no cross-test aggregates.
Primary question: which missing representation family can separate V97 residual collisions?
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from v110_residual_collider_state_discovery import hb, ll, logit, p97_predict, state_vec
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import build_v75, evidence_events
from v94_related_control import segmented_control, build_control

EPS=1e-5

def h(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def fit_oof(P,S,y,groups):
    q=np.zeros(len(y)); k=min(4,len(np.unique(groups)))
    for tr,va in GroupKFold(k).split(S,y,groups):
        sc=StandardScaler().fit(S[tr]); A=sc.transform(S[tr]); B=sc.transform(S[va])
        m=LogisticRegression(C=.15,max_iter=250,solver='liblinear',random_state=SEED).fit(np.c_[logit(P[tr]),A],y[tr])
        q[va]=m.predict_proba(np.c_[logit(P[va]),B])[:,1]
    return np.clip(q,EPS,1-EPS)
def evvec(E, mode):
    if not E: return np.zeros(12)
    pos=np.array([float(e['pos']) for e in E]); neg=np.array([float(e['neg']) for e in E]); ind=np.array([float(e['independent']) for e in E]); ass=np.array([float(e['assistance']) for e in E]); rel=np.array([float(e['rel']) for e in E]); n=len(E)
    if mode=='CONTENT':
        return np.array([n,pos.mean(),neg.mean(),ind.mean(),ass.mean(),rel.mean(),(pos*ind).mean(),(neg*rel).mean(),rel.max(),rel[-1],pos.sum()/max(1,n),neg.sum()/max(1,n)])
    if mode=='TERMINAL':
        z=np.arange(n); lastp=np.max(np.where(pos>0,z,-1)); lastn=np.max(np.where(neg>0,z,-1)); lasti=np.max(np.where((pos*ind)>0,z,-1));
        return np.array([n,pos[-1],neg[-1],ind[-1],ass[-1],rel[-1],lastp/n,lastn/n,lasti/n,(lasti-lastn)/n,(lastp-lastn)/n,(pos[-min(3,n):]*ind[-min(3,n):]).mean()])
    if mode=='ORDER':
        return state_vec(E,(.7,.5,.7,.75),False)[:12]
    if mode=='ORDER_ABLATE':
        return state_vec(E,(.7,.5,.7,.75),True)[:12]
    raise ValueError(mode)

def main(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    print('features columns',list(f.columns),flush=True)
    # deterministic balanced screen: discovery objectives only, <= N rows, preserve many objectives
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    cand=np.where(np.array([hb(x,5)!=0 for x in obj]))[0]
    ix=np.array(sorted(cand,key=lambda i:h(f.response_id.iloc[i]))[:a.rows]); f=f.iloc[ix].reset_index(drop=True)
    y=f.target.to_numpy(int); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); support=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in np.unique(sess)}
    rt=[]; rz=[]; EV=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        seg,_=choose_target_segment(cache[str(r.session_id)],str(r.learning_objective)); EV.append(evidence_events(seg,str(r.learning_objective)))
    X75=build_v75(f,cache); Xr=build_control(rt,rz)
    P=np.zeros(len(f)); splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(f)),y,obj))
    for tr,va in splits: P[va],_=p97_predict(X75,Xr,y,tr,va,support)
    base=ll(y,P); out={'rows':len(f),'objectives':len(np.unique(obj)),'v97':base,'tests':{}}
    mats={m:np.vstack([evvec(E,m) for E in EV]) for m in ['CONTENT','TERMINAL','ORDER','ORDER_ABLATE']}
    # Highest-impact screen A: does event content carry missing information at all?
    for m,S in mats.items():
        q=fit_oof(P,S,y,obj); out['tests'][m]={'ll':ll(y,q),'gain':base-ll(y,q)}
    out['tests']['CHRONOLOGY_CAUSAL']={'gain':out['tests']['ORDER']['gain']-out['tests']['ORDER_ABLATE']['gain']}
    # Screen B: objective relevance is the suspected bottleneck. Remove rel dimensions and compare.
    S=mats['CONTENT'].copy(); Sr=S.copy(); Sr[:,5]=0; Sr[:,7]=0; Sr[:,8]=0; Sr[:,9]=0
    qr=fit_oof(P,Sr,y,obj); out['tests']['RELEVANCE_ABLATION']={'ll':ll(y,qr),'gain':base-ll(y,qr),'relevance_value':out['tests']['CONTENT']['gain']-(base-ll(y,qr))}
    # Screen C: tight residual geometry. Opposite-label nearest neighbor distance in P within objective.
    ds=[]
    for o in np.unique(obj):
        z=np.where(obj==o)[0]; a0=z[y[z]==0]; a1=z[y[z]==1]
        if len(a0) and len(a1):
            p1=np.sort(P[a1]); ds.extend([float(np.min(np.abs(p1-P[i]))) for i in a0])
    out['residual_geometry']={'opposite_nn_p_median':float(np.median(ds)) if ds else None,'opposite_nn_p_p10':float(np.quantile(ds,.1)) if ds else None,'pairs_basis':len(ds)}
    gains={k:v.get('gain',-9) for k,v in out['tests'].items() if isinstance(v,dict)}; winner=max(gains,key=gains.get)
    out['decision']={'winner':winner,'winner_gain':gains[winner],'rule':'Escalate only a family with >=.003 grouped-OOF screen gain; chronology requires >=.001 ORDER-over-ABLATE. Otherwise change observable/extraction, not grammar.'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--rows',type=int,default=2500); p.add_argument('--out',default='v111_fast_residual_screen.json'); main(p.parse_args())

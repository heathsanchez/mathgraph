#!/usr/bin/env python3
"""V110: residual-collider mastery-state discovery.

Freeze V97. Split objectives by SHA before grammar search. On discovery objectives,
produce objective-cold OOF V97 predictions, then search a small causal grammar of
ordered mastery-state machines. Select by grouped OOF log loss with a collider
constraint. Freeze the winning grammar. Verify on untouched objectives in two worlds:
(1) objective-cold/unseen support, (2) session-cold/supported support.

Phase-change claim requires >= .010 log-loss gain in either untouched world,
non-inferiority in the other, and ordered-state advantage over an order ablation.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import build_v75, evidence_events
from v94_related_control import segmented_control, build_control

EPS=1e-5

def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))
def logit(p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS); return np.log(p/(1-p))
def hb(x,n=5): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)%n

def fit_base(X,y,tr,va):
    m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
    return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)
def p97_predict(X75,Xr,y,tr,va,support):
    p75=fit_base(X75,y,tr,va); pr=fit_base(Xr,y,tr,va)
    seen=set(support[tr].tolist()); uns=np.asarray([support[i] not in seen for i in va],bool)
    q=np.where(uns,.65*p75+.35*pr,p75)
    return np.clip(q,EPS,1-EPS),uns


def sig(e):
    s=(str(e['state'])+'|'+str(round(float(e['rel']),2))+'|'+str(e['assistance'])+'|'+str(e['q'])).encode('utf8','ignore')
    return hashlib.sha1(s).hexdigest()
def state_vec(events,cfg,destroy_order=False):
    decay,rel_power,assist_pen,error_pen=cfg
    E=list(events)
    if destroy_order: E=sorted(E,key=sig)
    if not E: return np.zeros(14,float)
    vals=[]; K=[]; k=0.; streak=0; best_streak=0; recoveries=0; regressions=0
    last_neg=-1; last_ind=-1; ind_after_neg=0; contradictions_after_ind=0
    for t,e in enumerate(E):
        rel=max(.01,float(e['rel']))**rel_power
        ass=float(e['assistance']); ind=1. if e['independent'] else 0.
        if e['neg']: v=-error_pen*rel*(1.-.5*ass)
        elif e['pos']: v=rel*(assist_pen+(1-assist_pen)*(1-ass))*(1.+.35*ind)
        else: v=.05*rel*(1-ass)
        k=decay*k+v; vals.append(v); K.append(k)
        good=bool(e['pos'] and e['independent'])
        if good:
            streak+=1; best_streak=max(best_streak,streak); last_ind=t
            if last_neg>=0 and t>last_neg: ind_after_neg+=1
        elif e['neg']: streak=0; last_neg=t
        if t and E[t-1]['neg'] and e['pos']: recoveries+=1
        if t and E[t-1]['pos'] and e['neg']: regressions+=1
        if e['neg'] and last_ind>=0 and t>last_ind: contradictions_after_ind+=1
    V=np.asarray(vals,float); A=np.asarray(K,float); n=len(E)
    suffix=0
    for e in reversed(E):
        if e['pos'] and not e['neg']: suffix+=1
        else: break
    post_neg = float(sum(1 for j,e in enumerate(E) if j>last_neg and e['pos'] and e['independent'])) if last_neg>=0 else float(sum(e['pos'] and e['independent'] for e in E))
    return np.asarray([
        A[-1],A.max(),A.min(),A.mean(),A[-1]-A[0],V[-1],V.sum(),
        best_streak/n,suffix/n,recoveries/n,regressions/n,post_neg/n,
        contradictions_after_ind/n,ind_after_neg/n
    ],float)


def collider_mask(obj,p,y):
    b=np.floor(np.clip(p,0,.999999)*20).astype(int); keys=np.asarray([f'{o}|{z}' for o,z in zip(obj,b)])
    keep=np.zeros(len(y),bool)
    for k in np.unique(keys):
        ix=np.where(keys==k)[0]
        if len(ix)>=4 and len(np.unique(y[ix]))==2: keep[ix]=True
    return keep
def meta_cv(P,S,y,groups,splits):
    q=np.zeros(len(y)); covered=np.zeros(len(y),bool)
    for tr,va in splits:
        sc=StandardScaler().fit(S[tr]); ztr=sc.transform(S[tr]); zva=sc.transform(S[va])
        Xtr=np.c_[logit(P[tr]),ztr,ztr[:,0]*logit(P[tr])]
        Xva=np.c_[logit(P[va]),zva,zva[:,0]*logit(P[va])]
        m=LogisticRegression(C=.15,max_iter=300,solver='liblinear',random_state=SEED).fit(Xtr,y[tr])
        q[va]=np.clip(m.predict_proba(Xva)[:,1],EPS,1-EPS); covered[va]=True
    return q,covered
def fit_meta(P,S,y):
    sc=StandardScaler().fit(S); Z=sc.transform(S); X=np.c_[logit(P),Z,Z[:,0]*logit(P)]
    m=LogisticRegression(C=.15,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y)
    return sc,m
def apply_meta(sc,m,P,S):
    Z=sc.transform(S); X=np.c_[logit(P),Z,Z[:,0]*logit(P)]
    return np.clip(m.predict_proba(X)[:,1],EPS,1-EPS)


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    y=f.target.to_numpy(int); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    support=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
    print('features columns',list(f.columns),flush=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in np.unique(sess)}
    rt=[]; rz=[]; EV=[]
    for i,r in f.iterrows():
        sid=str(r.session_id); text=str(r.learning_objective)
        t,z=segmented_control(cache[sid],text,'related'); rt.append(t); rz.append(z)
        seg,_=choose_target_segment(cache[sid],text); EV.append(evidence_events(seg,text))
        if (i+1)%2500==0: print('rows',i+1,flush=True)
    X75=build_v75(f,cache); Xr=build_control(rt,rz)

    verify=np.asarray([hb(x,5)==0 for x in obj]); disc=~verify
    D=np.where(disc)[0]; V=np.where(verify)[0]
    print('split',{'discovery_rows':len(D),'verification_rows':len(V),'verification_objectives':int(len(np.unique(obj[V])))},flush=True)

    gd=obj[D]; nsp=min(4,len(np.unique(gd))); raw=list(GroupKFold(nsp).split(np.zeros(len(D)),y[D],gd))
    splits=[]; P=np.zeros(len(D))
    for ltr,lva in raw:
        tr=D[ltr]; va=D[lva]; q,_=p97_predict(X75,Xr,y,tr,va,support); P[lva]=q; splits.append((ltr,lva))
    base_disc=ll(y[D],P); C=collider_mask(obj[D],P,y[D]); print('discovery_v97',base_disc,'collider_rows',int(C.sum()),flush=True)

    configs=list(itertools.product([.50,.70,.85,.95],[.5,1.0,1.5],[.20,.45,.70],[.75,1.0,1.30]))
    leaderboard=[]; best=None; bestS=None
    for j,cfg in enumerate(configs):
        S=np.vstack([state_vec(EV[i],cfg,False) for i in D])
        q,cov=meta_cv(P,S,y[D],gd,splits); gain=base_disc-ll(y[D][cov],q[cov]); cg=(ll(y[D][C],P[C])-ll(y[D][C],q[C])) if C.sum() else 0.
        rec={'cfg':list(cfg),'gain':gain,'collider_gain':cg}
        leaderboard.append(rec)
        if cg>=0 and (best is None or gain>best['gain']): best=rec; bestS=S
        if (j+1)%24==0: print('grammar',j+1,'best',best,flush=True)
    if best is None: best=max(leaderboard,key=lambda r:r['gain']); bestS=np.vstack([state_vec(EV[i],tuple(best['cfg']),False) for i in D])
    cfg=tuple(best['cfg']); qord,cov=meta_cv(P,bestS,y[D],gd,splits)
    Sab=np.vstack([state_vec(EV[i],cfg,True) for i in D]); qab,_=meta_cv(P,Sab,y[D],gd,splits)
    ordered_gain=base_disc-ll(y[D],qord); ablated_gain=base_disc-ll(y[D],qab); causal=ordered_gain-ablated_gain
    print('SELECTED',best,'ordered_gain',ordered_gain,'ablation_gain',ablated_gain,'causal',causal,flush=True)

    sc_u,meta_u=fit_meta(P,bestS,y[D])
    pV,unsV=p97_predict(X75,Xr,y,D,V,support); SV=np.vstack([state_vec(EV[i],cfg,False) for i in V]); qV=apply_meta(sc_u,meta_u,pV,SV)
    verify_obj={'rows':int(len(V)),'unseen_fraction':float(unsV.mean()),'v97':ll(y[V],pV),'v110':ll(y[V],qV),'gain':ll(y[V],pV)-ll(y[V],qV)}
    print('VERIFY_OBJECTIVE',verify_obj,flush=True)

    ns=min(4,len(np.unique(sess[D]))); sraw=list(GroupKFold(ns).split(np.zeros(len(D)),y[D],sess[D])); Ps=np.zeros(len(D))
    for ltr,lva in sraw:
        tr=D[ltr]; va=D[lva]; qq,_=p97_predict(X75,Xr,y,tr,va,support); Ps[lva]=qq
    sc_s,meta_s=fit_meta(Ps,bestS,y[D])
    vv=V[np.asarray([hb(sess[i],5)==0 for i in V])]
    tr=np.where(np.asarray([hb(s,5)!=0 for s in sess]))[0]
    pS,unsS=p97_predict(X75,Xr,y,tr,vv,support); SS=np.vstack([state_vec(EV[i],cfg,False) for i in vv]); qS=apply_meta(sc_s,meta_s,pS,SS)
    verify_sess={'rows':int(len(vv)),'unseen_fraction':float(unsS.mean()),'v97':ll(y[vv],pS),'v110':ll(y[vv],qS),'gain':ll(y[vv],pS)-ll(y[vv],qS)}
    print('VERIFY_SESSION',verify_sess,flush=True)

    gains=[verify_obj['gain'],verify_sess['gain']]
    if max(gains)>=.010 and min(gains)>=-.001 and causal>=.001: verdict='PHASE_CHANGE_STATE_LIFT'
    elif max(gains)>=.003 and min(gains)>=-.001: verdict='PROMISING_STATE_LIFT'
    else: verdict='SUPPRESS_V110_GRAMMAR'
    out={'protocol':'objective-hash discovery/untouched verification','selected':best,'discovery':{'v97':base_disc,'ordered_gain':ordered_gain,'order_ablation_gain':ablated_gain,'causal_order_gain':causal,'collider_rows':int(C.sum()),'top10':sorted(leaderboard,key=lambda r:r['gain'],reverse=True)[:10]},'verification':{'objective_cold':verify_obj,'session_supported':verify_sess},'decision':{'verdict':verdict,'precommit':'PHASE_CHANGE iff max untouched gain >= .010, other >= -.001, causal order gain >= .001; PROMISING iff max >= .003 and other >= -.001'}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v110_residual_collider_state_discovery.json'); run(p.parse_args())

# Trigger-only low-level ref update; experiment logic unchanged.
# Low-level trigger sequence 2.

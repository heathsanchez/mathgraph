#!/usr/bin/env python3
"""V134: verifier x tutor-feedback contradiction over frozen V97.

V133 closes arithmetic truth in isolation. V75, however, derives mastery states from
tutor feedback. V134 tests the missing relation: whether independent arithmetic truth
agrees with the tutor's subsequent positive/negative judgment.

Control: deterministically rotate tutor judgments across verifiable events within each
session, preserving truth and feedback marginals while destroying their pairing.
No sweep. Outer validation untouched; residual fit uses inner-OOF V97 only.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from v110_residual_collider_state_discovery import ll,logit,p97_predict
from v75_canonical_trajectory import SEED,POS_RE,NEG_RE
from v133_verified_math_evidence import expected,answer_value,QUESTION_RE
EPS=1e-5; C=.05

def events(rows):
    out=[]
    for i,r in enumerate(rows):
        if str(r.get('role','')).lower()!='tutor': continue
        q=str(r.get('content',''))
        if not QUESTION_RE.search(q): continue
        ex=expected(q)
        if not np.isfinite(ex): continue
        ai=None
        for j in range(i+1,min(len(rows),i+6)):
            role=str(rows[j].get('role','')).lower(); txt=str(rows[j].get('content',''))
            if role=='student' and txt.strip(): ai=j; break
            if role=='tutor' and QUESTION_RE.search(txt) and j>i+1: break
        if ai is None: continue
        av=answer_value(rows[ai].get('content',''))
        if not np.isfinite(av): continue
        fb=''
        for j in range(ai+1,min(len(rows),ai+6)):
            if str(rows[j].get('role','')).lower()=='tutor': fb=str(rows[j].get('content','')); break
        judge=1 if POS_RE.search(fb) and not NEG_RE.search(fb) else -1 if NEG_RE.search(fb) and not POS_RE.search(fb) else 0
        truth=1 if np.isclose(av,ex,rtol=1e-6,atol=1e-6) else -1
        out.append((truth,judge,ai/max(1,len(rows)-1)))
    return out

def vec(E,shift=0):
    n=len(E)
    if not n:return np.zeros(10,float)
    truth=np.asarray([e[0] for e in E],float); judge=np.asarray([e[1] for e in E],float); rec=np.asarray([e[2] for e in E],float)
    if shift and n>1: judge=np.roll(judge,shift)
    judged=judge!=0; agree=judged&(truth==judge); contra=judged&(truth!=judge)
    false_pos=(judge==1)&(truth==-1); false_neg=(judge==-1)&(truth==1)
    w=np.exp(2*(rec-1));w/=w.sum()+1e-12
    def mean(x):return float(np.mean(x))
    return np.asarray([np.log1p(n),mean(judged),mean(agree),mean(contra),mean(false_pos),mean(false_neg),float((w*contra).sum()),float((w*agree).sum()),float(rec[contra].max()) if np.any(contra) else 0.,float(contra[-1])],float)

def inner_base(X75,Xr,y,groups,support):
    P=np.zeros(len(y)); nsp=min(3,len(np.unique(groups)))
    for tr,va in GroupKFold(nsp).split(np.zeros(len(y)),y,groups):P[va],_=p97_predict(X75,Xr,y,tr,va,support)
    return np.clip(P,EPS,1-EPS)
def fit_res(P,R,y):
    mu=R.mean(0);sd=R.std(0)+1e-6;X=np.c_[logit(P),(R-mu)/sd]
    m=LogisticRegression(C=C,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y);return mu,sd,m
def apply_res(mod,P,R):
    mu,sd,m=mod;X=np.c_[logit(P),(R-mu)/sd];return np.clip(m.predict_proba(X)[:,1],EPS,1-EPS)
def eval_geom(name,groups,X75,Xr,y,support,R,A,covered):
    groups=np.asarray(groups);PB=np.zeros(len(y));QR=np.zeros(len(y));QA=np.zeros(len(y));folds=[]
    for k,(tr,va) in enumerate(GroupKFold(min(4,len(np.unique(groups)))).split(np.zeros(len(y)),y,groups),1):
        pva,_=p97_predict(X75,Xr,y,tr,va,support);pin=inner_base(X75[tr],Xr[tr],y[tr],groups[tr],support[tr])
        qr=apply_res(fit_res(pin,R[tr],y[tr]),pva,R[va]);qa=apply_res(fit_res(pin,A[tr],y[tr]),pva,A[va]);PB[va]=pva;QR[va]=qr;QA[va]=qa
        folds.append({'fold':k,'base_ll':ll(y[va],pva),'contradiction_ll':ll(y[va],qr),'control_ll':ll(y[va],qa),'covered':int(covered[va].sum())})
    b,r,a=ll(y,PB),ll(y,QR),ll(y,QA);cov=np.asarray(covered,bool)
    return {'geometry':name,'baseline_v97_ll':b,'contradiction':{'ll':r,'gain':b-r},'rotated_judgment_control':{'ll':a,'gain':b-a},'real_minus_control_gain':a-r,'coverage_fraction':float(cov.mean()),'covered_rows':int(cov.sum()),'covered_only':({'baseline_ll':ll(y[cov],PB[cov]),'contradiction_ll':ll(y[cov],QR[cov]),'gain':ll(y[cov],PB[cov])-ll(y[cov],QR[cov])} if cov.any() else None),'folds':folds}
def main(a):
    d=Path(a.dir);z=np.load(d/'arrays.npz',allow_pickle=True);y=z['y'];obj=z['objectives'];support=z['support'];sessions=z['sessions'];X75=load_npz(d/'X75.npz');Xr=load_npz(d/'Xr.npz');cache={}
    with zipfile.ZipFile(a.archive) as za:
        names=set(za.namelist())
        for sid in np.unique(sessions):
            name=f'{sid}.csv'
            if name not in names:raise RuntimeError('missing '+name)
            with za.open(name) as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            E=events(rows);shift=(1+int(hashlib.sha256(str(sid).encode()).hexdigest()[:8],16)%max(1,len(E)-1)) if len(E)>1 else 0
            cache[str(sid)]=(vec(E,0),vec(E,shift),len(E))
    R=np.vstack([cache[str(s)][0] for s in sessions]);A=np.vstack([cache[str(s)][1] for s in sessions]);covered=np.asarray([cache[str(s)][2]>0 for s in sessions])
    out={'protocol':'V134_VERIFIER_FEEDBACK_CONTRADICTION','rows':int(len(y)),'hypothesis':'independent truth x tutor judgment contradiction is a missing sample-local relation over V97','precommit':{'residual_C':C,'outer_folds':4,'inner_folds':3,'no_sweep':True,'promote_gain_each_geometry':.001,'real_minus_control_each_geometry':.0005,'phase_change_gain_each_geometry':.003}}
    out['objective_grouped']=eval_geom('objective_grouped',obj,X75,Xr,y,support,R,A,covered);out['session_grouped']=eval_geom('session_grouped',sessions,X75,Xr,y,support,R,A,covered)
    def ok(x,t=.001):return x['contradiction']['gain']>=t and x['real_minus_control_gain']>=.0005
    po,ps=ok(out['objective_grouped']),ok(out['session_grouped']);phase=ok(out['objective_grouped'],.003) and ok(out['session_grouped'],.003)
    out['decision']={'objective_pass':bool(po),'session_pass':bool(ps),'verdict':'PHASE_CHANGE_VERIFIER_FEEDBACK_CONTRADICTION' if phase else 'PROMOTE_VERIFIER_FEEDBACK_CONTRADICTION' if po and ps else 'SUPPRESS_VERIFIER_FEEDBACK_CONTRADICTION'}
    Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--dir',required=True);p.add_argument('--out',required=True);main(p.parse_args())

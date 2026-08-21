#!/usr/bin/env python3
"""V133: verifier-derived mathematical evidence over frozen V97.

Constraint-derived hypothesis: current residual requires a new sample-local observable,
not another semantic/routing feature. V75 records tutor feedback but never independently
checks whether an explicit arithmetic student answer is mathematically correct.

Primary separator: exact arithmetic question->student-answer verification.
Control: deterministically rotate student numeric answers among the same session's
verifiable questions, preserving question/answer marginals but destroying the relation.
No threshold/feature sweep. Each outer fold fits the residual only from inner-OOF V97
predictions on outer-training rows, then evaluates untouched outer validation rows.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from v110_residual_collider_state_discovery import ll,logit,p97_predict
from v75_canonical_trajectory import SEED

EPS=1e-5
C=.05
NUM=r"(-?\d+(?:\.\d+)?(?:\s*/\s*-?\d+(?:\.\d+)?)?)"
PATTERNS=[
 (re.compile(rf"{NUM}\s*(?:\+|plus)\s*{NUM}",re.I),lambda a,b:a+b),
 (re.compile(rf"{NUM}\s*(?:-|minus)\s*{NUM}",re.I),lambda a,b:a-b),
 (re.compile(rf"{NUM}\s*(?:x|×|\*|times|multiplied\s+by)\s*{NUM}",re.I),lambda a,b:a*b),
 (re.compile(rf"{NUM}\s*(?:/|÷|divided\s+by)\s*{NUM}",re.I),lambda a,b:a/b if abs(b)>1e-12 else np.nan),
]
ANS_RE=re.compile(NUM)
QUESTION_RE=re.compile(r"\?|\b(?:what|calculate|work out|solve|how much|how many)\b",re.I)

def number(s):
    s=str(s).replace(' ','')
    try:
        if '/' in s:
            a,b=s.split('/',1); b=float(b); return float(a)/b if abs(b)>1e-12 else np.nan
        return float(s)
    except Exception:return np.nan

def expected(q):
    q=str(q).replace(',','')
    for p,op in PATTERNS:
        m=p.search(q)
        if m:
            a,b=number(m.group(1)),number(m.group(2))
            if np.isfinite(a) and np.isfinite(b):
                try:return float(op(a,b))
                except Exception:return np.nan
    return np.nan

def answer_value(a):
    m=ANS_RE.search(str(a).replace(',',''))
    return number(m.group(1)) if m else np.nan

def events(rows):
    out=[]
    for i,r in enumerate(rows):
        if str(r.get('role','')).lower()!='tutor':continue
        q=str(r.get('content',''))
        if not QUESTION_RE.search(q):continue
        e=expected(q)
        if not np.isfinite(e):continue
        ai=None
        for j in range(i+1,min(len(rows),i+6)):
            role=str(rows[j].get('role','')).lower(); txt=str(rows[j].get('content',''))
            if role=='student' and txt.strip(): ai=j; break
            if role=='tutor' and QUESTION_RE.search(txt) and j>i+1: break
        if ai is None:continue
        av=answer_value(rows[ai].get('content',''))
        if np.isfinite(av):out.append((e,av,ai/max(1,len(rows)-1)))
    return out

def vec(E,shift=0):
    n=len(E)
    if not n:return np.zeros(8,float)
    ans=np.asarray([x[1] for x in E],float)
    if shift and n>1: ans=np.roll(ans,shift)
    exp=np.asarray([x[0] for x in E],float); rec=np.asarray([x[2] for x in E],float)
    ok=np.isclose(ans,exp,rtol=1e-6,atol=1e-6).astype(float); bad=1-ok
    w=np.exp(2*(rec-1)); w/=w.sum()+1e-12
    return np.asarray([np.log1p(n),ok.mean(),bad.mean(),ok[-1]-bad[-1],float((w*ok).sum()),float((w*bad).sum()),float(rec[ok>0].max()) if np.any(ok>0) else 0.,float(rec[bad>0].max()) if np.any(bad>0) else 0.],float)

def inner_base(X75,Xr,y,groups,support):
    nsp=min(3,len(np.unique(groups))); P=np.zeros(len(y))
    for tr,va in GroupKFold(nsp).split(np.zeros(len(y)),y,groups): P[va],_=p97_predict(X75,Xr,y,tr,va,support)
    return np.clip(P,EPS,1-EPS)
def fit_res(P,R,y):
    mu=R.mean(0); sd=R.std(0)+1e-6
    X=np.c_[logit(P),(R-mu)/sd]
    m=LogisticRegression(C=C,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y)
    return mu,sd,m
def apply_res(mod,P,R):
    mu,sd,m=mod; X=np.c_[logit(P),(R-mu)/sd]
    return np.clip(m.predict_proba(X)[:,1],EPS,1-EPS)
def eval_geom(name,groups,X75,Xr,y,support,R,A,covered):
    groups=np.asarray(groups); PB=np.zeros(len(y)); QR=np.zeros(len(y)); QA=np.zeros(len(y)); rows=[]
    for k,(tr,va) in enumerate(GroupKFold(min(4,len(np.unique(groups)))).split(np.zeros(len(y)),y,groups),1):
        pva,_=p97_predict(X75,Xr,y,tr,va,support); pin=inner_base(X75[tr],Xr[tr],y[tr],groups[tr],support[tr])
        qr=apply_res(fit_res(pin,R[tr],y[tr]),pva,R[va]); qa=apply_res(fit_res(pin,A[tr],y[tr]),pva,A[va])
        PB[va]=pva;QR[va]=qr;QA[va]=qa
        rows.append({'fold':k,'rows':int(len(va)),'base_ll':ll(y[va],pva),'verified_ll':ll(y[va],qr),'control_ll':ll(y[va],qa),'covered':int(covered[va].sum())})
    b,r,a=ll(y,PB),ll(y,QR),ll(y,QA); cov=np.asarray(covered,bool)
    return {'geometry':name,'baseline_v97_ll':b,'verified':{'ll':r,'gain':b-r},'rotated_control':{'ll':a,'gain':b-a},'real_minus_control_gain':a-r,'coverage_fraction':float(cov.mean()),'covered_rows':int(cov.sum()),'covered_only':({'baseline_ll':ll(y[cov],PB[cov]),'verified_ll':ll(y[cov],QR[cov]),'gain':ll(y[cov],PB[cov])-ll(y[cov],QR[cov])} if cov.any() else None),'folds':rows}
def main(a):
    d=Path(a.dir); z=np.load(d/'arrays.npz',allow_pickle=True); y=z['y']; obj=z['objectives']; support=z['support']; sessions=z['sessions']
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz'); cache={}
    with zipfile.ZipFile(a.archive) as za:
        names=set(za.namelist())
        for sid in np.unique(sessions):
            name=f'{sid}.csv'
            if name not in names:raise RuntimeError('missing '+name)
            with za.open(name) as f: rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            E=events(rows); shift=(1+int(hashlib.sha256(str(sid).encode()).hexdigest()[:8],16)%max(1,len(E)-1)) if len(E)>1 else 0
            cache[str(sid)]=(vec(E,0),vec(E,shift),len(E))
    R=np.vstack([cache[str(s)][0] for s in sessions]); A=np.vstack([cache[str(s)][1] for s in sessions]); covered=np.asarray([cache[str(s)][2]>0 for s in sessions])
    out={'protocol':'V133_VERIFIED_MATH_EVIDENCE','rows':int(len(y)),'hypothesis':'independent arithmetic verification is a missing sample-local observable over V97','precommit':{'residual_C':C,'outer_folds':4,'inner_folds':3,'no_sweep':True,'promote_gain_each_geometry':.001,'real_minus_control_each_geometry':.0005,'phase_change_gain_each_geometry':.003}}
    out['objective_grouped']=eval_geom('objective_grouped',obj,X75,Xr,y,support,R,A,covered)
    out['session_grouped']=eval_geom('session_grouped',sessions,X75,Xr,y,support,R,A,covered)
    def ok(x,t=.001):return x['verified']['gain']>=t and x['real_minus_control_gain']>=.0005
    po,ps=ok(out['objective_grouped']),ok(out['session_grouped']); phase=ok(out['objective_grouped'],.003) and ok(out['session_grouped'],.003)
    out['decision']={'objective_pass':bool(po),'session_pass':bool(ps),'verdict':'PHASE_CHANGE_VERIFIED_MATH_EVIDENCE' if phase else 'PROMOTE_VERIFIED_MATH_EVIDENCE' if po and ps else 'SUPPRESS_VERIFIED_MATH_EVIDENCE'}
    Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--dir',required=True);p.add_argument('--out',required=True);main(p.parse_args())

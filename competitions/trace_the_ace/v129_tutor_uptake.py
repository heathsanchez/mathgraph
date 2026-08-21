#!/usr/bin/env python3
"""V129 TUTOR UPTAKE residual over frozen V97.

Primary separator: whether the tutor's next utterance lexically/structurally takes
up the student's immediately preceding language. V75 raw hashing preserves words,
but not this cross-turn relation explicitly.

Control: deterministically rotate tutor replies among student->tutor pairs inside
each session, preserving the exact student/tutor text multisets and pair count while
destroying local response alignment. No labels enter feature construction. No sweep.
"""
from __future__ import annotations
import argparse,csv,io,json,re,zipfile,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from v110_residual_collider_state_discovery import ll,logit
from v121_pretrained_semantic_residual import p97_oof,collision_mask
from v75_canonical_trajectory import SEED

TOK=re.compile(r"[a-z0-9]+(?:\.[0-9]+)?",re.I)
NEG=re.compile(r"\b(?:no|not quite|incorrect|wrong|careful|try again|almost|remember|instead|actually)\b",re.I)
POS=re.compile(r"\b(?:yes|yeah|correct|right|exactly|perfect|good|great|well done|that's it|thats it|you got it|spot on)\b",re.I)
QUESTION=re.compile(r"\?|\b(?:what|which|how|why|can you|could you|tell me|work out|calculate|solve|find)\b",re.I)
STOP={'the','a','an','and','or','to','of','in','on','for','with','is','are','be','as','by','from','this','that','these','those','you','your','we','it','its'}
EPS=1e-5

def toks(s): return {x for x in TOK.findall(str(s).lower()) if len(x)>1 and x not in STOP}
def jac(a,b):
    A,B=toks(a),toks(b)
    return len(A&B)/len(A|B) if A and B else 0.0

def pairs(rows):
    out=[]
    for i,r in enumerate(rows[:-1]):
        if str(r.get('role','')).lower()!='student': continue
        s=str(r.get('content',''))
        j=None
        for k in range(i+1,min(len(rows),i+4)):
            if str(rows[k].get('role','')).lower()=='tutor': j=k; break
            if str(rows[k].get('role','')).lower()=='student': break
        if j is not None: out.append((s,str(rows[j].get('content',''))))
    return out

def feats(P,shift=0):
    if not P: return np.zeros(10,float)
    S=[p[0] for p in P]; T=[p[1] for p in P]; n=len(P)
    if shift and n>1: T=T[shift%n:]+T[:shift%n]
    o=np.array([jac(s,t) for s,t in zip(S,T)],float)
    neg=np.array([bool(NEG.search(t)) for t in T]); pos=np.array([bool(POS.search(t)) for t in T]); q=np.array([bool(QUESTION.search(t)) for t in T])
    substantive=np.array([len(toks(s))>=2 or bool(re.search(r'\d|[=+\-/*×÷%]',s)) for s in S])
    def mean(mask): return float(o[mask].mean()) if mask.any() else 0.0
    return np.array([o.mean(),np.quantile(o,.75),np.quantile(o,.9),o.max(),mean(neg),mean(pos),mean(q),mean(substantive),float((o>0).mean()),np.log1p(n)],float)

def residual_oof(P,X,y,splits):
    q=np.zeros(len(y),float)
    for tr,va in splits:
        mu=X[tr].mean(0); sd=X[tr].std(0)+1e-6
        A=np.c_[logit(P[tr]),(X[tr]-mu)/sd]; B=np.c_[logit(P[va]),(X[va]-mu)/sd]
        m=LogisticRegression(C=.05,max_iter=300,solver='liblinear',random_state=SEED).fit(A,y[tr])
        q[va]=m.predict_proba(B)[:,1]
    return np.clip(q,EPS,1-EPS)

def evalg(name,groups,X75,Xr,y,support,obj,Xreal,Xctrl):
    P,splits=p97_oof(X75,Xr,y,groups,support); Q=residual_oof(P,Xreal,y,splits); C=residual_oof(P,Xctrl,y,splits)
    b=ll(y,P); r=ll(y,Q); c=ll(y,C); mask=collision_mask(P,y,obj,.01)
    out={'geometry':name,'baseline_v97_ll':b,'uptake':{'ll':r,'gain':b-r},'rotated_reply_control':{'ll':c,'gain':b-c},'uptake_minus_control_gain':c-r,'hard_collision':{'rows':int(mask.sum())}}
    if mask.any():
        bb=ll(y[mask],P[mask]); rr=ll(y[mask],Q[mask]); cc=ll(y[mask],C[mask])
        out['hard_collision'].update({'baseline_ll':bb,'uptake_ll':rr,'uptake_gain':bb-rr,'control_ll':cc,'uptake_minus_control_gain':cc-rr})
    return out

def main(a):
    d=Path(a.dir); z=np.load(d/'arrays.npz',allow_pickle=True); y=z['y']; obj=z['objectives']; support=z['support']; sessions=z['sessions']
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz'); cache={}
    with zipfile.ZipFile(a.archive) as za:
        names=set(za.namelist())
        for sid in np.unique(sessions):
            name=f'{sid}.csv'
            if name not in names: raise RuntimeError('missing '+name)
            with za.open(name) as f: rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            P=pairs(rows); shift=1+(int(hashlib.sha256(str(sid).encode()).hexdigest()[:8],16)%max(1,len(P)-1)) if len(P)>1 else 0
            cache[str(sid)]=(feats(P,0),feats(P,shift))
    R=np.vstack([cache[str(s)][0] for s in sessions]); C=np.vstack([cache[str(s)][1] for s in sessions])
    res={'protocol':'V129_TUTOR_UPTAKE','rows':int(len(y)),'primary':'student -> next tutor lexical uptake','control':'deterministic within-session rotation of tutor replies','precommit':{'promote_gain_each_geometry':.0015,'phase_change_gain_each_geometry':.003,'real_minus_control_each_geometry':.001,'hard_collision_gain_each_geometry':'>0','no_parameter_sweep':True}}
    res['objective_grouped']=evalg('objective_grouped',obj,X75,Xr,y,support,obj,R,C); res['session_grouped']=evalg('session_grouped',sessions,X75,Xr,y,support,obj,R,C)
    def ok(x,t): return x['uptake']['gain']>=t and x['uptake_minus_control_gain']>=.001 and x['hard_collision'].get('uptake_gain',-1)>0
    po=ok(res['objective_grouped'],.0015); ps=ok(res['session_grouped'],.0015); ph=ok(res['objective_grouped'],.003) and ok(res['session_grouped'],.003)
    verdict='PHASE_CHANGE_CANDIDATE' if ph else 'PROMOTE_TUTOR_UPTAKE_LAW' if po and ps else 'SUPPRESS_TUTOR_UPTAKE'
    res['decision']={'objective_pass':bool(po),'session_pass':bool(ps),'verdict':verdict}
    Path(a.out).write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--dir',required=True); p.add_argument('--out',required=True); main(p.parse_args())

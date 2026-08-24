#!/usr/bin/env python3
"""V153: explicit student-response -> tutor-feedback relational binding.

Residual after V152: canonical-state elaboration is saturated. V75 preserves raw ordered
text but uses local hashed n-grams; it does not explicitly expose the tensor product
between a student's answer and the tutor reaction caused by that answer.

Frozen discovery protocol (no sweep):
- deterministic 2,500-row sample by SHA256(response_id);
- exact V135 incumbent reconstructed under 4-fold outer / 3-fold inner OOF;
- one relational expert whose tokens contain answer-token x subsequent-feedback-token pairs;
- matched controls preserve answer/feedback marginals but either omit the binding or
  deterministically shuffle feedback among events within the same row before pairing;
- evaluate both session-grouped and objective-grouped geometries;
- advance only if gain >= .006 in BOTH geometries, every outer fold improves, and the
  bound representation beats both controls in both geometries.

Discovery never authorizes a smoke directly.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, extract_canonical_events, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
from v110_residual_collider_state_discovery import EPS, ll, logit, fit_base
from v135_nested_supported_stack import components, feats, fit_stack

ROWS=2500
C_META=.10
TOK_RE=re.compile(r"[a-z0-9]+(?:[./%+-][a-z0-9]+)?",re.I)
HV=HashingVectorizer(n_features=2**19,alternate_sign=False,norm='l2',analyzer='word',ngram_range=(1,1),token_pattern=r'(?u)\b\w\w+\b',lowercase=False)

def h64(x:str)->int:
    return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)

def toks(s:str,limit:int=12)->list[str]:
    # Stable unique lexical units. Prefixing below makes answer/feedback roles explicit.
    out=[]; seen=set()
    for t in TOK_RE.findall(str(s).lower()):
        z=re.sub(r'\W+','_',t).strip('_')
        if len(z)<1 or z in seen: continue
        seen.add(z); out.append(z)
        if len(out)>=limit: break
    return out

def interaction_docs(events, seed_key:str):
    answers=[toks(e.answer) for e in events]
    feedback=[toks(e.feedback) for e in events]
    # Deterministic non-label sham: permute feedback event assignment within row.
    perm=np.arange(len(events))
    if len(events)>1:
        rng=np.random.default_rng(h64(seed_key)&((1<<63)-1)); rng.shuffle(perm)
        if np.all(perm==np.arange(len(events))): perm=np.roll(perm,1)
    def build(pairs:bool, use_perm:bool):
        z=[]
        for i,(aa,ff0) in enumerate(zip(answers,feedback)):
            ff=feedback[int(perm[i])] if use_perm else ff0
            # identical marginals in all three arms
            z += [f'A_{a}' for a in aa]
            z += [f'F_{f}' for f in ff0]
            if pairs:
                # Relational tensor. Pair cap is fixed by 12x12 lexical caps above.
                z += [f'AF_{a}__{f}' for a in aa for f in ff]
        return ' '.join(z)
    return build(True,False),build(False,False),build(True,True)

def meta_base(q0,p75,pr,pp,c,seen):
    return np.column_stack([logit(q0),logit(p75),logit(pr),logit(pp),np.log1p(c),seen.astype(float)])

def meta_plus(base,p):
    lp=logit(p); return np.column_stack([base,lp,lp-base[:,0]])

def fit_meta(X,y):
    return LogisticRegression(C=C_META,max_iter=400,solver='liblinear',random_state=SEED).fit(X,y)

def outer_components(X75,Xr,Xb,Xm,Xs,y,tr,va,support):
    q0,p75,pr,pp,c,seen=components(X75,Xr,y,tr,va,support)
    pb=fit_base(Xb,y,tr,va); pm=fit_base(Xm,y,tr,va); ps=fit_base(Xs,y,tr,va)
    return q0,p75,pr,pp,c,seen,pb,pm,ps

def geometry(name,groups,X75,Xr,Xb,Xm,Xs,y,support):
    n=len(y); groups=np.asarray(groups); outer=list(GroupKFold(4).split(np.zeros(n),y,groups))
    P135=np.zeros(n); PB=np.zeros(n); PM=np.zeros(n); PS=np.zeros(n); folds=[]
    for k,(tr,va) in enumerate(outer,1):
        oq0,o75,orr,opp,oc,oseen,opb,opm,ops=outer_components(X75,Xr,Xb,Xm,Xs,y,tr,va,support)
        ig=groups[tr]; inner=list(GroupKFold(min(3,len(np.unique(ig)))).split(np.zeros(len(tr)),y[tr],ig))
        iq0=np.zeros(len(tr)); i75=np.zeros(len(tr)); ir=np.zeros(len(tr)); ipp=np.zeros(len(tr)); ic=np.zeros(len(tr)); iseen=np.zeros(len(tr),bool)
        ib=np.zeros(len(tr)); im=np.zeros(len(tr)); ish=np.zeros(len(tr))
        for ltr,lva in inner:
            atr=tr[ltr]; ava=tr[lva]
            z=outer_components(X75,Xr,Xb,Xm,Xs,y,atr,ava,support)
            iq0[lva],i75[lva],ir[lva],ipp[lva],ic[lva],iseen[lva],ib[lva],im[lva],ish[lva]=z
        q135=oq0.copy(); fitmask=iseen
        if fitmask.sum()>=50 and len(np.unique(y[tr][fitmask]))==2:
            m135=fit_stack(feats(i75[fitmask],ir[fitmask],ipp[fitmask],ic[fitmask],True),y[tr][fitmask])
            if oseen.any(): q135[oseen]=np.clip(m135.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)
        base_i=meta_base(iq0,i75,ir,ipp,ic,iseen); base_o=meta_base(oq0,o75,orr,opp,oc,oseen)
        mb=fit_meta(meta_plus(base_i,ib),y[tr]); mm=fit_meta(meta_plus(base_i,im),y[tr]); ms=fit_meta(meta_plus(base_i,ish),y[tr])
        qb=np.clip(mb.predict_proba(meta_plus(base_o,opb))[:,1],EPS,1-EPS)
        qm=np.clip(mm.predict_proba(meta_plus(base_o,opm))[:,1],EPS,1-EPS)
        qs=np.clip(ms.predict_proba(meta_plus(base_o,ops))[:,1],EPS,1-EPS)
        P135[va]=q135; PB[va]=qb; PM[va]=qm; PS[va]=qs
        r={'fold':k,'rows':int(len(va)),'v135_ll':ll(y[va],q135),'bound_ll':ll(y[va],qb),'marginal_ll':ll(y[va],qm),'shuffled_binding_ll':ll(y[va],qs)}
        r['gain_bound_vs_v135']=r['v135_ll']-r['bound_ll']; r['gain_bound_vs_marginal']=r['marginal_ll']-r['bound_ll']; r['gain_bound_vs_shuffle']=r['shuffled_binding_ll']-r['bound_ll']; folds.append(r)
        print(name,'FOLD',json.dumps(r),flush=True)
    out={'geometry':name,'v135_ll':ll(y,P135),'bound_ll':ll(y,PB),'marginal_ll':ll(y,PM),'shuffled_binding_ll':ll(y,PS),'folds':folds}
    out['gain_bound_vs_v135']=out['v135_ll']-out['bound_ll']; out['gain_bound_vs_marginal']=out['marginal_ll']-out['bound_ll']; out['gain_bound_vs_shuffle']=out['shuffled_binding_ll']-out['bound_ll']; out['all_folds_positive']=all(r['gain_bound_vs_v135']>0 for r in folds)
    return out

def main(a):
    t0=time.time(); f0=load_training(a.features,a.labels).reset_index(drop=True)
    ix=np.array(sorted(range(len(f0)),key=lambda i:h64(f0.response_id.iloc[i]))[:min(ROWS,len(f0))])
    f=f0.iloc[ix].reset_index(drop=True); y=f.target.to_numpy(int)
    sessions=f.session_id.astype(str).to_numpy(); objectives=f.learning_objective_id.astype(str).to_numpy() if 'learning_objective_id' in f else f.learning_objective.astype(str).to_numpy(); support=f.learning_objective.astype(str).to_numpy()
    cache={}; us=np.unique(sessions)
    for j,sid in enumerate(us,1):
        cache[str(sid)]=load_transcript(a.transcripts/f'{sid}.csv')
        if j%500==0: print('TRANSCRIPTS',j,'/',len(us),'elapsed',round(time.time()-t0,1),flush=True)
    print('BUILD V75',flush=True); X75=build_v75(f,cache)
    rt=[]; rz=[]; bd=[]; md=[]; sd=[]; event_counts=[]
    for _,r in f.iterrows():
        d=cache[str(r.session_id)]; obj=str(r.learning_objective)
        txt,z=segmented_control(d,obj,'related'); rt.append(txt); rz.append(z)
        ev=extract_canonical_events(d,obj); event_counts.append(len(ev))
        b,m,s=interaction_docs(ev,str(r.response_id)); bd.append(b); md.append(m); sd.append(s)
    Xr=build_control(rt,rz); Xb=HV.transform(bd); Xm=HV.transform(md); Xs=HV.transform(sd)
    print('SHAPES',X75.shape,Xr.shape,Xb.shape,'events_mean',float(np.mean(event_counts)),'multi_event_frac',float(np.mean(np.array(event_counts)>1)),'elapsed',round(time.time()-t0,1),flush=True)
    out={'protocol':'V153_RESPONSE_FEEDBACK_BINDING','rows':int(len(y)),'precommit':{'sample':'lowest SHA256(response_id), 2500 rows','outer_folds':4,'inner_folds':3,'no_sweep':True,'binding':'answer-token x subsequent-feedback-token','controls':['same marginals without binding','within-row shuffled feedback binding'],'discovery_gain_both_geometries':.006,'all_outer_folds_positive':True,'must_beat_both_controls_both_geometries':True,'full_run_before_smoke':True},'event_stats':{'mean':float(np.mean(event_counts)),'multi_event_fraction':float(np.mean(np.array(event_counts)>1))}}
    out['session_grouped']=geometry('session_grouped',sessions,X75,Xr,Xb,Xm,Xs,y,support)
    out['objective_grouped']=geometry('objective_grouped',objectives,X75,Xr,Xb,Xm,Xs,y,support)
    S=out['session_grouped']; O=out['objective_grouped']
    advance=(S['gain_bound_vs_v135']>=.006 and O['gain_bound_vs_v135']>=.006 and S['all_folds_positive'] and O['all_folds_positive'] and S['gain_bound_vs_marginal']>0 and O['gain_bound_vs_marginal']>0 and S['gain_bound_vs_shuffle']>0 and O['gain_bound_vs_shuffle']>0)
    out['decision']={'verdict':'ADVANCE_V153_TO_FULL' if advance else 'CLOSE_RESPONSE_FEEDBACK_BINDING','advance':bool(advance),'next':'Run exact full-data V153 and attack binding with stronger shams before any smoke.' if advance else 'Ratchet pair-binding negative; residual lies outside explicit local response-feedback coupling.'}
    out['elapsed_seconds']=time.time()-t0; Path(a.out).write_text(json.dumps(out,indent=2)); print('FINAL',json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v153_response_feedback_binding.json'); main(p.parse_args())

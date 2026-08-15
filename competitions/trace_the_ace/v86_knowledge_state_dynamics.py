#!/usr/bin/env python3
"""V86: RGRS sequential knowledge-state dynamics separator.

Hypothesis: the missing object is not merely an EvidenceEvent multiset but the
objective-conditioned *state trajectory* induced by ordered evidence.

Arms (objective-cold, frozen folds/model family):
A0: EvidenceEvent multiset representation (same event extractor as V85).
A1: ordered EvidenceEvents + explicit cumulative/decayed knowledge-state dynamics.
A2: causal ablation: same events/state formulas with event order canonically sorted
    by content signature, destroying observed temporal order while preserving the
    event multiset and most marginal features.

A1 must beat A0 materially and A2 must lose the gain to support an ordering/state
representation claim. Otherwise retain a negative/conditional law.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import evidence_events, render, nums, PHASE_WEIGHT


def event_value(e):
    """Signed mastery evidence, deliberately simple and inspectable."""
    rel=float(e['rel']); assist=float(e['assistance']); phase=PHASE_WEIGHT.get(e['phase'],.4)
    independent=1.0 if e['independent'] else 0.0
    if e['neg']:
        # An unassisted, relevant error is strong negative evidence.
        return - rel * phase * (0.55 + 0.45*(1-assist))
    if e['pos']:
        # Correctness after strong assistance is weaker than independent production.
        return rel * phase * (0.25 + 0.75*(1-assist)) * (1.0 + 0.25*independent)
    # Unjudged substantive production is weak evidence, not zero.
    return 0.08 * rel * phase * (1-assist)


def signature(e):
    s=(str(e['q'])+'\x1f'+str(e['a'])+'\x1f'+str(e['state'])).encode('utf-8','ignore')
    return hashlib.sha1(s).hexdigest()


def state_features(events, destroy_order=False):
    if not events:
        return np.zeros(46,float), '[NO_EVENTS]'
    E=list(events)
    if destroy_order:
        # Canonical deterministic order: same event multiset, observed chronology removed.
        E=sorted(E,key=signature)
    vals=[]; ks=[]; fast=[]; slow=[]
    k=0.0; kf=0.0; kslo=0.0
    prev_state='START'; transitions=[]
    for t,e in enumerate(E):
        v=event_value(e); vals.append(v)
        # bounded additive state + two recency scales
        k=np.tanh(0.78*np.arctanh(np.clip(k,-.999,.999)) + v)
        kf=.55*kf + v
        kslo=.88*kslo + v
        ks.append(k); fast.append(kf); slow.append(kslo)
        transitions.append(prev_state+'>'+str(e['state'])); prev_state=str(e['state'])
    V=np.asarray(vals); K=np.asarray(ks); F=np.asarray(fast); S=np.asarray(slow)
    n=len(E); q=max(1,n//4)
    pos=np.asarray([e['pos'] for e in E],float); neg=np.asarray([e['neg'] for e in E],float)
    ind=np.asarray([e['independent'] for e in E],float); ass=np.asarray([e['assistance'] for e in E],float)
    rel=np.asarray([e['rel'] for e in E],float)
    app=np.asarray([e['phase']=='APPLICATION' for e in E],float)
    # Transition features target the educational trajectory directly.
    err_to_ind=0; guide_to_ind=0; recovery=0; regress=0
    for a,b in zip(E[:-1],E[1:]):
        if a['neg'] and b['independent'] and b['pos']: err_to_ind+=1
        if a['assistance']>=.6 and b['independent'] and b['pos']: guide_to_ind+=1
        if a['neg'] and b['pos']: recovery+=1
        if a['pos'] and b['neg']: regress+=1
    last_pos=max([i for i,e in enumerate(E) if e['pos']],default=-1)/(max(1,n-1))
    last_neg=max([i for i,e in enumerate(E) if e['neg']],default=-1)/(max(1,n-1))
    last_ind=max([i for i,e in enumerate(E) if e['independent'] and e['pos']],default=-1)/(max(1,n-1))
    feats=[
        n, V.mean(), V.sum(), V[-1], V[:q].mean(), V[-q:].mean(),
        K[-1], K.max(), K.min(), K.mean(), K[-q:].mean(),
        F[-1], F.max(), F.min(), S[-1], S.max(), S.min(),
        float(K[-1]-K[0]), float(F[-1]-F[0]), float(S[-1]-S[0]),
        pos.mean(), neg.mean(), ind.mean(), ass.mean(), rel.mean(), app.mean(),
        float((pos*ind*rel).sum()), float((neg*(1-ass)*rel).sum()),
        err_to_ind, guide_to_ind, recovery, regress,
        last_pos,last_neg,last_ind,
        float(any(e['neg'] for e in E[-3:])),
        float(any(e['independent'] and e['pos'] for e in E[-3:])),
        float(sum(e['independent'] and e['pos'] for e in E[-5:])),
        float(sum(e['neg'] for e in E[-5:])),
        float(np.polyfit(np.arange(n),K,1)[0] if n>1 else 0),
        float(np.polyfit(np.arange(n),V,1)[0] if n>1 else 0),
        float(np.std(V)),float(np.std(K)),
        float(np.mean(np.abs(np.diff(K))) if n>1 else 0),
        float(np.max(np.abs(np.diff(K))) if n>1 else 0),
        float(sum(t=='UNRESOLVED_ERROR>INDEPENDENT_CORRECT' for t in transitions)),
    ]
    # Render ordered state path so sparse model can exploit categorical transitions too.
    rows=[]
    for i,(e,v,kv) in enumerate(zip(E,V,K)):
        rows.append(f"[T={i} PHASE={e['phase']} STATE={e['state']} ASSIST={e['assistance']:.1f} INDEP={int(e['independent'])} REL={e['rel']:.2f} DV={v:.2f} K={kv:.2f}]")
    return np.asarray(feats,float), ' '.join(rows)


def build(texts,Z,prefix):
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    X=hv.transform([f'[{prefix}] '+x for x in texts]); Z=np.vstack(Z); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6)
    return hstack([X,csr_matrix(Z)],format='csr')


def oof(X,y,sp,name):
    p=np.zeros(len(y)); folds=[]
    for k,(tr,va) in enumerate(sp,1):
        m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
        q=np.clip(m.predict_proba(X[va])[:,1],1e-5,1-1e-5); p[va]=q
        r={'fold':k,'logloss':float(log_loss(y[va],q)),'auc':float(roc_auc_score(y[va],q))}; print(name,r); folds.append(r)
    return p,folds


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    if a.limit: f=f.iloc[:a.limit].copy().reset_index(drop=True)
    cache={}; base_t=[]; base_n=[]; seq_t=[]; seq_n=[]; abl_t=[]; abl_n=[]; counts=[]
    for i,r in f.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
        seg,_=choose_target_segment(cache[sid],str(r.learning_objective)); ev=evidence_events(seg,str(r.learning_objective)); counts.append(len(ev))
        base_t.append(render(ev,str(r.learning_objective),False)); base_n.append(nums(ev,False))
        z,t=state_features(ev,False); za,ta=state_features(ev,True)
        seq_t.append(f"[OBJECTIVE] {r.learning_objective} [STATE_PATH] {t} [EVENTS] {base_t[-1]}"); seq_n.append(np.r_[base_n[-1],z])
        abl_t.append(f"[OBJECTIVE] {r.learning_objective} [STATE_PATH_ORDER_ABLATED] {ta} [EVENTS] {base_t[-1]}"); abl_n.append(np.r_[base_n[-1],za])
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sp=list(GroupKFold(5).split(np.zeros(len(y)),y,groups))
    X0=build(base_t,base_n,'EVENT_MULTISET'); X1=build(seq_t,seq_n,'STATE_ORDERED'); X2=build(abl_t,abl_n,'STATE_ORDER_ABLATED')
    p0,f0=oof(X0,y,sp,'A0_multiset'); p1,f1=oof(X1,y,sp,'A1_ordered_state'); p2,f2=oof(X2,y,sp,'A2_order_ablation')
    ll0=float(log_loss(y,p0)); ll1=float(log_loss(y,p1)); ll2=float(log_loss(y,p2))
    gain=ll0-ll1; causal=ll2-ll1
    # Check orthogonality if state helps only in blend.
    best=None
    for w in np.linspace(0,1,21):
        q=np.clip((1-w)*p0+w*p1,1e-5,1-1e-5); ll=float(log_loss(y,q))
        if best is None or ll<best['logloss']: best={'state_weight':float(w),'logloss':ll}
    if gain>=.003 and causal>=.001: decision='SEQUENTIAL_STATE_BREAKTHROUGH'
    elif gain>=.001 and causal>0: decision='PROMISING_SEQUENTIAL_STATE'
    elif best['logloss']<=ll0-.001: decision='ORTHOGONAL_SEQUENCE_SIGNAL'
    else: decision='ORDER_NOT_CAUSAL_OR_REFINE_R5'
    out={'primary':'objective-cold','A0_event_multiset':ll0,'A1_ordered_state':ll1,'A2_order_ablation':ll2,
         'gain_vs_A0':gain,'causal_order_gain':causal,'best_blend':best,'decision':decision,
         'event_stats':{'mean_events':float(np.mean(counts)),'zero_event_fraction':float(np.mean(np.asarray(counts)==0))},
         'folds':{'A0':f0,'A1':f1,'A2':f2}}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v86_knowledge_state_dynamics.json'); p.add_argument('--limit',type=int,default=0); run(p.parse_args())

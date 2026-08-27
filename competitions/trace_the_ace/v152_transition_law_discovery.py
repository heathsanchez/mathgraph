#!/usr/bin/env python3
"""V152: explicit transition-law discovery beyond V135.

Verified-residual separator after V145 and V146-V151 close local composition,
routing, support, graph, and latent-session surrogates as top-3 magnitude routes.

H1: the missing row-local distinction is the trajectory of canonical student-state
transitions, not merely transcript content/state counts. V75 retains ordered text but
its learner does not explicitly expose a transition grammar.

Frozen discovery protocol:
- deterministic 2,500-row sample by SHA256(response_id);
- two protected geometries: session-grouped and objective-grouped, 4 outer folds;
- within each outer training partition, 3-fold grouped OOF creates all meta inputs;
- incumbent is exact V135 construction on the same rows;
- candidate adds one fixed transition expert from adjacent canonical states;
- controls: predictions-only meta, state-count-only expert, and deterministic
  within-row shuffled-order transition expert;
- no sweep and no result-dependent feature selection.

Discovery advances to full 35,072 only if transition gain >= .006 in BOTH geometries,
all outer folds are positive, and real transitions beat both count-only and shuffled-order
controls in both geometries. Discovery itself never authorizes a smoke submission.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from v75_canonical_trajectory import load_training, extract_canonical_events, STATE_ORDER, SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
from v110_residual_collider_state_discovery import EPS, ll, logit, fit_base
from v135_nested_supported_stack import components, feats, fit_stack

ROWS=2500
STATES=list(STATE_ORDER.keys())
S2I={s:i for i,s in enumerate(STATES)}
D=8 + 64 + 64 + 6
C_META=.10


def h64(x:str)->int:
    return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)


def vec_from_states(states:list[str], shuffled:bool=False, seed_key:str='')->np.ndarray:
    st=list(states)
    if shuffled and len(st)>1:
        rng=np.random.default_rng(h64(seed_key) & ((1<<63)-1)); rng.shuffle(st)
    x=np.zeros(D,float)
    # state counts
    for s in st: x[S2I[s]] += 1.0
    # adjacent transition counts + recency weighted transition counts
    off=8; woff=8+64
    den=max(1,len(st)-1)
    reversals=0; same=0
    scores=[STATE_ORDER[s] for s in st]
    for j,(a,b) in enumerate(zip(st[:-1],st[1:])):
        k=S2I[a]*8+S2I[b]; x[off+k]+=1.0; x[woff+k]+=(j+1)/den
        same += int(a==b)
        if j and np.sign(scores[j]-scores[j-1]) != np.sign(scores[j+1]-scores[j]) and scores[j]!=scores[j-1] and scores[j+1]!=scores[j]: reversals += 1
    # compact sequence summaries
    base=8+128
    x[base+0]=len(st)
    x[base+1]=same
    x[base+2]=reversals
    x[base+3]=scores[-1]-scores[0] if len(scores)>=2 else 0.0
    x[base+4]=scores[-1] if scores else 0.0
    # longest monotone nondecreasing run
    best=cur=1 if scores else 0
    for a,b in zip(scores[:-1],scores[1:]):
        cur=cur+1 if b>=a else 1; best=max(best,cur)
    x[base+5]=best
    return x


def count_only(v:np.ndarray)->np.ndarray:
    z=np.zeros_like(v); z[:8]=v[:8]; z[-6]=v[-6]; return z


def meta_base(q0,p75,pr,pp,c,seen):
    return np.column_stack([logit(q0),logit(p75),logit(pr),logit(pp),np.log1p(c),seen.astype(float)])


def meta_plus(base,p):
    lp=logit(p); return np.column_stack([base,lp,lp-base[:,0]])


def fit_meta(X,y):
    return LogisticRegression(C=C_META,max_iter=400,solver='liblinear',random_state=SEED).fit(X,y)


def outer_components(X75,Xr,Xt,Xc,Xs,y,tr,va,support):
    q0,p75,pr,pp,c,seen=components(X75,Xr,y,tr,va,support)
    pt=fit_base(Xt,y,tr,va); pc=fit_base(Xc,y,tr,va); ps=fit_base(Xs,y,tr,va)
    return q0,p75,pr,pp,c,seen,pt,pc,ps


def geometry(name,groups,X75,Xr,Xt,Xc,Xs,y,support):
    n=len(y); groups=np.asarray(groups); outer=list(GroupKFold(4).split(np.zeros(n),y,groups))
    P135=np.zeros(n); PM=np.zeros(n); PT=np.zeros(n); PC=np.zeros(n); PS=np.zeros(n); folds=[]
    for k,(tr,va) in enumerate(outer,1):
        oq0,o75,orr,opp,oc,oseen,opt,opc,ops=outer_components(X75,Xr,Xt,Xc,Xs,y,tr,va,support)
        ig=groups[tr]; inner=list(GroupKFold(min(3,len(np.unique(ig)))).split(np.zeros(len(tr)),y[tr],ig))
        iq0=np.zeros(len(tr)); i75=np.zeros(len(tr)); ir=np.zeros(len(tr)); ipp=np.zeros(len(tr)); ic=np.zeros(len(tr)); iseen=np.zeros(len(tr),bool)
        it=np.zeros(len(tr)); ico=np.zeros(len(tr)); ish=np.zeros(len(tr))
        for ltr,lva in inner:
            atr=tr[ltr]; ava=tr[lva]
            z=outer_components(X75,Xr,Xt,Xc,Xs,y,atr,ava,support)
            iq0[lva],i75[lva],ir[lva],ipp[lva],ic[lva],iseen[lva],it[lva],ico[lva],ish[lva]=z
        # Exact V135 incumbent on supported rows.
        q135=oq0.copy(); fitmask=iseen
        if fitmask.sum()>=50 and len(np.unique(y[tr][fitmask]))==2:
            m135=fit_stack(feats(i75[fitmask],ir[fitmask],ipp[fitmask],ic[fitmask],True),y[tr][fitmask])
            if oseen.any(): q135[oseen]=np.clip(m135.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)
        ib=meta_base(iq0,i75,ir,ipp,ic,iseen); ob=meta_base(oq0,o75,orr,opp,oc,oseen)
        # Same-capacity/nesting controls establish whether any gain is transition-specific.
        mb=fit_meta(ib,y[tr]); mt=fit_meta(meta_plus(ib,it),y[tr]); mc=fit_meta(meta_plus(ib,ico),y[tr]); ms=fit_meta(meta_plus(ib,ish),y[tr])
        qm=np.clip(mb.predict_proba(ob)[:,1],EPS,1-EPS)
        qt=np.clip(mt.predict_proba(meta_plus(ob,opt))[:,1],EPS,1-EPS)
        qc=np.clip(mc.predict_proba(meta_plus(ob,opc))[:,1],EPS,1-EPS)
        qs=np.clip(ms.predict_proba(meta_plus(ob,ops))[:,1],EPS,1-EPS)
        P135[va]=q135; PM[va]=qm; PT[va]=qt; PC[va]=qc; PS[va]=qs
        r={'fold':k,'rows':int(len(va)),'v135_ll':ll(y[va],q135),'predictions_only_ll':ll(y[va],qm),'transition_ll':ll(y[va],qt),'count_only_ll':ll(y[va],qc),'shuffled_order_ll':ll(y[va],qs)}
        r['gain_transition_vs_v135']=r['v135_ll']-r['transition_ll']; r['gain_transition_vs_count']=r['count_only_ll']-r['transition_ll']; r['gain_transition_vs_shuffle']=r['shuffled_order_ll']-r['transition_ll']
        folds.append(r); print(name,'FOLD',json.dumps(r),flush=True)
    out={'geometry':name,'v135_ll':ll(y,P135),'predictions_only_ll':ll(y,PM),'transition_ll':ll(y,PT),'count_only_ll':ll(y,PC),'shuffled_order_ll':ll(y,PS),'folds':folds}
    out['gain_transition_vs_v135']=out['v135_ll']-out['transition_ll']; out['gain_transition_vs_predictions_only']=out['predictions_only_ll']-out['transition_ll']; out['gain_transition_vs_count']=out['count_only_ll']-out['transition_ll']; out['gain_transition_vs_shuffle']=out['shuffled_order_ll']-out['transition_ll']; out['all_folds_positive']=all(r['gain_transition_vs_v135']>0 for r in folds)
    return out


def main(a):
    t0=time.time(); f0=load_training(a.features,a.labels).reset_index(drop=True)
    order=sorted(range(len(f0)),key=lambda i:h64(f0.response_id.iloc[i])); ix=np.array(order[:min(ROWS,len(order))]); f=f0.iloc[ix].reset_index(drop=True)
    y=f.target.to_numpy(int); sessions=f.session_id.astype(str).to_numpy(); objectives=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); support=f.learning_objective.astype(str).to_numpy()
    cache={}; us=np.unique(sessions)
    for j,sid in enumerate(us,1):
        cache[str(sid)]=load_transcript(a.transcripts/f'{sid}.csv')
        if j%500==0: print('TRANSCRIPTS',j,'/',len(us),'elapsed',round(time.time()-t0,1),flush=True)
    print('BUILD V75',flush=True); X75=build_v75(f,cache)
    rt=[]; rz=[]; vr=[]; vc=[]; vs=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; obj=str(r.learning_objective)
        txt,z=segmented_control(d,obj,'related'); rt.append(txt); rz.append(z)
        st=[e.state for e in extract_canonical_events(d,obj)]
        real=vec_from_states(st,False,str(r.response_id)); sham=vec_from_states(st,True,str(r.response_id)); vr.append(real); vc.append(count_only(real)); vs.append(sham)
    Xr=build_control(rt,rz); Xt=csr_matrix(np.asarray(vr)); Xc=csr_matrix(np.asarray(vc)); Xs=csr_matrix(np.asarray(vs))
    print('SHAPES',X75.shape,Xr.shape,Xt.shape,'elapsed',round(time.time()-t0,1),flush=True)
    out={'protocol':'V152_TRANSITION_LAW_DISCOVERY','rows':int(len(y)),'states':STATES,'feature_dim':D,'precommit':{'sample':'lowest SHA256(response_id), 2500 rows','outer_folds':4,'inner_folds':3,'no_sweep':True,'discovery_gain_both_geometries':.006,'all_outer_folds_positive':True,'must_beat_count_and_shuffle_both':True,'full_run_before_smoke':True}}
    out['session_grouped']=geometry('session_grouped',sessions,X75,Xr,Xt,Xc,Xs,y,support)
    out['objective_grouped']=geometry('objective_grouped',objectives,X75,Xr,Xt,Xc,Xs,y,support)
    S=out['session_grouped']; O=out['objective_grouped']
    advance=(S['gain_transition_vs_v135']>=.006 and O['gain_transition_vs_v135']>=.006 and S['all_folds_positive'] and O['all_folds_positive'] and S['gain_transition_vs_count']>0 and O['gain_transition_vs_count']>0 and S['gain_transition_vs_shuffle']>0 and O['gain_transition_vs_shuffle']>0)
    out['decision']={'verdict':'ADVANCE_V152_TO_FULL' if advance else 'CLOSE_TRANSITION_LAW_DISCOVERY','advance':bool(advance),'next':'Run frozen full-data V152 with same representation and gates.' if advance else 'Ratchet transition grammar negative; zoom out to a representation not expressible by existing canonical-event sequence.'}
    out['elapsed_seconds']=time.time()-t0
    Path(a.out).write_text(json.dumps(out,indent=2)); print('FINAL',json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v152_transition_law_discovery.json'); main(p.parse_args())

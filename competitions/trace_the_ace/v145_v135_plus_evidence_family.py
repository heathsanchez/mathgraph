#!/usr/bin/env python3
"""V145: closure-before-invention test over the strongest old unsummed capability family.

Residual entering V145:
- V135 is lawful and externally smoke-positive, but its full-data gain is too small for top 3.
- simple calibration and 1D/2D/component applicability have been closed.
- V81/V84/V87 contain target-segment, instructional-phase, and student-evidence views that
  are not present as separate experts in V135.

Frozen separator:
A0 = exact nested V135 incumbent.
A1 = nested V135 + target-segment + phase + evidence experts.
C0 = matched-capacity alignment control: same extra experts, but their row alignment is
     deterministically permuted within support-status strata before meta fitting/application.

All base-expert predictions used by a meta learner are OOF inside the corresponding outer
training partition. No test aggregates, same-session labels, or hidden outcomes are used at
inference. The full-data gate requires >= .004 LL gain over V135 in BOTH session- and
objective-grouped worlds, plus A1 beating C0 in both worlds.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import log_loss

from v75_canonical_trajectory import load_training, trajectory_views, SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
from v81_target_segment_phase import choose_target_segment, phase_views, build_X
from v84_student_evidence import evidence_view, build_evidence
from v110_residual_collider_state_discovery import EPS, fit_base, logit
from v135_nested_supported_stack import prior_apply, fit_stack, feats as v135_feats

STACK_C=.10
GAIN_GATE=.004


def ll(y,p):
    return float(log_loss(y,np.clip(p,EPS,1-EPS)))


def fit_lr(X,y):
    return LogisticRegression(C=STACK_C,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y)


def extra_feats(p75,pr,pp,c,ps,pph,pe,seen):
    """Two routing-compatible feature spaces: prior allowed only when support is seen."""
    common=np.column_stack([
        logit(p75),logit(pr),logit(p75)-logit(pr),
        logit(ps),logit(pph),logit(pe),
        logit(ps)-logit(p75),logit(pph)-logit(p75),logit(pe)-logit(p75),
    ])
    full=np.column_stack([common,logit(pp),np.log1p(c)])
    return full,common


def deterministic_perm(n,seed):
    rng=np.random.RandomState(seed)
    return rng.permutation(n)


def permute_extras(ps,pph,pe,seen,seed):
    a,b,c=np.asarray(ps).copy(),np.asarray(pph).copy(),np.asarray(pe).copy()
    for j,maskval in enumerate([False,True]):
        idx=np.flatnonzero(np.asarray(seen)==maskval)
        if len(idx)>1:
            p=deterministic_perm(len(idx),seed+97*j)
            src=idx[p]
            a[idx]=np.asarray(ps)[src]; b[idx]=np.asarray(pph)[src]; c[idx]=np.asarray(pe)[src]
    return a,b,c


def base_components(X75,Xr,Xs,Xp,Xe,y,tr,va,support):
    p75=fit_base(X75,y,tr,va)
    pr=fit_base(Xr,y,tr,va)
    ps=fit_base(Xs,y,tr,va)
    pph=fit_base(Xp,y,tr,va)
    pe=fit_base(Xe,y,tr,va)
    pp,c,seen=prior_apply(y,tr,va,support)
    p97=np.where(seen,p75,.65*p75+.35*pr)
    return [np.clip(x,EPS,1-EPS) for x in [p97,p75,pr,pp,ps,pph,pe]],c,seen


def nested_world(name,groups,X75,Xr,Xs,Xp,Xe,y,support):
    groups=np.asarray(groups); support=np.asarray(support); n=len(y)
    p135=np.zeros(n); p145=np.zeros(n); pctl=np.zeros(n); folds=[]
    outer=list(GroupKFold(min(4,len(np.unique(groups)))).split(np.zeros(n),y,groups))
    for k,(tr,va) in enumerate(outer,1):
        q97,o75,orr,opp,os,oph,oe,oc,oseen = (*base_components(X75,Xr,Xs,Xp,Xe,y,tr,va,support)[0], *base_components(X75,Xr,Xs,Xp,Xe,y,tr,va,support)[1:])
        # NOTE: avoid recomputing the expensive fits; tuple assembly above is replaced below.
        raise RuntimeError('UNREACHABLE_PLACEHOLDER')
    return {}


def nested_world(name,groups,X75,Xr,Xs,Xp,Xe,y,support):
    groups=np.asarray(groups); support=np.asarray(support); n=len(y)
    p135=np.zeros(n); p145=np.zeros(n); pctl=np.zeros(n); folds=[]
    outer=list(GroupKFold(min(4,len(np.unique(groups)))).split(np.zeros(n),y,groups))
    for k,(tr,va) in enumerate(outer,1):
        comps,oc,oseen=base_components(X75,Xr,Xs,Xp,Xe,y,tr,va,support)
        q97,o75,orr,opp,os,oph,oe=comps

        ig=groups[tr]
        inner=list(GroupKFold(min(3,len(np.unique(ig)))).split(np.zeros(len(tr)),y[tr],ig))
        ip75=np.zeros(len(tr)); ipr=np.zeros(len(tr)); ipp=np.zeros(len(tr)); ic=np.zeros(len(tr));
        ips=np.zeros(len(tr)); ipph=np.zeros(len(tr)); ipe=np.zeros(len(tr)); iseen=np.zeros(len(tr),bool)
        for ltr,lva in inner:
            atr=tr[ltr]; ava=tr[lva]
            cc,ac,aseen=base_components(X75,Xr,Xs,Xp,Xe,y,atr,ava,support)
            _,a75,ar,ap,as_,aph,ae=cc
            ip75[lva]=a75; ipr[lva]=ar; ipp[lva]=ap; ic[lva]=ac
            ips[lva]=as_; ipph[lva]=aph; ipe[lva]=ae; iseen[lva]=aseen

        # Exact V135 baseline: supported stack trained only on inner-OOF support-seen rows;
        # unsupported outer rows remain exact V97.
        q135=q97.copy()
        sm=iseen
        if sm.sum()>=50 and len(np.unique(y[tr][sm]))>1:
            m135=fit_stack(v135_feats(ip75[sm],ipr[sm],ipp[sm],ic[sm],True),y[tr][sm])
            if oseen.any():
                q135[oseen]=np.clip(m135.predict_proba(v135_feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)

        # V145 intervention: support-specific meta learners. Seen support gets prior + extras;
        # unseen support gets only sample-local experts (no objective prior).
        fin_s,fin_u=extra_feats(ip75,ipr,ipp,ic,ips,ipph,ipe,iseen)
        fout_s,fout_u=extra_feats(o75,orr,opp,oc,os,oph,oe,oseen)
        q145=q135.copy()
        if sm.sum()>=50 and len(np.unique(y[tr][sm]))>1:
            ms=fit_lr(fin_s[sm],y[tr][sm])
            if oseen.any(): q145[oseen]=np.clip(ms.predict_proba(fout_s[oseen])[:,1],EPS,1-EPS)
        um=~iseen
        if um.sum()>=50 and len(np.unique(y[tr][um]))>1:
            mu=fit_lr(fin_u[um],y[tr][um])
            if (~oseen).any(): q145[~oseen]=np.clip(mu.predict_proba(fout_u[~oseen])[:,1],EPS,1-EPS)

        # Alignment control with identical model capacity and marginals.
        cis,ciph,cie=permute_extras(ips,ipph,ipe,iseen,SEED+1000*k)
        cos,coph,coe=permute_extras(os,oph,oe,oseen,SEED+2000*k)
        cin_s,cin_u=extra_feats(ip75,ipr,ipp,ic,cis,ciph,cie,iseen)
        cout_s,cout_u=extra_feats(o75,orr,opp,oc,cos,coph,coe,oseen)
        qctl=q135.copy()
        if sm.sum()>=50 and len(np.unique(y[tr][sm]))>1:
            cms=fit_lr(cin_s[sm],y[tr][sm])
            if oseen.any(): qctl[oseen]=np.clip(cms.predict_proba(cout_s[oseen])[:,1],EPS,1-EPS)
        if um.sum()>=50 and len(np.unique(y[tr][um]))>1:
            cmu=fit_lr(cin_u[um],y[tr][um])
            if (~oseen).any(): qctl[~oseen]=np.clip(cmu.predict_proba(cout_u[~oseen])[:,1],EPS,1-EPS)

        p135[va]=q135; p145[va]=q145; pctl[va]=qctl
        folds.append({
            'fold':k,'rows':int(len(va)),'supported_fraction':float(oseen.mean()),
            'v135_ll':ll(y[va],q135),'v145_ll':ll(y[va],q145),'control_ll':ll(y[va],qctl),
            'gain_v145_vs_v135':ll(y[va],q135)-ll(y[va],q145),
            'real_vs_control':ll(y[va],qctl)-ll(y[va],q145),
            'inner_supported':int(sm.sum()),'inner_unsupported':int(um.sum())
        })
        print(name,'FOLD',json.dumps(folds[-1]),flush=True)
    b=ll(y,p135); a=ll(y,p145); c=ll(y,pctl)
    return {'geometry':name,'v135_ll':b,'v145_ll':a,'control_ll':c,
            'gain_vs_v135':b-a,'real_vs_control':c-a,'folds':folds}


def main(a):
    t0=time.time(); f=load_training(a.features,a.labels).reset_index(drop=True)
    print('ROWS',len(f),'COLUMNS',list(f.columns),flush=True)
    y=f.target.to_numpy(int); sessions=f.session_id.astype(str).to_numpy()
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    support=f.learning_objective.astype(str).to_numpy()

    cache={}; us=np.unique(sessions)
    for j,sid in enumerate(us,1):
        cache[str(sid)]=load_transcript(a.transcripts/f'{sid}.csv')
        if j%2500==0: print('TRANSCRIPTS',j,'/',len(us),'elapsed',round(time.time()-t0,1),flush=True)

    print('BUILD_V75',flush=True); X75=build_v75(f,cache)
    rt=[]; rz=[]; seg_rows=[]; seg_nums=[]; phase_rows=[]; phase_nums=[]; ev_whole=[]; ev_seg=[]; ev_num=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; o=str(r.learning_objective)
        tx,z=segmented_control(d,o,'related'); rt.append(tx); rz.append(z)
        seg,_=choose_target_segment(d,o)
        vs,ns,_=trajectory_views(seg,o); seg_rows.append(vs); seg_nums.append(ns)
        pv,pn=phase_views(seg,o); phase_rows.append({**vs,**pv}); phase_nums.append(np.concatenate([ns,pn]))
        ew,enw=evidence_view(d,o); es,ens=evidence_view(seg,o)
        ev_whole.append(ew); ev_seg.append(es); ev_num.append(np.concatenate([enw,ens]))
        if (i+1)%5000==0: print('VIEW_ROWS',i+1,'elapsed',round(time.time()-t0,1),flush=True)
    Xr=build_control(rt,rz)
    Xs=build_X(f,seg_rows,seg_nums,'SEG')
    Xp=build_X(f,phase_rows,phase_nums,'PHASE')
    Xe=build_evidence(f,ev_whole,ev_seg,ev_num)
    for nm,X in [('V75',X75),('RELATED',Xr),('SEGMENT',Xs),('PHASE',Xp),('EVIDENCE',Xe)]:
        print(nm,'SHAPE',X.shape,'NNZ',X.nnz,flush=True)

    S=nested_world('session_grouped',sessions,X75,Xr,Xs,Xp,Xe,y,support)
    O=nested_world('objective_grouped',obj,X75,Xr,Xs,Xp,Xe,y,support)
    pass_mag=(S['gain_vs_v135']>=GAIN_GATE and O['gain_vs_v135']>=GAIN_GATE)
    pass_ctl=(S['real_vs_control']>0 and O['real_vs_control']>0)
    all_pos=(all(x['gain_v145_vs_v135']>0 for x in S['folds']) and all(x['gain_v145_vs_v135']>0 for x in O['folds']))
    verdict='PROMOTE_V145_TO_SMOKE' if pass_mag and pass_ctl and all_pos else 'CLOSE_V81_V84_V87_FAMILY_FOR_TOP3'
    out={'protocol':'V145_V135_PLUS_EVIDENCE_FAMILY','rows':int(len(f)),
         'residual':'V135 transfers externally but lacks top3 magnitude',
         'hypothesis':'target segment + instructional phase + evidence IR contain complementary sample-local information not already represented by V135',
         'precommit':{'gain_gate_each_geometry':GAIN_GATE,'real_beats_alignment_control_both':True,'all_outer_folds_positive':True,'no_sweep':True},
         'session_grouped':S,'objective_grouped':O,
         'decision':{'magnitude_pass':bool(pass_mag),'control_pass':bool(pass_ctl),'all_folds_positive':bool(all_pos),'verdict':verdict},
         'elapsed_seconds':float(time.time()-t0)}
    Path(a.out).write_text(json.dumps(out,indent=2)); print('FINAL',json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v145_v135_plus_evidence_family.json'); main(p.parse_args())

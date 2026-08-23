#!/usr/bin/env python3
"""V139: component-specific applicability induced by V138.

The whole-V135 two-literal gate was not admitted, but all V138 meta-folds selected
support_log<=q80 AND prior_disp>q20. V139 asks whether that geometry belongs only
to the objective-prior component. Composition-only is retained everywhere else.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.metrics import log_loss

from v75_canonical_trajectory import load_training,SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control
from v135_nested_supported_stack import components,feats,fit_stack,EPS,logit

RNG_SEED=20260823
SUPPORT_Q=.80
DISP_Q=.20

def main(a):
    t0=time.time(); f=load_training(a.features,a.labels).reset_index(drop=True)
    y=f.target.to_numpy(int); support=f.learning_objective.astype(str).to_numpy(); sessions=f.session_id.astype(str).to_numpy()
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    print('ROWS',len(f),'SESSIONS',len(np.unique(sessions)),'OBJECTIVES',len(np.unique(obj)),flush=True)
    cache={}; us=np.unique(sessions)
    for j,sid in enumerate(us,1):
        cache[str(sid)]=load_transcript(a.transcripts/f'{sid}.csv')
        if j%2500==0: print('TRANSCRIPTS',j,'/',len(us),'elapsed',round(time.time()-t0,1),flush=True)
    X75=build_v75(f,cache); print('V75',X75.shape,X75.nnz,'elapsed',round(time.time()-t0,1),flush=True)
    rt=[];rz=[]
    for i,r in f.iterrows():
        text,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(text);rz.append(z)
        if (i+1)%5000==0: print('RELATED_ROWS',i+1,'elapsed',round(time.time()-t0,1),flush=True)
    Xr=build_control(rt,rz); print('RELATED',Xr.shape,Xr.nnz,'elapsed',round(time.time()-t0,1),flush=True)

    n=len(y); P0=np.zeros(n);P1=np.zeros(n);P2=np.zeros(n);PG=np.zeros(n);PC=np.zeros(n);GM=np.zeros(n,bool)
    folds=[]; rng=np.random.default_rng(RNG_SEED)
    outer=list(GroupKFold(4).split(np.zeros(n),y,sessions))
    for k,(tr,va) in enumerate(outer,1):
        q0,o75,orr,opp,oc,oseen=components(X75,Xr,y,tr,va,support)
        ig=sessions[tr]; inner=list(GroupKFold(3).split(np.zeros(len(tr)),y[tr],ig))
        ip75=np.zeros(len(tr));ipr=np.zeros(len(tr));ipp=np.zeros(len(tr));ic=np.zeros(len(tr));iseen=np.zeros(len(tr),bool)
        for ltr,lva in inner:
            atr=tr[ltr];ava=tr[lva]
            _,a75,ar,ap,ac,aseen=components(X75,Xr,y,atr,ava,support)
            ip75[lva]=a75;ipr[lva]=ar;ipp[lva]=ap;ic[lva]=ac;iseen[lva]=aseen
        fitmask=iseen
        m1=fit_stack(feats(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask],False),y[tr][fitmask])
        m2=fit_stack(feats(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask],True),y[tr][fitmask])
        q1=q0.copy();q2=q0.copy()
        if oseen.any():
            q1[oseen]=np.clip(m1.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],False))[:,1],EPS,1-EPS)
            q2[oseen]=np.clip(m2.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)

        # Frozen V138-derived component region. Thresholds come only from outer-training inner-OOF fields.
        train_support=np.log1p(ic[fitmask])
        train_disp=np.abs(logit(ipp[fitmask])-logit(ip75[fitmask]))
        sth=float(np.quantile(train_support,SUPPORT_Q)); dth=float(np.quantile(train_disp,DISP_Q))
        outer_support=np.log1p(oc); outer_disp=np.abs(logit(opp)-logit(o75))
        gm=oseen & (outer_support<=sth) & (outer_disp>dth)
        qg=q1.copy(); qg[gm]=q2[gm]

        # Matched-coverage random prior activation among supported rows.
        sup_idx=np.flatnonzero(oseen); n_on=int(gm.sum()); cm=np.zeros(len(va),bool)
        if n_on>0:
            chosen=rng.choice(sup_idx,size=n_on,replace=False); cm[chosen]=True
        qc=q1.copy(); qc[cm]=q2[cm]

        P0[va]=q0;P1[va]=q1;P2[va]=q2;PG[va]=qg;PC[va]=qc;GM[va]=gm
        fr={'fold':k,'rows':int(len(va)),'supported_fraction':float(oseen.mean()),'prior_coverage':float(gm.mean()),
            'support_q80_threshold':sth,'prior_disp_q20_threshold':dth,
            'v97_ll':float(log_loss(y[va],q0)),'composition_ll':float(log_loss(y[va],q1)),
            'full_v135_ll':float(log_loss(y[va],q2)),'component_ll':float(log_loss(y[va],qg)),
            'random_control_ll':float(log_loss(y[va],qc))}
        folds.append(fr);print('FOLD',json.dumps(fr),flush=True)

    l0=float(log_loss(y,P0));l1=float(log_loss(y,P1));l2=float(log_loss(y,P2));lg=float(log_loss(y,PG));lc=float(log_loss(y,PC))
    inc=l2-lg; causal=lc-lg; all_nonreg=all(r['component_ll']<=r['v97_ll']+1e-12 for r in folds); beats=sum(r['component_ll']<r['full_v135_ll'] for r in folds)
    if inc>=.0005 and causal>=.0005 and beats>=3 and all_nonreg:
        verdict='PROMOTE_COMPONENT_LAW'; next_action='competition_shaped_runtime_verification'
    elif inc>0 and causal>=.0002 and beats>=3:
        verdict='RETAIN_COMPONENT_SIGNAL'; next_action='attack_then_untouched_verification'
    else:
        verdict='CLOSE_COMPONENT_APPLICABILITY_HYPOTHESIS'; next_action='zoom_out_beyond_current_composition_applicability'
    out={'protocol':'V139_COMPONENT_APPLICABILITY','rows':int(n),
      'controller':{'push':'full_v135','residual':'V138 stable support x prior-displacement geometry but whole-operator gate unadmitted',
        'diagnosis':{'primary':'component_applicability','secondary':'composition_representation'},
        'rival':'V138 interaction is incidental and matched random prior activation performs as well',
        'K_effect':['retain_v97_unsupported','retain_composition_outside_prior_region','label_free_inference','beat_full_v135','beat_matched_random_control'],
        'operator':'composition-only on supported rows except full V135 when support_log<=train_q80 and prior_disp>train_q20',
        'control':'same-count random prior activation','epistemic_status':'second_generation_mechanism_test_not_final_admission'},
      'v97_ll':l0,'composition_ll':l1,'composition_gain':l0-l1,'full_v135_ll':l2,'full_v135_gain':l0-l2,
      'component_ll':lg,'component_gain':l0-lg,'incremental_vs_v135':inc,'random_control_ll':lc,'gain_vs_random_control':causal,
      'prior_coverage':float(GM.mean()),'folds_beating_v135':int(beats),'all_fold_nonregression':bool(all_nonreg),'folds':folds,
      'decision':{'verdict':verdict,'next_action':next_action},'elapsed_seconds':float(time.time()-t0)}
    Path(a.out).write_text(json.dumps(out,indent=2));print('FINAL',json.dumps(out,indent=2),flush=True)
    np.savez_compressed(a.oof,y=y,sessions=sessions,objectives=obj,support=support,p_v97=P0,p_comp=P1,p_v135=P2,p_component=PG,p_random=PC,prior_gate=GM)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('v139_component_applicability.json'));p.add_argument('--oof',type=Path,default=Path('v139_component_oof.npz'));main(p.parse_args())

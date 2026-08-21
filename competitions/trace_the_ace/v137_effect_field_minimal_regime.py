#!/usr/bin/env python3
"""V137: residual-effect field -> minimal lawful supported-regime refinement.

V136 established a real but attenuated V135 effect on the full 35,072-row corpus:
+0.001771 session-grouped, positive in all four folds, exact objective-cold fallback.
V137 asks whether that attenuation is explained by ONE runtime-visible scalar split.

Protocol:
- session-grouped 4 outer folds; outer rows untouched;
- inner 3-fold OOF components and V135 stack inside each outer training partition;
- derive rowwise V135-vs-V97 loss benefit ONLY on inner-OOF supported rows;
- choose exactly one scalar, one threshold, one direction from a frozen small family;
- threshold candidates are frozen inner quantiles 0.1..0.9; no outer tuning;
- apply V135 only inside selected outer regime, V97 elsewhere;
- identical selector search on deterministically shuffled inner benefit is control;
- objective-shift safety is inherited structurally: unsupported rows always exact V97;
- emit row-level OOF field so future experiments do not need to rebuild transcripts.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import log_loss

from v75_canonical_trajectory import load_training,SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control
from v135_nested_supported_stack import components,feats,fit_stack,EPS,logit

QS=np.arange(.1,1.0,.1)
MIN_COVER=.10; MAX_COVER=.90
RNG_SEED=20260821

def sample_loss(y,p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS); y=np.asarray(y,float)
    return -(y*np.log(p)+(1-y)*np.log(1-p))

def runtime_field(p75,pr,pp,c):
    return {
      'support_log':np.log1p(c),
      'prior_disp':np.abs(logit(pp)-logit(p75)),
      'expert_disagree':np.abs(logit(p75)-logit(pr)),
      'prior_conf':np.abs(pp-.5),
      'v75_conf':np.abs(p75-.5),
      'prior_shift':logit(pp)-logit(p75),
    }

def choose_split(field,benefit):
    best=None
    for name,x in field.items():
        x=np.asarray(x,float)
        for q in QS:
            th=float(np.quantile(x,q))
            for direction in ('le','gt'):
                m=x<=th if direction=='le' else x>th
                cov=float(m.mean())
                if cov<MIN_COVER or cov>MAX_COVER: continue
                # Gain in mean loss across all rows if V135 is applied only on m.
                gain=float(np.mean(np.where(m,benefit,0.0)))
                rec={'feature':name,'quantile':float(q),'threshold':th,'direction':direction,
                     'coverage':cov,'inner_gain':gain}
                if best is None or gain>best['inner_gain']+1e-15:
                    best=rec
    return best

def apply_split(field,rule):
    x=np.asarray(field[rule['feature']],float)
    return x<=rule['threshold'] if rule['direction']=='le' else x>rule['threshold']

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
        text,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related');rt.append(text);rz.append(z)
        if (i+1)%5000==0: print('RELATED_ROWS',i+1,'elapsed',round(time.time()-t0,1),flush=True)
    Xr=build_control(rt,rz); print('RELATED',Xr.shape,Xr.nnz,'elapsed',round(time.time()-t0,1),flush=True)

    n=len(y); P0=np.zeros(n);P2=np.zeros(n);PG=np.zeros(n);PC=np.zeros(n);GM=np.zeros(n,bool)
    FOUT={k:np.zeros(n,float) for k in ['support_log','prior_disp','expert_disagree','prior_conf','v75_conf','prior_shift']}
    outer=list(GroupKFold(4).split(np.zeros(n),y,sessions)); fold_rows=[]; rng=np.random.default_rng(RNG_SEED)
    for k,(tr,va) in enumerate(outer,1):
        q0,o75,orr,opp,oc,oseen=components(X75,Xr,y,tr,va,support)
        ig=sessions[tr]; inner=list(GroupKFold(3).split(np.zeros(len(tr)),y[tr],ig))
        ip0=np.zeros(len(tr));ip75=np.zeros(len(tr));ipr=np.zeros(len(tr));ipp=np.zeros(len(tr));ic=np.zeros(len(tr));iseen=np.zeros(len(tr),bool)
        for ltr,lva in inner:
            atr=tr[ltr];ava=tr[lva]
            aq0,a75,ar,ap,ac,aseen=components(X75,Xr,y,atr,ava,support)
            ip0[lva]=aq0;ip75[lva]=a75;ipr[lva]=ar;ipp[lva]=ap;ic[lva]=ac;iseen[lva]=aseen
        fitmask=iseen
        m2=fit_stack(feats(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask],True),y[tr][fitmask])
        iq2=ip0.copy(); iq2[fitmask]=np.clip(m2.predict_proba(feats(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask],True))[:,1],EPS,1-EPS)
        q2=q0.copy();
        if oseen.any(): q2[oseen]=np.clip(m2.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)

        # Effect-field discovery only on supported inner-OOF rows.
        benefit=sample_loss(y[tr][fitmask],ip0[fitmask])-sample_loss(y[tr][fitmask],iq2[fitmask])
        fin=runtime_field(ip75[fitmask],ipr[fitmask],ipp[fitmask],ic[fitmask])
        rule=choose_split(fin,benefit)
        shuffled=benefit.copy(); rng.shuffle(shuffled)
        crule=choose_split(fin,shuffled)

        fout=runtime_field(o75,orr,opp,oc)
        gm=apply_split(fout,rule)&oseen
        cm=apply_split(fout,crule)&oseen
        qg=q0.copy();qg[gm]=q2[gm]
        qc=q0.copy();qc[cm]=q2[cm]
        P0[va]=q0;P2[va]=q2;PG[va]=qg;PC[va]=qc;GM[va]=gm
        for name in FOUT:FOUT[name][va]=fout[name]
        fr={'fold':k,'rows':int(len(va)),'supported_fraction':float(oseen.mean()),
            'v97_ll':float(log_loss(y[va],q0)),'full_v135_ll':float(log_loss(y[va],q2)),
            'gated_ll':float(log_loss(y[va],qg)),'shuffle_gate_ll':float(log_loss(y[va],qc)),
            'gated_coverage':float(gm.mean()),'control_coverage':float(cm.mean()),
            'rule':rule,'control_rule':crule}
        fold_rows.append(fr);print('FOLD',json.dumps(fr),flush=True)

    l0=float(log_loss(y,P0));l2=float(log_loss(y,P2));lg=float(log_loss(y,PG));lc=float(log_loss(y,PC))
    gated_gain=l0-lg; incremental=l2-lg; causal=lc-lg
    all_nonreg=all(r['gated_ll']<=r['v97_ll']+1e-12 for r in fold_rows)
    verdict=('PROMOTE_MINIMAL_REGIME_REFINEMENT' if gated_gain>=.003 and incremental>=.001 and causal>=.001 and all_nonreg
             else 'RETAIN_STRUCTURED_REGIME_SIGNAL' if gated_gain>l0-l2 and causal>0
             else 'CLOSE_ONE_SCALAR_REGIME_REFINEMENT')
    out={'protocol':'V137_EFFECT_FIELD_MINIMAL_REGIME','rows':int(n),
      'residual':'V135 effect attenuated from +0.009665 on 2500 discovery rows to +0.001771 on full 35072 while preserving sign across all folds',
      'version_space':{'operator':'one runtime-visible scalar split','features':list(FOUT),'quantiles':[float(x) for x in QS],
                       'directions':['le','gt'],'min_coverage':MIN_COVER,'max_coverage':MAX_COVER,'no_outer_tuning':True},
      'precommit':{'gated_gain':.003,'incremental_vs_full_v135':.001,'gain_vs_shuffled_selector':.001,'all_outer_folds_nonregress':True},
      'v97_ll':l0,'full_v135_ll':l2,'full_v135_gain':l0-l2,'gated_ll':lg,'gated_gain':gated_gain,
      'incremental_vs_full_v135':incremental,'shuffle_gate_ll':lc,'gain_vs_shuffle_gate':causal,
      'gated_coverage':float(GM.mean()),'folds':fold_rows,'decision':{'all_fold_nonregression':bool(all_nonreg),'verdict':verdict},
      'elapsed_seconds':float(time.time()-t0)}
    Path(a.out).write_text(json.dumps(out,indent=2));print('FINAL',json.dumps(out,indent=2),flush=True)
    np.savez_compressed(a.oof,y=y,sessions=sessions,objectives=obj,support=support,p_v97=P0,p_v135=P2,p_gated=PG,p_control=PC,gate=GM,
                        **{f'field_{k}':v for k,v in FOUT.items()})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',default='v137_effect_field.json');p.add_argument('--oof',default='v137_oof_field.npz');main(p.parse_args())

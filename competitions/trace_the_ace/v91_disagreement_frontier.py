#!/usr/bin/env python3
"""V91: disagreement-frontier applicability separator.

RGRS EXPEDITION after V88 R7 composition win.
Question: when V75 and EvidenceEvents disagree, can sample-local observable information
predict which expert should receive more weight?

All base predictions are objective-cold OOF. For each held-out fold, the router is fit only
on the other folds. Reports a fixed/global cross-fit blend, routed blend, and oracle headroom.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import evidence_events, render, nums, build_sparse, build_v75, oof


def row_features(df, seg, ev, p0, pe):
    n=max(1,len(df)); ns=max(1,len(seg))
    roles=df.role.fillna('').astype(str).str.lower()
    stu=(roles=='student').sum(); tut=(roles=='tutor').sum()
    texts=df.content.fillna('').astype(str)
    student_text=' '.join(df.loc[roles=='student','content'].fillna('').astype(str))
    math_chars=sum(c.isdigit() or c in '=+-*/%' for c in student_text)
    chars=max(1,len(student_text))
    rels=np.array([e['rel'] for e in ev],float) if ev else np.zeros(0)
    positions=np.array([e['position'] for e in ev],float) if ev else np.zeros(0)
    states=[e['state'] for e in ev]
    return np.array([
        p0, pe, pe-p0, abs(pe-p0), abs(p0-.5), abs(pe-.5),
        len(df), len(seg), ns/n, stu/n, tut/n, len(ev),
        float(rels.mean()) if len(rels) else 0., float(rels.max()) if len(rels) else 0.,
        float(positions.mean()) if len(positions) else 0.,
        float(sum(s=='INDEPENDENT_CORRECT' for s in states)),
        float(sum(s=='UNRESOLVED_ERROR' for s in states)),
        math_chars/chars,
        float(np.mean([len(x) for x in texts])) if len(texts) else 0.,
    ],float)


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    texts=[]; zz=[]; stored=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; seg,m=choose_target_segment(d,str(r.learning_objective)); ev=evidence_events(seg,str(r.learning_objective))
        texts.append(render(ev,str(r.learning_objective),ablate=True)); zz.append(nums(ev,ablate=True)); stored.append((d,seg,ev,m))
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    splits=list(GroupKFold(5).split(np.zeros(len(y)),y,groups))
    p0,_=oof(build_v75(f,cache),y,splits,'V75')
    pe,_=oof(build_sparse(texts,zz,'EVIDENCE_ABL'),y,splits,'EVIDENCE')
    X=np.vstack([row_features(*stored[i][:3],p0[i],pe[i]) for i in range(len(y))])
    # normalize within each training partition only below
    fold_id=np.empty(len(y),int)
    for k,(_,va) in enumerate(splits): fold_id[va]=k
    q_fixed=np.zeros(len(y)); q_route=np.zeros(len(y)); selected=[]
    grid=np.linspace(0,0.8,33)
    for k,(_,va) in enumerate(splits):
        tr=np.where(fold_id!=k)[0]
        # cross-fit fixed blend reference
        best=min(((float(log_loss(y[tr],np.clip((1-w)*p0[tr]+w*pe[tr],1e-5,1-1e-5))),float(w)) for w in grid), key=lambda z:z[0])
        wf=best[1]; q_fixed[va]=np.clip((1-wf)*p0[va]+wf*pe[va],1e-5,1-1e-5)
        # expert-win label: lower per-row log loss, equivalent to closer probability to realized label in log space
        l0=-(y[tr]*np.log(np.clip(p0[tr],1e-6,1))+(1-y[tr])*np.log(np.clip(1-p0[tr],1e-6,1)))
        le=-(y[tr]*np.log(np.clip(pe[tr],1e-6,1))+(1-y[tr])*np.log(np.clip(1-pe[tr],1e-6,1)))
        z=(le<l0).astype(int)
        mu=X[tr].mean(0); sd=X[tr].std(0)+1e-6
        model=LogisticRegression(C=.1,max_iter=500,class_weight='balanced').fit((X[tr]-mu)/sd,z)
        pr=model.predict_proba((X[va]-mu)/sd)[:,1]
        # router controls evidence weight around the empirically safe fixed weight; cap avoids hard switching
        wr=np.clip(wf*(0.35+1.65*pr),0,0.8)
        q_route[va]=np.clip((1-wr)*p0[va]+wr*pe[va],1e-5,1-1e-5)
        auc=float(roc_auc_score(((-(y[va]*np.log(np.clip(pe[va],1e-6,1))+(1-y[va])*np.log(np.clip(1-pe[va],1e-6,1)))) < (-(y[va]*np.log(np.clip(p0[va],1e-6,1))+(1-y[va])*np.log(np.clip(1-p0[va],1e-6,1))))).astype(int),pr)) if len(np.unique(y[va]))>1 else float('nan')
        selected.append({'fold':k+1,'fixed_weight':wf,'mean_routed_weight':float(wr.mean()),'router_win_auc':auc,'fixed_ll':float(log_loss(y[va],q_fixed[va])),'routed_ll':float(log_loss(y[va],q_route[va]))})
    # oracle only quantifies headroom; never admissible
    choose_e=np.where(y==1,pe>p0,pe<p0)
    q_oracle=np.where(choose_e,pe,p0)
    ll0=float(log_loss(y,p0)); llf=float(log_loss(y,q_fixed)); llr=float(log_loss(y,q_route)); llo=float(log_loss(y,q_oracle))
    out={'primary':'objective-cold-crossfitted','v75':ll0,'fixed_crossfit':llf,'routed_crossfit':llr,
         'gain_route_vs_v75':ll0-llr,'gain_route_vs_fixed':llf-llr,'oracle_headroom_vs_fixed':llf-llo,
         'oracle_logloss':llo,'folds':selected,
         'decision':'R5_APPLICABILITY_CONFIRMED' if llf-llr>=.001 else ('R5_WEAK' if llf-llr>0 else 'REJECT_ROUTER_CURRENT_FEATURES')}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v91_disagreement_frontier.json'); run(p.parse_args())

#!/usr/bin/env python3
"""V87: RGRS composition-before-invention test.

R7 hypothesis: V81 target/phase structure and V84 student-evidence IR are individually
incomplete but complementary to V75 whole-session context. Build all four OOF predictors
on identical objective-cold folds, then choose convex blend weights for each held-out fold
using ONLY the other four folds' OOF predictions.

This removes the optimistic full-OOF blend-weight selection used in exploratory V81/V84.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, trajectory_views
from v81_target_segment_phase import choose_target_segment, phase_views, build_X, oof
from v84_student_evidence import evidence_view, build_evidence


def simplex_grid(step=.1):
    vals=np.arange(0,1+1e-9,step)
    for w0 in vals:
      for w1 in vals:
        for w2 in vals:
          s=w0+w1+w2
          if s>1+1e-9: continue
          w3=1-s
          yield np.array([w0,w1,w2,w3],float)


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={}; whole_rows=[]; whole_nums=[]; seg_rows=[]; seg_nums=[]; phase_rows=[]; phase_nums=[]; ev_whole=[]; ev_seg=[]; ev_num=[]
    for i,r in f.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
        d=cache[sid]; obj=str(r.learning_objective)
        vw,nw,_=trajectory_views(d,obj); whole_rows.append(vw); whole_nums.append(nw)
        seg,_=choose_target_segment(d,obj); vs,ns,_=trajectory_views(seg,obj); seg_rows.append(vs); seg_nums.append(ns)
        pv,pn=phase_views(seg,obj); phase_rows.append({**vs,**pv}); phase_nums.append(np.concatenate([ns,pn]))
        ew,enw=evidence_view(d,obj); es,ens=evidence_view(seg,obj); ev_whole.append(ew); ev_seg.append(es); ev_num.append(np.concatenate([enw,ens]))
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); grp=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sp=list(GroupKFold(5).split(np.zeros(len(y)),y,grp))
    Xw=build_X(f,whole_rows,whole_nums,'WHOLE'); Xs=build_X(f,seg_rows,seg_nums,'SEG'); Xp=build_X(f,phase_rows,phase_nums,'PHASE'); Xe=build_evidence(f,ev_whole,ev_seg,ev_num)
    pw,_=oof(Xw,y,sp,'whole'); ps,_=oof(Xs,y,sp,'segment'); pp,_=oof(Xp,y,sp,'phase'); pe,_=oof(Xe,y,sp,'evidence')
    P=np.column_stack([pw,ps,pp,pe]); names=['whole','segment','phase','evidence']
    # Cross-fit the blend: each outer fold's weights are selected on the other 4 folds only.
    final=np.zeros(len(y)); fold_rows=[]
    all_idx=np.arange(len(y))
    for k,(_,va) in enumerate(sp,1):
        trmeta=np.setdiff1d(all_idx,va,assume_unique=False)
        best=None
        for w in simplex_grid(a.step):
            q=np.clip(P[trmeta]@w,1e-5,1-1e-5); ll=float(log_loss(y[trmeta],q))
            if best is None or ll<best[0]: best=(ll,w.copy())
        w=best[1]; q=np.clip(P[va]@w,1e-5,1-1e-5); final[va]=q
        row={'fold':k,'rows':len(va),'meta_train_logloss':best[0],'weights':{n:float(x) for n,x in zip(names,w)},'heldout_logloss':float(log_loss(y[va],q))}; fold_rows.append(row); print('FOLD',row)
    base=float(log_loss(y,pw)); composed=float(log_loss(y,final)); gain=base-composed
    # Fixed transparent candidate from exploratory V81+V84 geometry, evaluated only as secondary.
    # 0.525*(.72 whole + .20 seg + .08 phase) + .475 evidence
    wf=np.array([.378,.105,.042,.475]); fixed=np.clip(P@wf,1e-5,1-1e-5); fixed_ll=float(log_loss(y,fixed))
    out={'primary':'cross_fitted_objective_cold','whole_logloss':base,'crossfit_composition_logloss':composed,'gain_vs_whole':gain,
         'fixed_composition_logloss':fixed_ll,'folds':fold_rows,
         'decision':'R7_COMPOSITION_WIN' if gain>=.003 else ('R7_PROMISING' if gain>=.001 else 'R7_INSUFFICIENT')}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v87_rgrs_composition.json'); p.add_argument('--step',type=float,default=.1); run(p.parse_args())

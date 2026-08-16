#!/usr/bin/env python3
"""V94: smallest separator for the V89/V93 applicability residual.

Question: does non-target student evidence help only when it is a *comparable
control* for the target objective?

A0 GLOBAL  : all non-target transcript evidence (V89 representation).
A1 RELATED : only the most objective-related non-target lesson segments.
A2 DISTANT : deliberately least-related non-target segments (causal ablation).

Opposing discriminators:
  * objective-cold -- V93 says GLOBAL ability helps strongly.
  * session-cold   -- V93 says GLOBAL ability should be suppressed.

Promotion requires RELATED to preserve objective-cold gain while reducing the
session-cold penalty, and DISTANT must not reproduce the same effect.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import log_loss

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v81_target_segment_phase import choose_target_segment, split_segments, rel_text
from v85_evidence_state import build_v75, oof, evidence_events
from v89_relative_ability_composition import non_target_ability, build_ability, POS, NEG
from v93_shift_robust_validation import folds_from_groups


def _ability_from_rows(rows: pd.DataFrame, obj: str, meta: dict, tag: str):
    if rows is None or not len(rows):
        rows = pd.DataFrame(columns=['role','content'])
    roles = rows.role.astype(str).str.lower() if 'role' in rows else pd.Series([], dtype=str)
    contents = rows.content.fillna('').astype(str) if 'content' in rows else pd.Series([], dtype=str)
    students = contents[roles.eq('student')].tolist()
    tutors = contents[roles.eq('tutor')].tolist()
    pos = sum(bool(POS.search(x)) for x in tutors)
    neg = sum(bool(NEG.search(x)) for x in tutors)
    substantive = sum(bool(re.search(r"\d|[=+\-*/%]",x)) or len(x.split()) >= 2 for x in students)
    explain = sum(any(k in x.lower() for k in ['because','so ','therefore','i think','first','then']) for x in students)
    math = sum(bool(re.search(r"\d|[=+\-*/%]",x)) for x in students)
    n=max(1,len(students)); fbn=max(1,pos+neg)
    ev = evidence_events(rows.reset_index(drop=True), obj) if len(rows) else []
    z=np.asarray([
        len(rows),len(students),len(tutors),substantive/n,explain/n,math/n,
        pos/fbn,neg/fbn,(pos-neg)/fbn,len(ev),
        float(meta.get('chosen_mean_rel',0.0)),float(meta.get('chosen_max_rel',0.0)),
        float(meta.get('available_segments',0)),float(meta.get('chosen_segments',0)),
    ],float)
    text=' [STUDENT] '.join(students[-80:])
    verdict=' '.join('[POS]' if POS.search(x) else '[NEG]' if NEG.search(x) else '' for x in tutors[-100:])
    return f'[{tag}] {text} [VERDICTS] {verdict}', z


def segmented_control(df: pd.DataFrame, obj: str, mode: str):
    _, tm = choose_target_segment(df, obj)
    ts,te=int(tm['start']),int(tm['end'])
    cand=[]
    for s,e in split_segments(df):
        # exclude any segment overlapping the selected target segment
        if not (e <= ts or s >= te):
            continue
        part=df.iloc[s:e].copy().reset_index(drop=True)
        txt=' '.join(part.content.fillna('').astype(str))
        rel=float(rel_text(txt,obj))
        cand.append((rel,s,e,part))
    if not cand:
        rest=df.iloc[list(range(0,ts))+list(range(te,len(df)))].copy().reset_index(drop=True)
        return _ability_from_rows(rest,obj,{'available_segments':0,'chosen_segments':0},mode.upper())
    cand=sorted(cand,key=lambda x:(x[0],x[1]))
    # Keep about half the non-target segments, capped to three, to make RELATED and
    # DISTANT equal-budget representations rather than a length confound.
    k=max(1,min(3,int(np.ceil(len(cand)/2))))
    chosen = cand[-k:] if mode=='related' else cand[:k]
    rows=pd.concat([x[3] for x in sorted(chosen,key=lambda z:z[1])],ignore_index=True)
    rels=[x[0] for x in chosen]
    meta={'available_segments':len(cand),'chosen_segments':len(chosen),
          'chosen_mean_rel':float(np.mean(rels)),'chosen_max_rel':float(np.max(rels))}
    return _ability_from_rows(rows,obj,meta,mode.upper())


def build_control(texts, nums):
    hv=HashingVectorizer(n_features=2**17,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    X=hv.transform(texts); Z=np.vstack(nums).astype(float); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6)
    return hstack([X,csr_matrix(Z)],format='csr')


def eval_arm(name, X0, Xa, y, sp):
    p0,_=oof(X0,y,sp,name+':V75'); pa,_=oof(Xa,y,sp,name+':ABILITY')
    grid=np.linspace(0,0.6,25); curve=[]
    for w in grid:
        q=np.clip((1-w)*p0+w*pa,1e-5,1-1e-5)
        curve.append({'w':float(w),'ll':float(log_loss(y,q))})
    best=min(curve,key=lambda z:z['ll'])
    return {'v75':float(log_loss(y,p0)),'ability':float(log_loss(y,pa)),'best':best,
            'gain':float(log_loss(y,p0)-best['ll'])}


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    gt=[];gz=[];rt=[];rz=[];dt=[];dz=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; obj=str(r.learning_objective)
        t,z=non_target_ability(d,obj); gt.append(t); gz.append(z)
        t,z=segmented_control(d,obj,'related'); rt.append(t); rz.append(z)
        t,z=segmented_control(d,obj,'distant'); dt.append(t); dz.append(z)
        if (i+1)%2500==0: print('rows',i+1)
    X0=build_v75(f,cache); Xg=build_ability(gt,gz); Xr=build_control(rt,rz); Xd=build_control(dt,dz)
    y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sess=f.session_id.astype(str).to_numpy()
    worlds={'objective_cold':folds_from_groups(obj),'session_cold':folds_from_groups(sess)}
    out={'primary':'related-control-separator','worlds':{}}
    for wn,sp in worlds.items():
        out['worlds'][wn]={
            'global':eval_arm(wn+':GLOBAL',X0,Xg,y,sp),
            'related':eval_arm(wn+':RELATED',X0,Xr,y,sp),
            'distant':eval_arm(wn+':DISTANT',X0,Xd,y,sp),
        }
    o=out['worlds']['objective_cold']; s=out['worlds']['session_cold']
    obj_preserve=o['related']['gain'] >= 0.75*max(1e-9,o['global']['gain'])
    session_repair=s['related']['best']['ll'] <= s['global']['best']['ll']-0.0005
    causal=o['related']['best']['ll'] <= o['distant']['best']['ll']-0.0005
    if obj_preserve and session_repair and causal:
        verdict='PROMOTE_RELATED_CONTROL'
    elif o['related']['best']['ll'] < o['global']['best']['ll'] and causal:
        verdict='PARTIAL_R5_REFINE'
    else:
        verdict='REJECT_RELATEDNESS_OBSERVABLE'
    out['decision']={'objective_gain_preserved':bool(obj_preserve),'session_penalty_repaired':bool(session_repair),
                     'causal_vs_distant':bool(causal),'verdict':verdict}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v94_related_control.json'); run(p.parse_args())

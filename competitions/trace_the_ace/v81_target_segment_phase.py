#!/usr/bin/env python3
"""V81: target-segment phase automaton for Trace the Ace.

Hypothesis: the strongest remaining representation error is mixing evidence from
multiple lessons/objectives inside one tutoring session. V81 detects explicit
lesson boundaries and instructional phases, selects the segment most aligned to
the assessed objective, then compares:
  A) frozen-style whole-session V75 views
  B) V75 views on the selected target segment only
  C) target-segment phase-state views + explicit before/after mastery features
Primary validation: exact-objective-cold GroupKFold.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from v71_mastery_events import inspect_headers, load_transcript, tokens, jaccard, char_ngram_overlap
from v75_canonical_trajectory import trajectory_views, load_training, SEED

BOUNDARY_RE = re.compile(r"\b(?:next lesson|next learning objective|move on to the next|start something new|new lesson|completed this (?:whole )?lesson|finished this lesson|move on|next topic)\b", re.I)
GOAL_RE = re.compile(r"\b(?:learning goal|learning objective|today we(?:'re| are) learning|we are going to learn|we(?:'ll| will) learn)\b", re.I)
PRIOR_RE = re.compile(r"\b(?:prior learning|before we start|what do you already know|recap|remember from)\b", re.I)
GUIDED_RE = re.compile(r"\b(?:i do|let me show|watch me|we do|let's do|lets do|together|with me|guided)\b", re.I)
INDEP_RE = re.compile(r"\b(?:you do|your turn|try this one|have a go|independently|by yourself|on your own)\b", re.I)
APPLY_RE = re.compile(r"\b(?:application|apply|challenge|reasoning|problem solving|different example|another example|transfer)\b", re.I)


def rel_text(text: str, objective: str) -> float:
    return float(max(jaccard(tokens(text), tokens(objective)), 0.5*char_ngram_overlap(text, objective)))


def split_segments(df: pd.DataFrame) -> list[tuple[int,int]]:
    txt=df.content.fillna('').astype(str).tolist(); starts=[0]
    for i,t in enumerate(txt):
        if i>0 and BOUNDARY_RE.search(t): starts.append(i)
    starts=sorted(set(starts)); segs=[]
    for j,s in enumerate(starts):
        e=starts[j+1] if j+1<len(starts) else len(df)
        if e>s: segs.append((s,e))
    return segs or [(0,len(df))]


def choose_target_segment(df: pd.DataFrame, objective: str) -> tuple[pd.DataFrame, dict]:
    segs=split_segments(df); best=None
    for s,e in segs:
        part=df.iloc[s:e].copy(); text=' '.join(part.content.fillna('').astype(str))
        score=rel_text(text,objective)
        # explicit goal language near the segment front is strong evidence
        front=' '.join(part.content.fillna('').astype(str).head(20))
        goal_bonus=0.15 if GOAL_RE.search(front) else 0.0
        total=score+goal_bonus
        row=(total,score,goal_bonus,s,e)
        if best is None or row>best: best=row
    _,score,bonus,s,e=best
    return df.iloc[s:e].copy().reset_index(drop=True), {'segments':len(segs),'start':int(s),'end':int(e),'segment_fraction':float((e-s)/max(1,len(df))),'segment_relevance':float(score),'goal_bonus':float(bonus)}


def phase_for(text: str, current: str) -> str:
    if GOAL_RE.search(text): return 'GOAL'
    if PRIOR_RE.search(text): return 'PRIOR'
    if APPLY_RE.search(text): return 'APPLICATION'
    if INDEP_RE.search(text): return 'INDEPENDENT'
    if GUIDED_RE.search(text): return 'GUIDED'
    return current


def phase_views(seg: pd.DataFrame, objective: str) -> tuple[dict[str,str], np.ndarray]:
    phase='OTHER'; buckets={k:[] for k in ['GOAL','PRIOR','GUIDED','INDEPENDENT','APPLICATION','OTHER']}
    for r in seg[['role','content']].itertuples(index=False):
        text=str(r.content); phase=phase_for(text,phase)
        buckets[phase].append(f'[{str(r.role).upper()}] {text}')
    texts={k:' '.join(v) for k,v in buckets.items()}
    # Reuse V75 state extraction per phase so the abstraction stays comparable.
    phase_num=[]; phase_state=[]
    for k in ['PRIOR','GUIDED','INDEPENDENT','APPLICATION']:
        sub=seg.iloc[0:0].copy()
        if buckets[k]:
            # recover rows by a simple phase replay
            phase2='OTHER'; idx=[]
            for i,r in enumerate(seg[['content']].itertuples(index=False)):
                phase2=phase_for(str(r.content),phase2)
                if phase2==k: idx.append(i)
            if idx: sub=seg.iloc[idx].copy().reset_index(drop=True)
        if len(sub):
            v,n,_=trajectory_views(sub,objective); phase_num.append(n); phase_state.append(v['canonical'])
        else:
            phase_num.append(np.zeros(28,float)); phase_state.append('')
    P=np.vstack(phase_num)
    # Explicit learning-gain contrasts; first 28 are phase means collapsed pairwise.
    pre=P[0]; guided=P[1]; indep=P[2]; app=P[3]
    gain_ind=indep-pre; gain_app=app-pre
    # compact summary scalars on key V75 dimensions: state score, positive/error/independent weighted-ish slots
    key=[12,13,14,15,17,21,22,23,24,25]
    scal=[]
    for arr in [pre,guided,indep,app,gain_ind,gain_app]: scal.extend(arr[key].tolist())
    nums=np.asarray(scal,float)
    views={
      'phase_prior':texts['PRIOR'], 'phase_guided':texts['GUIDED'],
      'phase_independent':texts['INDEPENDENT'], 'phase_application':texts['APPLICATION'],
      'phase_states':' [PHASE] '.join(phase_state),
    }
    return views,nums


def folds(groups):
    g=groups.astype(str).to_numpy(); z=np.zeros(len(g)); return list(GroupKFold(5).split(z,z,g))


def build_X(frame, rows, nums, prefix):
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    parts=[hv.transform([f'[OBJECTIVE] {x}' for x in frame.learning_objective])]
    keys=list(rows[0].keys())
    for k in keys: parts.append(hv.transform([f'[{prefix}_{k.upper()}] '+r[k] for r in rows]))
    Z=np.vstack(nums).astype(float); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6)
    parts.append(csr_matrix(Z)); return hstack(parts,format='csr')


def oof(X,y,split,name):
    p=np.zeros(len(y)); fr=[]
    for k,(tr,va) in enumerate(split,1):
        m=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X[tr],y[tr])
        q=np.clip(m.predict_proba(X[va])[:,1],1e-5,1-1e-5); p[va]=q
        row={'fold':k,'rows':len(va),'logloss':float(log_loss(y[va],q)),'auc':float(roc_auc_score(y[va],q))}; fr.append(row); print(name,row)
    return p,fr


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    if a.limit: f=f.iloc[:a.limit].copy().reset_index(drop=True)
    whole_rows=[]; whole_nums=[]; seg_rows=[]; seg_nums=[]; phase_rows=[]; phase_nums=[]; meta=[]; cache={}
    for i,r in f.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
        d=cache[sid]; vw,nw,_=trajectory_views(d,str(r.learning_objective)); whole_rows.append(vw); whole_nums.append(nw)
        seg,m=choose_target_segment(d,str(r.learning_objective)); vs,ns,_=trajectory_views(seg,str(r.learning_objective)); seg_rows.append(vs); seg_nums.append(ns)
        pv,pn=phase_views(seg,str(r.learning_objective)); phase_rows.append({**vs,**pv}); phase_nums.append(np.concatenate([ns,pn])); meta.append(m)
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); grp=f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective; sp=folds(grp)
    Xw=build_X(f,whole_rows,whole_nums,'WHOLE'); Xs=build_X(f,seg_rows,seg_nums,'SEG'); Xp=build_X(f,phase_rows,phase_nums,'PHASE')
    pw,fw=oof(Xw,y,sp,'whole'); ps,fs=oof(Xs,y,sp,'segment'); pp,fp=oof(Xp,y,sp,'phase')
    grid=[]; best=None
    for ws in np.linspace(0,1,11):
      for wp in np.linspace(0,1-ws,11):
        ww=1-ws-wp; q=np.clip(ww*pw+ws*ps+wp*pp,1e-5,1-1e-5); ll=float(log_loss(y,q)); row={'whole_weight':float(ww),'segment_weight':float(ws),'phase_weight':float(wp),'logloss':ll}
        grid.append(row); best=row if best is None or ll<best['logloss'] else best
    result={'rows':len(f),'primary':'objective-cold','whole_logloss':float(log_loss(y,pw)),'segment_logloss':float(log_loss(y,ps)),'phase_logloss':float(log_loss(y,pp)),'best_blend':best,'folds':{'whole':fw,'segment':fs,'phase':fp},'segmentation':{'mean_fraction':float(np.mean([m['segment_fraction'] for m in meta])),'mean_segments':float(np.mean([m['segments'] for m in meta])),'fraction_multisegment':float(np.mean([m['segments']>1 for m in meta]))}}
    Path(a.out).write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v81_target_segment_phase.json'); p.add_argument('--limit',type=int,default=0); run(p.parse_args())

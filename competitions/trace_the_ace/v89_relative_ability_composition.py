#!/usr/bin/env python3
"""V89: target mastery relative to within-session student ability.

RGRS hypothesis: V88 captures target-local evidence but not the student's general
baseline competence expressed elsewhere in the same transcript. Build a sample-
local, non-target ability view and test whether it adds orthogonal signal to
V75 + EvidenceEvents under objective-cold cross-fitted composition.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment, split_segments
from v85_evidence_state import evidence_events, render, nums, build_sparse, build_v75, oof

POS=re.compile(r"\b(?:correct|right|exactly|great|brilliant|well done|good job|perfect|yes)\b",re.I)
NEG=re.compile(r"\b(?:incorrect|wrong|not quite|try again|check|almost|no[, .])\b",re.I)


def non_target_ability(df,obj):
    target,meta=choose_target_segment(df,obj)
    ts,te=meta['start'],meta['end']
    # preserve all transcript rows outside selected target segment
    rest=df.iloc[list(range(0,ts))+list(range(te,len(df)))].copy().reset_index(drop=True)
    if not len(rest): rest=df.iloc[0:0].copy()
    ev=evidence_events(rest,obj)
    # objective relevance is intentionally not required here: this is general ability.
    students=rest[rest.role.astype(str).str.lower().eq('student')].content.fillna('').astype(str).tolist() if len(rest) else []
    tutors=rest[rest.role.astype(str).str.lower().eq('tutor')].content.fillna('').astype(str).tolist() if len(rest) else []
    pos=sum(bool(POS.search(x)) for x in tutors); neg=sum(bool(NEG.search(x)) for x in tutors)
    substantive=sum(bool(re.search(r"\d|[=+\-*/%]",x)) or len(x.split())>=2 for x in students)
    explain=sum(any(k in x.lower() for k in ['because','so ','therefore','i think','first','then']) for x in students)
    math=sum(bool(re.search(r"\d|[=+\-*/%]",x)) for x in students)
    n=max(1,len(students)); fbn=max(1,pos+neg)
    z=np.asarray([
        len(rest),len(students),len(tutors),substantive/n,explain/n,math/n,
        pos/fbn,neg/fbn,(pos-neg)/fbn,len(ev),meta['segment_fraction'],meta['segments']
    ],float)
    # compact text: student production + tutor verdict tokens, no target segment content
    text=' [STUDENT] '.join(students[-80:])
    verdict=' '.join('[POS]' if POS.search(x) else '[NEG]' if NEG.search(x) else '' for x in tutors[-100:])
    return f'[GENERAL_STUDENT] {text} [GENERAL_VERDICTS] {verdict}',z


def build_ability(texts,z):
    hv=HashingVectorizer(n_features=2**17,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    X=hv.transform(texts); Z=np.vstack(z); Z=(Z-Z.mean(0))/(Z.std(0)+1e-6)
    return hstack([X,csr_matrix(Z)],format='csr')


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True); cache={}
    for sid in f.session_id.astype(str).unique(): cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
    et=[]; ez=[]; at=[]; az=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; obj=str(r.learning_objective)
        seg,_=choose_target_segment(d,obj); ev=evidence_events(seg,obj)
        et.append(render(ev,obj,ablate=True)); ez.append(nums(ev,ablate=True))
        t,z=non_target_ability(d,obj); at.append(t); az.append(z)
        if (i+1)%2500==0: print('rows',i+1)
    y=f.target.to_numpy(int); groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sp=list(GroupKFold(5).split(np.zeros(len(y)),y,groups)); fold=np.empty(len(y),int)
    for k,(_,va) in enumerate(sp): fold[va]=k
    X0=build_v75(f,cache); Xe=build_sparse(et,ez,'EVIDENCE_ABL'); Xa=build_ability(at,az)
    p0,_=oof(X0,y,sp,'V75'); pe,_=oof(Xe,y,sp,'EVIDENCE'); pa,_=oof(Xa,y,sp,'ABILITY')
    q=np.zeros(len(y)); sel=[]
    grid=np.arange(0,0.61,0.1)
    for k,(_,va) in enumerate(sp):
        tune=np.where(fold!=k)[0]; best=None
        for we in grid:
            for wa in grid:
                if we+wa>.8: continue
                p=np.clip((1-we-wa)*p0[tune]+we*pe[tune]+wa*pa[tune],1e-5,1-1e-5)
                ll=float(log_loss(y[tune],p))
                if best is None or ll<best['tune_logloss']: best={'evidence_weight':float(we),'ability_weight':float(wa),'tune_logloss':ll}
        we,wa=best['evidence_weight'],best['ability_weight']; q[va]=np.clip((1-we-wa)*p0[va]+we*pe[va]+wa*pa[va],1e-5,1-1e-5)
        best.update(fold=k+1,heldout_logloss=float(log_loss(y[va],q[va]))); sel.append(best); print(best)
    ll0=float(log_loss(y,p0)); llq=float(log_loss(y,q)); out={
      'primary':'objective-cold-crossfitted','v75':ll0,'evidence':float(log_loss(y,pe)),'ability':float(log_loss(y,pa)),
      'composition':llq,'gain_vs_v75':ll0-llq,'gain_vs_v88_reference':0.589227-llq,
      'selected_by_fold':sel,'mean_evidence_weight':float(np.mean([x['evidence_weight'] for x in sel])),
      'mean_ability_weight':float(np.mean([x['ability_weight'] for x in sel]))}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v89_relative_ability.json'); run(p.parse_args())

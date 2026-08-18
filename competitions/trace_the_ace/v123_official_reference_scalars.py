#!/usr/bin/env python3
"""V123 — inject the three official DrivenData productive-math-talk scalars into V97.

Residual: V75/V97 use L2-normalized hashed text plus event-state numerics, so they do not
explicitly retain absolute student word volume or the reference solution's two number-use ratios.

Frozen fast protocol:
- deterministic 2500-row sample (same stable hash style as V112)
- baseline: fold-local V97
- intervention: logistic residual [logit(V97), n_student_words,
  numeric_turns_per_word, digit_chars_per_word]
- two untouched geometries: objective-grouped and session-grouped 4-fold OOF
- control: deterministic permutation of the three scalar rows before residual fitting
- no hyperparameter search; C=.15
- retain as a law only if gain >= .0015 in BOTH geometries and each exceeds its shuffle
  control by >= .001. >= .003 in both is a phase-change candidate.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from v71_mastery_events import load_transcript, normalize_roles
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control

EPS=1e-5
WORD_RE=re.compile(r"[a-z0-9]+(?:'[a-z]+)?",re.I)
DIGIT_RE=re.compile(r"\d")

def stable(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def logit(p):
 p=np.clip(np.asarray(p,float),EPS,1-EPS); return np.log(p/(1-p))
def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS),labels=[0,1]))

def reference_scalars(df: pd.DataFrame):
 d=normalize_roles(df).reset_index(drop=True)
 roles=d.role_repaired.astype(str).str.lower()
 student=d.loc[roles.eq('student'),'content'].fillna('').astype(str)
 text=' '.join(student.tolist())
 n_words=len(WORD_RE.findall(text))
 if n_words<=0: return np.array([0.,0.,0.],float)
 return np.array([
   float(n_words),
   float(student.str.contains(r'\d',regex=True).sum()/n_words),
   float(len(DIGIT_RE.findall(text))/n_words),
 ],float)

def base_predictions(X75,Xr,y,support,groups):
 q=np.zeros(len(y),float)
 for tr,va in GroupKFold(min(4,len(np.unique(groups)))).split(np.zeros(len(y)),y,groups):
   m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr])
   mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr])
   p0=m0.predict_proba(X75[va])[:,1]; pr=mr.predict_proba(Xr[va])[:,1]
   counts=pd.Series(support[tr]).value_counts()
   unseen=np.array([counts.get(x,0)==0 for x in support[va]])
   q[va]=np.where(unseen,.65*p0+.35*pr,p0)
 return np.clip(q,EPS,1-EPS)

def residual_oof(base,Z,y,groups):
 q=np.zeros(len(y),float)
 splits=list(GroupKFold(min(4,len(np.unique(groups)))).split(Z,y,groups))
 for tr,va in splits:
   sc=StandardScaler().fit(Z[tr])
   xt=np.c_[logit(base[tr]),sc.transform(Z[tr])]
   xv=np.c_[logit(base[va]),sc.transform(Z[va])]
   m=LogisticRegression(C=.15,max_iter=250,solver='liblinear',random_state=SEED).fit(xt,y[tr])
   q[va]=m.predict_proba(xv)[:,1]
 return np.clip(q,EPS,1-EPS)

def run(a):
 f=load_training(a.features,a.labels).reset_index(drop=True)
 print('joined columns',list(f.columns),flush=True)
 oid=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
 order=np.argsort(np.array([stable(x) for x in f.response_id.astype(str)]))[:a.rows]
 f=f.iloc[order].reset_index(drop=True)
 y=f.target.to_numpy(int); oid=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
 sess=f.session_id.astype(str).to_numpy(); support=f.learning_objective.astype(str).to_numpy()
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}
 session_Z={s:reference_scalars(cache[s]) for s in np.unique(sess)}
 Z=np.vstack([session_Z[s] for s in sess])
 print('scalar means',Z.mean(0).tolist(),'scalar stds',Z.std(0).tolist(),flush=True)
 rt=[];rz=[]
 for i,r in f.iterrows():
   t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related');rt.append(t);rz.append(z)
   if (i+1)%500==0: print('prepared',i+1,flush=True)
 X75=build_v75(f,cache); Xr=build_control(rt,rz)
 rng=np.random.default_rng(20260818); perm=rng.permutation(len(Z)); Zs=Z[perm]
 out={'rows':int(len(f)),'sessions':int(len(np.unique(sess))),'objectives':int(len(np.unique(oid))),
      'features':['n_student_words','numeric_turns_per_word','digit_chars_per_word'],'geometries':{}}
 for name,g in [('objective_cold',oid),('session_cold',sess)]:
   b=base_predictions(X75,Xr,y,support,g); q=residual_oof(b,Z,y,g); qs=residual_oof(b,Zs,y,g)
   base_ll=ll(y,b); qll=ll(y,q); sll=ll(y,qs)
   out['geometries'][name]={'v97_ll':base_ll,'reference_scalar_ll':qll,'gain':base_ll-qll,
                            'shuffle_ll':sll,'shuffle_gain':base_ll-sll,'ablation_margin':sll-qll}
   print(name,out['geometries'][name],flush=True)
 go=out['geometries']['objective_cold']['gain']; gs=out['geometries']['session_cold']['gain']
 mo=out['geometries']['objective_cold']['ablation_margin']; ms=out['geometries']['session_cold']['ablation_margin']
 if go>=.003 and gs>=.003 and mo>=.001 and ms>=.001: verdict='PHASE_CHANGE_SCALARS'
 elif go>=.0015 and gs>=.0015 and mo>=.001 and ms>=.001: verdict='RETAIN_REFERENCE_SCALAR_LAW'
 else: verdict='SUPPRESS_REFERENCE_SCALAR_INJECTION'
 out['decision']={'verdict':verdict,'rule':'retain >=.0015 gain both geometries and >=.001 ablation margin both; phase-change >=.003 both'}
 Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v123_official_reference_scalars.json');run(p.parse_args())

#!/usr/bin/env python3
"""V114 REPRESENTATION -> APPLICABILITY intervention.

Question left by V112/V113:
  V112: raw transcript views did not improve direct label prediction.
  V113: geometry/support/session metadata did not recover the endpoint-oracle gap.

V114 asks the missing cross: can richer row-level representation predict WHICH already-capable
endpoint (V75 or RELATED) should apply? This is an applicability target, not another label model.

Frozen protocol:
- deterministic 2500-row sample (same hash rule as V112/V113)
- objective-grouped 4-fold outer OOF
- endpoints trained only on outer-train rows
- oracle-choice target formed per row from endpoint losses, used only inside outer-train for gate fit
- fixed conservative routing weight 0.65; no hyperparameter sweep
- families: geometry, objective semantics, raw transcript, objective+raw, full representation
- controls: response/session ID placebo; shuffled applicability target; flipped-route ablation

Decision thresholds (precommitted before result):
- PHASE_CHANGE_REPRESENTATION: gain >= .010 and all folds nonnegative, OR gain >= .008 and >=15% oracle-gap recovery
- REPRESENTATION_REPAIR_FOUND: gain >= .003, >=3/4 positive folds, controls <25% real gain, flipped route <=0
- STRUCTURED_REPRESENTATION_HINT: .001 <= gain < .003 and best family beats geometry by >=.001
- otherwise REPRESENTATION_NOT_OBSERVED
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import HistGradientBoostingClassifier
from v71_mastery_events import load_transcript, normalize_roles
from v75_canonical_trajectory import load_training, SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
from v110_residual_collider_state_discovery import hb, ll

EPS=1e-5

def H(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def lossrow(y,p):
 p=np.clip(p,EPS,1-EPS)
 return -(y*np.log(p)+(1-y)*np.log(1-p))
def geometry(p0,pr):
 d=pr-p0
 return np.c_[p0,pr,d,np.abs(d),np.abs(p0-.5),np.abs(pr-.5),np.minimum(p0,pr),np.maximum(p0,pr)]
def transcript_views(df,obj):
 d=normalize_roles(df).reset_index(drop=True)
 roles=d.role_repaired.astype(str).tolist(); c=d.content.fillna('').astype(str).tolist()
 stu=' '.join(x for r,x in zip(roles,c) if r=='student')
 tut=' '.join(x for r,x in zip(roles,c) if r=='tutor')
 full=' '.join(f'[{r}] {x}' for r,x in zip(roles,c))
 seg,_=choose_target_segment(df,obj); s=normalize_roles(seg).reset_index(drop=True)
 local=' '.join(f'[{r}] {x}' for r,x in zip(s.role_repaired.astype(str),s.content.fillna('').astype(str)))
 last=' '.join(f'[{r}] {x}' for r,x in list(zip(roles,c))[-8:])
 return stu,tut,full,local,last

def route(p0,pr,g,flip=False):
 if flip: g=1-g
 w=np.clip(.65*g,0,.65)
 return np.clip((1-w)*p0+w*pr,EPS,1-EPS)
def fit_dense_gate(X,win,sw,tr,va):
 m=HistGradientBoostingClassifier(max_depth=2,max_iter=70,learning_rate=.05,min_samples_leaf=80,l2_regularization=2.,random_state=SEED)
 m.fit(X[tr],win[tr],sample_weight=sw[tr])
 return m.predict_proba(X[va])[:,1]
def fit_sparse_gate(X,win,sw,tr,va,shuffle=False):
 yt=win[tr].copy()
 if shuffle:
  rng=np.random.default_rng(SEED+len(tr)+len(va)); yt=yt[rng.permutation(len(yt))]
 # geometry is already concatenated into X; fixed regularization, no sweep
 m=LogisticRegression(C=.08,max_iter=220,solver='liblinear',random_state=SEED)
 m.fit(X[tr],yt,sample_weight=sw[tr])
 return m.predict_proba(X[va])[:,1]
def main(a):
 f0=load_training(a.features,a.labels).reset_index(drop=True)
 print('features columns',list(f0.columns),flush=True)
 objall=(f0.learning_objective_id if 'learning_objective_id' in f0 else f0.learning_objective).astype(str).to_numpy()
 cand=np.where(np.array([hb(x,5)!=0 for x in objall]))[0]
 ix=np.array(sorted(cand,key=lambda i:H(f0.response_id.iloc[i]))[:a.rows])
 f=f0.iloc[ix].reset_index(drop=True)
 y=f.target.to_numpy(int)
 obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
 key=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}
 rt=[]; rz=[]; T={k:[] for k in ['STUDENT','TUTOR','FULL','LOCAL','LAST8']}
 for _,r in f.iterrows():
  d=cache[str(r.session_id)]
  t,z=segmented_control(d,str(r.learning_objective),'related'); rt.append(t); rz.append(z)
  vals=transcript_views(d,str(r.learning_objective))
  for k,v in zip(T,vals): T[k].append(v)
 X75=build_v75(f,cache); Xr=build_control(rt,rz)
 P0=np.zeros(len(f)); PR=np.zeros(len(f)); fold=np.full(len(f),-1,int)
 splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(y)),y,obj))
 for k,(tr,va) in enumerate(splits):
  m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr])
  mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr])
  P0[va]=np.clip(m0.predict_proba(X75[va])[:,1],EPS,1-EPS)
  PR[va]=np.clip(mr.predict_proba(Xr[va])[:,1],EPS,1-EPS); fold[va]=k
 # exact-support V97 reconstruction, same rule as V113
 base=np.zeros(len(y))
 allidx=np.arange(len(y))
 for i in range(len(y)):
  tr=allidx[fold!=fold[i]]
  base[i]=.65*P0[i]+.35*PR[i] if np.sum(key[tr]==key[i])==0 else P0[i]
 base=np.clip(base,EPS,1-EPS)
 base_ll=ll(y,base)
 L0=lossrow(y,P0); LR=lossrow(y,PR); win=(LR<L0).astype(int); sw=np.abs(L0-LR)+.01
 oracle=np.where(win==1,PR,P0); oracle_ll=ll(y,oracle); gap=base_ll-oracle_ll
 G=geometry(P0,PR)
 hvw=HashingVectorizer(n_features=2**15,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
 hvc=HashingVectorizer(n_features=2**15,alternate_sign=False,norm='l2',analyzer='char_wb',ngram_range=(3,5),lowercase=True)
 OBJW=hvw.transform(key); OBJC=hvc.transform(key)
 RAW=hstack([hvw.transform(T['STUDENT']),hvw.transform(T['TUTOR']),hvw.transform(T['LOCAL']),hvw.transform(T['LAST8'])],format='csr')
 GS=csr_matrix(G)
 ID=csr_matrix(np.c_[np.array([H(x)%997 for x in f.response_id.astype(str)])/997.,np.array([H(x)%31 for x in sess])/31.])
 mats={
  'GEOMETRY':G,
  'OBJECTIVE_SEMANTICS':hstack([GS,OBJW,OBJC],format='csr'),
  'RAW_TRANSCRIPT':hstack([GS,RAW],format='csr'),
  'OBJECTIVE_X_RAW':hstack([GS,OBJW,OBJC,RAW],format='csr'),
  'FULL_REPRESENTATION':hstack([GS,OBJW,OBJC,RAW,csr_matrix(X75),csr_matrix(Xr)],format='csr'),
  'ID_PLACEBO':hstack([GS,ID],format='csr')
 }
 preds={k:np.zeros(len(y)) for k in mats}; shuffled=np.zeros(len(y)); gate_keep={k:np.zeros(len(y)) for k in mats}
 for _,(tr,va) in enumerate(splits):
  for name,X in mats.items():
   gp=fit_dense_gate(X,win,sw,tr,va) if name=='GEOMETRY' else fit_sparse_gate(X,win,sw,tr,va)
   gate_keep[name][va]=gp; preds[name][va]=route(P0[va],PR[va],gp)
  shuffled[va]=route(P0[va],PR[va],fit_sparse_gate(mats['OBJECTIVE_X_RAW'],win,sw,tr,va,shuffle=True))
 tests={}
 for name,q in preds.items():
  fg=[float(ll(y[va],base[va])-ll(y[va],q[va])) for _,va in splits]
  tests[name]={'ll':float(ll(y,q)),'gain':float(base_ll-ll(y,q)),'fold_gains':fg,'positive_folds':int(np.sum(np.array(fg)>0))}
 shgain=float(base_ll-ll(y,shuffled))
 real=['OBJECTIVE_SEMANTICS','RAW_TRANSCRIPT','OBJECTIVE_X_RAW','FULL_REPRESENTATION']
 winner=max(real,key=lambda n:tests[n]['gain']); gain=tests[winner]['gain']; rec=gain/gap if gap>0 else 0.
 flipped=route(P0,PR,gate_keep[winner],flip=True); flipped_gain=float(base_ll-ll(y,flipped))
 geometry_gain=tests['GEOMETRY']['gain']; idgain=tests['ID_PLACEBO']['gain']; control=max(idgain,shgain)
 phase=(gain>=.010 and min(tests[winner]['fold_gains'])>=0) or (gain>=.008 and rec>=.15)
 found=(gain>=.003 and tests[winner]['positive_folds']>=3 and control<.25*gain and flipped_gain<=0)
 hint=(.001<=gain<.003 and gain-geometry_gain>=.001)
 verdict='PHASE_CHANGE_REPRESENTATION' if phase else 'REPRESENTATION_REPAIR_FOUND' if found else 'STRUCTURED_REPRESENTATION_HINT' if hint else 'REPRESENTATION_NOT_OBSERVED'
 out={
  'rows':len(y),'objectives':len(np.unique(obj)),'v97':base_ll,'row_endpoint_oracle':oracle_ll,'oracle_gap':gap,
  'oracle_related_win_rate':float(np.mean(win)),'tests':tests,'winner':winner,'winner_gain':gain,
  'oracle_gap_recovered_fraction':rec,'controls':{'shuffled_applicability_gain':shgain,'id_placebo_gain':idgain,'flipped_winner_route_gain':flipped_gain},
  'representation_increment_over_geometry':float(gain-geometry_gain),'decision':verdict,
  'precommit':{
   'phase':'gain >=.010 and all folds nonnegative OR gain >=.008 and >=15% oracle recovery',
   'repair_found':'gain >=.003, >=3/4 positive folds, controls <25% real gain, flipped route <=0',
   'structured':'.001-.003 and representation beats geometry by >=.001',
   'otherwise':'representation not observed'
  }
 }
 Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--rows',type=int,default=2500); p.add_argument('--out',default='v114_representation_applicability.json'); main(p.parse_args())

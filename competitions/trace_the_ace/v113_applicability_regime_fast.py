#!/usr/bin/env python3
"""V113 frozen fast pass: applicability + regime fingerprint.
Primary: can sample-local non-text/support topology explain when RELATED beats V75?
Frozen: deterministic 2500 rows, objective-grouped 4-fold OOF, fixed HistGB gate.
Thresholds: phase >=.010 (and all folds nonnegative) or >=.008 + >=15% oracle recovery;
escalate >=.003 with >=3/4 positive folds and placebo <25% real gain; structured .001-.003 only
if a family ablation removes >=.001; otherwise suppress metadata router.
No cross-test aggregates enter prediction.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import log_loss,roc_auc_score
from v71_mastery_events import load_transcript,normalize_roles
from v75_canonical_trajectory import load_training,SEED
from v81_target_segment_phase import choose_target_segment
from v85_evidence_state import build_v75
from v93_shift_robust_validation import obj_family
from v94_related_control import segmented_control,build_control
from v110_residual_collider_state_discovery import hb,p97_predict,ll
EPS=1e-5

def H(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def lossrow(y,p): return -(y*np.log(np.clip(p,EPS,1))+(1-y)*np.log(np.clip(1-p,EPS,1)))
def counts(train_vals, eval_vals):
 u,n=np.unique(train_vals,return_counts=True);d=dict(zip(u,n));return np.array([d.get(x,0) for x in eval_vals],float)
def transcript_meta(d,obj):
 z=normalize_roles(d).reset_index(drop=True); roles=z.role_repaired.astype(str).to_numpy(); n=max(1,len(z));
 seg,_=choose_target_segment(d,obj); ns=len(seg)
 stu=float(np.sum(roles=='student')); tut=float(np.sum(roles=='tutor'))
 # timestamp duration only when parseable; otherwise 0.
 dur=0.
 for c in ['timestamp','time','created_at']:
  if c in z.columns:
   try:
    t=np.array(np.asarray(__import__('pandas').to_datetime(z[c],errors='coerce').astype('int64')),float); good=t>0
    if good.sum()>1: dur=float((t[good].max()-t[good].min())/1e9)
   except Exception: pass
   break
 start=0.
 if ns and len(seg):
  try: start=float(seg.index.min())/n
  except Exception: start=0.
 return np.array([len(z),stu,tut,stu/n,tut/n,ns,ns/n,start,np.log1p(max(dur,0.))],float)
def geometry(p0,pr):
 d=pr-p0
 return np.c_[p0,pr,d,np.abs(d),np.abs(p0-.5),np.abs(pr-.5),np.minimum(p0,pr),np.maximum(p0,pr)]
def fit_gate(X,ywin,sw,tr,va):
 m=HistGradientBoostingClassifier(max_depth=2,max_iter=70,learning_rate=.05,min_samples_leaf=80,l2_regularization=2.,random_state=SEED)
 m.fit(X[tr],ywin[tr],sample_weight=sw[tr]); return m.predict_proba(X[va])[:,1]
def route(p0,pr,g):
 # fixed conservative interpolation; no sweep
 w=np.clip(.65*g,0,.65); return np.clip((1-w)*p0+w*pr,EPS,1-EPS)
def run(a):
 f0=load_training(a.features,a.labels).reset_index(drop=True); print('features columns',list(f0.columns),flush=True)
 objall=(f0.learning_objective_id if 'learning_objective_id' in f0 else f0.learning_objective).astype(str).to_numpy(); cand=np.where(np.array([hb(x,5)!=0 for x in objall]))[0]
 ix=np.array(sorted(cand,key=lambda i:H(f0.response_id.iloc[i]))[:a.rows]); f=f0.iloc[ix].reset_index(drop=True)
 y=f.target.to_numpy(int); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); key=f.learning_objective.astype(str).to_numpy(); fam=np.array([obj_family(x) for x in key]); sess=f.session_id.astype(str).to_numpy()
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}
 rt=[];rz=[];meta=[]
 for _,r in f.iterrows():
  d=cache[str(r.session_id)];t,z=segmented_control(d,str(r.learning_objective),'related');rt.append(t);rz.append(z);meta.append(transcript_meta(d,str(r.learning_objective)))
 X75=build_v75(f,cache);Xr=build_control(rt,rz); P0=np.zeros(len(f));PR=np.zeros(len(f)); fold=np.full(len(f),-1,int)
 splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(y)),y,obj))
 # experts once, true outer OOF
 for k,(tr,va) in enumerate(splits):
  P0[va],_=p97_predict(X75,Xr,y,tr,va,key); # returns V97, so fit experts explicitly below is unavailable
  # recover endpoints with same base learner via helper's ingredients: fixed V97 endpoint reconstruction impossible from p97 alone.
  # use imported logistic expert fitter locally.
  from sklearn.linear_model import LogisticRegression
  m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr]); mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr])
  P0[va]=np.clip(m0.predict_proba(X75[va])[:,1],EPS,1-EPS);PR[va]=np.clip(mr.predict_proba(Xr[va])[:,1],EPS,1-EPS);fold[va]=k
 base=np.where(np.array([np.sum(key[np.setdiff1d(np.arange(len(y)),np.where(fold==fold[i])[0])]==key[i]) for i in range(len(y))])==0,.65*P0+.35*PR,P0)
 base_ll=ll(y,base); oracle=np.where(lossrow(y,PR)<lossrow(y,P0),PR,P0); oracle_ll=ll(y,oracle); gap=base_ll-oracle_ll
 M=np.vstack(meta); tests={}; foldg={}
 families=['GEOMETRY','SUPPORT','SESSION','SUPPORT_X_DISAGREEMENT','ALL_APPLICABILITY','ID_PLACEBO']
 Xfam={k:np.zeros((len(y),1)) for k in families}
 # fold-specific support features must be built using each fold's train only
 preds={k:np.zeros(len(y)) for k in families}
 for k,(tr,va) in enumerate(splits):
  ec=counts(key[tr],key);fc=counts(fam[tr],fam);sc=counts(sess[tr],sess)
  # related support: family minus exact is a frozen cheap relational proxy
  rel=np.maximum(fc-ec,0); support=np.c_[np.log1p(ec),np.log1p(fc),np.log1p(rel),ec>0,fc>0,np.divide(ec,fc+1.)]
  G=geometry(P0,PR); I=np.c_[np.log1p(np.array([H(x)%997 for x in f.response_id.astype(str)])),np.array([H(x)%31 for x in sess])]
  D=np.abs(PR-P0)[:,None]; SX=np.c_[D*support[:,:3],(PR-P0)[:,None]*support[:,:3],D*(support[:,3:5])]
  allx=np.c_[G,support,M,SX]
  mats={'GEOMETRY':G,'SUPPORT':support,'SESSION':M,'SUPPORT_X_DISAGREEMENT':SX,'ALL_APPLICABILITY':allx,'ID_PLACEBO':I}
  win=(lossrow(y,PR)<lossrow(y,P0)).astype(int); sw=np.abs(lossrow(y,P0)-lossrow(y,PR))+.01
  for name,X in mats.items():
   gp=fit_gate(X,win,sw,tr,va); preds[name][va]=route(P0[va],PR[va],gp)
 for name in families:
  q=preds[name]; v=ll(y,q); fg=[]
  for k,(_,va) in enumerate(splits): fg.append(float(ll(y[va],base[va])-ll(y[va],q[va])))
  win=(lossrow(y,PR)<lossrow(y,P0)).astype(int)
  # report routing gain; AUC omitted because gate probabilities are not retained separately
  tests[name]={'ll':v,'gain':base_ll-v,'fold_gains':fg,'positive_folds':int(np.sum(np.array(fg)>0))}
 real=[x for x in families if x!='ID_PLACEBO']; winner=max(real,key=lambda n:tests[n]['gain']); gain=tests[winner]['gain']; rec=(gain/gap if gap>0 else 0.); placebo=tests['ID_PLACEBO']['gain']
 # family ablation criterion: ALL minus best non-all as observable diagnostic
 ablation=max([tests[x]['gain'] for x in ['GEOMETRY','SUPPORT','SESSION','SUPPORT_X_DISAGREEMENT']])
 all_gain=tests['ALL_APPLICABILITY']['gain']; removal=all_gain-ablation
 phase=(gain>=.010 and min(tests[winner]['fold_gains'])>=0) or (gain>=.008 and rec>=.15)
 escalate=(gain>=.003 and tests[winner]['positive_folds']>=3 and placebo < .25*gain)
 structured=(.001<=gain<.003 and abs(removal)>=.001)
 verdict='PHASE_CHANGE_APPLICABILITY' if phase else 'ESCALATE_APPLICABILITY' if escalate else 'STRUCTURED_HINT' if structured else 'SUPPRESS_METADATA_ROUTER'
 out={'rows':len(y),'objectives':len(np.unique(obj)),'v97':base_ll,'row_endpoint_oracle':oracle_ll,'oracle_gap':gap,'tests':tests,'winner':winner,'winner_gain':gain,'oracle_gap_recovered_fraction':rec,'all_vs_best_family_delta':removal,'decision':verdict,'precommit':{'phase':'>=.010 and all folds nonnegative OR >=.008 and >=15% oracle recovery','escalate':'>=.003, >=3/4 folds positive, placebo <25% real gain','structured':'.001-.003 only if family ablation >=.001','otherwise':'suppress metadata router'}}
 # Optional label-free real-test fingerprint when test_features exists.
 out['regime_fingerprint']={'status':'UNAVAILABLE_NO_TEST_FEATURES'}
 if a.test_features and a.test_features.exists():
  te=__import__('pandas').read_csv(a.test_features); trkey=f0.learning_objective.astype(str).to_numpy(); trfam=np.array([obj_family(x) for x in trkey]); tek=te.learning_objective.astype(str).to_numpy(); tef=np.array([obj_family(x) for x in tek])
  ec=counts(trkey,tek);fc=counts(trfam,tef);out['regime_fingerprint']={'status':'AVAILABLE','rows':len(te),'exact_seen_rate':float(np.mean(ec>0)),'family_seen_rate':float(np.mean(fc>0)),'median_exact_support':float(np.median(ec)),'median_family_support':float(np.median(fc))}
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--test-features',type=Path,default=None);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v113_applicability_regime_fast.json');run(p.parse_args())

#!/usr/bin/env python3
"""V115 COLLISION-RESOLUTION AUDIT.
Orthogonal to V114's learned gate: use fixed kNN on held-out objectives to test whether widening
representation makes endpoint applicability locally identifiable.

Frozen: same 2500 rows, same endpoint oracle, GroupKFold by objective, k=15, no sweep.
Families compare geometry-only against objective semantics, raw transcript, and their union.
A real representation repair should improve routing, increase weighted neighbor agreement, survive
shuffled-target control, and fail under flipped routing.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from scipy.sparse import hstack,csr_matrix
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler,normalize
from v75_canonical_trajectory import load_training,SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control
from v110_residual_collider_state_discovery import hb,ll
from v114_representation_applicability import H,lossrow,geometry,transcript_views,route,EPS

def knn_gate_dense(X,win,sw,tr,va,k=15,shuffle=False):
 sc=StandardScaler().fit(X[tr]); A=sc.transform(X[tr]); B=sc.transform(X[va])
 nn=NearestNeighbors(n_neighbors=min(k,len(tr)),metric='euclidean').fit(A); d,ix=nn.kneighbors(B)
 yt=win[tr].copy()
 if shuffle:
  rng=np.random.default_rng(SEED+17+len(tr)); yt=yt[rng.permutation(len(yt))]
 wt=sw[tr][ix]/(d+0.25); return np.sum(wt*yt[ix],axis=1)/np.sum(wt,axis=1)
def knn_gate_sparse(X,win,sw,tr,va,k=15,shuffle=False):
 A=normalize(X[tr]); B=normalize(X[va]); nn=NearestNeighbors(n_neighbors=min(k,len(tr)),metric='cosine',algorithm='brute').fit(A); d,ix=nn.kneighbors(B)
 yt=win[tr].copy()
 if shuffle:
  rng=np.random.default_rng(SEED+19+len(tr)); yt=yt[rng.permutation(len(yt))]
 sim=np.maximum(1-d,0.01); wt=sw[tr][ix]*sim; return np.sum(wt*yt[ix],axis=1)/np.sum(wt,axis=1)
def main(a):
 f0=load_training(a.features,a.labels).reset_index(drop=True); print('features columns',list(f0.columns),flush=True)
 objall=(f0.learning_objective_id if 'learning_objective_id' in f0 else f0.learning_objective).astype(str).to_numpy(); cand=np.where(np.array([hb(x,5)!=0 for x in objall]))[0]
 ix=np.array(sorted(cand,key=lambda i:H(f0.response_id.iloc[i]))[:a.rows]); f=f0.iloc[ix].reset_index(drop=True)
 y=f.target.to_numpy(int); obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy(); key=f.learning_objective.astype(str).to_numpy(); sess=f.session_id.astype(str).to_numpy()
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}; rt=[];rz=[];T={k:[] for k in ['STUDENT','TUTOR','FULL','LOCAL','LAST8']}
 for _,r in f.iterrows():
  d=cache[str(r.session_id)];t,z=segmented_control(d,str(r.learning_objective),'related');rt.append(t);rz.append(z);vals=transcript_views(d,str(r.learning_objective))
  for k,v in zip(T,vals):T[k].append(v)
 X75=build_v75(f,cache);Xr=build_control(rt,rz);P0=np.zeros(len(f));PR=np.zeros(len(f));fold=np.full(len(f),-1,int);splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(y)),y,obj))
 for k,(tr,va) in enumerate(splits):
  m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr]);mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr]);P0[va]=np.clip(m0.predict_proba(X75[va])[:,1],EPS,1-EPS);PR[va]=np.clip(mr.predict_proba(Xr[va])[:,1],EPS,1-EPS);fold[va]=k
 allidx=np.arange(len(y));base=np.zeros(len(y))
 for i in range(len(y)):
  tr=allidx[fold!=fold[i]];base[i]=.65*P0[i]+.35*PR[i] if np.sum(key[tr]==key[i])==0 else P0[i]
 base=np.clip(base,EPS,1-EPS);base_ll=ll(y,base);L0=lossrow(y,P0);LR=lossrow(y,PR);win=(LR<L0).astype(int);sw=np.abs(L0-LR)+.01;oracle=np.where(win,PR,P0);oracle_ll=ll(y,oracle);gap=base_ll-oracle_ll;G=geometry(P0,PR)
 hv=HashingVectorizer(n_features=2**14,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True);hc=HashingVectorizer(n_features=2**14,alternate_sign=False,norm='l2',analyzer='char_wb',ngram_range=(3,5),lowercase=True)
 OBJ=hstack([hv.transform(key),hc.transform(key)],format='csr');RAW=hstack([hv.transform(T['STUDENT']),hv.transform(T['TUTOR']),hv.transform(T['LOCAL']),hv.transform(T['LAST8'])],format='csr');GS=csr_matrix(StandardScaler().fit_transform(G))
 mats={'GEOMETRY':G,'OBJECTIVE_SEMANTICS':hstack([GS,OBJ],format='csr'),'RAW_TRANSCRIPT':hstack([GS,RAW],format='csr'),'OBJECTIVE_X_RAW':hstack([GS,OBJ,RAW],format='csr')}
 preds={n:np.zeros(len(y)) for n in mats}; gates={n:np.zeros(len(y)) for n in mats}; shuffled=np.zeros(len(y))
 for tr,va in splits:
  for n,X in mats.items():
   gp=knn_gate_dense(X,win,sw,tr,va) if n=='GEOMETRY' else knn_gate_sparse(X,win,sw,tr,va);gates[n][va]=gp;preds[n][va]=route(P0[va],PR[va],gp)
  shuffled[va]=route(P0[va],PR[va],knn_gate_sparse(mats['OBJECTIVE_X_RAW'],win,sw,tr,va,shuffle=True))
 tests={}
 for n,q in preds.items():
  fg=[float(ll(y[va],base[va])-ll(y[va],q[va])) for _,va in splits];conf=np.abs(gates[n]-.5)*2;correct=((gates[n]>=.5)==win).astype(float)
  tests[n]={'ll':float(ll(y,q)),'gain':float(base_ll-ll(y,q)),'fold_gains':fg,'positive_folds':int(np.sum(np.array(fg)>0)),'oracle_choice_accuracy':float(np.mean(correct)),'confidence_weighted_agreement':float(np.sum(conf*correct)/(np.sum(conf)+1e-12))}
 real=['OBJECTIVE_SEMANTICS','RAW_TRANSCRIPT','OBJECTIVE_X_RAW'];winner=max(real,key=lambda n:tests[n]['gain']);gain=tests[winner]['gain'];rec=gain/gap if gap>0 else 0.;shgain=float(base_ll-ll(y,shuffled));flipped=route(P0,PR,gates[winner],flip=True);flipgain=float(base_ll-ll(y,flipped));geom=tests['GEOMETRY']['gain']
 phase=(gain>=.010 and min(tests[winner]['fold_gains'])>=0) or (gain>=.008 and rec>=.15);found=(gain>=.003 and tests[winner]['positive_folds']>=3 and shgain<.25*gain and flipgain<=0);hint=(.001<=gain<.003 and gain-geom>=.001)
 out={'rows':len(y),'objectives':len(np.unique(obj)),'v97':base_ll,'row_endpoint_oracle':oracle_ll,'oracle_gap':gap,'tests':tests,'winner':winner,'winner_gain':gain,'oracle_gap_recovered_fraction':rec,'representation_increment_over_geometry':float(gain-geom),'controls':{'shuffled_applicability_gain':shgain,'flipped_winner_route_gain':flipgain},'decision':'PHASE_CHANGE_COLLISION_RESOLUTION' if phase else 'NONLINEAR_REPRESENTATION_REPAIR_FOUND' if found else 'STRUCTURED_COLLISION_HINT' if hint else 'COLLISIONS_NOT_RESOLVED','precommit':{'phase':'gain >=.010 all folds nonnegative OR >=.008 and >=15% oracle recovery','repair_found':'gain >=.003, >=3/4 folds positive, shuffled <25% gain, flipped <=0','structured':'.001-.003 and >=.001 over geometry','otherwise':'collisions not resolved'}}
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v115_collision_resolution_knn.json');main(p.parse_args())

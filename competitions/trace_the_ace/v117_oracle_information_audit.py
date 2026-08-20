#!/usr/bin/env python3
"""V117 ORACLE INFORMATION AUDIT.

Tests whether the large per-row V75-vs-RELATED endpoint oracle gap is evidence of a latent
applicability regime or simply the value of revealing the realized label. For binary log loss,
if two endpoint probabilities differ, the lower-loss endpoint is determined by the label and the
sign of (PR-P0). This audit quantifies that identity on the frozen V113 sample and compares it with
strictly label-free/cross-fitted endpoint selection.

Frozen protocol: same deterministic 2500 rows, same objective-grouped 4-fold endpoint fits,
no result-dependent tuning. Meta selectors are trained only on outer-train rows.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from v75_canonical_trajectory import load_training,SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control
from v110_residual_collider_state_discovery import hb,ll
from v114_representation_applicability import H,lossrow,geometry,route,EPS

def main(a):
 f0=load_training(a.features,a.labels).reset_index(drop=True);print('features columns',list(f0.columns),flush=True)
 objall=(f0.learning_objective_id if 'learning_objective_id' in f0 else f0.learning_objective).astype(str).to_numpy();cand=np.where(np.array([hb(x,5)!=0 for x in objall]))[0];ix=np.array(sorted(cand,key=lambda i:H(f0.response_id.iloc[i]))[:a.rows]);f=f0.iloc[ix].reset_index(drop=True)
 y=f.target.to_numpy(int);obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy();key=f.learning_objective.astype(str).to_numpy();sess=f.session_id.astype(str).to_numpy();cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)};rt=[];rz=[]
 for _,r in f.iterrows():d=cache[str(r.session_id)];t,z=segmented_control(d,str(r.learning_objective),'related');rt.append(t);rz.append(z)
 X75=build_v75(f,cache);Xr=build_control(rt,rz);P0=np.zeros(len(f));PR=np.zeros(len(f));fold=np.full(len(f),-1,int);splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(y)),y,obj))
 for k,(tr,va) in enumerate(splits):
  m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr]);mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr]);P0[va]=np.clip(m0.predict_proba(X75[va])[:,1],EPS,1-EPS);PR[va]=np.clip(mr.predict_proba(Xr[va])[:,1],EPS,1-EPS);fold[va]=k
 allidx=np.arange(len(y));base=np.zeros(len(y))
 for i in range(len(y)):
  tr=allidx[fold!=fold[i]];base[i]=.65*P0[i]+.35*PR[i] if np.sum(key[tr]==key[i])==0 else P0[i]
 base=np.clip(base,EPS,1-EPS);L0=lossrow(y,P0);LR=lossrow(y,PR);win=(LR<L0).astype(int);oracle=np.where(win,PR,P0);base_ll=ll(y,base);oracle_ll=ll(y,oracle);gap=base_ll-oracle_ll
 d=PR-P0;ties=np.isclose(d,0,atol=1e-15);clairvoyant=np.where(y==1,d>0,d<0).astype(int);mask=~ties;identity=float(np.mean(win[mask]==clairvoyant[mask])) if np.any(mask) else 1.
 # Counterfactual label flip: lower-loss endpoint must flip whenever endpoint probabilities differ.
 yf=1-y;wf=(lossrow(yf,PR)<lossrow(yf,P0)).astype(int);flip_rate=float(np.mean(wf[mask]==1-win[mask])) if np.any(mask) else 1.
 # Strictly label-free endpoint-only selectors trained on outer train.
 G=geometry(P0,PR);q_log=np.zeros(len(y));q_hgb=np.zeros(len(y));gate_auc_proxy=[]
 sw=np.abs(L0-LR)+.01
 for tr,va in splits:
  ml=LogisticRegression(C=.08,max_iter=220,solver='liblinear',random_state=SEED).fit(G[tr],win[tr],sample_weight=sw[tr]);gl=ml.predict_proba(G[va])[:,1];q_log[va]=route(P0[va],PR[va],gl)
  mh=HistGradientBoostingClassifier(max_depth=2,max_iter=70,learning_rate=.05,min_samples_leaf=80,l2_regularization=2.,random_state=SEED).fit(G[tr],win[tr],sample_weight=sw[tr]);gh=mh.predict_proba(G[va])[:,1];q_hgb[va]=route(P0[va],PR[va],gh)
 # Best constant endpoint and 50/50 blend are label-free controls.
 p_half=.5*P0+.5*PR
 endpoint_ll={'V75':float(ll(y,P0)),'RELATED':float(ll(y,PR)),'HALF_BLEND':float(ll(y,p_half)),'V97':float(base_ll),'ROW_LABEL_ORACLE':float(oracle_ll),'OOF_GEOMETRY_LOGISTIC':float(ll(y,q_log)),'OOF_GEOMETRY_HGB':float(ll(y,q_hgb))}
 gains={k:float(base_ll-v) for k,v in endpoint_ll.items() if k not in ['V97','ROW_LABEL_ORACLE']}
 best_label_free=max(gains,key=gains.get);best_gain=gains[best_label_free];recovered=float(best_gain/gap) if gap>0 else 0.
 out={'rows':len(y),'objectives':len(np.unique(obj)),'endpoint_disagreement_rate':float(np.mean(mask)),'oracle_related_win_rate':float(np.mean(win)),'clairvoyant_choice_identity_rate':identity,'choice_flip_under_label_counterfactual_rate':flip_rate,'v97':float(base_ll),'row_label_oracle':float(oracle_ll),'oracle_gap':float(gap),'label_free_controls':endpoint_ll,'label_free_gains_vs_v97':gains,'best_label_free':best_label_free,'best_label_free_gain':best_gain,'best_label_free_oracle_gap_recovered_fraction':recovered}
 out['decision']='ROW_ORACLE_IS_REALIZED_LABEL_INFORMATION' if identity>=.999 and flip_rate>=.999 else 'ORACLE_HAS_NONTRIVIAL_APPLICABILITY_STRUCTURE'
 out['interpretation_rule']='If oracle choice matches label+endpoint-order identity and flips under counterfactual label >=99.9%, the row oracle is clairvoyant realized-outcome information; its raw gap must not be treated as recoverable capability without a separately validated label-free selector.'
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v117_oracle_information_audit.json');main(p.parse_args())

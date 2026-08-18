#!/usr/bin/env python3
"""V116 ROW-ALIGNMENT / REPRESENTATION-ALIAS AUDIT.

After V112/V113/V114/V115 fail to recover the large endpoint-oracle gap, test the upstream
hypothesis: distinct labelled responses may be mapped to the same session/objective state before
prediction. If identical representations contain different labels or different oracle endpoint
choices, no downstream router can resolve them without a new row-level alignment/state variable.

This is an aggregate diagnostic only: no raw transcript content is emitted.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from v75_canonical_trajectory import load_training,SEED
from v71_mastery_events import load_transcript
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control
from v110_residual_collider_state_discovery import hb,ll
from v114_representation_applicability import H,lossrow,EPS

def rep_hash(x):
 a=np.asarray(x,dtype=np.float64);a=np.nan_to_num(a,nan=0.,posinf=1e30,neginf=-1e30);a=np.round(a,10)
 return hashlib.sha256(a.tobytes()).hexdigest()
def summarize_groups(groups,y,win,Lbase,Loracle):
 collision=[]; mixed_y=[];mixed_w=[];gap=0.;rows=0
 for z in groups.values():
  if len(z)>1:
   collision.extend(z);rows+=len(z)
   yy=y[z];ww=win[z]
   if len(np.unique(yy))>1:mixed_y.extend(z)
   if len(np.unique(ww))>1:
    mixed_w.extend(z);gap+=float(np.sum(Lbase[z]-Loracle[z]))
 return {'groups_total':len(groups),'collision_groups':int(sum(len(z)>1 for z in groups.values())),'rows_in_collision_groups':len(set(collision)),'mixed_label_groups':int(sum(len(z)>1 and len(np.unique(y[z]))>1 for z in groups.values())),'rows_in_mixed_label_groups':len(set(mixed_y)),'mixed_oracle_choice_groups':int(sum(len(z)>1 and len(np.unique(win[z]))>1 for z in groups.values())),'rows_in_mixed_oracle_choice_groups':len(set(mixed_w)),'oracle_gap_sum_in_mixed_choice_groups':gap}
def main(a):
 f0=load_training(a.features,a.labels).reset_index(drop=True);print('features columns',list(f0.columns),flush=True)
 objall=(f0.learning_objective_id if 'learning_objective_id' in f0 else f0.learning_objective).astype(str).to_numpy();cand=np.where(np.array([hb(x,5)!=0 for x in objall]))[0];ix=np.array(sorted(cand,key=lambda i:H(f0.response_id.iloc[i]))[:a.rows]);f=f0.iloc[ix].reset_index(drop=True)
 y=f.target.to_numpy(int);obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy();key=f.learning_objective.astype(str).to_numpy();sess=f.session_id.astype(str).to_numpy();rid=f.response_id.astype(str).to_numpy()
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)};rt=[];rz=[]
 for _,r in f.iterrows():d=cache[str(r.session_id)];t,z=segmented_control(d,str(r.learning_objective),'related');rt.append(t);rz.append(z)
 X75=build_v75(f,cache);Xr=build_control(rt,rz);P0=np.zeros(len(f));PR=np.zeros(len(f));fold=np.full(len(f),-1,int);splits=list(GroupKFold(min(4,len(np.unique(obj)))).split(np.zeros(len(y)),y,obj))
 for k,(tr,va) in enumerate(splits):
  m0=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(X75[tr],y[tr]);mr=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xr[tr],y[tr]);P0[va]=np.clip(m0.predict_proba(X75[va])[:,1],EPS,1-EPS);PR[va]=np.clip(mr.predict_proba(Xr[va])[:,1],EPS,1-EPS);fold[va]=k
 allidx=np.arange(len(y));base=np.zeros(len(y))
 for i in range(len(y)):
  tr=allidx[fold!=fold[i]];base[i]=.65*P0[i]+.35*PR[i] if np.sum(key[tr]==key[i])==0 else P0[i]
 base=np.clip(base,EPS,1-EPS);L0=lossrow(y,P0);LR=lossrow(y,PR);win=(LR<L0).astype(int);oracle=np.where(win,PR,P0);Lbase=lossrow(y,base);Loracle=lossrow(y,oracle)
 groups_so=defaultdict(list);groups_rep=defaultdict(list);groups_endpoint=defaultdict(list)
 for i in range(len(y)):
  groups_so[(sess[i],obj[i])].append(i)
  groups_rep[rep_hash(np.r_[X75[i],Xr[i]])].append(i)
  groups_endpoint[rep_hash(np.r_[P0[i],PR[i]])].append(i)
 # transcript schema and exact response-id anchor audit, aggregate only
 headers=defaultdict(int);rid_set=set(rid);found=set();found_cols=defaultdict(set)
 for s,d in cache.items():
  for c in d.columns:headers[str(c)]+=1
  for c in d.columns:
   try:
    vals=set(d[c].dropna().astype(str).tolist());hit=vals & rid_set
    if hit:found.update(hit);found_cols[str(c)].update(hit)
   except Exception:pass
 # lower bound diagnostic for a predictor forced constant inside exact representation groups
 const_nll=0.;const_rows=0
 for z in groups_rep.values():
  if len(z)>1:
   p=float(np.clip(np.mean(y[z]),EPS,1-EPS));const_nll+=float(np.sum(lossrow(y[z],np.full(len(z),p))));const_rows+=len(z)
 out={'rows':len(y),'objectives':len(np.unique(obj)),'sessions':len(np.unique(sess)),'v97':float(ll(y,base)),'row_endpoint_oracle':float(ll(y,oracle)),'oracle_gap':float(ll(y,base)-ll(y,oracle)),'oracle_related_win_rate':float(np.mean(win)),'session_objective_aliases':summarize_groups(groups_so,y,win,Lbase,Loracle),'exact_feature_representation_aliases':summarize_groups(groups_rep,y,win,Lbase,Loracle),'endpoint_prediction_aliases':summarize_groups(groups_endpoint,y,win,Lbase,Loracle),'aggregate_alignment_evidence':{'transcript_columns':sorted(headers.keys()),'response_ids_found_exactly_anywhere':len(found),'response_id_anchor_rate':float(len(found)/len(rid)),'anchor_columns':{c:len(v) for c,v in found_cols.items()},'constant_within_rep_collision_empirical_nll':float(const_nll/const_rows) if const_rows else None,'constant_collision_rows':const_rows}}
 so=out['session_objective_aliases'];rp=out['exact_feature_representation_aliases'];anchor=out['aggregate_alignment_evidence']['response_id_anchor_rate']
 if rp['mixed_oracle_choice_groups']>0 and rp['rows_in_mixed_oracle_choice_groups']>=.05*len(y):verdict='REPRESENTATION_ALIAS_CONFIRMED'
 elif so['mixed_oracle_choice_groups']>0 and anchor<.5:verdict='ROW_ALIGNMENT_STATE_CANDIDATE'
 else:verdict='NO_STRONG_ROW_ALIAS_EVIDENCE'
 out['decision']=verdict;out['interpretation_rule']='Alias confirmed if exact X75+Xr collisions with mixed oracle choice cover >=5% rows; row-alignment candidate if session/objective aliases mix oracle choice and <50% response IDs anchor exactly in transcript.'
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v116_row_alignment_alias_audit.json');main(p.parse_args())

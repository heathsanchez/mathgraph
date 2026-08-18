#!/usr/bin/env python3
"""V119 public-anchor geometry search.

Recoverable-probe experiment. Historical V37/V48/V54/V57/V63 packages are not
available, so this does NOT claim a seven-model public reconstruction.

Question: which lawful validation strata reproduce the one directly executable
public anchor: V97 slightly beats V75 publicly (0.6044 vs 0.6047), while their
smoke scores tie (0.4693 vs 0.4693)?

Freeze:
- deterministic 6000-row session sample;
- 5-fold session-grouped OOF;
- V75 and V97 endpoints exactly as current repo lineage;
- cells from support x provider-proxy x session-length x objective-frequency;
- promote a cell only if V97 beats V75 in >=4/5 folds and aggregate delta is
  within 0.0005 of the public delta (-0.0003), with >=150 rows.

No leaderboard labels are used for fitting predictions; public scores are used
only as an external geometry target after OOF predictions are frozen.
"""
from __future__ import annotations
import argparse,json,hashlib,re
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from v71_mastery_events import load_transcript,normalize_roles
from v75_canonical_trajectory import load_training,SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control,build_control

EPS=1e-5; TARGET=-0.0003

def hh(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def ll(y,p): return float(log_loss(y,np.clip(p,EPS,1-EPS)))
def provider(df):
 d=normalize_roles(df).reset_index(drop=True); roles=d.role_repaired.astype(str).str.lower().to_numpy(); txt=d.content.fillna('').astype(str).tolist(); n=len(d); tut=int(np.sum(roles=='tutor')); mw=float(np.mean([len(x.split()) for x in txt])) if txt else 0.; markers=sum(bool(re.search(r'\b(?:learning objective|learning goal|prior learning|i do|we do|you do|application|slide|lesson)\b',x,re.I)) for x in txt); return 'TSL' if (n>=24 or markers>=2 or (tut>=12 and mw>=8)) else 'EEDI'
def fit(X,y,tr,va):
 m=LogisticRegression(C=.25,max_iter=250,solver='liblinear',random_state=SEED).fit(X[tr],y[tr]); return np.clip(m.predict_proba(X[va])[:,1],EPS,1-EPS)
def bin_support(x):
 return 'S0' if x==0 else 'S1_9' if x<10 else 'S10_29' if x<30 else 'S30P'
def qbin(x,cuts,prefix): return prefix+str(int(np.searchsorted(cuts,x,side='right')))

def run(a):
 f=load_training(a.features,a.labels).reset_index(drop=True); print('features columns',list(f.columns),flush=True)
 sessions=sorted(f.session_id.astype(str).unique(),key=hh); take=set(sessions[:min(a.sessions,len(sessions))]); f=f[f.session_id.astype(str).isin(take)].reset_index(drop=True)
 y=f.target.to_numpy(int); sess=f.session_id.astype(str).to_numpy(); key=f.learning_objective.astype(str).to_numpy()
 cache={s:load_transcript(a.transcripts/f'{s}.csv') for s in np.unique(sess)}; meta={s:(provider(cache[s]),len(cache[s])) for s in cache}
 X75=build_v75(f,cache); rt=[];rz=[]
 for _,r in f.iterrows(): t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related');rt.append(t);rz.append(z)
 Xr=build_control(rt,rz); p75=np.zeros(len(f));p97=np.zeros(len(f));support=np.zeros(len(f));foldid=np.zeros(len(f),int)
 splits=list(GroupKFold(5).split(np.zeros(len(y)),y,sess))
 for k,(tr,va) in enumerate(splits):
  q75=fit(X75,y,tr,va); qr=fit(Xr,y,tr,va); vals,cts=np.unique(key[tr],return_counts=True); d=dict(zip(vals,cts)); s=np.array([d.get(x,0) for x in key[va]],float); seen=s>0; q97=np.where(seen,q75,.65*q75+.35*qr); p75[va]=q75;p97[va]=q97;support[va]=s;foldid[va]=k
 global_counts=dict(zip(*np.unique(key,return_counts=True))); olen=np.array([global_counts[x] for x in key],float); slen=np.array([meta[s][1] for s in sess],float); prov=np.array([meta[s][0] for s in sess])
 slcuts=np.quantile(slen,[.25,.5,.75]); ocuts=np.quantile(olen,[.25,.5,.75]); cells={}
 labels=[]
 for i in range(len(f)):
  labels.append('|'.join([bin_support(support[i]),prov[i],qbin(slen[i],slcuts,'L'),qbin(olen[i],ocuts,'F')]))
 labels=np.array(labels); rows=[]
 for c in np.unique(labels):
  m=labels==c
  if m.sum()<150: continue
  d=ll(y[m],p97[m])-ll(y[m],p75[m]); fg=[]
  for k in range(5):
   z=m&(foldid==k)
   fg.append(None if z.sum()<20 else ll(y[z],p97[z])-ll(y[z],p75[z]))
  pos=sum(v is not None and v<0 for v in fg); err=abs(d-TARGET); rows.append({'cell':c,'rows':int(m.sum()),'v75':ll(y[m],p75[m]),'v97':ll(y[m],p97[m]),'delta_v97_minus_v75':d,'target_error':err,'fold_deltas':fg,'v97_better_folds':pos,'qualified':bool(pos>=4 and err<=.0005)})
 rows.sort(key=lambda r:(not r['qualified'],r['target_error'],-r['rows']))
 overall={'v75':ll(y,p75),'v97':ll(y,p97),'delta':ll(y,p97)-ll(y,p75)}
 q=[r for r in rows if r['qualified']]; verdict='PUBLIC_ANCHOR_CELL_FOUND' if q else 'CURRENT_SPLIT_GRAMMAR_NOT_PUBLIC_ALIGNED'
 out={'rows':len(f),'sessions':len(np.unique(sess)),'public_anchor':{'v75':.6047,'v97':.6044,'target_delta':TARGET},'smoke_anchor':{'v75':.4693,'v97':.4693,'delta':0.0},'overall':overall,'top_cells':rows[:20],'decision':{'verdict':verdict,'qualified_cells':len(q),'rule':'Cell requires >=150 rows, V97 better in >=4/5 folds, and aggregate V97-V75 delta within 0.0005 of public -0.0003.','next':'Use qualified cell(s) as public-aligned validation basis only if stable; otherwise expand split grammar beyond support/provider/session-length/objective-frequency.'}}
 Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--sessions',type=int,default=4000);p.add_argument('--out',default='v119_public_anchor_geometry.json');run(p.parse_args())

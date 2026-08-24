#!/usr/bin/env python3
"""V153 — interaction-timing phase-change discovery.

Residual after V152: canonical event/state elaboration is saturated. V75/V112 do not
use the raw transcript timestamp field. Test whether lawful single-session timing
(response latency, tutor reaction latency, hesitation and pace change) carries a
missing student-state distinction beyond V135.

Frozen controls:
  PACE_ONLY keeps timing distribution/session duration but removes role alignment.
  SHUFFLED_GAPS deterministically permutes the exact within-session gap multiset,
  preserving total timing distribution while destroying alignment to turns/roles.
No sweep. 2500 deterministic rows. Advance only at >=.006 gain over V135 in BOTH
session- and objective-grouped OOF, every outer fold positive, and real timing beats
both controls in both geometries.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.model_selection import GroupKFold
from v71_mastery_events import load_transcript, normalize_roles, QUESTION_RE
from v75_canonical_trajectory import load_training
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control
from v110_residual_collider_state_discovery import EPS, ll
from v152_transition_law_discovery import outer_components, meta_base, meta_plus, fit_meta

ROWS=2500
D=24

def h64(x): return int(hashlib.sha256(str(x).encode()).hexdigest()[:16],16)
def stat(a,q=.5):
    a=np.asarray(a,float); a=a[np.isfinite(a)]
    return float(np.quantile(a,q)) if len(a) else 0.0

def timing_vec(df, shuffled=False, key=''):
    d=normalize_roles(df).reset_index(drop=True)
    role=d.role_repaired.astype(str).str.lower().to_numpy(); text=d.content.fillna('').astype(str).to_numpy()
    ts=pd.to_datetime(d.timestamp,errors='coerce',utc=True)
    sec=np.full(len(d),np.nan)
    if len(d)>1:
        raw=np.diff(ts.astype('int64').to_numpy()/1e9)
        raw[(raw<0)|(raw>3600)]=np.nan
        if shuffled:
            z=raw.copy(); ok=np.where(np.isfinite(z))[0]
            rng=np.random.default_rng(h64(key)&((1<<63)-1)); vals=z[ok].copy(); rng.shuffle(vals); z[ok]=vals; raw=z
        sec[1:]=raw
    valid=np.isfinite(sec); gaps=sec[valid]
    stu=[sec[i] for i in range(1,len(d)) if role[i]=='student' and role[i-1]=='tutor' and np.isfinite(sec[i])]
    tut=[sec[i] for i in range(1,len(d)) if role[i]=='tutor' and role[i-1]=='student' and np.isfinite(sec[i])]
    qstu=[]
    for i in range(1,len(d)):
        if role[i]=='student' and role[i-1]=='tutor' and QUESTION_RE.search(text[i-1]) and np.isfinite(sec[i]): qstu.append(sec[i])
    def trend(a):
        if len(a)<2:return 0.0
        x=np.arange(len(a),dtype=float); return float(np.polyfit(x,np.log1p(np.asarray(a,float)),1)[0])
    first=gaps[:max(1,len(gaps)//2)]; second=gaps[len(gaps)//2:] if len(gaps)>1 else gaps
    x=np.array([
      float(valid.mean()) if len(valid) else 0.0, np.log1p(np.nansum(gaps)), stat(gaps,.5),stat(gaps,.75),stat(gaps,.9),stat(gaps,1.0),
      float(np.mean(gaps>30)) if len(gaps) else 0.0,float(np.mean(gaps>60)) if len(gaps) else 0.0,
      stat(stu,.5),stat(stu,.75),stat(stu,.9),stat(stu,1.0), stat(stu[-4:],.5),trend(stu),
      stat(tut,.5),stat(tut,.75),stat(tut,.9),stat(tut,1.0),
      stat(qstu,.5),stat(qstu,.75),stat(qstu[-4:],.5),trend(qstu),
      np.log1p(stat(second,.5))-np.log1p(stat(first,.5)), float(len(stu))/max(1,len(d))
    ],float)
    # Stabilise long-tail timing without choosing thresholds from labels.
    x[2:6]=np.log1p(np.maximum(x[2:6],0)); x[8:13]=np.log1p(np.maximum(x[8:13],0)); x[14:21]=np.log1p(np.maximum(x[14:21],0))
    return x

def pace_only(v):
    z=np.zeros_like(v); z[:8]=v[:8]; z[22]=v[22]; return z

def geometry(name,groups,X75,Xr,Xt,Xc,Xs,y,support):
    n=len(y); groups=np.asarray(groups); P135=np.zeros(n); PT=np.zeros(n); PC=np.zeros(n); PS=np.zeros(n); folds=[]
    for k,(tr,va) in enumerate(GroupKFold(4).split(np.zeros(n),y,groups),1):
        oq0,o75,orr,opp,oc,oseen,opt,opc,ops=outer_components(X75,Xr,Xt,Xc,Xs,y,tr,va,support)
        inner=list(GroupKFold(min(3,len(np.unique(groups[tr])))).split(np.zeros(len(tr)),y[tr],groups[tr]))
        iq0=np.zeros(len(tr));i75=np.zeros(len(tr));ir=np.zeros(len(tr));ipp=np.zeros(len(tr));ic=np.zeros(len(tr));iseen=np.zeros(len(tr),bool);it=np.zeros(len(tr));ico=np.zeros(len(tr));ish=np.zeros(len(tr))
        for ltr,lva in inner:
            z=outer_components(X75,Xr,Xt,Xc,Xs,y,tr[ltr],tr[lva],support)
            iq0[lva],i75[lva],ir[lva],ipp[lva],ic[lva],iseen[lva],it[lva],ico[lva],ish[lva]=z
        q135=oq0.copy(); fm=iseen
        from v135_nested_supported_stack import feats,fit_stack
        if fm.sum()>=50 and len(np.unique(y[tr][fm]))==2:
            m=fit_stack(feats(i75[fm],ir[fm],ipp[fm],ic[fm],True),y[tr][fm])
            if oseen.any(): q135[oseen]=np.clip(m.predict_proba(feats(o75[oseen],orr[oseen],opp[oseen],oc[oseen],True))[:,1],EPS,1-EPS)
        ib=meta_base(iq0,i75,ir,ipp,ic,iseen); ob=meta_base(oq0,o75,orr,opp,oc,oseen)
        mt=fit_meta(meta_plus(ib,it),y[tr]); mc=fit_meta(meta_plus(ib,ico),y[tr]); ms=fit_meta(meta_plus(ib,ish),y[tr])
        qt=np.clip(mt.predict_proba(meta_plus(ob,opt))[:,1],EPS,1-EPS); qc=np.clip(mc.predict_proba(meta_plus(ob,opc))[:,1],EPS,1-EPS); qs=np.clip(ms.predict_proba(meta_plus(ob,ops))[:,1],EPS,1-EPS)
        P135[va]=q135;PT[va]=qt;PC[va]=qc;PS[va]=qs
        r={'fold':k,'v135_ll':ll(y[va],q135),'timing_ll':ll(y[va],qt),'pace_only_ll':ll(y[va],qc),'shuffled_gaps_ll':ll(y[va],qs)}
        r['gain_vs_v135']=r['v135_ll']-r['timing_ll'];r['gain_vs_pace']=r['pace_only_ll']-r['timing_ll'];r['gain_vs_shuffle']=r['shuffled_gaps_ll']-r['timing_ll'];folds.append(r);print(name,'FOLD',json.dumps(r),flush=True)
    out={'geometry':name,'v135_ll':ll(y,P135),'timing_ll':ll(y,PT),'pace_only_ll':ll(y,PC),'shuffled_gaps_ll':ll(y,PS),'folds':folds}
    out['gain_vs_v135']=out['v135_ll']-out['timing_ll'];out['gain_vs_pace']=out['pace_only_ll']-out['timing_ll'];out['gain_vs_shuffle']=out['shuffled_gaps_ll']-out['timing_ll'];out['all_folds_positive']=all(r['gain_vs_v135']>0 for r in folds);return out

def main(a):
    t0=time.time();f0=load_training(a.features,a.labels).reset_index(drop=True);ix=np.array(sorted(range(len(f0)),key=lambda i:h64(f0.response_id.iloc[i]))[:min(ROWS,len(f0))]);f=f0.iloc[ix].reset_index(drop=True)
    y=f.target.to_numpy(int);sess=f.session_id.astype(str).to_numpy();obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy();support=f.learning_objective.astype(str).to_numpy();cache={}
    for s in np.unique(sess):cache[s]=load_transcript(a.transcripts/f'{s}.csv')
    rt=[];rz=[];vr=[];vc=[];vs=[];valid=[]
    for _,r in f.iterrows():
        d=cache[str(r.session_id)];t,z=segmented_control(d,str(r.learning_objective),'related');rt.append(t);rz.append(z);real=timing_vec(d,False,str(r.response_id));sham=timing_vec(d,True,str(r.response_id));vr.append(real);vc.append(pace_only(real));vs.append(sham);valid.append(real[0])
    print('TIMING_CENSUS',json.dumps({'mean_valid_gap_fraction':float(np.mean(valid)),'rows':len(f),'sessions':len(cache)}),flush=True)
    X75=build_v75(f,cache);Xr=build_control(rt,rz);Xt=csr_matrix(np.asarray(vr));Xc=csr_matrix(np.asarray(vc));Xs=csr_matrix(np.asarray(vs))
    out={'protocol':'V153_INTERACTION_TIMING_DISCOVERY','rows':len(f),'feature_dim':D,'census':{'mean_valid_gap_fraction':float(np.mean(valid))}}
    out['session_grouped']=geometry('session_grouped',sess,X75,Xr,Xt,Xc,Xs,y,support);out['objective_grouped']=geometry('objective_grouped',obj,X75,Xr,Xt,Xc,Xs,y,support)
    S=out['session_grouped'];O=out['objective_grouped'];advance=(S['gain_vs_v135']>=.006 and O['gain_vs_v135']>=.006 and S['all_folds_positive'] and O['all_folds_positive'] and S['gain_vs_pace']>0 and O['gain_vs_pace']>0 and S['gain_vs_shuffle']>0 and O['gain_vs_shuffle']>0)
    out['decision']={'verdict':'ADVANCE_V153_TO_FULL' if advance else 'CLOSE_INTERACTION_TIMING_DISCOVERY','advance':bool(advance),'rule':'>=.006 gain both geometries; every fold positive; beat pace-only and shuffled-gap controls; full run before smoke'};out['elapsed_seconds']=time.time()-t0
    Path(a.out).write_text(json.dumps(out,indent=2));print('FINAL',json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',default='v153_interaction_timing_discovery.json');main(p.parse_args())

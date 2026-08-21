#!/usr/bin/env python3
"""V128 REAL CLOCK PACING residual over frozen V97.

Primary separator: actual transcript clock gaps that V75/V97 discard.
Control: preserve identical turn order/roles but replace timestamps with evenly
spaced synthetic times, removing real pacing while retaining turn-count/role
structure. No parameter sweep; inference remains sample-local.
"""
from __future__ import annotations
import argparse, csv, io, json, zipfile
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from v110_residual_collider_state_discovery import ll, logit
from v121_pretrained_semantic_residual import p97_oof, collision_mask
from v75_canonical_trajectory import SEED

EPS=1e-5

def sec(s):
    p=str(s).strip().split(':')
    if len(p)!=3: return np.nan
    try: return int(p[0])*3600+int(p[1])*60+float(p[2])
    except: return np.nan

def features(rows, warp=False):
    roles=[str(r.get('role','')).lower() for r in rows]
    t=np.arange(len(rows),dtype=float) if warp else np.array([sec(r.get('timestamp','')) for r in rows],dtype=float)
    ok=np.isfinite(t)
    if ok.sum()<2: return np.zeros(10,float)
    # preserve archive order; negative clock jumps are treated as zero rather than reordered.
    gaps=np.maximum(np.diff(t),0.0)
    pos=gaps[gaps>0]
    duration=max(0.0,float(t[ok][-1]-t[ok][0]))
    def pair(a,b):
        x=[gaps[i] for i in range(len(gaps)) if roles[i]==a and roles[i+1]==b]
        return np.asarray(x,float)
    ts=pair('tutor','student'); st=pair('student','tutor')
    def med(x): return float(np.median(x)) if len(x) else 0.0
    def p90(x): return float(np.quantile(x,.9)) if len(x) else 0.0
    return np.array([
      np.log1p(duration), np.log1p(med(pos)), np.log1p(p90(pos)), np.log1p(float(pos.max()) if len(pos) else 0.0),
      float(np.mean(gaps==0)) if len(gaps) else 0.0,
      np.log1p(med(ts)), np.log1p(p90(ts)), np.log1p(med(st)), np.log1p(p90(st)),
      np.log1p(float(len(rows))),
    ],float)

def residual_oof(P,X,y,splits):
    q=np.zeros(len(y),float)
    for tr,va in splits:
        mu=X[tr].mean(0); sd=X[tr].std(0)+1e-6
        A=np.c_[logit(P[tr]),(X[tr]-mu)/sd]
        B=np.c_[logit(P[va]),(X[va]-mu)/sd]
        m=LogisticRegression(C=.05,max_iter=300,solver='liblinear',random_state=SEED).fit(A,y[tr])
        q[va]=m.predict_proba(B)[:,1]
    return np.clip(q,EPS,1-EPS)

def eval_geom(name,groups,X75,Xr,y,support,objectives,Xclock,Xwarp):
    P,splits=p97_oof(X75,Xr,y,groups,support)
    Q=residual_oof(P,Xclock,y,splits); W=residual_oof(P,Xwarp,y,splits)
    base=ll(y,P); real=ll(y,Q); warp=ll(y,W)
    mask=collision_mask(P,y,objectives,.01)
    out={'geometry':name,'rows':int(len(y)),'groups':int(len(np.unique(groups))),
         'baseline_v97_ll':float(base),'real_clock':{'ll':float(real),'gain':float(base-real)},
         'even_spacing_control':{'ll':float(warp),'gain':float(base-warp)},
         'real_minus_control_gain':float(warp-real),'hard_collision':{'rows':int(mask.sum())}}
    if mask.any():
        b=ll(y[mask],P[mask]); r=ll(y[mask],Q[mask]); w=ll(y[mask],W[mask])
        out['hard_collision'].update({'baseline_ll':float(b),'real_clock_ll':float(r),'real_clock_gain':float(b-r),
                                      'control_ll':float(w),'real_minus_control_gain':float(w-r)})
    return out

def main(a):
    d=Path(a.dir); z=np.load(d/'arrays.npz',allow_pickle=True)
    y=z['y']; objectives=z['objectives']; support=z['support']; sessions=z['sessions']
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz')
    cache={}
    with zipfile.ZipFile(a.archive) as za:
        names=set(za.namelist())
        for sid in np.unique(sessions):
            name=f'{sid}.csv'
            if name not in names: raise RuntimeError(f'missing transcript {name}')
            with za.open(name) as f:
                rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            cache[str(sid)]=(features(rows,False),features(rows,True))
    Xclock=np.vstack([cache[str(s)][0] for s in sessions]); Xwarp=np.vstack([cache[str(s)][1] for s in sessions])
    res={'protocol':'V128_REAL_CLOCK_PACING','rows':int(len(y)),
         'features':['log_duration','log_median_positive_gap','log_p90_positive_gap','log_max_gap','zero_gap_fraction','log_tutor_to_student_median','log_tutor_to_student_p90','log_student_to_tutor_median','log_student_to_tutor_p90','log_turn_count'],
         'control':'identical transcript order/roles with timestamps replaced by 0,1,2,...',
         'precommit':{'promote_gain_each_geometry':.0015,'phase_change_gain_each_geometry':.003,'real_minus_control_each_geometry':.001,'hard_collision_gain_each_geometry':'>0','no_parameter_sweep':True}}
    res['objective_grouped']=eval_geom('objective_grouped',objectives,X75,Xr,y,support,objectives,Xclock,Xwarp)
    res['session_grouped']=eval_geom('session_grouped',sessions,X75,Xr,y,support,objectives,Xclock,Xwarp)
    def promote(r): return r['real_clock']['gain']>=.0015 and r['real_minus_control_gain']>=.001 and r['hard_collision'].get('real_clock_gain',-1)>0
    def phase(r): return r['real_clock']['gain']>=.003 and r['real_minus_control_gain']>=.001 and r['hard_collision'].get('real_clock_gain',-1)>0
    po,ps=promote(res['objective_grouped']),promote(res['session_grouped']); ph=phase(res['objective_grouped']) and phase(res['session_grouped'])
    verdict='PHASE_CHANGE_CANDIDATE' if ph else 'PROMOTE_REAL_CLOCK_LAW' if po and ps else 'SUPPRESS_REAL_CLOCK_PACING'
    res['decision']={'objective_pass':bool(po),'session_pass':bool(ps),'verdict':verdict}
    Path(a.out).write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--dir',required=True); p.add_argument('--out',required=True); main(p.parse_args())

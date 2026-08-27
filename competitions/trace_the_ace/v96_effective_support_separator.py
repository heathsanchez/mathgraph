#!/usr/bin/env python3
"""V96: refine V95 raw support into an effective-support observable.

V95 established a causal regime transition: RELATED ability is valuable with
little target-objective support and should be suppressed once V75 has enough
support. Raw dose was too crude because many held-out objectives saturate early.

This separator keeps V95's fixed evaluation rows and nested support intervention,
but asks which observable explains the transition better:
  COUNT    realised labelled rows for the objective;
  COVERAGE realised rows / available support-pool rows (saturation);
  BALANCE  labelled support containing both classes;
  CAPACITY available support-pool size (objective prevalence control).

For every dose we fit V75 and RELATED exactly as in V95, then score per-objective
losses on the same evaluation rows. For each observable we fit a tiny deterministic
threshold router: below threshold use the globally selected V95 blend weight for
that dose, above threshold use V75. Thresholds are selected on a deterministic
half of held-out objectives and evaluated on the other half. This is a routing
separator, not a leaderboard fit.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups
from v94_related_control import segmented_control, build_control
from v95_objective_support_activation import make_fixed_support_design, support_indices, fit_predict, best_blend, LEVELS


def split_objectives(objs):
    def key(g): return hashlib.sha256(f'V96|{SEED}|{g}'.encode()).hexdigest()
    s=sorted(objs,key=key); return set(s[::2]),set(s[1::2])

def ll(y,p): return float(log_loss(y,np.clip(p,1e-5,1-1e-5)))

def route_eval(y,p0,pa,groups,metric,fit_objs,test_objs,w):
    vals=np.array([metric[str(g)] for g in groups],float)
    uniq=np.unique([metric[g] for g in fit_objs if g in metric])
    if len(uniq)>20: cuts=np.unique(np.quantile(uniq,np.linspace(0,1,21)))
    else: cuts=uniq
    candidates=[-1e-12]+[float(x) for x in cuts]+[float(np.max(uniq)+1e-9)] if len(uniq) else [0.0]
    fit=np.array([str(g) in fit_objs for g in groups]); test=np.array([str(g) in test_objs for g in groups])
    rows=[]
    for t in candidates:
        # low effective support => ability blend; high => V75
        use=vals<=t; q=np.where(use,(1-w)*p0+w*pa,p0)
        rows.append((t,ll(y[fit],q[fit]),ll(y[test],q[test]),float(np.mean(use[test]))))
    best=min(rows,key=lambda z:z[1])
    return {'threshold':best[0],'fit_ll':best[1],'test_ll':best[2],'test_ability_fraction':best[3],
            'test_v75':ll(y[test],p0[test]),'test_global_blend':ll(y[test],((1-w)*p0+w*pa)[test]),
            'gain_vs_v75':ll(y[test],p0[test])-best[2]}

def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in f.session_id.astype(str).unique()}
    rt=[]; rz=[]
    for i,r in f.iterrows():
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related'); rt.append(t); rz.append(z)
        if (i+1)%2500==0: print('rows',i+1)
    X0=build_v75(f,cache); Xr=build_control(rt,rz); y=f.target.to_numpy(int)
    obj=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    base,held=folds_from_groups(obj)[0]; pools,ev=make_fixed_support_design(f,held,obj); ey=y[ev]; eg=obj[ev]
    fit_objs,test_objs=split_objectives(sorted(pools))
    out={'primary':'effective-support-separator','objective_router_split':{'fit':len(fit_objs),'test':len(test_objs)},'levels':[]}
    for level in LEVELS:
        si,counts=support_indices(pools,level); tr=np.concatenate([np.asarray(base,int),si])
        p0=fit_predict(X0,y,tr,ev); pa=fit_predict(Xr,y,tr,ev); b,_=best_blend(ey,p0,pa); w=float(b['w'])
        count={}; coverage={}; balance={}; capacity={}
        for g in pools:
            pool=pools[g]; k=len(pool) if level=='32+' else min(int(level),len(pool)); chosen=pool[:k]
            count[g]=float(k); capacity[g]=float(len(pool)); coverage[g]=float(k/max(1,len(pool)))
            balance[g]=float(len(np.unique(y[chosen]))>=2) if k else 0.0
        arms={
          'count':route_eval(ey,p0,pa,eg,count,fit_objs,test_objs,w),
          'coverage':route_eval(ey,p0,pa,eg,coverage,fit_objs,test_objs,w),
          'balance':route_eval(ey,p0,pa,eg,balance,fit_objs,test_objs,w),
          'capacity':route_eval(ey,p0,pa,eg,capacity,fit_objs,test_objs,w),
        }
        out['levels'].append({'support':str(level),'global_weight':w,'arms':arms})
        print('LEVEL',level,'W',w,{k:round(v['gain_vs_v75'],6) for k,v in arms.items()})
    # Decision uses only levels where V95 had a nonzero specialist weight.
    useful=[x for x in out['levels'] if x['global_weight']>0]
    means={k:float(np.mean([x['arms'][k]['gain_vs_v75'] for x in useful])) for k in ('count','coverage','balance','capacity')}
    wins={k:int(sum(x['arms'][k]['test_ll'] <= min(v['test_ll'] for v in x['arms'].values())+1e-12 for x in useful)) for k in means}
    best=max(means,key=means.get)
    # Promotion needs positive held-out routing value and superiority to raw count.
    if best!='count' and means[best]>=0.001 and means[best]>=means['count']+0.0005:
        verdict='PROMOTE_'+best.upper()+'_AS_EFFECTIVE_SUPPORT'
    elif max(means.values())>=0.0005:
        verdict='R5_REFINE_COMPOSITE_SUPPORT'
    else:
        verdict='SUPPRESS_SIMPLE_SUPPORT_ROUTING'
    out['decision']={'mean_test_gain_vs_v75':means,'wins':wins,'best_observable':best,'verdict':verdict,
      'precommit':'promote non-count observable iff held-out mean gain>=.001 and >= raw-count gain+.0005; else refine if any >=.0005'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v96_effective_support.json'); run(p.parse_args())

#!/usr/bin/env python3
"""V126 objective↔context alignment residual over frozen V97/V121 artifacts.

Single primary separator: cosine displacement between the frozen objective-only
embedding and the frozen objective+context embedding. This tests a relational
feature that V121's linear residual does not explicitly represent.

Control: within-objective shuffled semantic embedding before displacement.
No embedding rerun, no parameter sweep, no label-informed routing.
"""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from v121_pretrained_semantic_residual import (
    p97_oof, residual_oof, within_objective_shuffle, collision_mask, ll, MODEL_NAME
)
from v121_staged_transport import load_embeddings

EPS=1e-12

def cosine_displacement(a,b):
    an=np.linalg.norm(a,axis=1); bn=np.linalg.norm(b,axis=1)
    cos=np.sum(a*b,axis=1)/np.maximum(an*bn,EPS)
    return (1.0-np.clip(cos,-1,1)).reshape(-1,1)

def eval_geom(name,groups,X75,Xr,y,support,objectives,D,Dsh):
    P,splits=p97_oof(X75,Xr,y,groups,support)
    Q=residual_oof(P,D,y,splits); Qsh=residual_oof(P,Dsh,y,splits)
    base=ll(y,P); real=ll(y,Q); sh=ll(y,Qsh)
    mask=collision_mask(P,y,objectives,tol=.01)
    out={'geometry':name,'rows':int(len(y)),'groups':int(len(np.unique(groups))),
         'baseline_v97_ll':float(base),
         'alignment':{'ll':float(real),'gain':float(base-real)},
         'alignment_shuffled_within_objective':{'ll':float(sh),'gain':float(base-sh)},
         'alignment_minus_shuffle_gain':float(sh-real),
         'hard_collision':{'rows':int(mask.sum())}}
    if mask.any():
        b=ll(y[mask],P[mask]); r=ll(y[mask],Q[mask]); s=ll(y[mask],Qsh[mask])
        out['hard_collision'].update({'baseline_ll':float(b),'alignment_ll':float(r),
            'alignment_gain':float(b-r),'shuffled_ll':float(s),'alignment_minus_shuffle_gain':float(s-r)})
    return out

def main(a):
    d=Path(a.dir)
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz')
    z=np.load(d/'arrays.npz',allow_pickle=True)
    y=z['y']; objectives=z['objectives']; support=z['support']; sessions=z['sessions']
    E_obj,E_sem=load_embeddings(Path(a.embeddings))
    E_sh=within_objective_shuffle(E_sem,objectives)
    D=cosine_displacement(E_obj,E_sem); Dsh=cosine_displacement(E_obj,E_sh)
    res={'protocol':'V126_OBJECTIVE_CONTEXT_ALIGNMENT','model':MODEL_NAME,'rows':int(len(y)),
         'primary_separator':'1-cosine(objective_embedding, objective_plus_context_embedding)',
         'control':'within-objective shuffled context embedding before displacement',
         'precommit':{'promote_gain_each_geometry':.0015,'phase_change_gain_each_geometry':.003,
                      'real_minus_shuffle_each_geometry':.001,'no_parameter_sweep':True}}
    res['objective_grouped']=eval_geom('objective_grouped',objectives,X75,Xr,y,support,objectives,D,Dsh)
    res['session_grouped']=eval_geom('session_grouped',sessions,X75,Xr,y,support,objectives,D,Dsh)
    def promote(r): return r['alignment']['gain']>=.0015 and r['alignment_minus_shuffle_gain']>=.001
    def phase(r): return r['alignment']['gain']>=.003 and r['alignment_minus_shuffle_gain']>=.001
    po,ps=promote(res['objective_grouped']),promote(res['session_grouped'])
    ph=phase(res['objective_grouped']) and phase(res['session_grouped'])
    if ph: verdict='PHASE_CHANGE_CANDIDATE'
    elif po and ps: verdict='PROMOTE_ALIGNMENT_LAW'
    else: verdict='SUPPRESS_ALIGNMENT_RESIDUAL'
    res['decision']={'objective_pass':bool(po),'session_pass':bool(ps),'verdict':verdict}
    Path(a.out).write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--dir',required=True); p.add_argument('--embeddings',required=True); p.add_argument('--out',required=True); main(p.parse_args())

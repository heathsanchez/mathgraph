#!/usr/bin/env python3
"""V131: deployable prediction-crowding gate for V129 tutor uptake.

Derived from the residual constraint intersection:
- V129 uptake is globally harmful,
- but improves label-defined same-objective hard collisions and beats reply rotation,
- therefore the missing object may be an applicability predicate, not a new feature.

This test removes the forbidden label clause from the hard-collision definition.
A row is gate-positive iff another row with the same objective has a V97 prediction
within 0.01. That predicate is batch-visible and label-free at inference time.
Inside the gate we use the frozen V129 uptake residual correction; outside it we
leave V97 unchanged. The control uses identically gated rotated-reply correction.
No threshold sweep.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz

from v110_residual_collider_state_discovery import ll
from v121_pretrained_semantic_residual import p97_oof
from v129_tutor_uptake import feats,pairs,residual_oof

TOL=0.01


def crowding_mask(P: np.ndarray, objectives: np.ndarray, tol: float=TOL) -> np.ndarray:
    m=np.zeros(len(P),bool)
    for o in np.unique(objectives):
        z=np.where(objectives==o)[0]
        if len(z)<2: continue
        p=P[z]
        D=np.abs(p[:,None]-p[None,:])
        np.fill_diagonal(D,np.inf)
        m[z[np.min(D,axis=1)<=tol]]=True
    return m


def evalg(name,groups,X75,Xr,y,support,obj,R,C):
    P,splits=p97_oof(X75,Xr,y,groups,support)
    Q=residual_oof(P,R,y,splits)
    QC=residual_oof(P,C,y,splits)
    gate=crowding_mask(P,obj,TOL)
    G=P.copy(); GC=P.copy(); G[gate]=Q[gate]; GC[gate]=QC[gate]
    b=ll(y,P); g=ll(y,G); gc=ll(y,GC)
    out={
        'geometry':name,
        'baseline_v97_ll':b,
        'gate_rows':int(gate.sum()),
        'gate_fraction':float(gate.mean()),
        'gated_uptake':{'ll':g,'gain':b-g},
        'gated_rotated_control':{'ll':gc,'gain':b-gc},
        'real_minus_control_gain':gc-g,
    }
    if gate.any():
        bb=ll(y[gate],P[gate]); rr=ll(y[gate],Q[gate]); cc=ll(y[gate],QC[gate])
        out['gate_only']={
            'baseline_ll':bb,
            'uptake_ll':rr,
            'uptake_gain':bb-rr,
            'control_ll':cc,
            'real_minus_control_gain':cc-rr,
        }
    return out


def main(a):
    d=Path(a.dir); z=np.load(d/'arrays.npz',allow_pickle=True)
    y=z['y']; obj=z['objectives']; support=z['support']; sessions=z['sessions']
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz')
    cache={}
    with zipfile.ZipFile(a.archive) as za:
        names=set(za.namelist())
        for sid in np.unique(sessions):
            name=f'{sid}.csv'
            if name not in names: raise RuntimeError('missing '+name)
            with za.open(name) as f:
                rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            P=pairs(rows)
            shift=1+(int(hashlib.sha256(str(sid).encode()).hexdigest()[:8],16)%max(1,len(P)-1)) if len(P)>1 else 0
            cache[str(sid)]=(feats(P,0),feats(P,shift))
    R=np.vstack([cache[str(s)][0] for s in sessions]); C=np.vstack([cache[str(s)][1] for s in sessions])
    res={
        'protocol':'V131_CROWDING_GATED_UPTAKE',
        'rows':int(len(y)),
        'gate':'same objective has another row within abs(V97_i-V97_j)<=0.01; no labels',
        'precommit':{
            'global_gain_each_geometry':0.0005,
            'real_minus_control_each_geometry':0.0005,
            'gate_only_gain_each_geometry':'>0',
            'threshold_sweep':False,
            'tol':TOL,
        }
    }
    res['objective_grouped']=evalg('objective_grouped',obj,X75,Xr,y,support,obj,R,C)
    res['session_grouped']=evalg('session_grouped',sessions,X75,Xr,y,support,obj,R,C)
    def ok(r):
        return r['gated_uptake']['gain']>=.0005 and r['real_minus_control_gain']>=.0005 and r.get('gate_only',{}).get('uptake_gain',-1)>0
    po,ps=ok(res['objective_grouped']),ok(res['session_grouped'])
    res['decision']={
        'objective_pass':bool(po),'session_pass':bool(ps),
        'verdict':'PROMOTE_DEPLOYABLE_UPTAKE_GATE' if po and ps else 'SUPPRESS_CROWDING_GATE'
    }
    Path(a.out).write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--dir',required=True); p.add_argument('--out',required=True); main(p.parse_args())

#!/usr/bin/env python3
"""Infrastructure-only evaluator for the already-frozen V121 artifacts.

The only repair relative to v121_staged_transport.evaluate is loading the frozen
string arrays with allow_pickle=True. Scientific features, folds, controls,
models, thresholds, and interpretation are unchanged.
"""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from v121_pretrained_semantic_residual import MODEL_NAME, eval_geometry, within_objective_shuffle
from v121_staged_transport import load_embeddings


def main(a):
    d=Path(a.dir)
    X75=load_npz(d/'X75.npz'); Xr=load_npz(d/'Xr.npz')
    z=np.load(d/'arrays.npz', allow_pickle=True)
    y=z['y']; objectives=z['objectives']; support=z['support']; sessions=z['sessions']
    E_obj,E_sem=load_embeddings(Path(a.embeddings))
    if len(y)!=E_obj.shape[0] or len(y)!=E_sem.shape[0]:
        raise RuntimeError('evaluation embedding row mismatch')
    E_shuf=within_objective_shuffle(E_sem, objectives)
    manifest=json.loads((d/'manifest.json').read_text())
    results={
      'protocol':'V121_PRETRAINED_SEMANTIC_RESIDUAL','model':MODEL_NAME,
      'rows':int(len(y)),'objectives':int(len(np.unique(objectives))),
      'sessions':int(len(np.unique(sessions))),
      'transport_manifest':manifest,'transport':{'embedding_shards_merged':True,'serialization_repair':'allow_pickle_for_frozen_string_arrays'},
      'precommit':{'semantic_gain_each_geometry':.003,'semantic_minus_shuffle_each_geometry':.002,'hard_collision_gain_each_geometry':'>0','no_hyperparameter_sweep':True},
    }
    results['objective_grouped']=eval_geometry('objective_grouped',objectives,X75,Xr,y,support,objectives,E_obj,E_sem,E_shuf)
    results['session_grouped']=eval_geometry('session_grouped',sessions,X75,Xr,y,support,objectives,E_obj,E_sem,E_shuf)
    def passes(r):
        return r['semantic']['gain']>=.003 and r['semantic_minus_shuffle_gain']>=.002 and r['hard_collision'].get('semantic_gain',-1.)>0
    ok_obj=passes(results['objective_grouped']); ok_sess=passes(results['session_grouped'])
    if ok_obj and ok_sess:
        verdict='PHASE_CHANGE_CANDIDATE'; nxt='Promote pretrained semantic residual to larger frozen validation and public-probe packaging.'
    else:
        verdict='NO_ROBUST_SEMANTIC_PHASE_CHANGE'; nxt='Treat remaining oracle gap as largely unidentifiable from supplied transcript/objective observables; pivot to validation geometry / assessment-process inference rather than more text feature search.'
    results['decision']={'objective_grouped_pass':bool(ok_obj),'session_grouped_pass':bool(ok_sess),'verdict':verdict,'next':nxt}
    Path(a.out).write_text(json.dumps(results,indent=2)); print(json.dumps(results,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--dir',required=True); p.add_argument('--embeddings',required=True); p.add_argument('--out',required=True); main(p.parse_args())

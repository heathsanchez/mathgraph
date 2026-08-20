#!/usr/bin/env python3
"""Infrastructure-only staged transport for frozen V121.

This module does not define new scientific features, models, folds, controls, or
gates. It serializes the exact V121 computation across short-lived hosted runner
jobs so preparation, embedding, and evaluation can complete independently.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from scipy.sparse import load_npz, save_npz

from v110_residual_collider_state_discovery import hb
from v121_pretrained_semantic_residual import (
    MODEL_NAME,
    build_semantic_text,
    embed,
    eval_geometry,
    stable_hash,
    within_objective_shuffle,
)
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control


def prepare(a):
    out = Path(a.dir); out.mkdir(parents=True, exist_ok=True)
    f = load_training(a.features, a.labels).reset_index(drop=True)
    print('features columns', list(f.columns), flush=True)
    obj0 = (f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    cand = np.where(np.array([hb(x, 5) != 0 for x in obj0]))[0]
    ix = np.array(sorted(cand, key=lambda i: stable_hash(f.response_id.iloc[i]))[:a.rows])
    f = f.iloc[ix].reset_index(drop=True)

    y = f.target.to_numpy(int)
    objectives = (f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    support = f.learning_objective.astype(str).to_numpy()
    sessions = f.session_id.astype(str).to_numpy()

    cache = {s: load_transcript(a.transcripts / f'{s}.csv') for s in np.unique(sessions)}
    rt, rz, sem_text, obj_text = [], [], [], []
    for i, r in f.iterrows():
        d = cache[str(r.session_id)]
        t, z = segmented_control(d, str(r.learning_objective), 'related')
        rt.append(t); rz.append(z)
        obj_text.append(f'learning objective: {r.learning_objective}')
        sem_text.append(build_semantic_text(str(r.learning_objective), d))
        if (i + 1) % 500 == 0:
            print('prepared rows', i + 1, flush=True)

    save_npz(out / 'X75.npz', build_v75(f, cache))
    save_npz(out / 'Xr.npz', build_control(rt, rz))
    np.savez_compressed(out / 'arrays.npz', y=y, objectives=objectives, support=support, sessions=sessions)
    (out / 'texts.json').write_text(json.dumps({'objective': obj_text, 'semantic': sem_text}))
    manifest = {
        'protocol': 'V121_PRETRAINED_SEMANTIC_RESIDUAL', 'rows': int(len(f)),
        'objectives': int(len(np.unique(objectives))), 'sessions': int(len(np.unique(sessions))),
        'response_ids_sha256': __import__('hashlib').sha256('\n'.join(f.response_id.astype(str)).encode()).hexdigest(),
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2), flush=True)


def do_embed(a):
    d = Path(a.dir)
    texts = json.loads((d / 'texts.json').read_text())
    print('loading embedding model', MODEL_NAME, flush=True)
    model = TextEmbedding(model_name=MODEL_NAME)
    print('embedding objective control', flush=True)
    E_obj = embed(model, texts['objective'])
    print('embedding semantic intervention', flush=True)
    E_sem = embed(model, texts['semantic'])
    if E_obj.shape[0] != E_sem.shape[0]: raise RuntimeError('embedding row mismatch')
    np.savez_compressed(Path(a.out), E_obj=E_obj, E_sem=E_sem)
    print('embedding shapes', E_obj.shape, E_sem.shape, flush=True)


def evaluate(a):
    d = Path(a.dir)
    X75 = load_npz(d / 'X75.npz'); Xr = load_npz(d / 'Xr.npz')
    z = np.load(d / 'arrays.npz', allow_pickle=False)
    y=z['y']; objectives=z['objectives']; support=z['support']; sessions=z['sessions']
    e = np.load(a.embeddings, allow_pickle=False); E_obj=e['E_obj']; E_sem=e['E_sem']
    E_shuf = within_objective_shuffle(E_sem, objectives)
    manifest=json.loads((d/'manifest.json').read_text())
    results = {
        'protocol': 'V121_PRETRAINED_SEMANTIC_RESIDUAL', 'model': MODEL_NAME,
        'rows': int(len(y)), 'objectives': int(len(np.unique(objectives))),
        'sessions': int(len(np.unique(sessions))),
        'transport_manifest': manifest,
        'precommit': {'semantic_gain_each_geometry': .003,
                      'semantic_minus_shuffle_each_geometry': .002,
                      'hard_collision_gain_each_geometry': '>0',
                      'no_hyperparameter_sweep': True},
    }
    results['objective_grouped'] = eval_geometry('objective_grouped', objectives, X75, Xr, y, support, objectives, E_obj, E_sem, E_shuf)
    results['session_grouped'] = eval_geometry('session_grouped', sessions, X75, Xr, y, support, objectives, E_obj, E_sem, E_shuf)
    def passes(r):
        return r['semantic']['gain'] >= .003 and r['semantic_minus_shuffle_gain'] >= .002 and r['hard_collision'].get('semantic_gain', -1.) > 0
    ok_obj=passes(results['objective_grouped']); ok_sess=passes(results['session_grouped'])
    if ok_obj and ok_sess:
        verdict='PHASE_CHANGE_CANDIDATE'; nxt='Promote pretrained semantic residual to larger frozen validation and public-probe packaging.'
    else:
        verdict='NO_ROBUST_SEMANTIC_PHASE_CHANGE'; nxt='Treat remaining oracle gap as largely unidentifiable from supplied transcript/objective observables; pivot to validation geometry / assessment-process inference rather than more text feature search.'
    results['decision']={'objective_grouped_pass': bool(ok_obj), 'session_grouped_pass': bool(ok_sess), 'verdict': verdict, 'next': nxt}
    Path(a.out).write_text(json.dumps(results, indent=2)); print(json.dumps(results, indent=2), flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd', required=True)
    q=sp.add_parser('prepare'); q.add_argument('--features',type=Path,required=True); q.add_argument('--labels',type=Path,required=True); q.add_argument('--transcripts',type=Path,required=True); q.add_argument('--rows',type=int,default=2500); q.add_argument('--dir',required=True)
    q=sp.add_parser('embed'); q.add_argument('--dir',required=True); q.add_argument('--out',required=True)
    q=sp.add_parser('evaluate'); q.add_argument('--dir',required=True); q.add_argument('--embeddings',required=True); q.add_argument('--out',required=True)
    a=p.parse_args(); {'prepare':prepare,'embed':do_embed,'evaluate':evaluate}[a.cmd](a)

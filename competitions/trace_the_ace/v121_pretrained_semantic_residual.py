#!/usr/bin/env python3
"""V121 PRETRAINED SEMANTIC RESIDUAL TEST.

Qualitatively different from V112: fixed pretrained neural text embeddings rather
than hashed n-gram features. Tests whether semantic transcript/objective
representation adds row-local information beyond V97.

Frozen intervention:
- deterministic 2500-row sample, same hashing convention as V112
- pretrained jinaai/jina-embeddings-v2-small-en via FastEmbed 0.8.0
- three representations: objective-only control, objective+local/recent/student
  semantic intervention, and within-objective shuffled semantic ablation
- evaluate both objective-grouped and session-grouped 4-fold OOF
- evaluate a fixed hard-collision subset: an opposite-label same-objective row
  exists within |p97_i-p97_j| <= 0.01
- no hyperparameter sweep

Precommit:
PHASE_CHANGE if semantic gain >= .003 on BOTH split geometries, semantic beats
within-objective shuffled by >= .002 on BOTH, and hard-collision gain is positive
on BOTH. Otherwise do not promote.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from v110_residual_collider_state_discovery import hb, ll, logit, p97_predict
from v112_fast_raw_observable_screen import texts
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v94_related_control import segmented_control, build_control

EPS = 1e-5
MODEL_NAME = "jinaai/jina-embeddings-v2-small-en"


def stable_hash(x: object) -> int:
    return int(hashlib.sha256(str(x).encode()).hexdigest()[:16], 16)


def build_semantic_text(objective: str, transcript_df) -> str:
    student, _tutor, _full, local, last8 = texts(transcript_df, objective)
    # Keep a bounded tail while preserving the target segment and most recent turns.
    student_tail = student[-9000:]
    local_tail = local[-12000:]
    recent_tail = last8[-5000:]
    return (
        f"learning objective: {objective}\n"
        f"target tutoring context: {local_tail}\n"
        f"recent turns: {recent_tail}\n"
        f"student evidence: {student_tail}"
    )


def embed(model: TextEmbedding, seq: list[str]) -> np.ndarray:
    arr = np.vstack(list(model.embed(seq, batch_size=64))).astype(np.float32)
    if not np.isfinite(arr).all():
        raise RuntimeError("non-finite embedding")
    return arr


def p97_oof(X75, Xr, y, groups, support):
    q = np.zeros(len(y), dtype=float)
    splits = list(GroupKFold(min(4, len(np.unique(groups)))).split(np.zeros(len(y)), y, groups))
    for tr, va in splits:
        q[va], _ = p97_predict(X75, Xr, y, tr, va, support)
    return np.clip(q, EPS, 1 - EPS), splits


def residual_oof(P, E, y, splits):
    q = np.zeros(len(y), dtype=float)
    for tr, va in splits:
        Xtr = np.c_[logit(P[tr]), E[tr]]
        Xva = np.c_[logit(P[va]), E[va]]
        m = LogisticRegression(
            C=0.05,
            max_iter=300,
            solver="liblinear",
            random_state=SEED,
        ).fit(Xtr, y[tr])
        q[va] = m.predict_proba(Xva)[:, 1]
    return np.clip(q, EPS, 1 - EPS)


def within_objective_shuffle(E: np.ndarray, objectives: np.ndarray) -> np.ndarray:
    out = E.copy()
    rng = np.random.default_rng(SEED + 121)
    for o in np.unique(objectives):
        z = np.where(objectives == o)[0]
        if len(z) > 1:
            out[z] = E[rng.permutation(z)]
    return out


def collision_mask(P: np.ndarray, y: np.ndarray, objectives: np.ndarray, tol: float = 0.01) -> np.ndarray:
    mask = np.zeros(len(y), dtype=bool)
    for o in np.unique(objectives):
        z = np.where(objectives == o)[0]
        a0 = z[y[z] == 0]
        a1 = z[y[z] == 1]
        if len(a0) == 0 or len(a1) == 0:
            continue
        p0 = P[a0]
        p1 = P[a1]
        # sample is only 2500 rows, so explicit pairwise distances are small.
        D = np.abs(p0[:, None] - p1[None, :])
        mask[a0[np.min(D, axis=1) <= tol]] = True
        mask[a1[np.min(D, axis=0) <= tol]] = True
    return mask


def eval_geometry(name, groups, X75, Xr, y, support, objectives, E_obj, E_sem, E_shuf):
    P, splits = p97_oof(X75, Xr, y, groups, support)
    Qobj = residual_oof(P, E_obj, y, splits)
    Qsem = residual_oof(P, E_sem, y, splits)
    Qsh = residual_oof(P, E_shuf, y, splits)
    base = ll(y, P)
    mask = collision_mask(P, y, objectives, tol=0.01)
    out = {
        "geometry": name,
        "rows": int(len(y)),
        "groups": int(len(np.unique(groups))),
        "baseline_v97_ll": float(base),
        "objective_only": {"ll": float(ll(y, Qobj)), "gain": float(base - ll(y, Qobj))},
        "semantic": {"ll": float(ll(y, Qsem)), "gain": float(base - ll(y, Qsem))},
        "semantic_shuffled_within_objective": {"ll": float(ll(y, Qsh)), "gain": float(base - ll(y, Qsh))},
        "semantic_minus_shuffle_gain": float(ll(y, Qsh) - ll(y, Qsem)),
        "hard_collision": {"rows": int(mask.sum())},
    }
    if mask.any():
        b = ll(y[mask], P[mask])
        s = ll(y[mask], Qsem[mask])
        sh = ll(y[mask], Qsh[mask])
        out["hard_collision"].update({
            "baseline_ll": float(b),
            "semantic_ll": float(s),
            "semantic_gain": float(b - s),
            "shuffled_ll": float(sh),
            "semantic_minus_shuffle_gain": float(sh - s),
        })
    return out


def main(a):
    f = load_training(a.features, a.labels).reset_index(drop=True)
    print("features columns", list(f.columns), flush=True)
    obj0 = (f.learning_objective_id if "learning_objective_id" in f else f.learning_objective).astype(str).to_numpy()
    cand = np.where(np.array([hb(x, 5) != 0 for x in obj0]))[0]
    ix = np.array(sorted(cand, key=lambda i: stable_hash(f.response_id.iloc[i]))[: a.rows])
    f = f.iloc[ix].reset_index(drop=True)

    y = f.target.to_numpy(int)
    objectives = (f.learning_objective_id if "learning_objective_id" in f else f.learning_objective).astype(str).to_numpy()
    support = f.learning_objective.astype(str).to_numpy()
    sessions = f.session_id.astype(str).to_numpy()

    cache = {s: load_transcript(a.transcripts / f"{s}.csv") for s in np.unique(sessions)}
    rt, rz = [], []
    sem_text, obj_text = [], []
    for i, r in f.iterrows():
        d = cache[str(r.session_id)]
        t, z = segmented_control(d, str(r.learning_objective), "related")
        rt.append(t)
        rz.append(z)
        obj_text.append(f"learning objective: {r.learning_objective}")
        sem_text.append(build_semantic_text(str(r.learning_objective), d))
        if (i + 1) % 500 == 0:
            print("prepared rows", i + 1, flush=True)

    X75 = build_v75(f, cache)
    Xr = build_control(rt, rz)

    print("loading embedding model", MODEL_NAME, flush=True)
    model = TextEmbedding(model_name=MODEL_NAME)
    print("embedding objective control", flush=True)
    E_obj = embed(model, obj_text)
    print("embedding semantic intervention", flush=True)
    E_sem = embed(model, sem_text)
    E_shuf = within_objective_shuffle(E_sem, objectives)
    print("embedding shapes", E_obj.shape, E_sem.shape, flush=True)

    results = {
        "protocol": "V121_PRETRAINED_SEMANTIC_RESIDUAL",
        "model": MODEL_NAME,
        "rows": int(len(f)),
        "objectives": int(len(np.unique(objectives))),
        "sessions": int(len(np.unique(sessions))),
        "precommit": {
            "semantic_gain_each_geometry": 0.003,
            "semantic_minus_shuffle_each_geometry": 0.002,
            "hard_collision_gain_each_geometry": ">0",
            "no_hyperparameter_sweep": True,
        },
    }
    results["objective_grouped"] = eval_geometry(
        "objective_grouped", objectives, X75, Xr, y, support, objectives, E_obj, E_sem, E_shuf
    )
    results["session_grouped"] = eval_geometry(
        "session_grouped", sessions, X75, Xr, y, support, objectives, E_obj, E_sem, E_shuf
    )

    def passes(r):
        return (
            r["semantic"]["gain"] >= 0.003
            and r["semantic_minus_shuffle_gain"] >= 0.002
            and r["hard_collision"].get("semantic_gain", -1.0) > 0.0
        )

    ok_obj = passes(results["objective_grouped"])
    ok_sess = passes(results["session_grouped"])
    if ok_obj and ok_sess:
        verdict = "PHASE_CHANGE_CANDIDATE"
        nxt = "Promote pretrained semantic residual to larger frozen validation and public-probe packaging."
    else:
        verdict = "NO_ROBUST_SEMANTIC_PHASE_CHANGE"
        nxt = "Treat remaining oracle gap as largely unidentifiable from supplied transcript/objective observables; pivot to validation geometry / assessment-process inference rather than more text feature search."
    results["decision"] = {
        "objective_grouped_pass": bool(ok_obj),
        "session_grouped_pass": bool(ok_sess),
        "verdict": verdict,
        "next": nxt,
    }

    Path(a.out).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--labels", type=Path, required=True)
    p.add_argument("--transcripts", type=Path, required=True)
    p.add_argument("--rows", type=int, default=2500)
    p.add_argument("--out", default="v121_pretrained_semantic_residual.json")
    main(p.parse_args())

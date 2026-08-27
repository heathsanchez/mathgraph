#!/usr/bin/env python3
"""V95: objective-support activation law for the V94 RELATED ability specialist.

Residual
--------
V94 showed that RELATED relative-ability evidence helps objective-cold validation
but should receive zero weight in session-cold validation.  The proposed missing
applicability variable is epistemic support for the target objective.

Separator
---------
Take one deterministic objective-cold outer fold.  For every held-out objective,
reserve a deterministic support pool and a disjoint fixed evaluation set.  Reveal
nested amounts of labelled target-objective support (0, 1, 2, 4, 8, 16, 32+ per
objective), refit V75 and the V94 RELATED expert, and score the *same* evaluation
rows at every support level.

Prediction
----------
Optimal RELATED blend weight should be high at zero support and decline toward
zero as target-objective support increases.

Cheap causal ablation
---------------------
At support 8 and 32+, shuffle only the newly revealed support labels before
fitting the RELATED expert.  Extra rows without valid target information should
not reproduce a lawful support benefit.

No leaderboard score or hidden-test outcome is used anywhere in construction,
fitting, weighting, or the promotion decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, SEED
from v85_evidence_state import build_v75
from v93_shift_robust_validation import folds_from_groups
from v94_related_control import segmented_control, build_control


LEVELS = [0, 1, 2, 4, 8, 16, "32+"]
GRID = np.linspace(0.0, 0.6, 25)


def stable_key(obj: str, response_id: str) -> str:
    return hashlib.sha256(f"V95|{SEED}|{obj}|{response_id}".encode()).hexdigest()


def make_fixed_support_design(frame, val_idx, objective):
    """Return disjoint nested support pools and one fixed evaluation index.

    Up to half of each held-out objective (capped at 64 rows) is reserved as its
    support pool.  The complement is scored at every support level, eliminating
    changing-evaluation-set confounding.  Small objectives saturate naturally;
    the result records realised support counts for every level.
    """
    val_idx = np.asarray(val_idx, dtype=int)
    response = (
        frame.response_id.astype(str).to_numpy()
        if "response_id" in frame
        else np.arange(len(frame)).astype(str)
    )
    pools = {}
    eval_parts = []
    for g in sorted(np.unique(objective[val_idx])):
        idx = val_idx[objective[val_idx] == g]
        idx = np.asarray(sorted(idx, key=lambda i: stable_key(str(g), response[i])), dtype=int)
        pool_n = min(64, len(idx) // 2)
        pools[str(g)] = idx[:pool_n]
        eval_parts.append(idx[pool_n:])
    eval_idx = np.concatenate(eval_parts) if eval_parts else np.array([], dtype=int)
    return pools, np.asarray(sorted(eval_idx), dtype=int)


def support_indices(pools, level):
    out = []
    counts = []
    for g in sorted(pools):
        pool = pools[g]
        k = len(pool) if level == "32+" else min(int(level), len(pool))
        counts.append(k)
        if k:
            out.append(pool[:k])
    idx = np.concatenate(out) if out else np.array([], dtype=int)
    return np.asarray(sorted(idx), dtype=int), np.asarray(counts, dtype=int)


def fit_predict(X, y, train_idx, eval_idx, y_train_override=None):
    yy = y[train_idx] if y_train_override is None else np.asarray(y_train_override, dtype=int)
    m = LogisticRegression(
        C=0.25,
        max_iter=300,
        solver="liblinear",
        random_state=SEED,
    ).fit(X[train_idx], yy)
    return np.clip(m.predict_proba(X[eval_idx])[:, 1], 1e-5, 1 - 1e-5)


def best_blend(y, p0, pa):
    curve = []
    for w in GRID:
        q = np.clip((1 - w) * p0 + w * pa, 1e-5, 1 - 1e-5)
        curve.append({"w": float(w), "ll": float(log_loss(y, q))})
    return min(curve, key=lambda z: z["ll"]), curve


def realised_support_summary(counts):
    if not len(counts):
        return {"min": 0, "median": 0.0, "mean": 0.0, "max": 0, "objectives": 0}
    return {
        "min": int(np.min(counts)),
        "median": float(np.median(counts)),
        "mean": float(np.mean(counts)),
        "max": int(np.max(counts)),
        "objectives": int(len(counts)),
    }


def run(a):
    f = load_training(a.features, a.labels).reset_index(drop=True)
    cache = {
        sid: load_transcript(a.transcripts / f"{sid}.csv")
        for sid in f.session_id.astype(str).unique()
    }

    related_text, related_num = [], []
    for i, r in f.iterrows():
        d = cache[str(r.session_id)]
        t, z = segmented_control(d, str(r.learning_objective), "related")
        related_text.append(t)
        related_num.append(z)
        if (i + 1) % 2500 == 0:
            print("rows", i + 1)

    X0 = build_v75(f, cache)
    Xr = build_control(related_text, related_num)
    y = f.target.to_numpy(int)
    obj = (
        f.learning_objective_id
        if "learning_objective_id" in f
        else f.learning_objective
    ).astype(str).to_numpy()

    # Cheapest sufficient causal world: the first deterministic GroupKFold
    # objective-cold split, held fixed for every support dose.
    base_train, heldout = folds_from_groups(obj)[0]
    pools, eval_idx = make_fixed_support_design(f, heldout, obj)
    if not len(eval_idx):
        raise RuntimeError("V95 fixed evaluation set is empty")

    eval_y = y[eval_idx]
    results = []
    predictions = {}
    support_by_level = {}

    for level in LEVELS:
        sup_idx, counts = support_indices(pools, level)
        train_idx = np.concatenate([np.asarray(base_train, dtype=int), sup_idx])
        p0 = fit_predict(X0, y, train_idx, eval_idx)
        pr = fit_predict(Xr, y, train_idx, eval_idx)
        b, curve = best_blend(eval_y, p0, pr)
        ll0 = float(log_loss(eval_y, p0))
        llr = float(log_loss(eval_y, pr))
        label = str(level)
        results.append({
            "support": label,
            "realised_support_per_objective": realised_support_summary(counts),
            "support_rows_total": int(len(sup_idx)),
            "eval_rows": int(len(eval_idx)),
            "v75": ll0,
            "related_ability": llr,
            "best": b,
            "gain_vs_v75": float(ll0 - b["ll"]),
            "blend_curve": curve,
        })
        predictions[label] = (p0, pr)
        support_by_level[label] = (sup_idx, counts)
        print("SUPPORT", label, "V75", ll0, "RELATED", llr, "BEST", b)

    # Information-destruction ablation: same revealed rows and class marginal,
    # but support labels are deterministically shuffled.  Only RELATED is refit;
    # this asks whether valid labelled support, rather than row count alone,
    # improves the specialist representation.
    ablations = {}
    rng = np.random.RandomState(SEED + 95)
    for level in (8, "32+"):
        label = str(level)
        sup_idx, _ = support_by_level[label]
        train_idx = np.concatenate([np.asarray(base_train, dtype=int), sup_idx])
        yy = y[train_idx].copy()
        nbase = len(base_train)
        if len(sup_idx) > 1:
            yy[nbase:] = yy[nbase:][rng.permutation(len(sup_idx))]
        pr_bad = fit_predict(Xr, y, train_idx, eval_idx, y_train_override=yy)
        normal_pr = predictions[label][1]
        ablations[label] = {
            "normal_related_ll": float(log_loss(eval_y, normal_pr)),
            "shuffled_support_related_ll": float(log_loss(eval_y, pr_bad)),
            "valid_information_gain": float(log_loss(eval_y, pr_bad) - log_loss(eval_y, normal_pr)),
        }
        print("ABLATION", label, ablations[label])

    weights = np.asarray([r["best"]["w"] for r in results], dtype=float)
    # Use realised median support, with 32+ naturally reflecting the whole fixed pool.
    dose = np.asarray([r["realised_support_per_objective"]["median"] for r in results], dtype=float)
    rho = float(spearmanr(dose, weights).statistic) if len(np.unique(dose)) > 1 else 0.0
    near_monotone_steps = int(np.sum(np.diff(weights) <= 0.025 + 1e-12))
    possible_steps = len(weights) - 1
    delta = float(weights[0] - weights[-1])
    low_gain = float(results[0]["gain_vs_v75"])
    high_weight = float(weights[-1])

    clean = (
        near_monotone_steps >= possible_steps - 1
        and rho <= -0.75
        and delta >= 0.15
        and low_gain >= 0.003
        and high_weight <= 0.15
    )
    partial = rho <= -0.50 and delta >= 0.10 and low_gain >= 0.002
    if clean:
        verdict = "PROMOTE_OBJECTIVE_SUPPORT_ACTIVATION"
    elif partial:
        verdict = "R5_REFINE_EFFECTIVE_SUPPORT"
    else:
        verdict = "SUPPRESS_OBJECTIVE_SUPPORT"

    out = {
        "primary": "objective-support-activation-law",
        "design": {
            "outer_world": "first deterministic objective-cold GroupKFold split",
            "support_levels": [str(x) for x in LEVELS],
            "fixed_eval_rows": int(len(eval_idx)),
            "heldout_objectives": int(len(pools)),
            "support_pool_rule": "stable hash order; reserve up to half/objective capped at 64; score fixed complement",
            "note": "No leaderboard score or hidden-test outcome used in fitting, weighting, or decision.",
        },
        "support_response": results,
        "ablations": ablations,
        "decision": {
            "spearman_support_vs_weight": rho,
            "near_monotone_steps": near_monotone_steps,
            "possible_steps": possible_steps,
            "weight_drop_zero_to_32plus": delta,
            "zero_support_gain_vs_v75": low_gain,
            "high_support_weight": high_weight,
            "verdict": verdict,
            "precommit": {
                "promote": "near-monotone (<=1 tolerance step), rho<=-0.75, weight drop>=0.15, zero-support gain>=0.003, 32+ weight<=0.15",
                "refine": "rho<=-0.50, weight drop>=0.10, zero-support gain>=0.002",
                "otherwise": "suppress raw objective support and seek another observable",
            },
        },
    }
    Path(a.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--labels", type=Path, required=True)
    p.add_argument("--transcripts", type=Path, required=True)
    p.add_argument("--out", default="v95_objective_support_activation.json")
    run(p.parse_args())

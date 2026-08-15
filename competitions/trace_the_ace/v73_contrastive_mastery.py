#!/usr/bin/env python3
"""Trace the Ace V73: same-session contrastive mastery model.

V73 turns the structural observation behind V72 into a measurable model.
For each response it builds objective-conditioned mastery evidence from V71,
then trains two complementary learners inside each held-out split:

1. row model: predicts correctness from objective text + mastery evidence;
2. contrastive model: on mixed-label training sessions, learns which of two
   objectives in the SAME transcript is more likely to be correct.

Because the contrastive examples cancel session-wide ability, their coefficient
vector is forced toward objective-specific mastery evidence. The final prediction
combines row and contrastive logits using an inner training split only; validation
labels are never used to choose the blend.

The script inspects CSV headers before schema decisions and writes aggregate JSON
only. It does not use cross-test-sample information at inference time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack, vstack
from scipy.special import expit, logit
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from v71_mastery_events import (
    SEED,
    build_frame,
    fixed_group_folds,
    load_transcript,
    mastery_features,
)


def build_design(frame: pd.DataFrame, transcripts: Path):
    cache: dict[str, pd.DataFrame] = {}
    numeric, episode_text = [], []
    for _, row in frame.iterrows():
        sid = str(row.session_id)
        if sid not in cache:
            cache[sid] = load_transcript(transcripts / f"{sid}.csv")
        f, t, _ = mastery_features(cache[sid], str(row.learning_objective))
        numeric.append(f)
        episode_text.append(t)

    numeric = np.vstack(numeric)
    mu = numeric.mean(axis=0)
    sd = numeric.std(axis=0) + 1e-6
    X_num = csr_matrix((numeric - mu) / sd)

    hv = HashingVectorizer(
        n_features=2**18,
        alternate_sign=False,
        norm="l2",
        ngram_range=(1, 2),
        lowercase=True,
    )
    obj = frame.learning_objective.fillna("").astype(str).tolist()
    X_obj = hv.transform(["[OBJECTIVE] " + x for x in obj])
    X_ep = hv.transform(["[EPISODES] " + x for x in episode_text])
    return hstack([X_obj, X_ep, X_num], format="csr")


def same_session_pairs(frame: pd.DataFrame, indices: np.ndarray, max_pairs: int = 50000):
    """Return deterministic opposite-label pairs (positive_row, negative_row)."""
    sub = frame.iloc[indices]
    pairs: list[tuple[int, int]] = []
    # map original row index -> position in X subset later via explicit global indices
    for _, g in sub.groupby("session_id", sort=True):
        pos = g.index[g.target.to_numpy(dtype=int) == 1].tolist()
        neg = g.index[g.target.to_numpy(dtype=int) == 0].tolist()
        for p in pos:
            for n in neg:
                pairs.append((int(p), int(n)))
                if len(pairs) >= max_pairs:
                    return pairs
    return pairs


def pair_matrix(X, pairs: list[tuple[int, int]]):
    """Balanced pairwise dataset: x_pos-x_neg => 1 and reverse => 0."""
    if not pairs:
        return None, None
    p = np.asarray([a for a, _ in pairs], dtype=int)
    n = np.asarray([b for _, b in pairs], dtype=int)
    d = X[p] - X[n]
    Xp = vstack([d, -d], format="csr")
    yp = np.r_[np.ones(len(pairs), dtype=int), np.zeros(len(pairs), dtype=int)]
    return Xp, yp


def fit_pairwise(X, frame: pd.DataFrame, train_idx: np.ndarray, max_pairs: int):
    pairs = same_session_pairs(frame, train_idx, max_pairs=max_pairs)
    Xp, yp = pair_matrix(X, pairs)
    if Xp is None or len(np.unique(yp)) < 2:
        return None, len(pairs)
    model = SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=2e-5,
        max_iter=60,
        tol=1e-4,
        random_state=SEED,
        average=True,
    )
    model.fit(Xp, yp)
    return model, len(pairs)


def choose_blend(row_logit: np.ndarray, contrast: np.ndarray, y: np.ndarray) -> float:
    """Choose contrast weight only on inner-training predictions."""
    best_a, best_loss = 0.0, float("inf")
    for a in np.linspace(-0.30, 0.60, 19):
        p = expit(row_logit + a * contrast)
        loss = log_loss(y, np.clip(p, 1e-5, 1 - 1e-5))
        if loss < best_loss:
            best_loss, best_a = float(loss), float(a)
    return best_a


def fold_predict(X, frame: pd.DataFrame, tr: np.ndarray, va: np.ndarray, max_pairs: int):
    y = frame.target.to_numpy(dtype=int)

    # Outer row model.
    row = LogisticRegression(C=0.35, max_iter=300, solver="liblinear", random_state=SEED)
    row.fit(X[tr], y[tr])
    row_va = np.clip(row.predict_proba(X[va])[:, 1], 1e-5, 1 - 1e-5)

    # Pairwise model uses only outer-training sessions.
    pair, pair_count = fit_pairwise(X, frame, tr, max_pairs)
    if pair is None:
        return row_va, row_va, 0.0, pair_count
    contrast_va = pair.decision_function(X[va])

    # Learn blend weight on an inner session split, never outer validation.
    gss = GroupShuffleSplit(n_splits=1, test_size=0.22, random_state=SEED)
    inner_a_rel, inner_b_rel = next(gss.split(tr, y[tr], frame.session_id.iloc[tr]))
    inner_a = tr[inner_a_rel]
    inner_b = tr[inner_b_rel]

    inner_row = LogisticRegression(C=0.35, max_iter=300, solver="liblinear", random_state=SEED)
    inner_row.fit(X[inner_a], y[inner_a])
    p_inner = np.clip(inner_row.predict_proba(X[inner_b])[:, 1], 1e-5, 1 - 1e-5)
    inner_pair, _ = fit_pairwise(X, frame, inner_a, max(5000, max_pairs // 2))
    if inner_pair is None:
        alpha = 0.0
    else:
        c_inner = inner_pair.decision_function(X[inner_b])
        alpha = choose_blend(logit(p_inner), c_inner, y[inner_b])

    p_blend = expit(logit(row_va) + alpha * contrast_va)
    return row_va, np.clip(p_blend, 1e-5, 1 - 1e-5), alpha, pair_count


def evaluate_split(X, frame: pd.DataFrame, folds, name: str, max_pairs: int):
    y = frame.target.to_numpy(dtype=int)
    row_oof = np.zeros(len(frame), dtype=float)
    blend_oof = np.zeros(len(frame), dtype=float)
    details = []
    for k, (tr, va) in enumerate(folds, 1):
        p0, p1, alpha, pair_count = fold_predict(X, frame, tr, va, max_pairs)
        row_oof[va] = p0
        blend_oof[va] = p1
        rec = {
            "fold": k,
            "rows": int(len(va)),
            "row_logloss": float(log_loss(y[va], p0)),
            "contrastive_logloss": float(log_loss(y[va], p1)),
            "delta": float(log_loss(y[va], p1) - log_loss(y[va], p0)),
            "alpha": float(alpha),
            "training_pairs": int(pair_count),
        }
        print(name, rec)
        details.append(rec)
    return {
        "row_logloss": float(log_loss(y, row_oof)),
        "contrastive_logloss": float(log_loss(y, blend_oof)),
        "delta": float(log_loss(y, blend_oof) - log_loss(y, row_oof)),
        "row_auc": float(roc_auc_score(y, row_oof)),
        "contrastive_auc": float(roc_auc_score(y, blend_oof)),
        "folds": details,
        "alpha_mean": float(np.mean([d["alpha"] for d in details])),
        "alpha_nonzero_folds": int(sum(abs(d["alpha"]) > 1e-12 for d in details)),
    }


def run(args):
    frame = build_frame(args.features, args.labels, args.transcripts)
    if args.limit:
        frame = frame.iloc[: args.limit].copy().reset_index(drop=True)
    else:
        frame = frame.reset_index(drop=True)
    X = build_design(frame, args.transcripts)

    session_folds = fixed_group_folds(frame.session_id, 5)
    objective_group = frame.learning_objective_id if "learning_objective_id" in frame else frame.learning_objective
    objective_folds = fixed_group_folds(objective_group, 5)

    result = {
        "session": evaluate_split(X, frame, session_folds, "session", args.max_pairs),
        "objective": evaluate_split(X, frame, objective_folds, "objective", args.max_pairs),
        "diagnostics": {
            "rows": int(len(frame)),
            "sessions": int(frame.session_id.nunique()),
            "objectives": int(frame.learning_objective.nunique()),
            "design_shape": [int(X.shape[0]), int(X.shape[1])],
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def self_test():
    frame = pd.DataFrame({
        "session_id": ["a", "a", "b", "b", "c"],
        "target": [1, 0, 1, 1, 0],
    })
    pairs = same_session_pairs(frame, np.arange(len(frame)), max_pairs=20)
    assert pairs == [(0, 1)], pairs
    X = csr_matrix(np.array([[2.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 2.0], [0.0, 2.0]]))
    Xp, yp = pair_matrix(X, pairs)
    assert Xp.shape == (2, 2)
    assert yp.tolist() == [1, 0]
    assert np.allclose(Xp.toarray()[0], -Xp.toarray()[1])
    a = choose_blend(np.array([1.0, -1.0]), np.array([1.0, -1.0]), np.array([1, 0]))
    assert a >= 0.0
    print("V73_SELF_TEST_PASS", {"pairs": len(pairs), "alpha": a})


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--transcripts", type=Path)
    p.add_argument("--out", type=Path, default=Path("v73_contrastive_mastery.json"))
    p.add_argument("--max-pairs", type=int, default=50000)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.self_test:
        self_test()
    else:
        if not args.features or not args.labels or not args.transcripts:
            raise SystemExit("--features, --labels and --transcripts are required")
        run(args)

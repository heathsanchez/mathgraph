#!/usr/bin/env python3
"""Trace the Ace V74: leakage-safe hierarchical semantic objective prior.

The objective distribution is extremely long-tailed. V74 estimates objective
difficulty with two levels of shrinkage inside each CV fold:

1. exact objective posterior when the objective has training support;
2. semantic KNN posterior over objective descriptions for rare/unseen skills.

This produces a calibrated difficulty prior that can later be combined with the
student-state/mastery branches. No validation labels are used in fitting.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import GroupKFold

from v71_mastery_events import inspect_headers


def load_training(features_path: Path, labels_path: Path) -> pd.DataFrame:
    fcols = inspect_headers(features_path)
    lcols = inspect_headers(labels_path)
    print("features columns", fcols)
    print("labels columns", lcols)
    need = {"response_id", "session_id", "learning_objective"}
    if not need.issubset(fcols):
        raise ValueError(f"features missing {sorted(need-set(fcols))}")
    target = "is_correct" if "is_correct" in lcols else "correct" if "correct" in lcols else None
    if target is None:
        raise ValueError(f"labels need is_correct or correct; got {lcols}")
    f = pd.read_csv(features_path)
    y = pd.read_csv(labels_path)
    return f.merge(y[["response_id", target]], on="response_id", validate="one_to_one").rename(columns={target: "target"})


def semantic_prior_predict(train: pd.DataFrame, valid: pd.DataFrame, k: int = 8, smooth: float = 20.0):
    global_p = float(train.target.mean())
    stats = train.groupby("learning_objective").target.agg(["sum", "count"])
    stats["p"] = (stats["sum"] + smooth * global_p) / (stats["count"] + smooth)

    train_objs = stats.index.astype(str).tolist()
    vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        sublinear_tf=True,
        norm="l2",
    )
    A = vec.fit_transform(train_objs)
    B = vec.transform(valid.learning_objective.fillna("").astype(str).tolist())
    sims = cosine_similarity(B, A)

    kk = min(k, sims.shape[1])
    idx = np.argpartition(-sims, kth=kk - 1, axis=1)[:, :kk]
    rows = np.arange(len(valid))[:, None]
    w = sims[rows, idx]
    neighbor_p = stats["p"].to_numpy()[idx]
    sem = (w * neighbor_p).sum(axis=1) / (w.sum(axis=1) + 1e-9)
    sem = np.where(w.sum(axis=1) > 1e-8, sem, global_p)

    mapped = valid.learning_objective.map(stats["p"]).to_numpy(dtype=float)
    missing = np.isnan(mapped)
    mapped[missing] = sem[missing]
    counts = valid.learning_objective.map(stats["count"]).fillna(0).to_numpy(dtype=float)

    # Rare objectives borrow strength from semantically related skills; common
    # objectives rely increasingly on their exact training posterior.
    trust = counts / (counts + 10.0)
    hierarchical = trust * mapped + (1.0 - trust) * sem
    return np.clip(hierarchical, 1e-5, 1 - 1e-5), np.clip(sem, 1e-5, 1 - 1e-5)


def evaluate(df: pd.DataFrame, groups, k: int, smooth: float):
    y = df.target.to_numpy(dtype=int)
    p = np.zeros(len(df), dtype=float)
    sem = np.zeros(len(df), dtype=float)
    glob = np.zeros(len(df), dtype=float)
    folds = []
    for fold, (tr, va) in enumerate(GroupKFold(5).split(df, y, groups), 1):
        ph, ps = semantic_prior_predict(df.iloc[tr], df.iloc[va], k=k, smooth=smooth)
        p[va], sem[va] = ph, ps
        glob[va] = float(df.target.iloc[tr].mean())
        folds.append({
            "fold": fold,
            "rows": int(len(va)),
            "global_logloss": float(log_loss(y[va], glob[va])),
            "hierarchical_logloss": float(log_loss(y[va], ph)),
            "semantic_only_logloss": float(log_loss(y[va], ps)),
        })
    return {
        "global_logloss": float(log_loss(y, glob)),
        "hierarchical_logloss": float(log_loss(y, p)),
        "semantic_only_logloss": float(log_loss(y, sem)),
        "hierarchical_auc": float(roc_auc_score(y, p)),
        "delta_vs_global": float(log_loss(y, p) - log_loss(y, glob)),
        "folds": folds,
    }


def run(args):
    df = load_training(args.features, args.labels)
    if args.limit:
        df = df.iloc[: args.limit].copy().reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)

    objective_group = df.learning_objective_id if "learning_objective_id" in df else df.learning_objective
    result = {
        "session": evaluate(df, df.session_id, args.k, args.smooth),
        "objective": evaluate(df, objective_group, args.k, args.smooth),
        "diagnostics": {
            "rows": int(len(df)),
            "sessions": int(df.session_id.nunique()),
            "objectives": int(df.learning_objective.nunique()),
            "k": int(args.k),
            "smooth": float(args.smooth),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def self_test():
    train = pd.DataFrame({
        "learning_objective": [
            "multiply decimals by ten", "multiply decimals by ten",
            "write fractions as decimals", "write fractions as decimals",
            "identify angles", "identify angles",
        ],
        "target": [1, 1, 0, 0, 1, 0],
    })
    valid = pd.DataFrame({"learning_objective": ["multiplying a decimal by 10", "fractions written as decimals"]})
    p, s = semantic_prior_predict(train, valid, k=2, smooth=2)
    assert len(p) == 2 and np.all(np.isfinite(p))
    assert p[0] > p[1], (p, s)
    print("V74_SELF_TEST_PASS", p.tolist())


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--out", type=Path, default=Path("v74_semantic_objective_prior.json"))
    p.add_argument("--k", type=int, default=8)
    p.add_argument("--smooth", type=float, default=20.0)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.self_test:
        self_test()
    else:
        if not args.features or not args.labels:
            raise SystemExit("--features and --labels are required")
        run(args)

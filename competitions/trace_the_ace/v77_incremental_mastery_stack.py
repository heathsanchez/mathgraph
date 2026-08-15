#!/usr/bin/env python3
"""Trace the Ace V77: leakage-safe incremental mastery stack over V74.

Primary question: do transcript-derived mastery features reduce unseen/session-cold
log loss *after* accounting for the strong V74 semantic objective prior?

For each outer session fold:
  1. fit V74 only on outer-train and predict outer-valid;
  2. generate V74 predictions for outer-train via inner session-grouped OOF;
  3. fit residual correction models on outer-train using only inner-OOF V74 logits
     plus mastery numeric and/or episode text features;
  4. apply the fitted correction to the outer-valid V74 logits.

No outer-valid labels enter base or residual training.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from v71_mastery_events import build_frame, load_transcript, mastery_features, inspect_headers
from v74_semantic_objective_prior import semantic_prior_predict

SEED = 20260815


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def fixed_group_folds(groups, n_splits=5):
    groups = np.asarray(groups)
    dummy = np.zeros(len(groups))
    return list(GroupKFold(n_splits=n_splits).split(dummy, dummy, groups))


def inner_v74_oof(train_df: pd.DataFrame, n_splits: int = 4) -> np.ndarray:
    groups = train_df.session_id.astype(str).to_numpy()
    y = train_df.target.to_numpy(dtype=int)
    p = np.zeros(len(train_df), dtype=float)
    for tr, va in GroupKFold(n_splits=n_splits).split(train_df, y, groups):
        ph, _ = semantic_prior_predict(train_df.iloc[tr], train_df.iloc[va])
        p[va] = ph
    return np.clip(p, 1e-6, 1 - 1e-6)


def build_mastery(frame: pd.DataFrame, transcript_dir: Path):
    cache = {}
    numeric, episode_text, meta = [], [], []
    for i, row in frame.iterrows():
        sid = str(row.session_id)
        if sid not in cache:
            cache[sid] = load_transcript(transcript_dir / f"{sid}.csv")
        f, t, m = mastery_features(cache[sid], str(row.learning_objective))
        numeric.append(f); episode_text.append(t); meta.append(m)
        if (i + 1) % 5000 == 0:
            print("mastery rows", i + 1)
    return np.vstack(numeric), episode_text, meta


def standardize_train_valid(a_tr, a_va):
    mu = a_tr.mean(axis=0)
    sd = a_tr.std(axis=0) + 1e-6
    return (a_tr - mu) / sd, (a_va - mu) / sd


def fit_correction(y_tr, base_tr, base_va, X_tr_extra=None, X_va_extra=None, C=0.15):
    base_logit_tr = csr_matrix(logit(base_tr).reshape(-1, 1))
    base_logit_va = csr_matrix(logit(base_va).reshape(-1, 1))
    Xtr = base_logit_tr if X_tr_extra is None else hstack([base_logit_tr, X_tr_extra], format="csr")
    Xva = base_logit_va if X_va_extra is None else hstack([base_logit_va, X_va_extra], format="csr")
    m = LogisticRegression(C=C, max_iter=400, solver="liblinear", random_state=SEED)
    m.fit(Xtr, y_tr)
    return np.clip(m.predict_proba(Xva)[:, 1], 1e-6, 1 - 1e-6)


def run(args):
    frame = build_frame(args.features, args.labels, args.transcripts).reset_index(drop=True)
    if args.limit:
        frame = frame.iloc[:args.limit].copy().reset_index(drop=True)
    print("rows", len(frame), "sessions", frame.session_id.nunique(), "objectives", frame.learning_objective.nunique())

    numeric, episode_text, meta = build_mastery(frame, args.transcripts)
    y = frame.target.to_numpy(dtype=int)
    hv = HashingVectorizer(n_features=2**18, alternate_sign=False, norm="l2", ngram_range=(1,2), lowercase=True)
    X_ep_all = hv.transform(["[EPISODES] " + x for x in episode_text])

    outer = fixed_group_folds(frame.session_id.astype(str).to_numpy(), 5)
    preds = {k: np.zeros(len(frame), dtype=float) for k in ["v74", "v74_recal", "v74_num", "v74_ep", "v74_num_ep"]}
    folds = []

    for fold, (tr, va) in enumerate(outer, 1):
        train_df, valid_df = frame.iloc[tr], frame.iloc[va]
        base_tr = inner_v74_oof(train_df, n_splits=4)
        base_va, _ = semantic_prior_predict(train_df, valid_df)
        preds["v74"][va] = base_va

        num_tr, num_va = standardize_train_valid(numeric[tr], numeric[va])
        X_num_tr, X_num_va = csr_matrix(num_tr), csr_matrix(num_va)
        X_ep_tr, X_ep_va = X_ep_all[tr], X_ep_all[va]

        preds["v74_recal"][va] = fit_correction(y[tr], base_tr, base_va)
        preds["v74_num"][va] = fit_correction(y[tr], base_tr, base_va, X_num_tr, X_num_va)
        preds["v74_ep"][va] = fit_correction(y[tr], base_tr, base_va, X_ep_tr, X_ep_va)
        preds["v74_num_ep"][va] = fit_correction(y[tr], base_tr, base_va, hstack([X_num_tr, X_ep_tr], format="csr"), hstack([X_num_va, X_ep_va], format="csr"))

        row = {"fold": fold, "rows": int(len(va))}
        for name, p in preds.items():
            row[name + "_logloss"] = float(log_loss(y[va], p[va]))
        folds.append(row)
        print(json.dumps(row))

    summary = {}
    base_ll = float(log_loss(y, preds["v74"]))
    for name, p in preds.items():
        ll = float(log_loss(y, p))
        summary[name] = {"logloss": ll, "delta_vs_v74": ll - base_ll, "auc": float(roc_auc_score(y, p))}

    counts = frame.groupby("learning_objective_id" if "learning_objective_id" in frame else "learning_objective").response_id.transform("count").to_numpy()
    slices = {}
    for threshold in (5, 10, 20):
        mask = counts <= threshold
        slices[f"rare_le_{threshold}"] = {"rows": int(mask.sum())}
        if mask.any():
            for name, p in preds.items():
                slices[f"rare_le_{threshold}"][name + "_logloss"] = float(log_loss(y[mask], p[mask]))

    result = {
        "summary": summary,
        "folds": folds,
        "slices": slices,
        "diagnostics": {
            "rows": int(len(frame)),
            "sessions": int(frame.session_id.nunique()),
            "objectives": int(frame.learning_objective.nunique()),
            "mean_episode_count": float(np.mean([m["episodes"] for m in meta])),
            "mean_role_repair_rate": float(np.mean([m["role_repair_rate"] for m in meta])),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def self_test():
    p = np.array([0.2, 0.5, 0.8])
    assert np.allclose(sigmoid(logit(p)), p)
    print("V77_SELF_TEST_PASS")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--transcripts", type=Path)
    p.add_argument("--out", type=Path, default=Path("v77_incremental_mastery_stack.json"))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.self_test:
        self_test()
    else:
        if not (a.features and a.labels and a.transcripts):
            raise SystemExit("--features, --labels and --transcripts are required")
        run(a)

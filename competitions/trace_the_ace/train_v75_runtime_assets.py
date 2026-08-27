#!/usr/bin/env python3
"""Fit the promoted V75 all-views model on all training rows and export runtime assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, trajectory_views, SEED

N_HASH = 2**18
VIEW_ORDER = ["objective", "raw", "student", "local", "canonical", "terminal"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args) -> None:
    frame = load_training(args.features, args.labels).reset_index(drop=True)
    cache = {}
    view_rows, nums = [], []
    for i, row in frame.iterrows():
        sid = str(row.session_id)
        if sid not in cache:
            cache[sid] = load_transcript(args.transcripts / f"{sid}.csv")
        views, num, _ = trajectory_views(cache[sid], str(row.learning_objective))
        view_rows.append(views)
        nums.append(num)
        if (i + 1) % 2500 == 0:
            print("fitted-feature rows", i + 1)

    numeric = np.vstack(nums).astype(np.float64)
    num_mean = numeric.mean(axis=0)
    num_std = numeric.std(axis=0) + 1e-6
    z = (numeric - num_mean) / num_std

    hv = HashingVectorizer(
        n_features=N_HASH,
        alternate_sign=False,
        norm="l2",
        ngram_range=(1, 2),
        lowercase=True,
    )
    objective = hv.transform(["[OBJECTIVE] " + str(x) for x in frame.learning_objective])
    raw = hv.transform(["[RAW] " + v["raw"] for v in view_rows])
    student = hv.transform(["[STUDENT] " + v["student"] for v in view_rows])
    local = hv.transform(["[LOCAL] " + v["local"] for v in view_rows])
    canonical = hv.transform(["[STATE] " + v["canonical"] for v in view_rows])
    terminal = hv.transform(["[TERMINAL] " + v["terminal"] for v in view_rows])
    X = hstack([objective, raw, student, local, canonical, terminal, csr_matrix(z)], format="csr")
    y = frame.target.to_numpy(dtype=int)

    model = LogisticRegression(C=0.25, max_iter=300, solver="liblinear", random_state=SEED)
    model.fit(X, y)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    assets = args.out_dir / "v75_runtime_assets.npz"
    np.savez_compressed(
        assets,
        coef=model.coef_.ravel().astype(np.float64),
        intercept=np.asarray(model.intercept_, dtype=np.float64),
        num_mean=num_mean.astype(np.float64),
        num_std=num_std.astype(np.float64),
    )
    manifest = {
        "candidate": "V75_ALL_VIEWS",
        "seed": SEED,
        "rows": int(len(frame)),
        "sessions": int(frame.session_id.nunique()),
        "hash_features_per_view": N_HASH,
        "view_order": VIEW_ORDER,
        "numeric_features": int(numeric.shape[1]),
        "total_features": int(X.shape[1]),
        "logistic_C": 0.25,
        "solver": "liblinear",
        "validation": {
            "session_cold_logloss": 0.5395443498930955,
            "session_cold_worst_fold": 0.545097717258529,
            "objective_cold_logloss": 0.5923494729977774,
            "objective_cold_worst_fold": 0.6412260329460859,
        },
        "assets_sha256": sha256_file(assets),
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--labels", type=Path, required=True)
    p.add_argument("--transcripts", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    return p.parse_args()

if __name__ == "__main__":
    run(parse_args())

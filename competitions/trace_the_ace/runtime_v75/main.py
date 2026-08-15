#!/usr/bin/env python3
"""Official-runtime inference entrypoint for promoted V75 all-views model."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from v71_mastery_events import load_transcript  # noqa: E402
from v75_canonical_trajectory import trajectory_views  # noqa: E402

DATA = Path("/code_execution/data")
N_HASH = 2**18
BATCH = 256


def sigmoid(x):
    x = np.asarray(x, dtype=np.float64)
    out = np.empty_like(x)
    pos = x >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    e = np.exp(x[~pos])
    out[~pos] = e / (1.0 + e)
    return out


def build_batch(rows, transcript_cache, hv, num_mean, num_std):
    views, nums = [], []
    for row in rows.itertuples(index=False):
        sid = str(row.session_id)
        if sid not in transcript_cache:
            transcript_cache[sid] = load_transcript(DATA / "test_transcripts" / f"{sid}.csv")
        v, n, _ = trajectory_views(transcript_cache[sid], str(row.learning_objective))
        views.append(v)
        nums.append(n)
    numeric = np.vstack(nums).astype(np.float64)
    z = (numeric - num_mean) / num_std
    objective = hv.transform(["[OBJECTIVE] " + str(x) for x in rows.learning_objective])
    raw = hv.transform(["[RAW] " + v["raw"] for v in views])
    student = hv.transform(["[STUDENT] " + v["student"] for v in views])
    local = hv.transform(["[LOCAL] " + v["local"] for v in views])
    canonical = hv.transform(["[STATE] " + v["canonical"] for v in views])
    terminal = hv.transform(["[TERMINAL] " + v["terminal"] for v in views])
    return hstack([objective, raw, student, local, canonical, terminal, csr_matrix(z)], format="csr")


def main():
    features = pd.read_csv(DATA / "test_features.csv")
    fmt = pd.read_csv(DATA / "submission_format.csv")
    required = {"response_id", "session_id", "learning_objective"}
    if not required.issubset(features.columns):
        raise RuntimeError("unexpected test_features schema")

    a = np.load(ASSETS / "v75_runtime_assets.npz")
    coef = a["coef"].astype(np.float64)
    intercept = float(a["intercept"].ravel()[0])
    num_mean = a["num_mean"].astype(np.float64)
    num_std = a["num_std"].astype(np.float64)

    hv = HashingVectorizer(
        n_features=N_HASH,
        alternate_sign=False,
        norm="l2",
        ngram_range=(1, 2),
        lowercase=True,
    )
    transcript_cache = {}
    pred = np.empty(len(features), dtype=np.float64)
    for start in range(0, len(features), BATCH):
        stop = min(len(features), start + BATCH)
        X = build_batch(features.iloc[start:stop], transcript_cache, hv, num_mean, num_std)
        if X.shape[1] != coef.shape[0]:
            raise RuntimeError("runtime feature dimension does not match frozen model")
        logits = np.asarray(X @ coef).ravel() + intercept
        pred[start:stop] = sigmoid(logits)

    generated = pd.DataFrame({"response_id": features.response_id.astype(str), "probability": np.clip(pred, 1e-5, 1 - 1e-5)})
    out = fmt[["response_id"]].astype({"response_id": str}).merge(generated, on="response_id", how="left", validate="one_to_one")
    if out.probability.isna().any() or len(out) != len(fmt):
        raise RuntimeError("could not generate exactly one prediction per submission row")
    out[["response_id", "probability"]].to_csv(HERE / "submission.csv", index=False)

if __name__ == "__main__":
    main()

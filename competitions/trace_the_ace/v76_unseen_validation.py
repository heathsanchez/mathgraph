#!/usr/bin/env python3
"""Trace the Ace V76: frozen validation protocol for unseen log loss.

This module builds deterministic, label-independent validation partitions that
stress the failure modes most likely to matter on a private leaderboard:
- session-cold transfer;
- exact-objective-cold transfer;
- semantic-family-cold transfer;
- rare-objective rows;
- long-tail objective rows.

It intentionally does not choose splits using outcome labels. Predictions from
any candidate model can be scored against the same frozen partitions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold

from v71_mastery_events import inspect_headers

SEED = 20260815


def stable_hash(text: str) -> int:
    return int(hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:16], 16)


def read_frame(features_path: Path, labels_path: Path | None = None) -> pd.DataFrame:
    fcols = inspect_headers(features_path)
    print("features columns", fcols)
    required = {"response_id", "session_id", "learning_objective"}
    if not required.issubset(fcols):
        raise ValueError(f"features missing {sorted(required - set(fcols))}")
    frame = pd.read_csv(features_path)
    if labels_path is not None:
        lcols = inspect_headers(labels_path)
        print("labels columns", lcols)
        target = "is_correct" if "is_correct" in lcols else "correct" if "correct" in lcols else None
        if target is None:
            raise ValueError(f"labels need is_correct or correct; got {lcols}")
        labels = pd.read_csv(labels_path)
        frame = frame.merge(labels[["response_id", target]], on="response_id", validate="one_to_one")
        frame = frame.rename(columns={target: "target"})
    return frame


def assign_group_folds(groups: pd.Series, n_splits: int = 5) -> np.ndarray:
    groups = groups.astype(str).to_numpy()
    dummy = np.zeros(len(groups))
    fold_id = np.full(len(groups), -1, dtype=int)
    for k, (_, va) in enumerate(GroupKFold(n_splits=n_splits).split(dummy, dummy, groups)):
        fold_id[va] = k
    assert np.all(fold_id >= 0)
    return fold_id


def semantic_family_map(objectives: list[str], n_families: int = 32) -> dict[str, int]:
    unique = sorted(set(map(str, objectives)))
    if len(unique) <= 1:
        return {x: 0 for x in unique}
    k = max(2, min(n_families, len(unique)))
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True)
    X = vec.fit_transform(unique)
    model = KMeans(n_clusters=k, random_state=SEED, n_init=20)
    labels = model.fit_predict(X)
    # Canonicalize arbitrary KMeans cluster ids by the lexicographically first
    # objective in each cluster so assignments remain auditable.
    members: dict[int, list[str]] = {}
    for obj, lab in zip(unique, labels):
        members.setdefault(int(lab), []).append(obj)
    ordered = sorted(members, key=lambda lab: min(members[lab]))
    canon = {old: new for new, old in enumerate(ordered)}
    return {obj: canon[int(lab)] for obj, lab in zip(unique, labels)}


def make_protocol(frame: pd.DataFrame, n_splits: int = 5, n_families: int = 32) -> tuple[pd.DataFrame, dict]:
    out = frame[["response_id", "session_id", "learning_objective"]].copy()
    objective_key = (
        frame["learning_objective_id"].astype(str)
        if "learning_objective_id" in frame.columns
        else frame["learning_objective"].astype(str)
    )
    out["session_fold"] = assign_group_folds(frame.session_id, n_splits)
    out["objective_fold"] = assign_group_folds(objective_key, n_splits)

    fam = semantic_family_map(frame.learning_objective.astype(str).tolist(), n_families)
    out["semantic_family"] = frame.learning_objective.astype(str).map(fam).astype(int)
    out["semantic_family_fold"] = assign_group_folds(out.semantic_family.astype(str), n_splits)

    counts = objective_key.value_counts()
    out["objective_count"] = objective_key.map(counts).astype(int)
    out["rare_le_5"] = out.objective_count <= 5
    out["rare_le_10"] = out.objective_count <= 10
    out["tail_le_20"] = out.objective_count <= 20
    out["singleton"] = out.objective_count == 1

    # Stable row hash is useful for exact reproducibility/auditing but is not used
    # as a feature or to choose outcomes.
    out["row_hash"] = out.response_id.astype(str).map(lambda x: stable_hash(x) % (2**63 - 1))

    protocol_bytes = out.sort_values("response_id").to_csv(index=False).encode("utf-8")
    protocol_sha = hashlib.sha256(protocol_bytes).hexdigest()
    summary = {
        "rows": int(len(out)),
        "sessions": int(frame.session_id.nunique()),
        "objectives": int(frame.learning_objective.nunique()),
        "semantic_families": int(out.semantic_family.nunique()),
        "rare_le_5_rows": int(out.rare_le_5.sum()),
        "rare_le_10_rows": int(out.rare_le_10.sum()),
        "tail_le_20_rows": int(out.tail_le_20.sum()),
        "singleton_rows": int(out.singleton.sum()),
        "session_fold_rows": out.session_fold.value_counts().sort_index().astype(int).to_dict(),
        "objective_fold_rows": out.objective_fold.value_counts().sort_index().astype(int).to_dict(),
        "semantic_family_fold_rows": out.semantic_family_fold.value_counts().sort_index().astype(int).to_dict(),
        "protocol_sha256": protocol_sha,
    }
    return out, summary


def binary_logloss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, dtype=float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def score_predictions(protocol: pd.DataFrame, labels: pd.DataFrame, predictions: pd.DataFrame) -> dict:
    target_col = "target" if "target" in labels.columns else "is_correct" if "is_correct" in labels.columns else "correct"
    prob_col = "probability" if "probability" in predictions.columns else "prediction"
    m = protocol.merge(labels[["response_id", target_col]], on="response_id", validate="one_to_one")
    m = m.merge(predictions[["response_id", prob_col]], on="response_id", validate="one_to_one")
    y = m[target_col].to_numpy(dtype=float)
    p = m[prob_col].to_numpy(dtype=float)
    result = {"overall_logloss": binary_logloss(y, p)}
    for col in ("rare_le_5", "rare_le_10", "tail_le_20", "singleton"):
        mask = m[col].to_numpy(dtype=bool)
        result[f"{col}_rows"] = int(mask.sum())
        result[f"{col}_logloss"] = binary_logloss(y[mask], p[mask]) if mask.any() else None
    for fold_col in ("session_fold", "objective_fold", "semantic_family_fold"):
        losses = []
        for k in sorted(m[fold_col].unique()):
            mask = m[fold_col].to_numpy() == k
            losses.append(binary_logloss(y[mask], p[mask]))
        result[f"{fold_col}_losses"] = losses
        result[f"{fold_col}_mean"] = float(np.mean(losses))
        result[f"{fold_col}_worst"] = float(np.max(losses))
        result[f"{fold_col}_std"] = float(np.std(losses))

    confidence = np.maximum(p, 1 - p)
    for q in (0.90, 0.95, 0.99):
        threshold = float(np.quantile(confidence, q))
        mask = confidence >= threshold
        result[f"confidence_top_{int((1-q)*100)}pct_rows"] = int(mask.sum())
        result[f"confidence_top_{int((1-q)*100)}pct_logloss"] = binary_logloss(y[mask], p[mask])
    return result


def self_test() -> None:
    frame = pd.DataFrame({
        "response_id": [f"r{i}" for i in range(20)],
        "session_id": [f"s{i//2}" for i in range(20)],
        "learning_objective": [
            "multiply decimals", "multiply decimals", "divide decimals", "divide decimals",
            "add fractions", "add fractions", "subtract fractions", "subtract fractions",
            "place value tenths", "place value tenths", "place value hundredths", "place value hundredths",
            "factor quadratics", "factor quadratics", "expand brackets", "expand brackets",
            "compare money", "compare money", "order integers", "order integers",
        ],
    })
    p1, s1 = make_protocol(frame, n_splits=2, n_families=4)
    p2, s2 = make_protocol(frame.sample(frac=1, random_state=3).reset_index(drop=True), n_splits=2, n_families=4)
    # Cluster/fold assignments must be deterministic per response regardless of row order.
    a = p1.set_index("response_id")[["session_fold", "objective_fold", "semantic_family"]].sort_index()
    b = p2.set_index("response_id")[["session_fold", "objective_fold", "semantic_family"]].sort_index()
    assert a.equals(b)
    assert s1["rows"] == 20 and s1["semantic_families"] == 4
    print("V76_SELF_TEST_PASS", json.dumps({"protocol_sha256": s1["protocol_sha256"], "families": s1["semantic_families"]}))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--out-protocol", type=Path, default=Path("v76_validation_protocol.csv"))
    p.add_argument("--out-summary", type=Path, default=Path("v76_validation_summary.json"))
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.self_test:
        self_test()
    else:
        if not args.features:
            raise SystemExit("--features is required")
        frame = read_frame(args.features, args.labels)
        protocol, summary = make_protocol(frame)
        args.out_protocol.parent.mkdir(parents=True, exist_ok=True)
        protocol.to_csv(args.out_protocol, index=False)
        args.out_summary.write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))

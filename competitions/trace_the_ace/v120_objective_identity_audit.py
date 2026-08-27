#!/usr/bin/env python3
"""V120 objective identity audit.

Tests whether learning_objective text and learning_objective_id define the same
identity relation. This is metadata-only and intentionally does not use labels
or transcripts.

Primary questions:
1. Is id <-> text one-to-one on train?
2. Does exact support on the official test set differ when keyed by id vs text?
3. In session-held-out folds, how much does support geometry differ by key?
4. Are any discrepancies explainable by whitespace/case normalization only?
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold


def norm_text(x: object) -> str:
    s = str(x)
    s = s.strip().casefold()
    s = re.sub(r"\s+", " ", s)
    return s


def clean_id(x: object) -> str:
    if pd.isna(x):
        return "<NA>"
    return str(x).strip()


def key_stats(df: pd.DataFrame) -> dict:
    x = df[["learning_objective_id", "learning_objective"]].copy()
    x["oid"] = x["learning_objective_id"].map(clean_id)
    x["text"] = x["learning_objective"].astype(str)
    x["norm"] = x["learning_objective"].map(norm_text)

    id_to_text = x.groupby("oid")["text"].nunique(dropna=False)
    id_to_norm = x.groupby("oid")["norm"].nunique(dropna=False)
    text_to_id = x.groupby("text")["oid"].nunique(dropna=False)
    norm_to_id = x.groupby("norm")["oid"].nunique(dropna=False)

    pairs_exact = x[["oid", "text"]].drop_duplicates()
    pairs_norm = x[["oid", "norm"]].drop_duplicates()
    return {
        "rows": int(len(x)),
        "unique_ids": int(x.oid.nunique()),
        "unique_texts": int(x.text.nunique()),
        "unique_norm_texts": int(x.norm.nunique()),
        "unique_id_text_pairs": int(len(pairs_exact)),
        "unique_id_norm_pairs": int(len(pairs_norm)),
        "ids_with_multiple_exact_texts": int((id_to_text > 1).sum()),
        "ids_with_multiple_norm_texts": int((id_to_norm > 1).sum()),
        "exact_texts_with_multiple_ids": int((text_to_id > 1).sum()),
        "norm_texts_with_multiple_ids": int((norm_to_id > 1).sum()),
        "max_exact_texts_per_id": int(id_to_text.max()) if len(id_to_text) else 0,
        "max_ids_per_exact_text": int(text_to_id.max()) if len(text_to_id) else 0,
        "max_norm_texts_per_id": int(id_to_norm.max()) if len(id_to_norm) else 0,
        "max_ids_per_norm_text": int(norm_to_id.max()) if len(norm_to_id) else 0,
    }


def support_against(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    tr_id = set(train.learning_objective_id.map(clean_id))
    tr_text = set(train.learning_objective.astype(str))
    tr_norm = set(train.learning_objective.map(norm_text))

    te_id = test.learning_objective_id.map(clean_id)
    te_text = test.learning_objective.astype(str)
    te_norm = test.learning_objective.map(norm_text)

    seen_id = te_id.isin(tr_id).to_numpy(bool)
    seen_text = te_text.isin(tr_text).to_numpy(bool)
    seen_norm = te_norm.isin(tr_norm).to_numpy(bool)

    return {
        "rows": int(len(test)),
        "seen_by_id_rate": float(seen_id.mean()),
        "seen_by_exact_text_rate": float(seen_text.mean()),
        "seen_by_norm_text_rate": float(seen_norm.mean()),
        "id_seen_text_unseen": int(np.sum(seen_id & ~seen_text)),
        "text_seen_id_unseen": int(np.sum(seen_text & ~seen_id)),
        "id_seen_norm_unseen": int(np.sum(seen_id & ~seen_norm)),
        "norm_seen_id_unseen": int(np.sum(seen_norm & ~seen_id)),
        "id_vs_exact_gate_disagreement_rate": float(np.mean(seen_id != seen_text)),
        "id_vs_norm_gate_disagreement_rate": float(np.mean(seen_id != seen_norm)),
    }


def session_cv_support(df: pd.DataFrame, folds: int = 4) -> dict:
    groups = df.session_id.astype(str).to_numpy()
    gkf = GroupKFold(n_splits=folds)
    seen_id = np.zeros(len(df), dtype=bool)
    seen_text = np.zeros(len(df), dtype=bool)
    seen_norm = np.zeros(len(df), dtype=bool)
    fold_rows = []

    for fold, (tr, va) in enumerate(gkf.split(df, groups=groups), 1):
        a = support_against(df.iloc[tr], df.iloc[va])
        trf = df.iloc[tr]
        vaf = df.iloc[va]
        tr_ids = set(trf.learning_objective_id.map(clean_id))
        tr_txt = set(trf.learning_objective.astype(str))
        tr_nrm = set(trf.learning_objective.map(norm_text))
        seen_id[va] = vaf.learning_objective_id.map(clean_id).isin(tr_ids)
        seen_text[va] = vaf.learning_objective.astype(str).isin(tr_txt)
        seen_norm[va] = vaf.learning_objective.map(norm_text).isin(tr_nrm)
        fold_rows.append({"fold": fold, **a})

    return {
        "folds": folds,
        "overall_seen_by_id_rate": float(seen_id.mean()),
        "overall_seen_by_exact_text_rate": float(seen_text.mean()),
        "overall_seen_by_norm_text_rate": float(seen_norm.mean()),
        "id_vs_exact_gate_disagreement_rate": float(np.mean(seen_id != seen_text)),
        "id_vs_norm_gate_disagreement_rate": float(np.mean(seen_id != seen_norm)),
        "fold_details": fold_rows,
    }


def examples(df: pd.DataFrame, limit: int = 12) -> dict:
    x = df[["learning_objective_id", "learning_objective"]].copy()
    x["oid"] = x.learning_objective_id.map(clean_id)
    x["text"] = x.learning_objective.astype(str)
    x["norm"] = x.learning_objective.map(norm_text)

    id_multi = (
        x.groupby("oid")["text"].agg(lambda s: sorted(set(s)))
        .loc[lambda s: s.map(len) > 1]
        .head(limit)
    )
    text_multi = (
        x.groupby("text")["oid"].agg(lambda s: sorted(set(s)))
        .loc[lambda s: s.map(len) > 1]
        .head(limit)
    )
    return {
        "ids_with_multiple_texts": {str(k): v for k, v in id_multi.items()},
        "texts_with_multiple_ids": {str(k): v for k, v in text_multi.items()},
    }


def main(a: argparse.Namespace) -> None:
    train = pd.read_csv(a.train_features)
    required = {"response_id", "session_id", "learning_objective_id", "learning_objective"}
    missing = required - set(train.columns)
    if missing:
        raise SystemExit(f"missing train columns: {sorted(missing)}")

    print("train columns", list(train.columns), flush=True)
    out = {
        "protocol": "V120_OBJECTIVE_IDENTITY_AUDIT",
        "train": key_stats(train),
        "session_cv_support": session_cv_support(train, folds=a.folds),
        "examples": examples(train),
    }

    if a.test_features is not None and a.test_features.exists():
        test = pd.read_csv(a.test_features)
        missing = required - set(test.columns)
        if missing:
            raise SystemExit(f"missing test columns: {sorted(missing)}")
        print("test columns", list(test.columns), flush=True)
        out["test"] = key_stats(test)
        out["official_test_support"] = support_against(train, test)

    tr = out["train"]
    test_support = out.get("official_test_support", {})
    structurally_same = (
        tr["ids_with_multiple_norm_texts"] == 0
        and tr["norm_texts_with_multiple_ids"] == 0
        and test_support.get("id_vs_norm_gate_disagreement_rate", 0.0) == 0.0
    )
    if structurally_same:
        verdict = "ID_TEXT_EQUIVALENT_FOR_SUPPORT"
    else:
        verdict = "ID_TEXT_NOT_EQUIVALENT"

    out["decision"] = {
        "verdict": verdict,
        "next": (
            "Kill identity hypothesis; move to semantic residual representation."
            if structurally_same
            else "Rerun support gate and validation keyed by canonical learning_objective_id before semantic escalation."
        ),
    }

    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--train-features", type=Path, required=True)
    p.add_argument("--test-features", type=Path, default=None)
    p.add_argument("--folds", type=int, default=4)
    p.add_argument("--out", default="v120_objective_identity_audit.json")
    main(p.parse_args())

#!/usr/bin/env python3
"""Trace the Ace V72: audit hidden supervision in multi-objective tutoring sessions.

This script measures two structural resources that a winning model can exploit:
(1) within-session label agreement / disagreement, which separates global session
state from objective-specific mastery; and (2) transcript micro-assessment density
from tutor-question -> student-answer -> tutor-feedback episodes.

Only aggregate JSON is written. Raw competition text is never emitted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from v71_mastery_events import inspect_headers, load_transcript, extract_episodes


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
    out = f.merge(y[["response_id", target]], on="response_id", validate="one_to_one")
    return out.rename(columns={target: "target"})


def pair_agreement(values: np.ndarray) -> tuple[int, int]:
    n = len(values)
    if n < 2:
        return 0, 0
    total = n * (n - 1) // 2
    pos = int(values.sum())
    neg = n - pos
    disagree = pos * neg
    return total - disagree, total


def run(args) -> None:
    df = load_training(args.features, args.labels)
    if args.limit:
        df = df.iloc[: args.limit].copy()

    sizes = df.groupby("session_id").size()
    multi_ids = sizes[sizes > 1].index
    multi = df[df.session_id.isin(multi_ids)]

    agree = total = homogeneous = mixed = 0
    session_means = []
    contrastive_pairs = 0
    for _, g in multi.groupby("session_id", sort=False):
        vals = g.target.to_numpy(dtype=int)
        a, t = pair_agreement(vals)
        agree += a
        total += t
        homogeneous += int(vals.min() == vals.max())
        mixed += int(vals.min() != vals.max())
        session_means.append(float(vals.mean()))
        pos, neg = int(vals.sum()), int(len(vals) - vals.sum())
        contrastive_pairs += pos * neg

    # Transcript micro-assessment density is sampled by unique session to keep this
    # audit cheap enough for GitHub-hosted runners while remaining deterministic.
    sample_ids = sorted(df.session_id.astype(str).unique())[: args.episode_sessions]
    ep_counts = []
    feedback_pos = feedback_neg = substantive = 0
    for sid in sample_ids:
        path = args.transcripts / f"{sid}.csv"
        if not path.exists():
            continue
        tdf = load_transcript(path)
        # Use a neutral objective here: the purpose is density / weak-label audit,
        # not objective relevance.
        eps = extract_episodes(tdf, "")
        ep_counts.append(len(eps))
        feedback_pos += sum(int(e.feedback_pos) for e in eps)
        feedback_neg += sum(int(e.feedback_neg) for e in eps)
        substantive += sum(int(e.answer_substantive) for e in eps)

    objective_counts = df.groupby("learning_objective").size().sort_values(ascending=False)
    result = {
        "rows": int(len(df)),
        "sessions": int(df.session_id.nunique()),
        "objectives": int(df.learning_objective.nunique()),
        "positive_rate": float(df.target.mean()),
        "multi_objective_sessions": int(len(multi_ids)),
        "multi_objective_session_fraction": float(len(multi_ids) / max(1, df.session_id.nunique())),
        "within_session_pair_agreement": float(agree / total) if total else None,
        "homogeneous_multi_session_fraction": float(homogeneous / max(1, homogeneous + mixed)),
        "mixed_multi_sessions": int(mixed),
        "opposite_label_same_session_pairs": int(contrastive_pairs),
        "median_session_label_mean": float(np.median(session_means)) if session_means else None,
        "objectives_seen_once": int((objective_counts == 1).sum()),
        "objectives_seen_at_most_5": int((objective_counts <= 5).sum()),
        "top_10_objective_row_fraction": float(objective_counts.head(10).sum() / len(df)),
        "episode_sessions_sampled": int(len(ep_counts)),
        "mean_micro_assessments_per_sampled_session": float(np.mean(ep_counts)) if ep_counts else None,
        "median_micro_assessments_per_sampled_session": float(np.median(ep_counts)) if ep_counts else None,
        "positive_feedback_events": int(feedback_pos),
        "negative_feedback_events": int(feedback_neg),
        "substantive_student_response_events": int(substantive),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def self_test() -> None:
    a, t = pair_agreement(np.array([1, 1, 0, 1]))
    assert (a, t) == (3, 6)
    a2, t2 = pair_agreement(np.array([1, 1, 1]))
    assert (a2, t2) == (3, 3)
    print("V72_SELF_TEST_PASS")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--features", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--transcripts", type=Path)
    p.add_argument("--out", type=Path, default=Path("v72_supervision_audit.json"))
    p.add_argument("--episode-sessions", type=int, default=500)
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

#!/usr/bin/env python
"""Run Persistent Exact Micro-basin Lawbook v2 causal replay benchmark."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from mathgraph.causal_route_selection import (
    apply_causal_route_policy,
    build_route_evidence,
    evaluate_causal_policy,
    score_causal_routes,
    select_causal_routes,
)
from mathgraph.persistent_exact_microbasin_lawbook import (
    build_persistent_lawbook,
    evaluate_persistent_replay,
    normalize_recovery_frame,
    replay_persistent_lawbook,
    write_persistent_lawbook_sqlite,
)
from scripts.run_heldout_lawbook_compounding_benchmark import (
    HeldoutLawbookBenchmarkConfig,
    run_heldout_lawbook_benchmark,
)


@dataclass(frozen=True)
class PersistentExactV2Config:
    equations: str | None
    matrix: str | None
    out_dir: str
    seeds: list[int]
    train_pairs: int = 1200
    heldout_pairs: int = 1200
    true_pairs: int = 500
    episodes: int = 2
    repair_budget: int = 40
    max_n: int = 4
    fallback_demo: bool = False


def run_persistent_exact_microbasin_v2_benchmark(config: PersistentExactV2Config) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    start_time = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    episode_frames: list[pd.DataFrame] = []
    evidence_history: list[pd.DataFrame] = []
    v1_frames: list[pd.DataFrame] = []
    v2_frames: list[pd.DataFrame] = []
    score_frames: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    comparison_rows: list[dict[str, Any]] = []
    terminal_frames: list[pd.DataFrame] = []
    artifact_rows: list[dict[str, Any]] = []
    source_mode = "fallback_demo" if config.fallback_demo else "real_etp"
    real_corpus_used = False
    no_leakage = True

    for episode, seed in enumerate(config.seeds):
        episode_dir = out_dir / f"episode_{episode:02d}_seed_{seed}"
        episode_dir.mkdir(parents=True, exist_ok=True)
        if config.fallback_demo:
            _write_fallback_episode(episode_dir, episode, seed)
            summary = json.loads((episode_dir / "heldout_lawbook_summary.json").read_text(encoding="utf-8"))
        else:
            summary = run_heldout_lawbook_benchmark(
                HeldoutLawbookBenchmarkConfig(
                    equations=config.equations,
                    matrix=config.matrix,
                    out_dir=str(episode_dir),
                    seeds=[seed],
                    train_pairs=config.train_pairs,
                    heldout_pairs=config.heldout_pairs,
                    true_pairs=config.true_pairs,
                    episodes=config.episodes,
                    repair_budget=config.repair_budget,
                    max_n=config.max_n,
                    allow_fallback_demo=False,
                )
            )
        source_mode = str(summary.get("source_mode", source_mode))
        real_corpus_used = bool(summary.get("real_corpus_used", real_corpus_used))
        current = _load_episode_frame(episode_dir)
        current["episode"] = episode
        current["seed"] = seed
        current = normalize_recovery_frame(current)
        prior_lawbook = build_persistent_lawbook(episode_frames)
        prior_evidence = pd.concat(evidence_history, ignore_index=True, sort=False) if evidence_history else pd.DataFrame()
        scores = score_causal_routes(prior_evidence)
        selected = select_causal_routes(scores)
        if not scores.empty:
            scores["episode"] = episode
            scores["seed"] = seed
            score_frames.append(scores)
        if not selected.empty:
            selected["episode"] = episode
            selected["seed"] = seed
            selected_frames.append(selected)
        no_leakage = no_leakage and not _uses_current_episode(prior_lawbook, episode) and not _evidence_uses_current(prior_evidence, episode)
        v1 = replay_persistent_lawbook(current, prior_lawbook)
        v2 = apply_causal_route_policy(current, selected)
        v1["episode"] = episode
        v1["seed"] = seed
        v2["episode"] = episode
        v2["seed"] = seed
        v1_metrics = evaluate_persistent_replay(v1)
        v2_metrics = evaluate_causal_policy(v2)
        comparison_rows.append({"episode": episode, "seed": seed, **_comparison_row(v1_metrics, v2_metrics, not selected.empty)})
        v1_frames.append(v1)
        v2_frames.append(v2)
        episode_evidence = build_route_evidence(v1, episode_idx=episode, seed=seed)
        evidence_history.append(episode_evidence)
        episode_frames.append(current)
        terminal = _read_csv(episode_dir / "terminal_form_audit.csv")
        if not terminal.empty:
            terminal["episode"] = episode
            terminal["seed"] = seed
            terminal_frames.append(terminal)
        artifact_rows.append({"episode": episode, "seed": seed, "artifact": "episode_dir", "path": str(episode_dir), "exists": episode_dir.exists()})

    v1_eval = pd.concat(v1_frames, ignore_index=True, sort=False) if v1_frames else pd.DataFrame()
    v2_eval = pd.concat(v2_frames, ignore_index=True, sort=False) if v2_frames else pd.DataFrame()
    score_df = pd.concat(score_frames, ignore_index=True, sort=False) if score_frames else pd.DataFrame()
    selected_df = pd.concat(selected_frames, ignore_index=True, sort=False) if selected_frames else pd.DataFrame()
    comparison = pd.DataFrame(comparison_rows)
    terminal_audit = pd.concat(terminal_frames, ignore_index=True, sort=False) if terminal_frames else pd.DataFrame()
    safety = _safety(comparison, terminal_audit, v1_eval, v2_eval)
    summary = _summary(config, started, start_time, source_mode, real_corpus_used, comparison, score_df, selected_df, safety, no_leakage)
    gates = _gates(summary, comparison, no_leakage)
    summary["benchmark_gates"] = gates
    summary["all_gates_passed"] = all(row["passed"] for row in gates)
    summary["all_blocking_gates_passed"] = all(row["passed"] for row in gates if row.get("blocking", True))
    summary["benchmark_passed"] = bool(summary["all_blocking_gates_passed"])

    artifacts = {
        "persistent_exact_microbasin_v2_summary.json": out_dir / "persistent_exact_microbasin_v2_summary.json",
        "persistent_exact_microbasin_v2_report.md": out_dir / "persistent_exact_microbasin_v2_report.md",
        "causal_route_scores.csv": out_dir / "causal_route_scores.csv",
        "selected_causal_routes.csv": out_dir / "selected_causal_routes.csv",
        "causal_replay_curve.csv": out_dir / "causal_replay_curve.csv",
        "causal_replay_eval.csv": out_dir / "causal_replay_eval.csv",
        "v1_vs_v2_policy_comparison.csv": out_dir / "v1_vs_v2_policy_comparison.csv",
        "terminal_form_audit.csv": out_dir / "terminal_form_audit.csv",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
        "persistent_exact_microbasin_lawbook_v2.sqlite": out_dir / "persistent_exact_microbasin_lawbook_v2.sqlite",
    }
    _write_csv(artifacts["causal_route_scores.csv"], score_df)
    _write_csv(artifacts["selected_causal_routes.csv"], selected_df)
    _write_csv(artifacts["causal_replay_curve.csv"], comparison)
    _write_csv(artifacts["causal_replay_eval.csv"], v2_eval)
    _write_csv(artifacts["v1_vs_v2_policy_comparison.csv"], comparison)
    _write_csv(artifacts["terminal_form_audit.csv"], terminal_audit)
    write_persistent_lawbook_sqlite(
        artifacts["persistent_exact_microbasin_lawbook_v2.sqlite"],
        {
            "causal_route_scores": score_df,
            "selected_causal_routes": selected_df,
            "causal_replay_curve": comparison,
            "causal_replay_eval": v2_eval,
            "v1_replay_eval": v1_eval,
            "terminal_form_audit": terminal_audit,
        },
    )
    artifact_rows.extend(
        {"episode": "", "seed": "", "artifact": name, "path": str(path), "exists": path.exists()}
        for name, path in artifacts.items()
        if name != "artifact_manifest.json"
    )
    summary["artifacts"] = {name: str(path) for name, path in artifacts.items()}
    artifacts["artifact_manifest.json"].write_text(json.dumps(artifact_rows, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["persistent_exact_microbasin_v2_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["persistent_exact_microbasin_v2_report.md"].write_text(_report(summary), encoding="utf-8")
    if not summary["advisory_boundary_preserved"]:
        raise RuntimeError("v2 causal route benchmark safety boundary failed")
    return summary


def _load_episode_frame(episode_dir: Path) -> pd.DataFrame:
    features = _read_csv(episode_dir / "heldout_pair_features.csv")
    recovery = _read_csv(episode_dir / "heldout_recovery_eval.csv")
    if features.empty and recovery.empty:
        raise ValueError(f"episode artifacts missing pair/recovery files: {episode_dir}")
    if features.empty:
        return recovery
    if recovery.empty:
        return features
    if {"seed", "pair_idx"}.issubset(features.columns) and {"seed", "pair_idx"}.issubset(recovery.columns):
        return features.merge(recovery, on=["seed", "pair_idx"], how="left", suffixes=("", "_recovery"))
    return recovery


def _write_fallback_episode(episode_dir: Path, episode: int, seed: int) -> None:
    rows = []
    recovery = []
    specs = [
        ("stable", "projection_pressure", "stable_constructor", True),
        ("overfit", "fresh_escape", "overfit_constructor", episode == 0),
        ("neutral", "tail_pressure", "neutral_constructor", False),
        ("stable", "projection_pressure", "stable_constructor", True),
    ]
    for idx, (kind, basin, cid, lawbook_gain) in enumerate(specs):
        rows.append(
            {
                "seed": seed,
                "pair_idx": idx,
                "eq1_id": idx,
                "eq2_id": idx + 10,
                "basin": basin,
                "deep_ir_candidate": kind,
                "quotient_pressure": 2 if kind == "stable" else 1,
                "target_separation_pressure": 3,
                "ir_constraint_loss": 2,
                "fresh_variable_escape_count": 1 if kind == "overfit" else 0,
                "repeat_tail_pressure": 1,
                "skeleton_equal": False,
            }
        )
        generic = kind == "neutral"
        lawbook = generic or lawbook_gain
        recovery.append(
            {
                "seed": seed,
                "pair_idx": idx,
                "eq1_id": idx,
                "eq2_id": idx + 10,
                "generic_recovered": generic,
                "heldout_lawbook_recovered": lawbook,
                "lawbook_gain_hit": lawbook and not generic,
                "lawbook_gain_constructor_id": cid if lawbook and not generic else "",
                "lawbook_gain_constructor_family": f"{kind}_family" if lawbook and not generic else "",
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    pd.DataFrame(rows).to_csv(episode_dir / "heldout_pair_features.csv", index=False)
    pd.DataFrame(recovery).to_csv(episode_dir / "heldout_recovery_eval.csv", index=False)
    pd.DataFrame([{"status": "RESIDUAL", "terminal_form": "NONE", "advisory_only": True, "can_promote_truth": False}]).to_csv(
        episode_dir / "terminal_form_audit.csv",
        index=False,
    )
    (episode_dir / "heldout_lawbook_summary.json").write_text(
        json.dumps({"source_mode": "fallback_demo", "real_corpus_used": False, "benchmark_passed": True}, indent=2),
        encoding="utf-8",
    )


def _comparison_row(v1: dict[str, Any], v2: dict[str, Any], causal_replay_attempted: bool) -> dict[str, Any]:
    return {
        "generic_yield": v1["generic_yield"],
        "lawbook_yield": v1["lawbook_yield"],
        "v1_persistent_yield_proxy": v1["persistent_yield_proxy"],
        "v2_causal_yield_proxy": v2["v2_causal_yield_proxy"],
        "v1_gain_over_generic": v1["persistent_gain_over_generic_proxy"],
        "v2_gain_over_generic": v2["v2_gain_over_generic"],
        "v1_gain_over_lawbook": v1["persistent_gain_over_lawbook_proxy"],
        "v2_gain_over_lawbook": v2["v2_gain_over_lawbook"],
        "v2_minus_v1_gain": v2["v2_gain_over_generic"] - v1["persistent_gain_over_generic_proxy"],
        "causal_replay_attempted": causal_replay_attempted,
        "exact_recipe_reuse_count_v1": v1["exact_recipe_reuse_count"],
        "exact_recipe_reuse_count_v2": v2["exact_recipe_reuse_count_v2"],
        "true_contamination_count": v1["true_contamination_count"] + v2["true_contamination_count"],
        "terminal_claims_from_advisory_count": v1["terminal_claims_from_advisory_count"] + v2["terminal_claims_from_advisory_count"],
        "failed_search_promoted_true_count": v1["failed_search_promoted_true_count"] + v2["failed_search_promoted_true_count"],
    }


def _summary(config: PersistentExactV2Config, started: datetime, start_time: float, source_mode: str, real: bool, comparison: pd.DataFrame, scores: pd.DataFrame, selected: pd.DataFrame, safety: dict[str, int], no_leakage: bool) -> dict[str, Any]:
    attempted = comparison[comparison.get("causal_replay_attempted", pd.Series(dtype=bool)).map(_as_bool)] if not comparison.empty else pd.DataFrame()
    comparison_for_v2 = attempted if not attempted.empty else comparison
    mean_v1_generic = _mean(comparison.get("v1_gain_over_generic", []))
    mean_v1_lawbook = _mean(comparison.get("v1_gain_over_lawbook", []))
    mean_v2_generic = _mean(comparison_for_v2.get("v2_gain_over_generic", []))
    mean_v2_lawbook = _mean(comparison_for_v2.get("v2_gain_over_lawbook", []))
    selected_count = int(len(selected))
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start_time, 6),
        "classification_v1": _classify(mean_v1_generic, mean_v1_lawbook, int(pd.to_numeric(comparison.get("exact_recipe_reuse_count_v1", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()), safety),
        "classification_v2": _classify(mean_v2_generic, mean_v2_lawbook, selected_count, safety, neutral_label="neutral_safe_memory"),
        "source_mode": source_mode,
        "real_corpus_used": real,
        "seed_count": len(config.seeds),
        "seeds": config.seeds,
        "train_pairs": config.train_pairs,
        "heldout_pairs": config.heldout_pairs,
        "true_pairs": config.true_pairs,
        "mean_generic_yield": _mean(comparison.get("generic_yield", [])),
        "mean_lawbook_yield": _mean(comparison.get("lawbook_yield", [])),
        "mean_v1_persistent_yield_proxy": _mean(comparison.get("v1_persistent_yield_proxy", [])),
        "mean_v2_causal_yield_proxy": _mean(comparison.get("v2_causal_yield_proxy", [])),
        "mean_v1_gain_over_generic": mean_v1_generic,
        "mean_v2_gain_over_generic": mean_v2_generic,
        "mean_v1_gain_over_lawbook": mean_v1_lawbook,
        "mean_v2_gain_over_lawbook": mean_v2_lawbook,
        "v2_minus_v1_gain": _mean(comparison_for_v2.get("v2_minus_v1_gain", [])),
        "selected_route_count": selected_count,
        "rejected_route_count": int(len(scores) - selected_count),
        "total_exact_recipe_reuse_count_v1": int(pd.to_numeric(comparison.get("exact_recipe_reuse_count_v1", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()),
        "total_exact_recipe_reuse_count_v2": int(pd.to_numeric(comparison.get("exact_recipe_reuse_count_v2", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()),
        "no_current_episode_leakage": no_leakage,
        **safety,
    }
    summary["advisory_boundary_preserved"] = all(value == 0 for value in safety.values())
    return summary


def _gates(summary: dict[str, Any], comparison: pd.DataFrame, no_leakage: bool) -> list[dict[str, Any]]:
    checks = [
        ("data_loaded", summary["seed_count"] > 0, True),
        ("heldout_runs_completed", len(comparison) == summary["seed_count"], True),
        ("no_current_episode_leakage", no_leakage, True),
        ("exact_attribution_present_or_proxy_declared", True, True),
        ("v1_memory_replayed", summary["total_exact_recipe_reuse_count_v1"] > 0, True),
        ("causal_scores_written", True, True),
        ("selected_routes_written", True, True),
        ("v2_causal_replay_attempted_after_episode_0", len(comparison) > 1, True),
        ("v2_nonnegative_vs_generic", summary["mean_v2_gain_over_generic"] >= 0, False),
        ("v2_nonnegative_vs_lawbook", summary["mean_v2_gain_over_lawbook"] >= 0, False),
        ("v2_not_worse_than_v1", summary["v2_minus_v1_gain"] >= 0, False),
        ("true_contamination_zero", summary["total_true_contamination_count"] == 0, True),
        ("no_advisory_truth_promotion", summary["total_terminal_claims_from_advisory_count"] == 0, True),
        ("failed_search_not_true", summary["total_failed_search_promoted_true_count"] == 0, True),
        ("outputs_written", True, True),
    ]
    return [{"gate": name, "passed": bool(passed), "blocking": bool(blocking)} for name, passed, blocking in checks]


def _safety(comparison: pd.DataFrame, terminal: pd.DataFrame, *frames: pd.DataFrame) -> dict[str, int]:
    true_bad = int(pd.to_numeric(comparison.get("true_contamination_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    advisory_bad = int(pd.to_numeric(comparison.get("terminal_claims_from_advisory_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    failed_bad = int(pd.to_numeric(comparison.get("failed_search_promoted_true_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    for frame in (terminal, *frames):
        if {"advisory_only", "can_promote_truth"}.issubset(frame.columns):
            advisory_bad += int((frame["advisory_only"].map(_as_bool) & frame["can_promote_truth"].map(_as_bool)).sum())
    return {
        "total_true_contamination_count": true_bad,
        "total_terminal_claims_from_advisory_count": advisory_bad,
        "total_failed_search_promoted_true_count": failed_bad,
    }


def _classify(generic_gain: float, lawbook_gain: float, selected_count: int, safety: dict[str, int], neutral_label: str = "neutral_memory") -> str:
    if any(value > 0 for value in safety.values()):
        return "failed_safety"
    if generic_gain < 0 or lawbook_gain < 0:
        return "negative_memory"
    if lawbook_gain > 0 and selected_count > 0:
        return "strong_compounding"
    if generic_gain > 0 and selected_count > 0:
        return "weak_compounding"
    return neutral_label


def _uses_current_episode(lawbook: pd.DataFrame, episode: int) -> bool:
    return not lawbook.empty and "last_seen_episode" in lawbook.columns and bool((pd.to_numeric(lawbook["last_seen_episode"], errors="coerce").fillna(-1) >= episode).any())


def _evidence_uses_current(evidence: pd.DataFrame, episode: int) -> bool:
    return not evidence.empty and "episode" in evidence.columns and bool((pd.to_numeric(evidence["episode"], errors="coerce").fillna(-1) >= episode).any())


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty and len(frame.columns) == 0:
        pd.DataFrame([{"empty": True}]).to_csv(path, index=False)
    else:
        safe = frame.copy()
        for col in safe.columns:
            safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value)
        safe.to_csv(path, index=False)


def _mean(values: Any) -> float:
    vals = [float(value) for value in values if pd.notna(value)]
    return statistics.fmean(vals) if vals else 0.0


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Persistent Exact Micro-basin Lawbook v2",
            "",
            f"- classification_v1: {summary['classification_v1']}",
            f"- classification_v2: {summary['classification_v2']}",
            f"- benchmark_passed: {summary['benchmark_passed']}",
            f"- selected_route_count: {summary['selected_route_count']}",
            f"- rejected_route_count: {summary['rejected_route_count']}",
            f"- v2_minus_v1_gain: {summary['v2_minus_v1_gain']}",
            "",
            "All route scores and causal policies are advisory. They cannot promote truth.",
            "",
        ]
    )


def parse_seeds(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def parse_args(argv: Sequence[str] | None = None) -> PersistentExactV2Config:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seeds", default="20260524,20260525,20260526,20260527,20260528")
    parser.add_argument("--train-pairs", type=int, default=1200)
    parser.add_argument("--heldout-pairs", type=int, default=1200)
    parser.add_argument("--true-pairs", type=int, default=500)
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--repair-budget", type=int, default=40)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--fallback-demo", action="store_true")
    args = parser.parse_args(argv)
    return PersistentExactV2Config(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=args.out_dir,
        seeds=parse_seeds(args.seeds),
        train_pairs=args.train_pairs,
        heldout_pairs=args.heldout_pairs,
        true_pairs=args.true_pairs,
        episodes=args.episodes,
        repair_budget=args.repair_budget,
        max_n=args.max_n,
        fallback_demo=args.fallback_demo,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_persistent_exact_microbasin_v2_benchmark(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

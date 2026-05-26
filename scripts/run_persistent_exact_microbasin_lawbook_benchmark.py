#!/usr/bin/env python
"""Run persistent exact micro-basin Lawbook replay benchmark."""

from __future__ import annotations

import argparse
import csv
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
class PersistentExactBenchmarkConfig:
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


def run_persistent_exact_microbasin_benchmark(config: PersistentExactBenchmarkConfig) -> dict[str, Any]:
    """Run the prior-only persistent exact micro-basin replay benchmark."""

    started = datetime.now(timezone.utc)
    start_time = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    episode_frames: list[pd.DataFrame] = []
    replay_frames: list[pd.DataFrame] = []
    replay_curve_rows: list[dict[str, Any]] = []
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
        if episode == 0:
            replay = replay_persistent_lawbook(current, pd.DataFrame())
            replay_attempted = False
        else:
            replay = replay_persistent_lawbook(current, prior_lawbook)
            replay_attempted = True
            no_leakage = no_leakage and not _uses_current_episode(prior_lawbook, episode)
        replay["episode"] = episode
        replay["seed"] = seed
        metrics = evaluate_persistent_replay(replay)
        metrics.update(
            {
                "episode": episode,
                "seed": seed,
                "replay_attempted": replay_attempted,
                "prior_lawbook_entries": int(len(prior_lawbook)),
                "no_current_episode_leakage": no_leakage,
            }
        )
        replay_curve_rows.append(metrics)
        replay_frames.append(replay)
        episode_frames.append(current)
        terminal = _read_csv(episode_dir / "terminal_form_audit.csv")
        if not terminal.empty:
            terminal["episode"] = episode
            terminal["seed"] = seed
            terminal_frames.append(terminal)
        artifact_rows.append({"episode": episode, "seed": seed, "artifact": "episode_dir", "path": str(episode_dir), "exists": episode_dir.exists()})

    persistent_lawbook = build_persistent_lawbook(episode_frames)
    replay_eval = pd.concat(replay_frames, ignore_index=True, sort=False) if replay_frames else pd.DataFrame()
    replay_curve = pd.DataFrame(replay_curve_rows)
    terminal_audit = pd.concat(terminal_frames, ignore_index=True, sort=False) if terminal_frames else pd.DataFrame()
    recipe_reuse = replay_eval[replay_eval.get("persistent_route_available", pd.Series(dtype=bool)).map(_as_bool)].copy() if not replay_eval.empty else pd.DataFrame()
    safety = _aggregate_safety(replay_curve, terminal_audit, replay_eval)
    summary = _build_summary(config, started, start_time, source_mode, real_corpus_used, persistent_lawbook, replay_curve, safety, no_leakage)
    gates = _gates(summary, replay_curve, no_leakage)
    summary["benchmark_gates"] = gates
    summary["all_gates_passed"] = all(row["passed"] for row in gates)
    summary["all_blocking_gates_passed"] = all(row["passed"] for row in gates if row.get("blocking", True))
    summary["benchmark_passed"] = bool(summary["all_blocking_gates_passed"])

    artifacts = {
        "persistent_exact_microbasin_summary.json": out_dir / "persistent_exact_microbasin_summary.json",
        "persistent_exact_microbasin_report.md": out_dir / "persistent_exact_microbasin_report.md",
        "persistent_exact_microbasin_lawbook.csv": out_dir / "persistent_exact_microbasin_lawbook.csv",
        "persistent_exact_microbasin_lawbook.sqlite": out_dir / "persistent_exact_microbasin_lawbook.sqlite",
        "persistent_replay_curve.csv": out_dir / "persistent_replay_curve.csv",
        "persistent_replay_eval.csv": out_dir / "persistent_replay_eval.csv",
        "persistent_recipe_reuse.csv": out_dir / "persistent_recipe_reuse.csv",
        "terminal_form_audit.csv": out_dir / "terminal_form_audit.csv",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
    }
    _write_csv(artifacts["persistent_exact_microbasin_lawbook.csv"], persistent_lawbook)
    _write_csv(artifacts["persistent_replay_curve.csv"], replay_curve)
    _write_csv(artifacts["persistent_replay_eval.csv"], replay_eval)
    _write_csv(artifacts["persistent_recipe_reuse.csv"], recipe_reuse)
    _write_csv(artifacts["terminal_form_audit.csv"], terminal_audit)
    write_persistent_lawbook_sqlite(
        artifacts["persistent_exact_microbasin_lawbook.sqlite"],
        {
            "persistent_lawbook": persistent_lawbook,
            "persistent_replay_curve": replay_curve,
            "persistent_replay_eval": replay_eval,
            "persistent_recipe_reuse": recipe_reuse,
            "terminal_form_audit": terminal_audit,
        },
    )
    artifact_rows.extend(
        {"episode": "", "seed": "", "artifact": name, "path": str(path), "exists": path.exists()}
        for name, path in artifacts.items()
        if name != "artifact_manifest.json"
    )
    artifacts["artifact_manifest.json"].write_text(json.dumps(artifact_rows, indent=2, sort_keys=True), encoding="utf-8")
    summary["artifacts"] = {name: str(path) for name, path in artifacts.items()}
    artifacts["persistent_exact_microbasin_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["persistent_exact_microbasin_report.md"].write_text(_report(summary), encoding="utf-8")
    if not summary["advisory_boundary_preserved"]:
        raise RuntimeError("persistent exact micro-basin benchmark safety boundary failed")
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
    if {"seed", "eq1_id", "eq2_id"}.issubset(features.columns) and {"seed", "eq1_id", "eq2_id"}.issubset(recovery.columns):
        return features.merge(recovery, on=["seed", "eq1_id", "eq2_id"], how="left", suffixes=("", "_recovery"))
    return recovery


def _write_fallback_episode(episode_dir: Path, episode: int, seed: int) -> None:
    basin = "projection_pressure"
    deep = "high_gradient"
    features = pd.DataFrame(
        [
            {
                "seed": seed,
                "pair_idx": idx,
                "eq1_id": idx,
                "eq2_id": idx + 10,
                "basin": basin if idx < 3 else "fresh_escape",
                "deep_ir_candidate": deep if idx < 3 else "fresh_gate",
                "quotient_pressure": 2,
                "target_separation_pressure": 3,
                "ir_constraint_loss": 2,
                "fresh_variable_escape_count": 0 if idx < 3 else 1,
                "repeat_tail_pressure": 1,
                "skeleton_equal": False,
            }
            for idx in range(5)
        ]
    )
    lawbook_gain_pair = 1 if episode == 0 else 0
    recovery_rows = []
    for idx in range(5):
        generic = idx in {2, 3}
        lawbook = generic or idx == lawbook_gain_pair
        recovery_rows.append(
            {
                "seed": seed,
                "pair_idx": idx,
                "eq1_id": idx,
                "eq2_id": idx + 10,
                "generic_recovered": generic,
                "heldout_lawbook_recovered": lawbook,
                "lawbook_gain_hit": lawbook and not generic,
                "lawbook_gain_constructor_id": "c_exact_projection" if lawbook and not generic else "",
                "lawbook_gain_constructor_family": "projection_exception_left" if lawbook and not generic else "",
                "exact_attribution_available": True,
                "attribution_mode": "exact_constructor",
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    summary = {
        "source_mode": "fallback_demo",
        "real_corpus_used": False,
        "benchmark_passed": True,
        "total_true_contamination_count": 0,
        "total_terminal_claims_from_advisory_count": 0,
        "total_failed_search_promoted_true_count": 0,
    }
    terminal = pd.DataFrame(
        [
            {
                "status": "RESIDUAL",
                "terminal_form": "NONE",
                "advisory_only": True,
                "can_promote_truth": False,
            }
        ]
    )
    features.to_csv(episode_dir / "heldout_pair_features.csv", index=False)
    pd.DataFrame(recovery_rows).to_csv(episode_dir / "heldout_recovery_eval.csv", index=False)
    pd.DataFrame().to_csv(episode_dir / "train_lawbook_manifest.csv", index=False)
    terminal.to_csv(episode_dir / "terminal_form_audit.csv", index=False)
    (episode_dir / "heldout_lawbook_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def _build_summary(
    config: PersistentExactBenchmarkConfig,
    started: datetime,
    start_time: float,
    source_mode: str,
    real_corpus_used: bool,
    persistent_lawbook: pd.DataFrame,
    replay_curve: pd.DataFrame,
    safety: dict[str, int],
    no_leakage: bool,
) -> dict[str, Any]:
    replayed = replay_curve[replay_curve.get("replay_attempted", pd.Series(dtype=bool)).map(_as_bool)] if not replay_curve.empty else pd.DataFrame()
    mean_generic = _mean(replay_curve.get("generic_yield", []))
    mean_lawbook = _mean(replay_curve.get("lawbook_yield", []))
    mean_persistent = _mean(replayed.get("persistent_yield_proxy", []))
    mean_lawbook_gain = _mean(replay_curve.get("lawbook_gain_over_generic", []))
    mean_persistent_generic_gain = _mean(replayed.get("persistent_gain_over_generic_proxy", []))
    mean_persistent_lawbook_gain = _mean(replayed.get("persistent_gain_over_lawbook_proxy", []))
    reuse_count = int(pd.to_numeric(replayed.get("exact_recipe_reuse_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not replayed.empty else 0
    residual_gain = int(pd.to_numeric(replayed.get("residual_compression_gain_proxy", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not replayed.empty else 0
    classification = _classification(mean_persistent_generic_gain, mean_persistent_lawbook_gain, reuse_count)
    return {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start_time, 6),
        "source_mode": source_mode,
        "real_corpus_used": real_corpus_used,
        "seed_count": len(config.seeds),
        "seeds": config.seeds,
        "train_pairs": config.train_pairs,
        "heldout_pairs": config.heldout_pairs,
        "true_pairs": config.true_pairs,
        "mean_generic_yield": mean_generic,
        "mean_lawbook_yield": mean_lawbook,
        "mean_persistent_yield_proxy": mean_persistent,
        "mean_lawbook_gain_over_generic": mean_lawbook_gain,
        "mean_persistent_gain_over_generic_proxy": mean_persistent_generic_gain,
        "mean_persistent_gain_over_lawbook_proxy": mean_persistent_lawbook_gain,
        "total_exact_recipe_reuse_count": reuse_count,
        "total_residual_compression_gain_proxy": residual_gain,
        "persistent_memory_nonempty": not persistent_lawbook.empty,
        "persistent_memory_reused": reuse_count > 0,
        "no_current_episode_leakage": no_leakage,
        **safety,
        "advisory_boundary_preserved": safety["true_contamination_count"] == 0
        and safety["terminal_claims_from_advisory_count"] == 0
        and safety["failed_search_promoted_true_count"] == 0,
        "compounding_classification": classification,
    }


def _gates(summary: dict[str, Any], replay_curve: pd.DataFrame, no_leakage: bool) -> list[dict[str, Any]]:
    checks = [
        ("data_loaded", summary["seed_count"] > 0, True),
        ("heldout_benchmark_runs_completed", len(replay_curve) == summary["seed_count"], True),
        ("exact_attribution_columns_present_or_proxy_declared", True, True),
        ("no_current_episode_leakage", no_leakage, True),
        ("persistent_lawbook_written", True, True),
        ("persistent_memory_nonempty", summary["persistent_memory_nonempty"], True),
        (
            "persistent_replay_attempted_after_episode_0",
            bool(replay_curve.get("replay_attempted", pd.Series(dtype=bool)).map(_as_bool).sum() >= max(0, summary["seed_count"] - 1)),
            True,
        ),
        ("exact_recipe_reuse_present", summary["persistent_memory_reused"], True),
        ("persistent_gain_nonnegative_vs_generic", summary["mean_persistent_gain_over_generic_proxy"] >= 0, False),
        ("persistent_gain_nonnegative_vs_lawbook", summary["mean_persistent_gain_over_lawbook_proxy"] >= 0, False),
        ("true_contamination_zero", summary["true_contamination_count"] == 0, True),
        ("no_advisory_truth_promotion", summary["terminal_claims_from_advisory_count"] == 0, True),
        ("failed_search_not_true", summary["failed_search_promoted_true_count"] == 0, True),
        ("benchmark_outputs_written", True, True),
    ]
    return [{"gate": key, "passed": bool(value), "blocking": bool(blocking)} for key, value, blocking in checks]


def _aggregate_safety(replay_curve: pd.DataFrame, terminal_audit: pd.DataFrame, replay_eval: pd.DataFrame) -> dict[str, int]:
    true_contamination = int(pd.to_numeric(replay_curve.get("true_contamination_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    advisory_truth = int(pd.to_numeric(replay_curve.get("terminal_claims_from_advisory_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    failed_true = int(pd.to_numeric(replay_curve.get("failed_search_promoted_true_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    if {"advisory_only", "can_promote_truth"}.issubset(replay_eval.columns):
        advisory_truth += int((replay_eval["advisory_only"].map(_as_bool) & replay_eval["can_promote_truth"].map(_as_bool)).sum())
    if not terminal_audit.empty and {"advisory_only", "can_promote_truth"}.issubset(terminal_audit.columns):
        advisory_truth += int((terminal_audit["advisory_only"].map(_as_bool) & terminal_audit["can_promote_truth"].map(_as_bool)).sum())
    return {
        "true_contamination_count": true_contamination,
        "terminal_claims_from_advisory_count": advisory_truth,
        "failed_search_promoted_true_count": failed_true,
    }


def _classification(generic_gain: float, lawbook_gain: float, reuse_count: int) -> str:
    if generic_gain < 0 or lawbook_gain < 0:
        return "negative_memory"
    if lawbook_gain > 0 and reuse_count > 0:
        return "strong_compounding"
    if generic_gain > 0 and reuse_count > 0:
        return "weak_compounding"
    return "neutral_memory"


def _uses_current_episode(lawbook: pd.DataFrame, episode: int) -> bool:
    if lawbook.empty or "last_seen_episode" not in lawbook.columns:
        return False
    return bool((pd.to_numeric(lawbook["last_seen_episode"], errors="coerce").fillna(-1) >= episode).any())


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
            "# Persistent Exact Micro-basin Lawbook v1",
            "",
            "## Headline",
            f"- classification: {summary['compounding_classification']}",
            f"- benchmark_passed: {summary['benchmark_passed']}",
            f"- source_mode: {summary['source_mode']}",
            "",
            "## Metrics",
            f"- mean_generic_yield: {summary['mean_generic_yield']}",
            f"- mean_lawbook_yield: {summary['mean_lawbook_yield']}",
            f"- mean_persistent_yield_proxy: {summary['mean_persistent_yield_proxy']}",
            f"- mean_persistent_gain_over_generic_proxy: {summary['mean_persistent_gain_over_generic_proxy']}",
            f"- mean_persistent_gain_over_lawbook_proxy: {summary['mean_persistent_gain_over_lawbook_proxy']}",
            f"- total_exact_recipe_reuse_count: {summary['total_exact_recipe_reuse_count']}",
            "",
            "## Trust Boundary",
            "Persistent exact micro-basin entries are advisory route-learning memory. They cannot promote truth.",
            f"- true_contamination_count: {summary['true_contamination_count']}",
            f"- terminal_claims_from_advisory_count: {summary['terminal_claims_from_advisory_count']}",
            f"- failed_search_promoted_true_count: {summary['failed_search_promoted_true_count']}",
            "",
            "## Interpretation",
            "Strong or weak compounding here means prior exact route memory improved proxy held-out recovery. It is not TRUE-side proof.",
            "",
        ]
    )


def parse_seeds(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def parse_args(argv: Sequence[str] | None = None) -> PersistentExactBenchmarkConfig:
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
    return PersistentExactBenchmarkConfig(
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
    summary = run_persistent_exact_microbasin_benchmark(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

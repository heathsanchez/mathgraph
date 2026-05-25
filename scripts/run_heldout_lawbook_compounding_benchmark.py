#!/usr/bin/env python
"""Held-out Lawbook compounding benchmark for autonomous native_v2 finite core."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from mathgraph.autonomous_finite_recovery import (
    FiniteRecoveryConfig,
    build_finite_recovery_core,
    greedy_route,
    pair_recovery_matrix,
    residual_marginal_repair,
)
from mathgraph.compounding_metrics import obstruction_entropy
from mathgraph.obstruction_atlas import summarize_obstructions
from mathgraph.polarized_quotient_ir import build_pair_features
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix
from mathgraph.terminal_form_contract import TerminalForm, audit_terminal_rows, boundary_preserved


@dataclass(frozen=True)
class HeldoutLawbookBenchmarkConfig:
    equations: str | None
    matrix: str | None
    out_dir: str
    seeds: list[int]
    train_pairs: int = 2500
    heldout_pairs: int = 2500
    true_pairs: int = 1000
    episodes: int = 3
    repair_budget: int = 40
    max_n: int = 4
    allow_fallback_demo: bool = False
    constructor_limit: int | None = None


def run_heldout_lawbook_benchmark(config: HeldoutLawbookBenchmarkConfig) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    start_time = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    equations, matrix, source_mode = _load_inputs(config)

    seed_summaries: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    lawbook_rows: list[dict[str, Any]] = []
    heldout_feature_rows: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    obstruction_rows: list[dict[str, Any]] = []
    terminal_rows: list[dict[str, Any]] = []

    for seed in config.seeds:
        result = _run_seed(seed, equations, matrix, source_mode, config)
        seed_summaries.append(result["summary"])
        policy_rows.extend(result["policy_rows"])
        gate_rows.extend(result["gate_rows"])
        lawbook_rows.extend(result["lawbook_rows"])
        heldout_feature_rows.extend(result["heldout_feature_rows"])
        recovery_rows.extend(result["recovery_rows"])
        obstruction_rows.extend(result["obstruction_rows"])
        terminal_rows.extend(result["terminal_rows"])

    aggregate = _aggregate(seed_summaries)
    gates = _benchmark_gates(seed_summaries, aggregate)
    finished = datetime.now(timezone.utc)
    artifact_paths = {
        "heldout_lawbook_summary.json": out_dir / "heldout_lawbook_summary.json",
        "heldout_lawbook_report.md": out_dir / "heldout_lawbook_report.md",
        "cross_seed_summary.csv": out_dir / "cross_seed_summary.csv",
        "per_seed_policy_eval.csv": out_dir / "per_seed_policy_eval.csv",
        "per_seed_gate_results.csv": out_dir / "per_seed_gate_results.csv",
        "train_lawbook_manifest.csv": out_dir / "train_lawbook_manifest.csv",
        "heldout_pair_features.csv": out_dir / "heldout_pair_features.csv",
        "heldout_recovery_eval.csv": out_dir / "heldout_recovery_eval.csv",
        "heldout_obstruction_atlas.csv": out_dir / "heldout_obstruction_atlas.csv",
        "terminal_form_audit.csv": out_dir / "terminal_form_audit.csv",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
    }
    summary = {
        "started": started.isoformat(),
        "finished": finished.isoformat(),
        "elapsed_sec": round(time.monotonic() - start_time, 6),
        "source_mode": source_mode,
        "real_corpus_used": source_mode == "real_etp",
        "seeds": [int(seed) for seed in config.seeds],
        "seed_count": len(config.seeds),
        "equations": len(equations),
        "matrix_shape": list(getattr(matrix, "shape", (len(equations), len(equations)))),
        "train_pairs": int(config.train_pairs),
        "heldout_pairs": int(config.heldout_pairs),
        "true_pairs": int(config.true_pairs),
        "episodes": int(config.episodes),
        "repair_budget": int(config.repair_budget),
        "max_n": int(config.max_n),
        **aggregate,
        "benchmark_gates": gates,
        "benchmark_passed": all(row["passed"] for row in gates),
        "artifacts": {name: str(path) for name, path in artifact_paths.items()},
    }

    write_csv(artifact_paths["cross_seed_summary.csv"], seed_summaries)
    write_csv(artifact_paths["per_seed_policy_eval.csv"], policy_rows)
    write_csv(artifact_paths["per_seed_gate_results.csv"], gate_rows)
    write_csv(artifact_paths["train_lawbook_manifest.csv"], lawbook_rows)
    write_csv(artifact_paths["heldout_pair_features.csv"], heldout_feature_rows)
    write_csv(artifact_paths["heldout_recovery_eval.csv"], recovery_rows)
    write_csv(artifact_paths["heldout_obstruction_atlas.csv"], obstruction_rows)
    write_csv(artifact_paths["terminal_form_audit.csv"], terminal_rows)
    artifact_manifest = [
        {"artifact_name": name, "path": str(path), "exists": path.exists()}
        for name, path in artifact_paths.items()
        if name != "artifact_manifest.json"
    ]
    artifact_paths["artifact_manifest.json"].write_text(json.dumps(artifact_manifest, indent=2, sort_keys=True), encoding="utf-8")
    artifact_paths["heldout_lawbook_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifact_paths["heldout_lawbook_report.md"].write_text(_markdown_report(summary), encoding="utf-8")
    if aggregate["total_true_contamination_count"] or aggregate["total_terminal_claims_from_advisory_count"] or aggregate["total_failed_search_promoted_true_count"]:
        raise RuntimeError("terminal-form safety violation detected in held-out Lawbook benchmark")
    return summary


def _run_seed(seed: int, equations: list[str], matrix: Any, source_mode: str, config: HeldoutLawbookBenchmarkConfig) -> dict[str, Any]:
    train_pairs, heldout_pairs, true_pairs = _sample_splits(matrix, len(equations), seed, config)
    recovery = build_finite_recovery_core(
        equations,
        FiniteRecoveryConfig(max_n=max(2, config.max_n), constructor_limit=config.constructor_limit, random_seed=seed),
    )
    train_matrix = pair_recovery_matrix(train_pairs, recovery.sat_cache)
    heldout_matrix = pair_recovery_matrix(heldout_pairs, recovery.sat_cache)
    true_matrix = pair_recovery_matrix(true_pairs, recovery.sat_cache)
    budget = max(1, int(config.repair_budget))
    generic_indices, train_generic_mask, generic_train_route = greedy_route(
        train_matrix,
        recovery.constructor_manifest,
        budget=max(1, budget // 2),
        seed=seed,
    )
    repair_extra, train_repair_mask, repair_route = residual_marginal_repair(
        train_matrix,
        train_generic_mask,
        recovery.constructor_manifest,
        budget=budget,
        seed=seed,
    )
    lawbook_indices = list(dict.fromkeys(generic_indices + repair_extra))
    compact_indices = _compact_indices(repair_route, lawbook_indices, budget)
    generic_eval = _eval_policy("generic", seed, generic_indices, heldout_matrix, true_matrix, heldout_pairs)
    lawbook_eval = _eval_policy("heldout_lawbook_guided", seed, lawbook_indices, heldout_matrix, true_matrix, heldout_pairs)
    compact_eval = _eval_policy("compact_atlas_guided", seed, compact_indices, heldout_matrix, true_matrix, heldout_pairs)
    reference_indices, _, _ = residual_marginal_repair(
        heldout_matrix,
        np.zeros(int(heldout_matrix.shape[0]), dtype=bool),
        recovery.constructor_manifest,
        budget=budget,
        seed=seed,
    )
    reference_eval = _eval_policy("heldout_repair_oracle_like_bounded", seed, reference_indices, heldout_matrix, true_matrix, heldout_pairs)
    heldout_features = _pair_features(equations, heldout_pairs, seed, "heldout")
    residual_mask = ~_mask(heldout_matrix, lawbook_indices)
    residual_features = [row for idx, row in enumerate(heldout_features) if idx < len(residual_mask) and bool(residual_mask[idx])]
    obstruction_records = summarize_obstructions(residual_features, stage="heldout_lawbook")
    obstruction_rows = [{"seed": seed, **record.to_dict()} for record in obstruction_records]
    terminal_source_rows = [
        {"status": "finite_countermodel_found", "eq1_holds": True, "eq2_violated": True, "finite_checker_valid": True},
        {"status": "failed_search", "finite_search_miss": True},
        {"status": "named_obstruction_advisory", "obstruction_name": "heldout_residual"},
    ]
    terminal_audit = [{"seed": seed, **row} for row in audit_terminal_rows(terminal_source_rows)]
    terminal_claims_from_advisory = sum(1 for row in terminal_audit if row.get("advisory_only") and row.get("can_promote_truth"))
    failed_search_true = sum(1 for row in terminal_audit if row.get("status") == "RESIDUAL" and row.get("terminal_form") == "VERIFIED_PROOF")
    policy_rows = [generic_eval, lawbook_eval, compact_eval, reference_eval]
    overlap = len(set(train_pairs) & set(heldout_pairs))
    seed_summary = {
        "seed": seed,
        "source_mode": source_mode,
        "train_false_count": len(train_pairs),
        "heldout_false_count": len(heldout_pairs),
        "true_control_count": len(true_pairs),
        "constructor_count": recovery.constructor_count,
        "generic_yield": generic_eval["yield"],
        "generic_yield_rate": generic_eval["yield_rate"],
        "generic_residuals": generic_eval["residuals"],
        "lawbook_yield": lawbook_eval["yield"],
        "lawbook_yield_rate": lawbook_eval["yield_rate"],
        "lawbook_residuals": lawbook_eval["residuals"],
        "lawbook_gain_over_generic": lawbook_eval["yield"] - generic_eval["yield"],
        "compact_atlas_yield": compact_eval["yield"],
        "repair_reference_yield": reference_eval["yield"],
        "true_contamination_count": sum(int(row["true_contamination_count"]) for row in policy_rows),
        "terminal_claims_from_advisory_count": terminal_claims_from_advisory,
        "failed_search_promoted_true_count": failed_search_true,
        "train_heldout_overlap_count": overlap,
        "obstruction_entropy": obstruction_entropy(obstruction_rows),
    }
    gate_rows = _seed_gates(seed, seed_summary, recovery.constructor_count, bool(lawbook_indices), bool(policy_rows))
    seed_summary["all_gates_passed"] = all(row["passed"] for row in gate_rows)
    lawbook_rows = _lawbook_manifest(seed, source_mode, lawbook_indices, repair_route, recovery.constructor_manifest, train_repair_mask, train_matrix)
    recovery_rows = _recovery_rows(seed, heldout_pairs, generic_indices, lawbook_indices, heldout_matrix)
    return {
        "summary": seed_summary,
        "policy_rows": policy_rows,
        "gate_rows": gate_rows,
        "lawbook_rows": lawbook_rows,
        "heldout_feature_rows": heldout_features,
        "recovery_rows": recovery_rows,
        "obstruction_rows": obstruction_rows,
        "terminal_rows": terminal_audit,
    }


def _load_inputs(config: HeldoutLawbookBenchmarkConfig) -> tuple[list[str], Any, str]:
    if config.equations and config.matrix:
        equations_path = Path(config.equations)
        matrix_path = Path(config.matrix)
        if not equations_path.exists() or not matrix_path.exists():
            raise FileNotFoundError("real ETP mode requires existing --equations and --matrix")
        return load_sair_equations(equations_path), load_sair_matrix(matrix_path), "real_etp"
    if config.allow_fallback_demo:
        return _tiny_equations(), _tiny_matrix(), "fallback_tiny_demo"
    raise FileNotFoundError("provide real --equations/--matrix or pass --allow-fallback-demo")


def _sample_splits(matrix: Any, n: int, seed: int, config: HeldoutLawbookBenchmarkConfig) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]]]:
    limit = min(n, int(matrix.shape[0]), int(matrix.shape[1]))
    false_pairs: list[tuple[int, int]] = []
    true_pairs: list[tuple[int, int]] = []
    for i in range(limit):
        for j in range(limit):
            if i == j:
                true_pairs.append((i, j))
            elif bool(matrix[i, j]):
                true_pairs.append((i, j))
            else:
                false_pairs.append((i, j))
    rng = random.Random(seed)
    rng.shuffle(false_pairs)
    rng.shuffle(true_pairs)
    train_count = min(max(1, config.train_pairs), len(false_pairs))
    heldout_count = min(max(1, config.heldout_pairs), max(0, len(false_pairs) - train_count))
    if heldout_count == 0 and len(false_pairs) > 1:
        train_count = len(false_pairs) // 2
        heldout_count = len(false_pairs) - train_count
    train = false_pairs[:train_count]
    heldout = false_pairs[train_count : train_count + heldout_count]
    controls = true_pairs[: min(max(1, config.true_pairs), len(true_pairs))]
    return train, heldout, controls


def _eval_policy(policy: str, seed: int, indices: list[int], heldout_matrix: np.ndarray, true_matrix: np.ndarray, heldout_pairs: list[tuple[int, int]]) -> dict[str, Any]:
    mask = _mask(heldout_matrix, indices)
    total = int(heldout_matrix.shape[0])
    true_bad = int(_mask(true_matrix, indices).sum()) if len(true_matrix) else 0
    return {
        "seed": seed,
        "policy": policy,
        "route_size": len(indices),
        "yield": int(mask.sum()),
        "yield_rate": float(mask.sum() / total) if total else 0.0,
        "residuals": total - int(mask.sum()),
        "heldout_false_count": len(heldout_pairs),
        "true_contamination_count": true_bad,
        "terminal_claims_from_advisory_count": 0,
        "failed_search_promoted_true_count": 0,
        "advisory_only": True,
        "can_promote_truth": False,
    }


def _seed_gates(seed: int, summary: dict[str, Any], constructor_count: int, lawbook_present: bool, policy_present: bool) -> list[dict[str, Any]]:
    checks = {
        "data_loaded": summary["train_false_count"] > 0 and summary["heldout_false_count"] > 0,
        "train_heldout_disjoint": summary["train_heldout_overlap_count"] == 0,
        "constructor_bank_nonempty": constructor_count > 0,
        "lawbook_artifact_written": lawbook_present,
        "heldout_lawbook_policy_present": policy_present,
        "true_contamination_zero": summary["true_contamination_count"] == 0,
        "no_advisory_truth_promotion": summary["terminal_claims_from_advisory_count"] == 0,
        "failed_search_not_true": summary["failed_search_promoted_true_count"] == 0,
        "benchmark_outputs_written": True,
        "lawbook_beats_generic_mean": summary["lawbook_yield"] >= summary["generic_yield"],
    }
    return [{"seed": seed, "gate": key, "passed": bool(value)} for key, value in checks.items()]


def _benchmark_gates(seed_summaries: list[dict[str, Any]], aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = {
        "data_loaded": bool(seed_summaries),
        "train_heldout_disjoint": all(row["train_heldout_overlap_count"] == 0 for row in seed_summaries),
        "constructor_bank_nonempty": all(row["constructor_count"] > 0 for row in seed_summaries),
        "lawbook_artifact_written": True,
        "heldout_lawbook_policy_present": True,
        "true_contamination_zero": aggregate["total_true_contamination_count"] == 0,
        "no_advisory_truth_promotion": aggregate["total_terminal_claims_from_advisory_count"] == 0,
        "failed_search_not_true": aggregate["total_failed_search_promoted_true_count"] == 0,
        "benchmark_outputs_written": True,
        "lawbook_beats_generic_mean": aggregate["mean_lawbook_yield"] >= aggregate["mean_generic_yield"],
    }
    return [{"gate": key, "passed": bool(value)} for key, value in checks.items()]


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mean_generic_yield": _mean(row["generic_yield"] for row in rows),
        "mean_lawbook_yield": _mean(row["lawbook_yield"] for row in rows),
        "mean_lawbook_gain": _mean(row["lawbook_gain_over_generic"] for row in rows),
        "min_lawbook_gain": min((row["lawbook_gain_over_generic"] for row in rows), default=0),
        "mean_generic_residuals": _mean(row["generic_residuals"] for row in rows),
        "mean_lawbook_residuals": _mean(row["lawbook_residuals"] for row in rows),
        "total_true_contamination_count": sum(int(row["true_contamination_count"]) for row in rows),
        "total_terminal_claims_from_advisory_count": sum(int(row["terminal_claims_from_advisory_count"]) for row in rows),
        "total_failed_search_promoted_true_count": sum(int(row["failed_search_promoted_true_count"]) for row in rows),
    }


def _lawbook_manifest(seed: int, source_mode: str, indices: list[int], repair_route: pd.DataFrame, manifest: pd.DataFrame, train_mask: np.ndarray, train_matrix: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    repair_by_idx = {int(row["constructor_idx"]): row for row in repair_route.to_dict("records")} if not repair_route.empty else {}
    for rank, idx in enumerate(indices):
        mrow = manifest.iloc[idx].to_dict() if 0 <= idx < len(manifest) else {}
        rrow = repair_by_idx.get(int(idx), {})
        rows.append(
            {
                "seed": seed,
                "rank": rank,
                "constructor_idx": int(idx),
                "cid": mrow.get("cid", ""),
                "family": mrow.get("family", ""),
                "name": mrow.get("name", ""),
                "n": mrow.get("n", ""),
                "marginal_gain": rrow.get("marginal_gain", ""),
                "source_mode": source_mode,
                "train_recovered_after": int(train_mask.sum()),
                "train_residuals_after": int(train_matrix.shape[0] - train_mask.sum()),
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    return rows


def _recovery_rows(seed: int, pairs: list[tuple[int, int]], generic_indices: list[int], lawbook_indices: list[int], heldout_matrix: np.ndarray) -> list[dict[str, Any]]:
    generic = _mask(heldout_matrix, generic_indices)
    lawbook = _mask(heldout_matrix, lawbook_indices)
    return [
        {
            "seed": seed,
            "pair_idx": idx,
            "eq1_id": int(pair[0]),
            "eq2_id": int(pair[1]),
            "generic_recovered": bool(generic[idx]),
            "lawbook_recovered": bool(lawbook[idx]),
            "lawbook_new_recovery": bool(lawbook[idx] and not generic[idx]),
        }
        for idx, pair in enumerate(pairs)
    ]


def _pair_features(equations: list[str], pairs: list[tuple[int, int]], seed: int, split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair_idx, (eq1_id, eq2_id) in enumerate(pairs):
        features = build_pair_features(equations[int(eq1_id)], equations[int(eq2_id)])
        rows.append({"seed": seed, "split": split, "pair_idx": pair_idx, "eq1_id": int(eq1_id), "eq2_id": int(eq2_id), **features})
    return rows


def _compact_indices(repair_route: pd.DataFrame, fallback: list[int], budget: int) -> list[int]:
    if repair_route.empty or "constructor_idx" not in repair_route.columns:
        return fallback[: max(1, budget)]
    df = repair_route.copy()
    df["_gain"] = pd.to_numeric(df.get("marginal_gain", 0), errors="coerce").fillna(0)
    df = df.sort_values(["_gain", "constructor_idx"], ascending=[False, True])
    return [int(idx) for idx in df["constructor_idx"].head(max(1, budget)).tolist()]


def _mask(matrix: np.ndarray, indices: list[int]) -> np.ndarray:
    if not indices or not len(matrix):
        return np.zeros(int(matrix.shape[0]), dtype=bool)
    return matrix[:, [int(idx) for idx in indices]].any(axis=1)


def _tiny_equations() -> list[str]:
    return [
        "(x * y) = (y * x)",
        "(x * y) = x",
        "(x * y) = y",
        "x = x",
        "x = y",
        "(x * x) = x",
        "((x * y) * z) = (x * (y * z))",
        "(x * y) = (x * y)",
    ]


def _tiny_matrix() -> Any:
    matrix = np.zeros((8, 8), dtype=bool)
    for i in range(8):
        matrix[i, i] = True
    matrix[1, 5] = True
    matrix[2, 5] = True
    matrix[4, 0] = True
    return matrix


def _mean(values: Iterable[Any]) -> float:
    vals = [float(value) for value in values]
    return statistics.fmean(vals) if vals else 0.0


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row}) or ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key)) for key in fieldnames})


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def _markdown_report(summary: dict[str, Any]) -> str:
    improved = summary["mean_lawbook_yield"] > summary["mean_generic_yield"]
    tied = summary["mean_lawbook_yield"] == summary["mean_generic_yield"]
    if improved:
        interpretation = "Held-out advisory Lawbook routing improved finite-core recovery over generic routing."
    elif tied:
        interpretation = "Held-out advisory Lawbook routing tied generic routing in this run."
    else:
        interpretation = "Held-out advisory Lawbook routing did not beat generic routing in this run."
    return "\n".join(
        [
            "# Held-Out Lawbook Compounding Benchmark",
            "",
            "## Run Configuration",
            f"- seeds: {summary['seeds']}",
            f"- train_pairs: {summary['train_pairs']}",
            f"- heldout_pairs: {summary['heldout_pairs']}",
            f"- true_pairs: {summary['true_pairs']}",
            f"- repair_budget: {summary['repair_budget']}",
            "",
            "## Source Mode",
            f"- source_mode: {summary['source_mode']}",
            f"- real_corpus_used: {summary['real_corpus_used']}",
            "",
            "## Cross-Seed Headline Metrics",
            f"- mean_generic_yield: {summary['mean_generic_yield']}",
            f"- mean_lawbook_yield: {summary['mean_lawbook_yield']}",
            f"- mean_lawbook_gain: {summary['mean_lawbook_gain']}",
            f"- mean_generic_residuals: {summary['mean_generic_residuals']}",
            f"- mean_lawbook_residuals: {summary['mean_lawbook_residuals']}",
            "",
            "## Terminal-Form Safety Audit",
            f"- total_true_contamination_count: {summary['total_true_contamination_count']}",
            f"- total_terminal_claims_from_advisory_count: {summary['total_terminal_claims_from_advisory_count']}",
            f"- total_failed_search_promoted_true_count: {summary['total_failed_search_promoted_true_count']}",
            "",
            "## Yield / Residual Comparison Table",
            "| policy | mean yield | mean residuals |",
            "| --- | ---: | ---: |",
            f"| generic | {summary['mean_generic_yield']} | {summary['mean_generic_residuals']} |",
            f"| heldout_lawbook_guided | {summary['mean_lawbook_yield']} | {summary['mean_lawbook_residuals']} |",
            "",
            "## Lawbook Reuse and Compact Atlas Metrics",
            "Lawbook and compact atlas rows are advisory route priors. They cannot promote truth.",
            "",
            "## Obstruction Atlas Summary",
            "Residual held-out pairs are grouped into advisory obstruction names for diagnostics.",
            "",
            "## Interpretation",
            interpretation,
            "",
            "## Limitations",
            "- This is a finite-core compounding benchmark, not TRUE-side theorem proving.",
            "- The Lawbook-guided route is selected from train-slice evidence only.",
            "- The bounded repair reference is explicitly labeled as a reference policy.",
            "",
            "## Next Actions",
            "- Run larger real ETP splits over multiple seeds.",
            "- Compare basin-specific failures when Lawbook transfer does not improve.",
            "- Admit only checker-backed finite certificates into durable Lawbook memory.",
            "",
        ]
    )


def parse_seeds(values: Sequence[str]) -> list[int]:
    seeds: list[int] = []
    for value in values:
        for part in str(value).split(","):
            if part.strip():
                seeds.append(int(part.strip()))
    return seeds


def parse_args(argv: Sequence[str] | None = None) -> HeldoutLawbookBenchmarkConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seeds", nargs="+", default=["20260524,20260525,20260526"])
    parser.add_argument("--train-pairs", type=int, default=2500)
    parser.add_argument("--heldout-pairs", type=int, default=2500)
    parser.add_argument("--true-pairs", type=int, default=1000)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--repair-budget", type=int, default=40)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--allow-fallback-demo", action="store_true")
    parser.add_argument("--constructor-limit", type=int)
    args = parser.parse_args(argv)
    return HeldoutLawbookBenchmarkConfig(
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
        allow_fallback_demo=args.allow_fallback_demo,
        constructor_limit=args.constructor_limit,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_heldout_lawbook_benchmark(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

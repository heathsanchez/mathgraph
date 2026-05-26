#!/usr/bin/env python
"""Run a cross-seed benchmark for the autonomous native v2 finite-core engine."""

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
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.autonomous_compounding_engine import AutonomousCompoundingConfig, run_autonomous_compounding


@dataclass(frozen=True)
class NativeV2BenchmarkConfig:
    equations: str | None
    matrix: str | None
    out_dir: str
    seeds: list[int]
    episodes: int
    sample_pairs: int
    repair_budget: int
    max_n: int
    tiny_demo: bool = False
    constructor_limit: int | None = None


def run_native_v2_benchmark(config: NativeV2BenchmarkConfig) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    started_monotonic = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tiny_demo = bool(config.tiny_demo or (not config.equations and not config.matrix))
    if bool(config.equations) != bool(config.matrix):
        raise FileNotFoundError("provide both --equations and --matrix, or neither for tiny fallback")
    if not tiny_demo:
        if not Path(str(config.equations)).exists() or not Path(str(config.matrix)).exists():
            raise FileNotFoundError("real native v2 benchmark requires existing equations and matrix files")

    summaries: list[dict[str, Any]] = []
    seed_dirs: list[Path] = []
    for seed in config.seeds:
        seed_dir = out_dir / f"seed_{int(seed)}"
        seed_dirs.append(seed_dir)
        seed_summary = run_autonomous_compounding(
            AutonomousCompoundingConfig(
                equations=config.equations,
                matrix=config.matrix,
                out_dir=seed_dir,
                episodes=config.episodes,
                sample_pairs=config.sample_pairs,
                repair_budget=config.repair_budget,
                max_n=config.max_n,
                seed=int(seed),
                tiny_demo=tiny_demo,
                finite_core_mode="native_v2",
                constructor_limit=config.constructor_limit,
                write_report=True,
                reuse_lawbook=True,
            )
        )
        summaries.append(seed_summary)

    seed_rows = [_seed_summary_row(seed, summary, seed_dirs[idx]) for idx, (seed, summary) in enumerate(zip(config.seeds, summaries))]
    artifact_rows = _artifact_rows(config.seeds, summaries, seed_dirs)
    gate_rows = concat_csvs(seed_dirs, "gate_results.csv", config.seeds)
    episode_rows = concat_csvs(seed_dirs, "episode_metrics.csv", config.seeds)
    obstruction_rows = concat_csvs(seed_dirs, "obstruction_atlas.csv", config.seeds)
    terminal_rows = concat_csvs(seed_dirs, "terminal_form_audit.csv", config.seeds)
    lawbook_rows = _lawbook_reuse_rows(config.seeds, summaries, episode_rows)

    aggregates = _aggregate_metrics(seed_rows, lawbook_rows)
    safety = {
        "total_true_contamination_count": sum(safe_int(row.get("true_contamination_count"), 0) for row in seed_rows),
        "total_terminal_claims_from_advisory_count": sum(safe_int(row.get("terminal_claims_from_advisory_count"), 0) for row in seed_rows),
        "total_failed_search_promoted_true_count": sum(
            safe_int(first_present(row, ["failed_search_promoted_true_count", "failed_search_promoted_true"], 0), 0)
            for row in seed_rows
        ),
    }
    gates = _benchmark_gates(seed_rows, aggregates, safety)
    finished = datetime.now(timezone.utc)
    summary = {
        "started": started.isoformat(),
        "finished": finished.isoformat(),
        "elapsed_sec": round(time.monotonic() - started_monotonic, 6),
        "source_mode": first_present(seed_rows[0], ["source_mode"], "unknown") if seed_rows else "unknown",
        "real_corpus_used": bool(seed_rows and str(seed_rows[0].get("real_corpus_used")).lower() == "true"),
        "seeds": [int(seed) for seed in config.seeds],
        "seed_count": len(config.seeds),
        "equations": safe_int(first_present(seed_rows[0], ["equations"], 0), 0) if seed_rows else 0,
        "matrix_shape": _json_value(first_present(seed_rows[0], ["matrix_shape"], None)) if seed_rows else None,
        "episodes": int(config.episodes),
        "sample_pairs": int(config.sample_pairs),
        "repair_budget": int(config.repair_budget),
        "max_n": int(config.max_n),
        **aggregates,
        **safety,
        "all_gates_passed": all(str(row.get("all_gates_passed")).lower() == "true" for row in seed_rows) if seed_rows else False,
        "all_terminal_safety_passed": all(value == 0 for value in safety.values()),
        "benchmark_gates": gates,
        "benchmark_passed": all(gate["passed"] for gate in gates),
        "artifacts": {},
    }

    artifacts = {
        "benchmark_summary.json": out_dir / "benchmark_summary.json",
        "benchmark_report.md": out_dir / "benchmark_report.md",
        "cross_seed_summary.csv": out_dir / "cross_seed_summary.csv",
        "cross_seed_episode_metrics.csv": out_dir / "cross_seed_episode_metrics.csv",
        "cross_seed_gate_results.csv": out_dir / "cross_seed_gate_results.csv",
        "cross_seed_obstruction_summary.csv": out_dir / "cross_seed_obstruction_summary.csv",
        "cross_seed_lawbook_reuse_summary.csv": out_dir / "cross_seed_lawbook_reuse_summary.csv",
        "cross_seed_terminal_audit.csv": out_dir / "cross_seed_terminal_audit.csv",
        "cross_seed_artifact_manifest.csv": out_dir / "cross_seed_artifact_manifest.csv",
    }
    write_csv(artifacts["cross_seed_summary.csv"], seed_rows)
    write_csv(artifacts["cross_seed_episode_metrics.csv"], episode_rows)
    write_csv(artifacts["cross_seed_gate_results.csv"], gate_rows)
    write_csv(artifacts["cross_seed_obstruction_summary.csv"], obstruction_rows)
    write_csv(artifacts["cross_seed_lawbook_reuse_summary.csv"], lawbook_rows)
    write_csv(artifacts["cross_seed_terminal_audit.csv"], terminal_rows)
    write_csv(artifacts["cross_seed_artifact_manifest.csv"], artifact_rows)
    summary["artifacts"] = {name: str(path) for name, path in artifacts.items()}
    artifacts["benchmark_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["benchmark_report.md"].write_text(_markdown_report(summary, seed_rows), encoding="utf-8")
    if not summary["all_terminal_safety_passed"]:
        raise RuntimeError("terminal-form safety violation detected in native v2 benchmark")
    return summary


def _seed_summary_row(seed: int, summary: dict[str, Any], seed_dir: Path) -> dict[str, Any]:
    row = {"seed": int(seed), "seed_dir": str(seed_dir)}
    for key in (
        "source_mode",
        "real_corpus_used",
        "all_gates_passed",
        "equations",
        "matrix_shape",
        "false_pair_count",
        "true_pair_count",
        "constructor_count",
        "generic_final_yield",
        "generic_final_yield_rate",
        "generic_final_residuals",
        "repair_final_yield",
        "repair_final_yield_rate",
        "repair_final_residuals",
        "repair_gain_over_generic",
        "lawbook_reuse_yield",
        "lawbook_reuse_gain_over_repair",
        "compact_atlas_yield",
        "compact_atlas_gain_over_lawbook",
        "true_contamination_count",
        "terminal_claims_from_advisory_count",
        "failed_search_promoted_true_count",
        "failed_search_promoted_true",
        "named_obstruction_count",
        "obstruction_entropy",
    ):
        row[key] = json.dumps(summary[key]) if isinstance(summary.get(key), (list, dict)) else summary.get(key)
    return row


def _artifact_rows(seeds: list[int], summaries: list[dict[str, Any]], seed_dirs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, summary, seed_dir in zip(seeds, summaries, seed_dirs):
        rows.append({"seed": seed, "artifact_name": "seed_output_dir", "path": str(seed_dir), "exists": seed_dir.exists()})
        for name, path in dict(summary.get("artifacts") or {}).items():
            rows.append({"seed": seed, "artifact_name": name, "path": str(path), "exists": Path(str(path)).exists()})
    return rows


def _lawbook_reuse_rows(seeds: list[int], summaries: list[dict[str, Any]], episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    residual_by_seed_policy: dict[tuple[int, str], int] = {}
    for row in episode_rows:
        residual_by_seed_policy[(safe_int(row.get("seed"), 0), str(row.get("policy")))] = safe_int(row.get("residuals"), 0)
    for seed, summary in zip(seeds, summaries):
        generic = safe_int(summary.get("generic_final_yield"), 0)
        lawbook = first_present(summary, ["lawbook_reuse_yield"], None)
        compact = first_present(summary, ["compact_atlas_yield"], None)
        rows.append(
            {
                "seed": int(seed),
                "policy": "lawbook_reuse",
                "yield": lawbook,
                "yield_gain_over_generic": None if lawbook is None else safe_int(lawbook, 0) - generic,
                "residuals": residual_by_seed_policy.get((int(seed), "lawbook_reuse")),
                "metric_available": lawbook is not None,
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
        rows.append(
            {
                "seed": int(seed),
                "policy": "compact_atlas",
                "yield": compact,
                "yield_gain_over_generic": None if compact is None else safe_int(compact, 0) - generic,
                "residuals": residual_by_seed_policy.get((int(seed), "compact_atlas")),
                "metric_available": compact is not None,
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    return rows


def _aggregate_metrics(seed_rows: list[dict[str, Any]], lawbook_rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    metric_keys = {
        "mean_generic_final_yield": "generic_final_yield",
        "mean_repair_final_yield": "repair_final_yield",
        "mean_lawbook_reuse_yield": "lawbook_reuse_yield",
        "mean_compact_atlas_yield": "compact_atlas_yield",
        "mean_generic_final_yield_rate": "generic_final_yield_rate",
        "mean_repair_final_yield_rate": "repair_final_yield_rate",
        "mean_lawbook_reuse_yield_rate": "lawbook_reuse_yield_rate",
        "mean_compact_atlas_yield_rate": "compact_atlas_yield_rate",
        "mean_repair_gain_over_generic": "repair_gain_over_generic",
        "mean_generic_final_residuals": "generic_final_residuals",
        "mean_repair_final_residuals": "repair_final_residuals",
    }
    for out_key, source_key in metric_keys.items():
        out[out_key] = mean_present(row.get(source_key) for row in seed_rows)
    out["mean_lawbook_gain_over_generic"] = mean_present(row.get("yield_gain_over_generic") for row in lawbook_rows if row.get("policy") == "lawbook_reuse")
    out["mean_compact_atlas_gain_over_generic"] = mean_present(row.get("yield_gain_over_generic") for row in lawbook_rows if row.get("policy") == "compact_atlas")
    out["mean_lawbook_reuse_residuals"] = mean_present(row.get("residuals") for row in lawbook_rows if row.get("policy") == "lawbook_reuse")
    out["mean_compact_atlas_residuals"] = mean_present(row.get("residuals") for row in lawbook_rows if row.get("policy") == "compact_atlas")
    return out


def _benchmark_gates(seed_rows: list[dict[str, Any]], aggregates: dict[str, Any], safety: dict[str, int]) -> list[dict[str, Any]]:
    lawbook_metric = aggregates.get("mean_lawbook_reuse_yield")
    compact_metric = aggregates.get("mean_compact_atlas_yield")
    checks = [
        ("real_or_tiny_data_loaded", bool(seed_rows and seed_rows[0].get("source_mode"))),
        ("at_least_one_seed_completed", bool(seed_rows)),
        ("every_seed_all_gates_passed", all(str(row.get("all_gates_passed")).lower() == "true" for row in seed_rows)),
        ("repair_yield_not_below_generic_mean", _gte(aggregates.get("mean_repair_final_yield"), aggregates.get("mean_generic_final_yield"))),
        ("repair_residuals_not_above_generic_mean", _lte(aggregates.get("mean_repair_final_residuals"), aggregates.get("mean_generic_final_residuals"))),
        ("true_contamination_zero", safety["total_true_contamination_count"] == 0),
        ("terminal_claims_from_advisory_zero", safety["total_terminal_claims_from_advisory_count"] == 0),
        ("failed_search_promoted_true_zero", safety["total_failed_search_promoted_true_count"] == 0),
        ("finite_search_failure_never_true", safety["total_failed_search_promoted_true_count"] == 0),
        ("benchmark_artifacts_written", True),
    ]
    if lawbook_metric is not None:
        checks.append(("lawbook_reuse_yield_not_below_generic_mean", _gte(lawbook_metric, aggregates.get("mean_generic_final_yield"))))
    if compact_metric is not None:
        checks.append(("compact_atlas_yield_not_below_generic_mean", _gte(compact_metric, aggregates.get("mean_generic_final_yield"))))
    return [{"gate": name, "passed": bool(passed)} for name, passed in checks]


def concat_csvs(seed_dirs: list[Path], filename: str, seeds: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, seed_dir in zip(seeds, seed_dirs):
        path = seed_dir / filename
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append({"seed": int(seed), **row})
    return rows


def load_summary_from_seed_dir(seed_dir: Path) -> dict[str, Any]:
    for name in ("autonomous_compounding_summary.json", "compounding_summary.json", "summary.json"):
        path = seed_dir / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def first_present(mapping: dict[str, Any], names: Sequence[str], default: Any = None) -> Any:
    for name in names:
        if name in mapping and mapping[name] not in ("", None):
            return mapping[name]
    return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def mean_present(values: Iterable[Any]) -> float | None:
    floats = [safe_float(value) for value in values if value not in ("", None)]
    floats = [value for value in floats if value is not None]
    return statistics.fmean(floats) if floats else None


def _gte(left: Any, right: Any) -> bool:
    lval = safe_float(left)
    rval = safe_float(right)
    return bool(lval is not None and rval is not None and lval >= rval)


def _lte(left: Any, right: Any) -> bool:
    lval = safe_float(left)
    rval = safe_float(right)
    return bool(lval is not None and rval is not None and lval <= rval)


def _json_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row}) or ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_cell(row.get(key)) for key in fieldnames})


def _csv_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value


def _markdown_report(summary: dict[str, Any], seed_rows: list[dict[str, Any]]) -> str:
    safety_ok = summary["all_terminal_safety_passed"]
    lawbook_note = "emitted" if summary.get("mean_lawbook_reuse_yield") is not None else "not emitted by the current engine version"
    compact_note = "emitted" if summary.get("mean_compact_atlas_yield") is not None else "not emitted by the current engine version"
    return "\n".join(
        [
            "# Autonomous Native v2 Finite-Core Benchmark",
            "",
            "## Run Configuration",
            f"- seeds: {summary['seeds']}",
            f"- episodes: {summary['episodes']}",
            f"- sample_pairs: {summary['sample_pairs']}",
            f"- repair_budget: {summary['repair_budget']}",
            f"- max_n: {summary['max_n']}",
            "",
            "## Source Mode",
            f"- source_mode: {summary['source_mode']}",
            f"- real_corpus_used: {summary['real_corpus_used']}",
            f"- equations: {summary['equations']}",
            f"- matrix_shape: {summary['matrix_shape']}",
            "",
            "## Cross-Seed Headline Metrics",
            f"- mean_generic_final_yield: {summary.get('mean_generic_final_yield')}",
            f"- mean_repair_final_yield: {summary.get('mean_repair_final_yield')}",
            f"- mean_lawbook_reuse_yield: {summary.get('mean_lawbook_reuse_yield')}",
            f"- mean_compact_atlas_yield: {summary.get('mean_compact_atlas_yield')}",
            f"- mean_repair_gain_over_generic: {summary.get('mean_repair_gain_over_generic')}",
            "",
            "## Terminal-Form Safety Audit",
            f"- all_terminal_safety_passed: {safety_ok}",
            f"- total_true_contamination_count: {summary['total_true_contamination_count']}",
            f"- total_terminal_claims_from_advisory_count: {summary['total_terminal_claims_from_advisory_count']}",
            f"- total_failed_search_promoted_true_count: {summary['total_failed_search_promoted_true_count']}",
            "",
            "## Yield / Residual Comparison Table",
            "| metric | mean |",
            "| --- | ---: |",
            f"| generic yield | {summary.get('mean_generic_final_yield')} |",
            f"| repair yield | {summary.get('mean_repair_final_yield')} |",
            f"| generic residuals | {summary.get('mean_generic_final_residuals')} |",
            f"| repair residuals | {summary.get('mean_repair_final_residuals')} |",
            "",
            "## Lawbook Reuse and Compact Atlas Metrics",
            f"- Lawbook reuse metric status: {lawbook_note}",
            f"- Compact atlas metric status: {compact_note}",
            "- These are advisory routing metrics, not verified truth.",
            "",
            "## Obstruction Atlas Summary",
            f"- seed_count: {len(seed_rows)}",
            f"- mean named obstruction count: {mean_present(row.get('named_obstruction_count') for row in seed_rows)}",
            "",
            "## Interpretation",
            _interpretation(summary),
            "",
            "## Limitations",
            "- This is a finite-core compounding benchmark, not autonomous theorem proving.",
            "- TRUE-side proof claims require proof-verifier evidence and are not produced by this benchmark.",
            "- Lawbook reuse and compact atlas routes are advisory unless independently verifier-backed.",
            "",
            "## Next Actions",
            "- Run larger real ETP splits in Colab.",
            "- Track whether Lawbook reuse beats repair across broader seeds.",
            "- Add durable Lawbook admission only for checker-backed finite certificates.",
            "",
        ]
    )


def _interpretation(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    if summary["all_terminal_safety_passed"]:
        lines.append("No terminal safety violations were detected.")
    else:
        lines.append("Terminal safety violations were detected; do not interpret routing metrics.")
    if _gte(summary.get("mean_repair_final_yield"), summary.get("mean_generic_final_yield")):
        lines.append("Residual repair tied or improved mean finite-countermodel recovery versus generic routing.")
    else:
        lines.append("Residual repair did not improve mean finite-countermodel recovery versus generic routing.")
    return " ".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> NativeV2BenchmarkConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20260524, 20260525, 20260526])
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--sample-pairs", type=int, default=4000)
    parser.add_argument("--repair-budget", type=int, default=40)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--tiny-demo", action="store_true")
    parser.add_argument("--constructor-limit", type=int)
    args = parser.parse_args(argv)
    return NativeV2BenchmarkConfig(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=args.out_dir,
        seeds=args.seeds,
        episodes=args.episodes,
        sample_pairs=args.sample_pairs,
        repair_budget=args.repair_budget,
        max_n=args.max_n,
        tiny_demo=args.tiny_demo,
        constructor_limit=args.constructor_limit,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_native_v2_benchmark(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

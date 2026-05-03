#!/usr/bin/env python
"""Run a real-asset MathGraph chewing smoke when assets are available."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import (  # noqa: E402
    CountermodelImportConfig,
    FiniteCountermodelConfig,
    HTiltScheduler,
    KernelOracle,
    LawbookStore,
    OutcomeDatasetBuilder,
    RouteLearner,
    TaskQueueConfig,
    build_candidate_frontier,
    build_task_queue,
    import_finite_countermodel_results,
    run_finite_countermodel_tasks,
)
from mathgraph.asset_discovery import (  # noqa: E402
    AssetDiscoveryConfig,
    discover_mathgraph_assets,
    materialize_assets,
)
from mathgraph.derived_certificates import DerivedCertificateGenerator  # noqa: E402
from mathgraph.frontier_builder import FrontierBuilderConfig  # noqa: E402
from scripts.run_vision_smoke import fallback_finite_countermodel_tasks  # noqa: E402


def run_real_chewing_smoke(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(out_dir)
    discovery = discover_mathgraph_assets(AssetDiscoveryConfig())
    materialized = materialize_assets(discovery, out_dir, copy=args.copy_assets)
    _write_json(discovery.to_dict(), paths["asset_discovery"])

    traces_json = args.traces_json or materialized.get("traces_json") or _selected_path(discovery, "traces_json")
    equations_path = args.equations_path or materialized.get("equations") or _selected_path(discovery, "equations")
    matrix_path = args.matrix_path or materialized.get("matrix") or _selected_path(discovery, "matrix")
    missing = []
    if not traces_json or not Path(traces_json).exists():
        missing.append("traces_json")
    if not equations_path or not Path(equations_path).exists():
        missing.append("equations_path")

    if missing and not args.allow_synthetic_fallback:
        report = _empty_report(paths, discovery, missing, started)
        _write_reports(report, paths)
        return report

    if missing and args.allow_synthetic_fallback:
        synthetic = _synthetic_assets(out_dir)
        traces_json = traces_json if traces_json and Path(traces_json).exists() else None
        equations_path = equations_path if equations_path and Path(equations_path).exists() else str(synthetic)
        matrix_path = matrix_path if matrix_path and Path(matrix_path).exists() else None

    store = LawbookStore(paths["store"])
    try:
        store.init_schema()
        if traces_json:
            store.import_traces_json(traces_json, replace=True)
        primitive_before = store.stats().trace_count
        derived_before = _derive_and_store(store, paths["derived_before"])
        outcomes_before = _build_outcomes(store, paths["outcomes_before"], paths["diagnostics_before"])
        route_learner = RouteLearner(outcomes_before)
        route_learner.build_policy_cards()
        route_learner.save_policy_cards_json(paths["route_policy"])
        route_learner.save_stats_json(paths["route_policy_stats"])
    finally:
        store.close()

    frontier_summary: dict[str, Any] = {"candidate_count": 0}
    scheduled_count = 0
    task_count = 0
    finite_task_count = 0
    synthetic_fallback_used = False
    no_finite_tasks = False
    finite_summary: dict[str, Any] = {"found_count": 0, "skipped_count": 0}
    import_summary: dict[str, Any] = {"imported_count": 0, "duplicate_count": 0}
    oracle_probe = {"summary": {"oracle_probe_count": 0, "oracle_probe_success_count": 0}, "probes": []}

    if equations_path:
        frontier = build_candidate_frontier(
            FrontierBuilderConfig(
                equations_path=equations_path,
                matrix_path=matrix_path,
                store_path=str(paths["store"]),
                out_jsonl=str(paths["frontier"]),
                max_candidates=args.max_frontier_pairs,
                random_seed=42,
            )
        )
        frontier_summary = frontier.summary
        pairs = _read_jsonl(paths["frontier"])
        store = LawbookStore(paths["store"])
        try:
            learner = RouteLearner(_read_jsonl(paths["outcomes_before"]))
            learner.build_policy_cards()
            scheduler = HTiltScheduler(oracle=KernelOracle(store), route_learner=learner)
            scheduled = scheduler.schedule(pairs, top_k=args.top_k_schedule, skip_known=True)
            scheduler.save_tasks_jsonl(paths["schedule"], scheduled)
            _write_json(scheduler.stats(scheduled).to_dict(), paths["schedule_summary"])
            scheduled_count = len(scheduled)
        finally:
            store.close()
        queue = build_task_queue(
            TaskQueueConfig(
                schedule_jsonl=str(paths["schedule"]),
                out_jsonl=str(paths["task_queue"]),
                max_tasks=args.max_tasks,
            )
        )
        task_count = int(queue.summary.get("task_count", 0))
        finite_task_count = int(queue.summary.get("by_task_kind", {}).get("finite_countermodel_search", 0))
        no_finite_tasks = finite_task_count == 0
        if no_finite_tasks and args.allow_synthetic_fallback:
            synthetic_fallback_used = True
            fallback = fallback_finite_countermodel_tasks()
            _write_jsonl(fallback, paths["task_queue"])
            task_count = len(fallback)
            finite_task_count = len(fallback)
        if finite_task_count > 0:
            finite_run = run_finite_countermodel_tasks(
                FiniteCountermodelConfig(
                    task_queue_jsonl=str(paths["task_queue"]),
                    out_jsonl=str(paths["finite_results"]),
                    max_tasks=args.max_tasks,
                    max_order=args.max_countermodel_order,
                    exhaustive_order_limit=min(args.max_countermodel_order, 3),
                    random_tables_per_order=args.random_tables_per_order,
                )
            )
            finite_summary = finite_run.summary
            imported = import_finite_countermodel_results(
                CountermodelImportConfig(
                    results_jsonl=str(paths["finite_results"]),
                    store_path=str(paths["store"]),
                    out_json=str(paths["import_summary"]),
                    revalidate=True,
                )
            )
            import_summary = imported.summary
            oracle_probe = _oracle_probe(paths["store"], imported.to_dict()["results"])
            _write_json(oracle_probe, paths["oracle_probe"])
        else:
            _write_jsonl([], paths["finite_results"])
            _write_json({"summary": import_summary, "results": []}, paths["import_summary"])
            _write_json(oracle_probe, paths["oracle_probe"])

    store = LawbookStore(paths["store"])
    try:
        primitive_after = store.stats().trace_count
        derived_after = _derive_and_store(store, paths["derived_after"])
        outcomes_after = _build_outcomes(store, paths["outcomes_after"], paths["diagnostics_after"])
    finally:
        store.close()

    summary = {
        "primitive_count_before": primitive_before,
        "derived_count_before": derived_before,
        "outcome_row_count_before": len(outcomes_before),
        "frontier_count": int(frontier_summary.get("candidate_count", 0)),
        "scheduled_count": scheduled_count,
        "task_count": task_count,
        "finite_task_count": finite_task_count,
        "finite_executor_verified_count": int(finite_summary.get("found_count", 0)),
        "imported_count": int(import_summary.get("imported_count", 0)),
        "primitive_count_after": primitive_after,
        "derived_count_after": derived_after,
        "outcome_row_count_after": len(outcomes_after),
        "oracle_probe_count": oracle_probe["summary"]["oracle_probe_count"],
        "oracle_probe_success_count": oracle_probe["summary"]["oracle_probe_success_count"],
        "warnings": [],
        "missing_assets": missing,
        "real_asset_mode": not missing,
        "synthetic_fallback_used": synthetic_fallback_used,
        "no_finite_tasks": no_finite_tasks,
        "elapsed_sec": time.perf_counter() - started,
    }
    if no_finite_tasks:
        summary["warnings"].append("No finite_countermodel_search tasks were produced by the real schedule.")
    ok = (not missing or synthetic_fallback_used) and summary["frontier_count"] > 0 and summary["scheduled_count"] > 0
    if summary["imported_count"] == 0:
        summary["warnings"].append("No new finite countermodels were imported.")
    report = {
        "ok": ok,
        "summary": summary,
        "asset_discovery": discovery.to_dict(),
        "paths": {key: str(value) for key, value in paths.items()},
    }
    _write_reports(report, paths)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--traces-json", default=None)
    parser.add_argument("--equations-path", default=None)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--max-frontier-pairs", type=int, default=250)
    parser.add_argument("--top-k-schedule", type=int, default=100)
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--random-tables-per-order", type=int, default=100)
    parser.add_argument("--allow-synthetic-fallback", action="store_true")
    parser.add_argument("--copy-assets", action="store_true")
    args = parser.parse_args(argv)

    report = run_real_chewing_smoke(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] or args.allow_synthetic_fallback else 1


def _derive_and_store(store: LawbookStore, path: Path) -> int:
    generator = DerivedCertificateGenerator(store)
    derived, _stats = generator.derive_all()
    generator.save_jsonl(derived, path)
    store.import_derived_certificates(derived, replace=True)
    return len(derived)


def _build_outcomes(store: LawbookStore, out_path: Path, diagnostics_path: Path) -> list[Any]:
    builder = OutcomeDatasetBuilder(store)
    outcomes = builder.build(include_primitive=True, include_derived=True)
    builder.save_jsonl(outcomes, out_path)
    diagnostics = builder.diagnostics(outcomes, episode_id="real_chewing_smoke")
    builder.save_diagnostics(diagnostics, diagnostics_path)
    return outcomes


def _oracle_probe(store_path: Path, import_results: list[dict[str, Any]]) -> dict[str, Any]:
    store = LawbookStore(store_path)
    probes = []
    success = 0
    try:
        oracle = KernelOracle(store)
        for row in [item for item in import_results if item.get("imported")][:5]:
            answer = oracle.query(str(row.get("source", "")), str(row.get("target", "")))
            ok = answer.status == "REFUTED" and answer.terminal_form == "FINITE_COUNTERMODEL"
            success += int(ok)
            probes.append({"ok": ok, "oracle_answer": answer.to_dict()})
    finally:
        store.close()
    return {"summary": {"oracle_probe_count": len(probes), "oracle_probe_success_count": success}, "probes": probes}


def _empty_report(paths: dict[str, Path], discovery: Any, missing: list[str], started: float) -> dict[str, Any]:
    summary = {
        "primitive_count_before": 0,
        "derived_count_before": 0,
        "outcome_row_count_before": 0,
        "frontier_count": 0,
        "scheduled_count": 0,
        "task_count": 0,
        "finite_task_count": 0,
        "finite_executor_verified_count": 0,
        "imported_count": 0,
        "primitive_count_after": 0,
        "derived_count_after": 0,
        "outcome_row_count_after": 0,
        "oracle_probe_count": 0,
        "oracle_probe_success_count": 0,
        "warnings": ["Missing required real assets."],
        "missing_assets": missing,
        "real_asset_mode": False,
        "synthetic_fallback_used": False,
        "elapsed_sec": time.perf_counter() - started,
    }
    return {
        "ok": False,
        "summary": summary,
        "asset_discovery": discovery.to_dict(),
        "paths": {key: str(value) for key, value in paths.items()},
    }


def _synthetic_assets(out_dir: Path) -> Path:
    path = out_dir / "synthetic_equations.txt"
    path.write_text("x = x\nx = y\nx * y = x\nx * y = y\n", encoding="utf-8")
    return path


def _selected_path(discovery: Any, key: str) -> str | None:
    selected = discovery.selected.get(key)
    return selected.get("path") if selected else None


def _paths(out_dir: Path) -> dict[str, Path]:
    return {
        "asset_discovery": out_dir / "asset_discovery_report.json",
        "store": out_dir / "lawbook_store.sqlite",
        "derived_before": out_dir / "derived_before.jsonl",
        "derived_after": out_dir / "derived_after.jsonl",
        "outcomes_before": out_dir / "pair_outcomes_before.jsonl",
        "outcomes_after": out_dir / "pair_outcomes_after.jsonl",
        "diagnostics_before": out_dir / "diagnostics_before.json",
        "diagnostics_after": out_dir / "diagnostics_after.json",
        "route_policy": out_dir / "route_policy.json",
        "route_policy_stats": out_dir / "route_policy_stats.json",
        "frontier": out_dir / "frontier.jsonl",
        "schedule": out_dir / "schedule.jsonl",
        "schedule_summary": out_dir / "schedule_summary.json",
        "task_queue": out_dir / "task_queue.jsonl",
        "finite_results": out_dir / "finite_results.jsonl",
        "import_summary": out_dir / "countermodel_import_summary.json",
        "oracle_probe": out_dir / "oracle_probe.json",
        "report_json": out_dir / "real_chewing_smoke_report.json",
        "report_md": out_dir / "real_chewing_smoke_report.md",
    }


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_reports(report: dict[str, Any], paths: dict[str, Path]) -> None:
    _write_json(report, paths["report_json"])
    summary = report["summary"]
    lines = [
        "# MathGraph Real Chewing Smoke Report",
        "",
        f"- ok: {report['ok']}",
        f"- real asset mode: {summary.get('real_asset_mode')}",
        f"- missing assets: {summary.get('missing_assets')}",
        f"- primitive before: {summary.get('primitive_count_before')}",
        f"- frontier count: {summary.get('frontier_count')}",
        f"- scheduled count: {summary.get('scheduled_count')}",
        f"- finite task count: {summary.get('finite_task_count')}",
        f"- imported count: {summary.get('imported_count')}",
        "",
        "Scheduler rows are not truth; finite imports are revalidated before promotion.",
    ]
    paths["report_md"].write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

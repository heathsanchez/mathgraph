"""End-to-end finite-countermodel chewing smoke harness."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.countermodel_importer import (
    CountermodelImportConfig,
    import_finite_countermodel_results,
)
from mathgraph.derived_certificates import DerivedCertificateGenerator
from mathgraph.finite_countermodel_executor import (
    FiniteCountermodelConfig,
    run_finite_countermodel_tasks,
)
from mathgraph.frontier_builder import FrontierBuilderConfig, build_candidate_frontier
from mathgraph.htilt_scheduler import HTiltScheduler
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore
from mathgraph.outcome_dataset import OutcomeDatasetBuilder
from mathgraph.route_learner import RoutePolicyCard, make_basin_key
from mathgraph.task_queue import TaskQueueConfig, build_task_queue


NO_IMPORT_WARNING = (
    "No finite countermodels imported; chewing path executed but did not produce a terminal certificate."
)


@dataclass(frozen=True)
class ChewingSmokeConfig:
    equations_path: str
    out_dir: str
    matrix_path: str | None = None
    traces_json: str | None = None
    max_frontier_pairs: int = 50
    top_k_schedule: int = 25
    max_tasks: int = 25
    max_countermodel_order: int = 3
    random_seed: int = 42
    require_imported_countermodel: bool = True
    rebuild_derived_after_import: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "equations_path": self.equations_path,
            "matrix_path": self.matrix_path,
            "traces_json": self.traces_json,
            "out_dir": self.out_dir,
            "max_frontier_pairs": self.max_frontier_pairs,
            "top_k_schedule": self.top_k_schedule,
            "max_tasks": self.max_tasks,
            "max_countermodel_order": self.max_countermodel_order,
            "random_seed": self.random_seed,
            "require_imported_countermodel": self.require_imported_countermodel,
            "rebuild_derived_after_import": self.rebuild_derived_after_import,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChewingSmokeConfig":
        return cls(
            equations_path=str(data["equations_path"]),
            matrix_path=data.get("matrix_path"),
            traces_json=data.get("traces_json"),
            out_dir=str(data["out_dir"]),
            max_frontier_pairs=int(data.get("max_frontier_pairs", 50)),
            top_k_schedule=int(data.get("top_k_schedule", 25)),
            max_tasks=int(data.get("max_tasks", 25)),
            max_countermodel_order=int(data.get("max_countermodel_order", 3)),
            random_seed=int(data.get("random_seed", 42)),
            require_imported_countermodel=bool(data.get("require_imported_countermodel", True)),
            rebuild_derived_after_import=bool(data.get("rebuild_derived_after_import", True)),
        )


@dataclass(frozen=True)
class ChewingSmokeStageResult:
    name: str
    ok: bool
    path: str | None
    summary: dict[str, Any]
    warnings: list[str]
    elapsed_sec: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "path": self.path,
            "summary": dict(self.summary),
            "warnings": list(self.warnings),
            "elapsed_sec": self.elapsed_sec,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChewingSmokeStageResult":
        return cls(
            name=str(data["name"]),
            ok=bool(data.get("ok", False)),
            path=data.get("path"),
            summary=dict(data.get("summary", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
            elapsed_sec=float(data.get("elapsed_sec", 0.0)),
        )


@dataclass(frozen=True)
class ChewingSmokeResult:
    ok: bool
    stages: list[ChewingSmokeStageResult]
    summary: dict[str, Any]
    paths: dict[str, str]
    warnings: list[str]
    created_ts: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "stages": [stage.to_dict() for stage in self.stages],
            "summary": dict(self.summary),
            "paths": dict(self.paths),
            "warnings": list(self.warnings),
            "created_ts": self.created_ts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChewingSmokeResult":
        return cls(
            ok=bool(data.get("ok", False)),
            stages=[ChewingSmokeStageResult.from_dict(item) for item in data.get("stages", [])],
            summary=dict(data.get("summary", {})),
            paths={str(key): str(value) for key, value in dict(data.get("paths", {})).items()},
            warnings=[str(item) for item in data.get("warnings", [])],
            created_ts=str(data.get("created_ts", "")),
        )


def run_chewing_smoke(config: ChewingSmokeConfig | dict[str, Any]) -> ChewingSmokeResult:
    config = config if isinstance(config, ChewingSmokeConfig) else ChewingSmokeConfig.from_dict(config)
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(out_dir)
    stages: list[ChewingSmokeStageResult] = []
    warnings: list[str] = []

    store_summary = _build_store_stage(config, paths, stages)
    frontier_summary = _frontier_stage(config, paths, stages)
    schedule_summary = _schedule_stage(config, paths, stages)
    task_summary = _task_queue_stage(config, paths, stages)
    executor_summary = _executor_stage(config, paths, stages)
    import_summary = _import_stage(config, paths, stages)
    oracle_summary = _oracle_probe_stage(paths, stages)
    derived_summary, outcome_summary = _refresh_stage(config, paths, stages)

    imported_count = int(import_summary.get("imported_count", 0))
    if imported_count == 0:
        warnings.append(NO_IMPORT_WARNING)
    ok = all(stage.ok for stage in stages)
    if config.require_imported_countermodel and imported_count == 0:
        ok = False
    if imported_count > 0 and oracle_summary.get("oracle_probe_success_count", 0) == 0:
        ok = False

    final_stats = _final_store_stats(paths["store"])
    summary = {
        "frontier_count": int(frontier_summary.get("candidate_count", 0)),
        "scheduled_count": int(schedule_summary.get("scheduled_count", 0)),
        "task_count": int(task_summary.get("task_count", 0)),
        "finite_executor_verified_count": int(executor_summary.get("found_count", 0)),
        "finite_executor_skipped_count": int(executor_summary.get("skipped_count", 0)),
        "imported_count": imported_count,
        "duplicate_count": int(import_summary.get("duplicate_count", 0)),
        "revalidation_failed_count": int(import_summary.get("revalidation_failed_count", 0)),
        "oracle_probe_count": int(oracle_summary.get("oracle_probe_count", 0)),
        "oracle_probe_success_count": int(oracle_summary.get("oracle_probe_success_count", 0)),
        "derived_count_after_import": int(derived_summary.get("total_derived_count", 0)),
        "outcome_row_count_after_import": int(outcome_summary.get("row_count", 0)),
        "lawbook_primitive_count_after_import": int(final_stats.get("trace_count", 0)),
        "initial_primitive_count": int(store_summary.get("trace_count", 0)),
        "ok": ok,
    }
    result = ChewingSmokeResult(
        ok=ok,
        stages=stages,
        summary=summary,
        paths={key: str(value) for key, value in paths.items()},
        warnings=warnings,
        created_ts=datetime.now(timezone.utc).isoformat(),
    )
    _write_json(result.to_dict(), paths["report_json"])
    _write_report_md(result, paths["report_md"])
    return result


def _build_store_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    store = LawbookStore(paths["store"])
    try:
        store.init_schema()
        if config.traces_json:
            stats = store.import_traces_json(config.traces_json, replace=True).to_dict()
        else:
            stats = store.stats().to_dict()
        stages.append(
            ChewingSmokeStageResult(
                name="lawbook_store",
                ok=True,
                path=str(paths["store"]),
                summary=stats,
                warnings=[] if config.traces_json else ["No initial trace corpus supplied; starting with empty LawbookStore."],
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return stats
    except Exception as exc:
        summary = {"error": str(exc)}
        stages.append(_failed_stage("lawbook_store", paths["store"], summary, started))
        return summary
    finally:
        store.close()


def _frontier_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = build_candidate_frontier(
            FrontierBuilderConfig(
                equations_path=config.equations_path,
                out_jsonl=str(paths["frontier"]),
                store_path=str(paths["store"]),
                matrix_path=config.matrix_path,
                max_candidates=config.max_frontier_pairs,
                include_matrix_false=True,
                include_matrix_true=False,
                include_unknown_matrix_missing=True,
                skip_known=True,
                random_seed=config.random_seed,
            )
        )
        stages.append(
            ChewingSmokeStageResult(
                name="frontier",
                ok=True,
                path=str(paths["frontier"]),
                summary=result.summary,
                warnings=list(result.summary.get("warnings", [])),
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return result.summary
    except Exception as exc:
        summary = {"error": str(exc), "candidate_count": 0}
        stages.append(_failed_stage("frontier", paths["frontier"], summary, started))
        _write_jsonl([], paths["frontier"])
        _write_json(summary, paths["frontier_summary"])
        return summary


def _schedule_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    store = LawbookStore(paths["store"])
    try:
        frontier_rows = _read_jsonl(paths["frontier"])
        policy_cards = _finite_policy_cards(frontier_rows)
        scheduler = HTiltScheduler(
            oracle=KernelOracle(store),
            policy_cards=policy_cards,
        )
        tasks = scheduler.schedule(frontier_rows, top_k=config.top_k_schedule, skip_known=True)
        scheduler.save_tasks_jsonl(paths["schedule"], tasks)
        stats = scheduler.stats(tasks).to_dict()
        _write_json(stats, paths["schedule_summary"])
        stages.append(
            ChewingSmokeStageResult(
                name="scheduler",
                ok=True,
                path=str(paths["schedule"]),
                summary=stats,
                warnings=list(stats.get("warnings", [])),
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return stats
    except Exception as exc:
        summary = {"error": str(exc), "scheduled_count": 0}
        stages.append(_failed_stage("scheduler", paths["schedule"], summary, started))
        _write_jsonl([], paths["schedule"])
        _write_json(summary, paths["schedule_summary"])
        return summary
    finally:
        store.close()


def _task_queue_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = build_task_queue(
            TaskQueueConfig(
                schedule_jsonl=str(paths["schedule"]),
                out_jsonl=str(paths["task_queue"]),
                max_tasks=config.max_tasks,
                min_priority=0.0,
                include_known=False,
            )
        )
        stages.append(
            ChewingSmokeStageResult(
                name="task_queue",
                ok=True,
                path=str(paths["task_queue"]),
                summary=result.summary,
                warnings=list(result.summary.get("warnings", [])),
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return result.summary
    except Exception as exc:
        summary = {"error": str(exc), "task_count": 0}
        stages.append(_failed_stage("task_queue", paths["task_queue"], summary, started))
        _write_jsonl([], paths["task_queue"])
        _write_json(summary, paths["task_queue_summary"])
        return summary


def _executor_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = run_finite_countermodel_tasks(
            FiniteCountermodelConfig(
                task_queue_jsonl=str(paths["finite_task_queue"]),
                out_jsonl=str(paths["finite_results"]),
                max_tasks=config.max_tasks,
                max_order=config.max_countermodel_order,
                exhaustive_order_limit=min(config.max_countermodel_order, 3),
                random_tables_per_order=0,
                include_deterministic_tables=True,
                stop_after_first=True,
                random_seed=config.random_seed,
            )
        )
        stages.append(
            ChewingSmokeStageResult(
                name="finite_countermodel_executor",
                ok=True,
                path=str(paths["finite_results"]),
                summary=result.summary,
                warnings=list(result.summary.get("warnings", [])),
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return result.summary
    except Exception as exc:
        summary = {"error": str(exc), "result_count": 0, "found_count": 0, "skipped_count": 0}
        stages.append(_failed_stage("finite_countermodel_executor", paths["finite_results"], summary, started))
        _write_jsonl([], paths["finite_results"])
        _write_json(summary, paths["finite_summary"])
        return summary


def _import_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = import_finite_countermodel_results(
            CountermodelImportConfig(
                results_jsonl=str(paths["finite_results"]),
                store_path=str(paths["store"]),
                out_json=str(paths["import_summary"]),
                revalidate=True,
                allow_duplicate_certificates=False,
            )
        )
        stages.append(
            ChewingSmokeStageResult(
                name="countermodel_importer",
                ok=True,
                path=str(paths["import_summary"]),
                summary=result.summary,
                warnings=[],
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return result.summary
    except Exception as exc:
        summary = {
            "error": str(exc),
            "imported_count": 0,
            "duplicate_count": 0,
            "revalidation_failed_count": 0,
        }
        stages.append(_failed_stage("countermodel_importer", paths["import_summary"], summary, started))
        _write_json({"summary": summary, "results": []}, paths["import_summary"])
        return summary


def _oracle_probe_stage(
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> dict[str, Any]:
    started = time.perf_counter()
    store = LawbookStore(paths["store"])
    try:
        payload = _read_json(paths["import_summary"]) if paths["import_summary"].exists() else {}
        imported = [row for row in payload.get("results", []) if row.get("imported")][:5]
        oracle = KernelOracle(store)
        probes = []
        success_count = 0
        for row in imported:
            answer = oracle.query(str(row.get("source", "")), str(row.get("target", "")))
            answer_dict = answer.to_dict()
            ok = answer.status != "UNKNOWN" and answer.terminal_form == "FINITE_COUNTERMODEL"
            if ok:
                success_count += 1
            probes.append(
                {
                    "source": row.get("source"),
                    "target": row.get("target"),
                    "ok": ok,
                    "oracle_answer": answer_dict,
                }
            )
        summary = {
            "oracle_probe_count": len(probes),
            "oracle_probe_success_count": success_count,
        }
        _write_json({"summary": summary, "probes": probes}, paths["oracle_probe"])
        stages.append(
            ChewingSmokeStageResult(
                name="oracle_probe",
                ok=success_count == len(probes),
                path=str(paths["oracle_probe"]),
                summary=summary,
                warnings=[] if probes else ["No imported countermodels available for oracle probe."],
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return summary
    except Exception as exc:
        summary = {"error": str(exc), "oracle_probe_count": 0, "oracle_probe_success_count": 0}
        stages.append(_failed_stage("oracle_probe", paths["oracle_probe"], summary, started))
        _write_json({"summary": summary, "probes": []}, paths["oracle_probe"])
        return summary
    finally:
        store.close()


def _refresh_stage(
    config: ChewingSmokeConfig,
    paths: dict[str, Path],
    stages: list[ChewingSmokeStageResult],
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    store = LawbookStore(paths["store"])
    try:
        if not config.rebuild_derived_after_import:
            _write_jsonl([], paths["derived_after"])
            _write_jsonl([], paths["outcome_after"])
            summary = {
                "total_derived_count": 0,
                "row_count": 0,
                "skipped": True,
            }
            stages.append(
                ChewingSmokeStageResult(
                    name="derived_outcome_refresh",
                    ok=True,
                    path=str(paths["outcome_after"]),
                    summary=summary,
                    warnings=["Derived/outcome refresh disabled by config."],
                    elapsed_sec=time.perf_counter() - started,
                )
            )
            return summary, summary

        generator = DerivedCertificateGenerator(store)
        derived, derived_stats = generator.derive_all()
        generator.save_jsonl(derived, paths["derived_after"])
        store.import_derived_certificates(derived, replace=True)
        builder = OutcomeDatasetBuilder(store)
        outcomes = builder.build(include_primitive=True, include_derived=True)
        builder.save_jsonl(outcomes, paths["outcome_after"])
        diagnostics = builder.diagnostics(outcomes, episode_id="chewing_smoke_after_import")
        summary = {
            "derived": derived_stats.to_dict(),
            "outcomes": builder.stats(outcomes).to_dict(),
            "diagnostics": diagnostics.to_dict(),
            "total_derived_count": derived_stats.total_derived_count,
            "row_count": len(outcomes),
        }
        stages.append(
            ChewingSmokeStageResult(
                name="derived_outcome_refresh",
                ok=True,
                path=str(paths["outcome_after"]),
                summary=summary,
                warnings=list(diagnostics.warnings),
                elapsed_sec=time.perf_counter() - started,
            )
        )
        return derived_stats.to_dict(), builder.stats(outcomes).to_dict()
    except Exception as exc:
        summary = {"error": str(exc), "total_derived_count": 0, "row_count": 0}
        stages.append(_failed_stage("derived_outcome_refresh", paths["outcome_after"], summary, started))
        _write_jsonl([], paths["derived_after"])
        _write_jsonl([], paths["outcome_after"])
        return summary, summary
    finally:
        store.close()


def _finite_policy_cards(frontier_rows: list[dict[str, Any]]) -> list[RoutePolicyCard]:
    cards: list[RoutePolicyCard] = []
    seen: set[tuple[str, ...]] = set()
    for row in frontier_rows:
        features = dict(row.get("features") or {})
        if not features:
            continue
        basin = make_basin_key("finite_countermodel", features).to_dict()
        key = tuple(basin.values())
        if key in seen:
            continue
        seen.add(key)
        confidence = 0.65 if row.get("label") == "matrix_false_unverified" else 0.55
        cards.append(
            RoutePolicyCard(
                basin_key=basin,
                support_count=1,
                route="finite_countermodel",
                success_count=1,
                failure_count=0,
                unknown_count=0,
                verified_true_count=0,
                verified_false_count=1,
                derived_count=0,
                primitive_count=1,
                success_rate=1.0,
                false_rate=1.0,
                true_rate=0.0,
                derived_rate=0.0,
                confidence=confidence,
                recommended_task_kind="finite_countermodel_search",
                warnings=[
                    "Smoke policy is scheduling pressure only.",
                    "Do not promote without a verified finite countermodel.",
                ],
                evidence={
                    "source": row.get("source"),
                    "target": row.get("target"),
                    "frontier_label": row.get("label"),
                },
            )
        )
    if cards:
        return cards
    return [
        RoutePolicyCard(
            basin_key=make_basin_key("finite_countermodel", {}).to_dict(),
            support_count=1,
            route="finite_countermodel",
            success_count=1,
            failure_count=0,
            unknown_count=0,
            verified_true_count=0,
            verified_false_count=1,
            derived_count=0,
            primitive_count=1,
            success_rate=1.0,
            false_rate=1.0,
            true_rate=0.0,
            derived_rate=0.0,
            confidence=0.45,
            recommended_task_kind="finite_countermodel_search",
            warnings=["Fallback smoke policy is advisory only."],
            evidence={},
        )
    ]


def _paths(out_dir: Path) -> dict[str, Path]:
    return {
        "store": out_dir / "lawbook.sqlite",
        "frontier": out_dir / "frontier.jsonl",
        "frontier_summary": out_dir / "frontier_summary.json",
        "schedule": out_dir / "schedule.jsonl",
        "schedule_summary": out_dir / "schedule_summary.json",
        "task_queue": out_dir / "task_queue.jsonl",
        "finite_task_queue": out_dir / "task_queue.jsonl",
        "task_queue_summary": out_dir / "task_queue_summary.json",
        "finite_results": out_dir / "finite_countermodel_results.jsonl",
        "finite_summary": out_dir / "finite_countermodel_summary.json",
        "import_summary": out_dir / "countermodel_import_summary.json",
        "oracle_probe": out_dir / "oracle_probe_results.json",
        "derived_after": out_dir / "derived_after_import.jsonl",
        "outcome_after": out_dir / "outcome_after_import.jsonl",
        "report_json": out_dir / "chewing_smoke_report.json",
        "report_md": out_dir / "chewing_smoke_report.md",
    }


def _final_store_stats(path: Path) -> dict[str, Any]:
    store = LawbookStore(path)
    try:
        return store.stats().to_dict()
    finally:
        store.close()


def _failed_stage(
    name: str,
    path: Path,
    summary: dict[str, Any],
    started: float,
) -> ChewingSmokeStageResult:
    return ChewingSmokeStageResult(
        name=name,
        ok=False,
        path=str(path),
        summary=summary,
        warnings=[str(summary.get("error", "stage failed"))],
        elapsed_sec=time.perf_counter() - started,
    )


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    input_path = Path(path)
    if not input_path.exists():
        return rows
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = row.to_dict() if hasattr(row, "to_dict") else row
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _write_report_md(result: ChewingSmokeResult, path: str | Path) -> None:
    summary = result.summary
    lines = [
        "# MathGraph Chewing Smoke Report",
        "",
        f"- ok: {result.ok}",
        f"- frontier candidates: {summary.get('frontier_count', 0)}",
        f"- scheduled candidates: {summary.get('scheduled_count', 0)}",
        f"- task queue rows: {summary.get('task_count', 0)}",
        f"- finite countermodels found: {summary.get('finite_executor_verified_count', 0)}",
        f"- imported countermodels: {summary.get('imported_count', 0)}",
        f"- oracle probe success: {summary.get('oracle_probe_success_count', 0)} / {summary.get('oracle_probe_count', 0)}",
        f"- derived certificates after import: {summary.get('derived_count_after_import', 0)}",
        f"- outcome rows after import: {summary.get('outcome_row_count_after_import', 0)}",
        "",
        "## Warnings",
    ]
    warnings = result.warnings or ["None."]
    lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(
        [
            "",
            "## Next Recommended Action",
            "- Inspect imported countermodels and run the smoke on a larger candidate frontier only after confirming artifact paths remain outside Git.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")

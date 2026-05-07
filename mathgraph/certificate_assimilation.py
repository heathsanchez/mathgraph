"""Certificate processing and assimilation episode pipeline."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.certificates import Certificate, TerminalForm, VerificationStatus
from mathgraph.countermodel_importer import CountermodelImportConfig, import_finite_countermodel_results
from mathgraph.derived_certificates import DerivedCertificateGenerator
from mathgraph.finite_countermodel_executor import FiniteCountermodelConfig, run_finite_countermodel_tasks
from mathgraph.frontier_builder import FrontierBuilderConfig, build_candidate_frontier
from mathgraph.htilt_scheduler import HTiltScheduler
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore
from mathgraph.outcome_dataset import OutcomeDatasetBuilder
from mathgraph.progress import ProgressLogger
from mathgraph.route_learner import RouteLearner
from mathgraph.task_queue import TaskQueueConfig, build_task_queue
from mathgraph.trace import Trace


TRUTH_BOUNDARY_NOTE = (
    "Only verified/revalidated terminal certificates were promoted. "
    "Scheduler/advisory/unknown rows were not promoted."
)


@dataclass(frozen=True)
class CertificateAssimilationConfig:
    traces_json: str | Path
    equations_path: str | Path
    matrix_path: str | Path | None
    out_dir: str | Path
    frontier_mode: str = "small_sample"
    frontier_scan_limit: int = 500
    max_frontier_pairs: int = 100
    top_k_schedule: int = 50
    max_tasks: int = 50
    max_countermodel_order: int = 3
    heartbeat_sec: float = 10.0
    progress: bool = True
    progress_jsonl: str | Path | None = None
    replace: bool = True
    import_derived_to_store: bool = False
    max_derived_per_rule: int | None = None
    run_oracle_probe: bool = True
    allow_synthetic_fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "traces_json": str(self.traces_json),
            "equations_path": str(self.equations_path),
            "matrix_path": str(self.matrix_path) if self.matrix_path is not None else None,
            "out_dir": str(self.out_dir),
            "frontier_mode": self.frontier_mode,
            "frontier_scan_limit": self.frontier_scan_limit,
            "max_frontier_pairs": self.max_frontier_pairs,
            "top_k_schedule": self.top_k_schedule,
            "max_tasks": self.max_tasks,
            "max_countermodel_order": self.max_countermodel_order,
            "heartbeat_sec": self.heartbeat_sec,
            "progress": self.progress,
            "progress_jsonl": str(self.progress_jsonl) if self.progress_jsonl is not None else None,
            "replace": self.replace,
            "import_derived_to_store": self.import_derived_to_store,
            "max_derived_per_rule": self.max_derived_per_rule,
            "run_oracle_probe": self.run_oracle_probe,
            "allow_synthetic_fallback": self.allow_synthetic_fallback,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateAssimilationConfig":
        return cls(
            traces_json=str(data["traces_json"]),
            equations_path=str(data["equations_path"]),
            matrix_path=data.get("matrix_path"),
            out_dir=str(data["out_dir"]),
            frontier_mode=str(data.get("frontier_mode", "small_sample")),
            frontier_scan_limit=int(data.get("frontier_scan_limit", 500)),
            max_frontier_pairs=int(data.get("max_frontier_pairs", 100)),
            top_k_schedule=int(data.get("top_k_schedule", 50)),
            max_tasks=int(data.get("max_tasks", 50)),
            max_countermodel_order=int(data.get("max_countermodel_order", 3)),
            heartbeat_sec=float(data.get("heartbeat_sec", 10.0)),
            progress=bool(data.get("progress", True)),
            progress_jsonl=data.get("progress_jsonl"),
            replace=bool(data.get("replace", True)),
            import_derived_to_store=bool(data.get("import_derived_to_store", False)),
            max_derived_per_rule=_optional_int(data.get("max_derived_per_rule")),
            run_oracle_probe=bool(data.get("run_oracle_probe", True)),
            allow_synthetic_fallback=bool(data.get("allow_synthetic_fallback", False)),
        )


@dataclass(frozen=True)
class CertificateAssimilationSummary:
    ok: bool
    real_asset_mode: bool
    synthetic_fallback_used: bool
    primitive_count_before: int
    primitive_count_after: int
    new_primitive_count: int
    derived_count_before: int
    derived_count_after: int
    new_derived_count: int
    outcome_row_count_before: int
    outcome_row_count_after: int
    new_outcome_row_count: int
    frontier_count: int
    scheduled_count: int
    task_count: int
    finite_task_count: int
    finite_executor_verified_count: int
    imported_count: int
    duplicate_count: int
    revalidation_failed_count: int
    oracle_probe_count: int
    oracle_probe_success_count: int
    residual_count: int
    elapsed_sec: float
    verified_count: int = 0
    not_found_count: int = 0
    verification_failed_count: int = 0
    obstruction_candidate_count: int = 0
    import_rate: float = 0.0
    unique_import_rate: float = 0.0
    duplicate_rate: float = 0.0
    frontier_known_pair_skipped_count: int = 0
    frontier_episode_duplicate_skipped_count: int = 0
    frontier_emitted_count: int = 0
    frontier_considered_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "real_asset_mode": self.real_asset_mode,
            "synthetic_fallback_used": self.synthetic_fallback_used,
            "primitive_count_before": self.primitive_count_before,
            "primitive_count_after": self.primitive_count_after,
            "new_primitive_count": self.new_primitive_count,
            "derived_count_before": self.derived_count_before,
            "derived_count_after": self.derived_count_after,
            "new_derived_count": self.new_derived_count,
            "outcome_row_count_before": self.outcome_row_count_before,
            "outcome_row_count_after": self.outcome_row_count_after,
            "new_outcome_row_count": self.new_outcome_row_count,
            "frontier_count": self.frontier_count,
            "scheduled_count": self.scheduled_count,
            "task_count": self.task_count,
            "finite_task_count": self.finite_task_count,
            "finite_executor_verified_count": self.finite_executor_verified_count,
            "imported_count": self.imported_count,
            "duplicate_count": self.duplicate_count,
            "revalidation_failed_count": self.revalidation_failed_count,
            "oracle_probe_count": self.oracle_probe_count,
            "oracle_probe_success_count": self.oracle_probe_success_count,
            "residual_count": self.residual_count,
            "elapsed_sec": self.elapsed_sec,
            "verified_count": self.verified_count,
            "not_found_count": self.not_found_count,
            "verification_failed_count": self.verification_failed_count,
            "obstruction_candidate_count": self.obstruction_candidate_count,
            "import_rate": self.import_rate,
            "unique_import_rate": self.unique_import_rate,
            "duplicate_rate": self.duplicate_rate,
            "frontier_known_pair_skipped_count": self.frontier_known_pair_skipped_count,
            "frontier_episode_duplicate_skipped_count": self.frontier_episode_duplicate_skipped_count,
            "frontier_emitted_count": self.frontier_emitted_count,
            "frontier_considered_count": self.frontier_considered_count,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "paths": dict(self.paths),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateAssimilationSummary":
        return cls(
            ok=bool(data.get("ok", False)),
            real_asset_mode=bool(data.get("real_asset_mode", False)),
            synthetic_fallback_used=bool(data.get("synthetic_fallback_used", False)),
            primitive_count_before=int(data.get("primitive_count_before", 0)),
            primitive_count_after=int(data.get("primitive_count_after", 0)),
            new_primitive_count=int(data.get("new_primitive_count", 0)),
            derived_count_before=int(data.get("derived_count_before", 0)),
            derived_count_after=int(data.get("derived_count_after", 0)),
            new_derived_count=int(data.get("new_derived_count", 0)),
            outcome_row_count_before=int(data.get("outcome_row_count_before", 0)),
            outcome_row_count_after=int(data.get("outcome_row_count_after", 0)),
            new_outcome_row_count=int(data.get("new_outcome_row_count", 0)),
            frontier_count=int(data.get("frontier_count", 0)),
            scheduled_count=int(data.get("scheduled_count", 0)),
            task_count=int(data.get("task_count", 0)),
            finite_task_count=int(data.get("finite_task_count", 0)),
            finite_executor_verified_count=int(data.get("finite_executor_verified_count", 0)),
            imported_count=int(data.get("imported_count", 0)),
            duplicate_count=int(data.get("duplicate_count", 0)),
            revalidation_failed_count=int(data.get("revalidation_failed_count", 0)),
            oracle_probe_count=int(data.get("oracle_probe_count", 0)),
            oracle_probe_success_count=int(data.get("oracle_probe_success_count", 0)),
            residual_count=int(data.get("residual_count", 0)),
            elapsed_sec=float(data.get("elapsed_sec", 0.0)),
            verified_count=int(data.get("verified_count", 0)),
            not_found_count=int(data.get("not_found_count", 0)),
            verification_failed_count=int(data.get("verification_failed_count", 0)),
            obstruction_candidate_count=int(data.get("obstruction_candidate_count", 0)),
            import_rate=float(data.get("import_rate", 0.0)),
            unique_import_rate=float(data.get("unique_import_rate", 0.0)),
            duplicate_rate=float(data.get("duplicate_rate", 0.0)),
            frontier_known_pair_skipped_count=int(data.get("frontier_known_pair_skipped_count", 0)),
            frontier_episode_duplicate_skipped_count=int(data.get("frontier_episode_duplicate_skipped_count", 0)),
            frontier_emitted_count=int(data.get("frontier_emitted_count", 0)),
            frontier_considered_count=int(data.get("frontier_considered_count", 0)),
            warnings=[str(item) for item in data.get("warnings", [])],
            errors=[str(item) for item in data.get("errors", [])],
            paths=dict(data.get("paths", {})),
        )


@dataclass(frozen=True)
class CertificateAssimilationResult:
    config: CertificateAssimilationConfig
    summary: CertificateAssimilationSummary
    new_certificates: list[dict[str, Any]]
    residual_tasks: list[dict[str, Any]]
    report_json_path: str
    report_md_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "summary": self.summary.to_dict(),
            "new_certificates": list(self.new_certificates),
            "residual_tasks": list(self.residual_tasks),
            "report_json_path": self.report_json_path,
            "report_md_path": self.report_md_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateAssimilationResult":
        return cls(
            config=CertificateAssimilationConfig.from_dict(data["config"]),
            summary=CertificateAssimilationSummary.from_dict(data["summary"]),
            new_certificates=list(data.get("new_certificates", [])),
            residual_tasks=list(data.get("residual_tasks", [])),
            report_json_path=str(data.get("report_json_path", "")),
            report_md_path=str(data.get("report_md_path", "")),
        )


def run_certificate_assimilation(
    config: CertificateAssimilationConfig | dict[str, Any],
) -> CertificateAssimilationResult:
    config = config if isinstance(config, CertificateAssimilationConfig) else CertificateAssimilationConfig.from_dict(config)
    started = time.perf_counter()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(out_dir)
    progress_jsonl = Path(config.progress_jsonl) if config.progress_jsonl else paths["progress"]
    logger = ProgressLogger(
        "certificate_assimilation",
        log_jsonl=progress_jsonl,
        heartbeat_sec=config.heartbeat_sec,
        enabled=config.progress,
        quiet=False,
    )

    warnings: list[str] = []
    errors: list[str] = []
    new_certificates: list[dict[str, Any]] = []
    residual_tasks: list[dict[str, Any]] = []
    synthetic_fallback_used = False
    real_asset_mode = True

    traces_json = Path(config.traces_json)
    equations_path = Path(config.equations_path)
    matrix_path = Path(config.matrix_path) if config.matrix_path else None

    with logger.stage("ingestion_validate_assets"):
        missing = []
        if not traces_json.exists():
            missing.append("traces_json")
        if not equations_path.exists():
            missing.append("equations_path")
        if matrix_path is not None and not matrix_path.exists():
            missing.append("matrix_path")
        if missing and config.allow_synthetic_fallback:
            synthetic_fallback_used = True
            real_asset_mode = False
            traces_json, equations_path, matrix_path = _write_synthetic_assets(out_dir)
            warnings.append(f"Synthetic fallback used because assets were missing: {missing}")
        elif missing:
            errors.append(f"Missing required assets: {missing}")
        else:
            trace_info = _validate_traces(traces_json)
            equation_info = _validate_equations(equations_path)
            _write_json({"traces": trace_info, "equations": equation_info, "matrix_path": str(matrix_path) if matrix_path else None}, paths["asset_validation"])

    if errors:
        summary = _make_summary(
            ok=False,
            real_asset_mode=real_asset_mode,
            synthetic_fallback_used=synthetic_fallback_used,
            started=started,
            warnings=warnings,
            errors=errors,
            paths=paths,
        )
        result = CertificateAssimilationResult(config, summary, [], [], str(paths["report_json"]), str(paths["report_md"]))
        _write_empty_episode_artifacts(paths)
        _write_result_reports(result, paths)
        return result

    store = LawbookStore(paths["store"])
    primitive_before = primitive_after = 0
    derived_before = derived_after = 0
    outcomes_before: list[Any] = []
    outcomes_after: list[Any] = []
    frontier_summary: dict[str, Any] = {}
    schedule_rows: list[dict[str, Any]] = []
    queue_rows: list[dict[str, Any]] = []
    finite_rows: list[dict[str, Any]] = []
    import_rows: list[dict[str, Any]] = []
    task_outcomes: list[dict[str, Any]] = []
    oracle_probe = {"summary": {"oracle_probe_count": 0, "oracle_probe_success_count": 0}, "probes": []}

    try:
        with logger.stage("ingestion_build_lawbook_store", input=str(traces_json), output=str(paths["store"])):
            store.init_schema()
            stats = store.import_traces_json(traces_json, replace=config.replace)
            primitive_before = stats.trace_count
            _write_json(stats.to_dict(), paths["lawbook_before"])

        with logger.stage("assimilation_derive_before"):
            derived_before = _derive(store, paths["derived_before"], config)

        with logger.stage("assimilation_outcomes_before"):
            outcomes_before = _build_outcomes(store, paths["outcomes_before"], paths["diagnostics_before"])

        with logger.stage("processing_route_policy", total=len(outcomes_before)):
            learner = RouteLearner(outcomes_before)
            learner.build_policy_cards()
            learner.save_policy_cards_json(paths["route_policy"])
            learner.save_stats_json(paths["route_policy_stats"])

        with logger.stage("processing_frontier_build", output=str(paths["frontier"])):
            frontier = build_candidate_frontier(
                FrontierBuilderConfig(
                    equations_path=str(equations_path),
                    out_jsonl=str(paths["frontier"]),
                    store_path=str(paths["store"]),
                    matrix_path=str(matrix_path) if matrix_path else None,
                    max_candidates=config.max_frontier_pairs,
                    frontier_mode=config.frontier_mode,
                    frontier_scan_limit=config.frontier_scan_limit,
                    duplicate_filter=True,
                    random_seed=42,
                ),
                progress=logger,
            )
            frontier_summary = frontier.summary

        with logger.stage("processing_schedule_tasks", total=int(frontier_summary.get("candidate_count", 0))):
            pairs = _read_jsonl(paths["frontier"])
            scheduler = HTiltScheduler(oracle=KernelOracle(store), route_learner=learner)
            scheduled = scheduler.schedule(pairs, top_k=config.top_k_schedule, skip_known=True)
            scheduler.save_tasks_jsonl(paths["schedule"], scheduled)
            scheduler.save_stats_json(paths["schedule_summary"], scheduler.stats(scheduled))
            schedule_rows = [task.to_dict() for task in scheduled]

        with logger.stage("processing_build_task_queue", total=len(schedule_rows)):
            queue_result = build_task_queue(
                TaskQueueConfig(
                    schedule_jsonl=str(paths["schedule"]),
                    out_jsonl=str(paths["task_queue"]),
                    max_tasks=config.max_tasks,
                )
            )
            queue_rows = queue_result.tasks

        with logger.stage("construction_verification_finite_countermodels", total=len(queue_rows)):
            finite_run = run_finite_countermodel_tasks(
                FiniteCountermodelConfig(
                    task_queue_jsonl=str(paths["task_queue"]),
                    out_jsonl=str(paths["finite_results"]),
                    max_tasks=config.max_tasks,
                    max_order=config.max_countermodel_order,
                    exhaustive_order_limit=min(config.max_countermodel_order, 3),
                )
            )
            finite_rows = finite_run.results

        with logger.stage("promotion_import_countermodels", total=len(finite_rows)):
            imported = import_finite_countermodel_results(
                CountermodelImportConfig(
                    results_jsonl=str(paths["finite_results"]),
                    store_path=str(paths["store"]),
                    out_json=str(paths["import_summary"]),
                    revalidate=True,
                )
            )
            import_rows = [row.to_dict() for row in imported.results]
            new_certificates = [row for row in import_rows if row.get("imported")]
            _write_jsonl(new_certificates, paths["new_certificates"])

        with logger.stage("assimilation_derive_after"):
            primitive_after = store.stats().trace_count
            _write_json(store.stats().to_dict(), paths["lawbook_after"])
            derived_after = _derive(store, paths["derived_after"], config)

        with logger.stage("assimilation_outcomes_after"):
            outcomes_after = _build_outcomes(store, paths["outcomes_after"], paths["diagnostics_after"])

        if config.run_oracle_probe:
            with logger.stage("assimilation_oracle_probe", total=len(new_certificates)):
                oracle_probe = _oracle_probe(store, new_certificates)
                _write_json(oracle_probe, paths["oracle_probe"])

        with logger.stage("assimilation_residual_export"):
            task_outcomes = _task_outcome_ledger(queue_rows, finite_rows, import_rows, paths)
            _write_jsonl(task_outcomes, paths["task_outcome_ledger"])
            duplicates = [row for row in task_outcomes if row.get("duplicate_status") == "duplicate"]
            _write_jsonl(duplicates, paths["duplicate_certificates"])
            residual_tasks = _residuals_from_outcomes(task_outcomes)
            _write_jsonl(residual_tasks, paths["residual_queue"])
            residual_outcome_rows = [
                row for row in task_outcomes
                if row.get("import_status") != "imported" and row.get("duplicate_status") != "duplicate"
            ]
            _write_jsonl(residual_outcome_rows, paths["residual_obstruction_candidates"])
    finally:
        store.close()

    finite_summary = _read_json(paths["finite_summary"])
    import_summary = _read_json(paths["import_summary"]).get("summary", {})
    task_summary = _read_json(paths["task_queue_summary"])
    episode_diagnostics = _episode_diagnostics(task_outcomes)
    episode_diagnostics["summary"]["frontier_known_pair_skipped_count"] = int(frontier_summary.get("known_pair_skipped_count", 0))
    episode_diagnostics["summary"]["frontier_episode_duplicate_skipped_count"] = int(frontier_summary.get("episode_duplicate_skipped_count", 0))
    episode_diagnostics["summary"]["frontier_emitted_count"] = int(frontier_summary.get("emitted_count", frontier_summary.get("candidate_count", 0)))
    episode_diagnostics["summary"]["frontier_considered_count"] = int(frontier_summary.get("considered_count", frontier_summary.get("pair_candidates_considered", 0)))
    _write_json(episode_diagnostics, paths["episode_diagnostics_json"])
    _write_diagnostics_markdown(episode_diagnostics, paths["episode_diagnostics_md"])
    summary = CertificateAssimilationSummary(
        ok=not errors,
        real_asset_mode=real_asset_mode,
        synthetic_fallback_used=synthetic_fallback_used,
        primitive_count_before=primitive_before,
        primitive_count_after=primitive_after,
        new_primitive_count=primitive_after - primitive_before,
        derived_count_before=derived_before,
        derived_count_after=derived_after,
        new_derived_count=derived_after - derived_before,
        outcome_row_count_before=len(outcomes_before),
        outcome_row_count_after=len(outcomes_after),
        new_outcome_row_count=len(outcomes_after) - len(outcomes_before),
        frontier_count=int(frontier_summary.get("candidate_count", 0)),
        scheduled_count=len(schedule_rows),
        task_count=int(task_summary.get("task_count", len(queue_rows))),
        finite_task_count=int(task_summary.get("by_task_kind", {}).get("finite_countermodel_search", 0)),
        finite_executor_verified_count=int(finite_summary.get("found_count", 0)),
        imported_count=int(import_summary.get("imported_count", 0)),
        duplicate_count=int(import_summary.get("duplicate_count", 0)),
        revalidation_failed_count=int(import_summary.get("revalidation_failed_count", 0)),
        oracle_probe_count=int(oracle_probe["summary"].get("oracle_probe_count", 0)),
        oracle_probe_success_count=int(oracle_probe["summary"].get("oracle_probe_success_count", 0)),
        residual_count=len(residual_tasks),
        elapsed_sec=time.perf_counter() - started,
        verified_count=episode_diagnostics["summary"]["verified_count"],
        not_found_count=episode_diagnostics["summary"]["not_found_count"],
        verification_failed_count=episode_diagnostics["summary"]["verification_failed_count"],
        obstruction_candidate_count=episode_diagnostics["summary"]["obstruction_candidate_count"],
        import_rate=episode_diagnostics["summary"]["import_rate"],
        unique_import_rate=episode_diagnostics["summary"]["unique_import_rate"],
        duplicate_rate=episode_diagnostics["summary"]["duplicate_rate"],
        frontier_known_pair_skipped_count=int(frontier_summary.get("known_pair_skipped_count", 0)),
        frontier_episode_duplicate_skipped_count=int(frontier_summary.get("episode_duplicate_skipped_count", 0)),
        frontier_emitted_count=int(frontier_summary.get("emitted_count", frontier_summary.get("candidate_count", 0))),
        frontier_considered_count=int(frontier_summary.get("considered_count", frontier_summary.get("pair_candidates_considered", 0))),
        warnings=[*warnings, *([] if new_certificates else ["No new primitive certificates were promoted."])],
        errors=errors,
        paths={key: str(value) for key, value in paths.items()},
    )
    result = CertificateAssimilationResult(
        config=config,
        summary=summary,
        new_certificates=new_certificates,
        residual_tasks=residual_tasks,
        report_json_path=str(paths["report_json"]),
        report_md_path=str(paths["report_md"]),
    )
    with logger.stage("assimilation_report_writing", output=str(paths["report_json"])):
        _write_result_reports(result, paths)
    return result


def _derive(store: LawbookStore, path: Path, config: CertificateAssimilationConfig) -> int:
    generator = DerivedCertificateGenerator(store)
    derived, _stats = generator.derive_all(max_per_rule=config.max_derived_per_rule)
    generator.save_jsonl(derived, path)
    if config.import_derived_to_store:
        store.import_derived_certificates(derived, replace=True)
    return len(derived)


def _build_outcomes(store: LawbookStore, out_path: Path, diagnostics_path: Path) -> list[Any]:
    builder = OutcomeDatasetBuilder(store)
    outcomes = builder.build(include_primitive=True, include_derived=True)
    builder.save_jsonl(outcomes, out_path)
    builder.save_diagnostics(builder.diagnostics(outcomes, episode_id="certificate_assimilation"), diagnostics_path)
    return outcomes


def _oracle_probe(store: LawbookStore, imported_rows: list[dict[str, Any]]) -> dict[str, Any]:
    oracle = KernelOracle(store)
    probes = []
    success = 0
    for row in imported_rows[:5]:
        answer = oracle.query(str(row.get("source", "")), str(row.get("target", "")))
        ok = answer.status == "REFUTED" and answer.terminal_form == "FINITE_COUNTERMODEL"
        success += int(ok)
        probes.append({"ok": ok, "source": row.get("source"), "target": row.get("target"), "oracle_answer": answer.to_dict()})
    return {"summary": {"oracle_probe_count": len(probes), "oracle_probe_success_count": success}, "probes": probes}


def _residuals(
    queue_rows: list[dict[str, Any]],
    finite_rows: list[dict[str, Any]],
    import_rows: list[dict[str, Any]],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    residuals: list[dict[str, Any]] = []
    finite_by_task = {row.get("task_id"): row for row in finite_rows}
    import_by_task = {row.get("task_id"): row for row in import_rows}
    for task in queue_rows:
        task_id = task.get("task_id")
        finite = finite_by_task.get(task_id)
        imported = import_by_task.get(task_id)
        reason = None
        upstream = paths["task_queue"]
        if task.get("task_kind") != "finite_countermodel_search":
            reason = "task_not_executed_by_finite_countermodel_executor"
        elif finite is None:
            reason = "finite_result_missing"
        elif finite.get("status") != "finite_countermodel_found":
            reason = finite.get("status") or "finite_countermodel_not_found"
            upstream = paths["finite_results"]
        elif imported is None:
            reason = "import_result_missing"
            upstream = paths["import_summary"]
        elif not imported.get("imported"):
            reason = imported.get("status") or "not_imported"
            upstream = paths["import_summary"]
        if reason:
            residuals.append(
                {
                    "task_id": task_id,
                    "source": task.get("source"),
                    "target": task.get("target"),
                    "route": task.get("route"),
                    "task_kind": task.get("task_kind"),
                    "reason": reason,
                    "priority": task.get("priority"),
                    "source_idx": task.get("source_idx"),
                    "target_idx": task.get("target_idx"),
                    "upstream_file": str(upstream),
                }
            )
    return residuals


def _task_outcome_ledger(
    queue_rows: list[dict[str, Any]],
    finite_rows: list[dict[str, Any]],
    import_rows: list[dict[str, Any]],
    paths: dict[str, Path],
) -> list[dict[str, Any]]:
    finite_by_task = {row.get("task_id"): row for row in finite_rows}
    import_by_task = {row.get("task_id"): row for row in import_rows}
    rows = []
    for task in queue_rows:
        task_id = task.get("task_id")
        finite = finite_by_task.get(task_id)
        imported = import_by_task.get(task_id)
        execution_status = "not_executed"
        verification_status = "NOT_VERIFIED"
        import_status = "not_attempted"
        duplicate_status = "not_duplicate"
        certificate_id = None
        terminal_form = None
        reason = None
        countermodel_order = None
        witness = None
        elapsed_sec = 0.0
        artifacts = {"task_queue": str(paths["task_queue"])}

        if task.get("task_kind") != "finite_countermodel_search":
            execution_status = "residual"
            reason = "task_kind_not_supported_by_live_constructor"
        elif finite is None:
            execution_status = "missing_result"
            reason = "finite executor did not emit a result"
        else:
            artifacts["finite_result"] = str(paths["finite_results"])
            execution_status = str(finite.get("status") or "")
            verification_status = str(finite.get("verification_status") or "NOT_VERIFIED")
            certificate_id = finite.get("certificate_id")
            terminal_form = finite.get("terminal_form")
            countermodel = finite.get("countermodel") or {}
            countermodel_order = countermodel.get("order")
            witness = finite.get("witness")
            elapsed_sec = float(finite.get("elapsed_sec") or 0.0)
            reason = finite.get("failure_reason")
            if finite.get("status") == "finite_countermodel_found":
                import_status = "missing_import_result"
            if imported is not None:
                artifacts["import_summary"] = str(paths["import_summary"])
                import_status = str(imported.get("status") or "not_imported")
                duplicate_status = "duplicate" if import_status == "skipped_duplicate" else "not_duplicate"
                if imported.get("imported"):
                    import_status = "imported"
                    reason = None
                elif imported.get("reason"):
                    reason = imported.get("reason")

        rows.append(
            {
                "task_id": task_id,
                "source": task.get("source"),
                "target": task.get("target"),
                "source_idx": task.get("source_idx"),
                "target_idx": task.get("target_idx"),
                "route": task.get("route"),
                "task_kind": task.get("task_kind"),
                "terminal_goal": task.get("terminal_goal"),
                "execution_status": execution_status,
                "verification_status": verification_status,
                "import_status": import_status,
                "duplicate_status": duplicate_status,
                "certificate_id": certificate_id,
                "terminal_form": terminal_form,
                "reason": reason,
                "artifact_paths": artifacts,
                "countermodel_order": countermodel_order,
                "witness": witness,
                "elapsed_sec": elapsed_sec,
                "priority": task.get("priority"),
            }
        )
    return rows


def _residuals_from_outcomes(task_outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    residuals = []
    for row in task_outcomes:
        if row.get("import_status") == "imported" or row.get("duplicate_status") == "duplicate":
            continue
        residuals.append(
            {
                "task_id": row.get("task_id"),
                "source": row.get("source"),
                "target": row.get("target"),
                "route": row.get("route"),
                "task_kind": row.get("task_kind"),
                "reason": row.get("reason") or row.get("execution_status") or row.get("import_status"),
                "priority": row.get("priority"),
                "source_idx": row.get("source_idx"),
                "target_idx": row.get("target_idx"),
                "upstream_file": row.get("artifact_paths", {}).get("finite_result") or row.get("artifact_paths", {}).get("task_queue"),
            }
        )
    return residuals


def _episode_diagnostics(task_outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    task_count = len(task_outcomes)
    verified = [row for row in task_outcomes if row.get("verification_status") == "FINITE_VERIFIED"]
    imported = [row for row in task_outcomes if row.get("import_status") == "imported"]
    duplicates = [row for row in task_outcomes if row.get("duplicate_status") == "duplicate"]
    not_found = [row for row in task_outcomes if row.get("execution_status") == "no_countermodel_found"]
    failed = [row for row in task_outcomes if row.get("execution_status") in {"parse_failed", "error"} or row.get("import_status") == "skipped_revalidation_failed"]
    residuals = [
        row for row in task_outcomes
        if row.get("import_status") != "imported" and row.get("duplicate_status") != "duplicate"
    ]
    obstructions = [row for row in residuals if row.get("task_kind") == "obstruction_analysis" or row.get("execution_status") in {"residual", "no_countermodel_found"}]
    task_outcome_counts = {
        "by_execution_status": _count_by(task_outcomes, "execution_status"),
        "by_verification_status": _count_by(task_outcomes, "verification_status"),
        "by_import_status": _count_by(task_outcomes, "import_status"),
        "by_duplicate_status": _count_by(task_outcomes, "duplicate_status"),
    }
    by_route: dict[str, dict[str, int]] = {}
    for row in task_outcomes:
        route = str(row.get("route") or "unknown")
        bucket = by_route.setdefault(route, {"task_count": 0, "verified_count": 0, "imported_count": 0, "duplicate_count": 0})
        bucket["task_count"] += 1
        if row.get("verification_status") == "FINITE_VERIFIED":
            bucket["verified_count"] += 1
        if row.get("import_status") == "imported":
            bucket["imported_count"] += 1
        if row.get("duplicate_status") == "duplicate":
            bucket["duplicate_count"] += 1
    best_route = None
    if by_route:
        best_route = sorted(
            by_route.items(),
            key=lambda item: (-(item[1]["imported_count"] / item[1]["task_count"] if item[1]["task_count"] else 0.0), item[0]),
        )[0][0]
    return {
        "summary": {
            "task_count": task_count,
            "verified_count": len(verified),
            "imported_count": len(imported),
            "duplicate_count": len(duplicates),
            "not_found_count": len(not_found),
            "verification_failed_count": len(failed),
            "revalidation_failed_count": sum(1 for row in task_outcomes if row.get("import_status") == "skipped_revalidation_failed"),
            "residual_count": len(residuals),
            "obstruction_candidate_count": len(obstructions),
            "import_rate": len(imported) / len(verified) if verified else 0.0,
            "unique_import_rate": len(imported) / task_count if task_count else 0.0,
            "duplicate_rate": len(duplicates) / len(verified) if verified else 0.0,
            "best_yield_route": best_route,
            "frontier_known_pair_skipped_count": 0,
            "frontier_episode_duplicate_skipped_count": 0,
        },
        "task_outcome_counts": task_outcome_counts,
        "consistency_checks": {
            "task_count_matches_ledger": task_count == len(task_outcomes),
            "imported_plus_duplicate_plus_residual_equals_task_count": (
                len(imported) + len(duplicates) + len(residuals) == task_count
            ),
            "duplicates_not_promoted": all(row.get("import_status") != "imported" for row in duplicates),
            "residuals_not_terminal_imports": all(row.get("import_status") != "imported" for row in residuals),
        },
        "new_certificates": imported,
        "duplicate_certificates": duplicates,
        "unresolved": residuals,
        "try_next": sorted(residuals, key=lambda row: (-(float(row.get("priority") or 0.0)), str(row.get("task_id"))))[:10],
        "route_yield": by_route,
        "truth_boundary": TRUTH_BOUNDARY_NOTE,
    }


def _make_summary(
    *,
    ok: bool,
    real_asset_mode: bool,
    synthetic_fallback_used: bool,
    started: float,
    warnings: list[str],
    errors: list[str],
    paths: dict[str, Path],
) -> CertificateAssimilationSummary:
    return CertificateAssimilationSummary(
        ok=ok,
        real_asset_mode=real_asset_mode,
        synthetic_fallback_used=synthetic_fallback_used,
        primitive_count_before=0,
        primitive_count_after=0,
        new_primitive_count=0,
        derived_count_before=0,
        derived_count_after=0,
        new_derived_count=0,
        outcome_row_count_before=0,
        outcome_row_count_after=0,
        new_outcome_row_count=0,
        frontier_count=0,
        scheduled_count=0,
        task_count=0,
        finite_task_count=0,
        finite_executor_verified_count=0,
        imported_count=0,
        duplicate_count=0,
        revalidation_failed_count=0,
        oracle_probe_count=0,
        oracle_probe_success_count=0,
        residual_count=0,
        elapsed_sec=time.perf_counter() - started,
        verified_count=0,
        not_found_count=0,
        verification_failed_count=0,
        obstruction_candidate_count=0,
        import_rate=0.0,
        unique_import_rate=0.0,
        duplicate_rate=0.0,
        frontier_known_pair_skipped_count=0,
        frontier_episode_duplicate_skipped_count=0,
        frontier_emitted_count=0,
        frontier_considered_count=0,
        warnings=warnings,
        errors=errors,
        paths={key: str(value) for key, value in paths.items()},
    )


def _write_synthetic_assets(out_dir: Path) -> tuple[Path, Path, None]:
    traces_path = out_dir / "synthetic_traces.json"
    equations_path = out_dir / "synthetic_equations.txt"
    trace = Trace(
        claim="x = x => x = y",
        source="x = x",
        target="x = y",
        routes_tried=["finite_countermodel"],
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        verification_status=VerificationStatus.REFUTED,
        certificate=Certificate(TerminalForm.FINITE_COUNTERMODEL, "x = x => x = y", payload={"model": {}}),
        metadata={"compiled_route": "finite_countermodel", "source_idx": 0, "target_idx": 1},
    )
    traces_path.write_text(json.dumps([trace.to_dict()], indent=2, sort_keys=True), encoding="utf-8")
    equations_path.write_text("x = x\nx = y\nx = z\nx * y = x\nx * y = y\n", encoding="utf-8")
    return traces_path, equations_path, None


def _validate_traces(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"path": str(path), "trace_count": len(data), "valid": True}
    if isinstance(data, dict):
        traces = data.get("traces") or data.get("records") or []
        return {"path": str(path), "trace_count": len(traces) if isinstance(traces, list) else None, "valid": True}
    raise ValueError(f"unsupported traces JSON shape: {path}")


def _validate_equations(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {"path": str(path), "line_count": len(lines), "sample": lines[:3], "valid": bool(lines)}


def _paths(out_dir: Path) -> dict[str, Path]:
    return {
        "progress": out_dir / "progress.jsonl",
        "asset_validation": out_dir / "asset_validation.json",
        "store": out_dir / "lawbook.sqlite",
        "lawbook_before": out_dir / "lawbook_store_summary_before.json",
        "lawbook_after": out_dir / "lawbook_store_summary_after.json",
        "derived_before": out_dir / "derived_before.jsonl",
        "derived_after": out_dir / "derived_after.jsonl",
        "outcomes_before": out_dir / "pair_outcomes_before.jsonl",
        "outcomes_after": out_dir / "pair_outcomes_after.jsonl",
        "diagnostics_before": out_dir / "diagnostics_before.json",
        "diagnostics_after": out_dir / "diagnostics_after.json",
        "route_policy": out_dir / "route_policy.json",
        "route_policy_stats": out_dir / "route_policy_stats.json",
        "frontier": out_dir / "frontier.jsonl",
        "frontier_summary": out_dir / "frontier_summary.json",
        "schedule": out_dir / "schedule.jsonl",
        "schedule_summary": out_dir / "schedule_summary.json",
        "task_queue": out_dir / "task_queue.jsonl",
        "task_queue_summary": out_dir / "task_queue_summary.json",
        "finite_results": out_dir / "finite_results.jsonl",
        "finite_summary": out_dir / "finite_countermodel_summary.json",
        "import_summary": out_dir / "countermodel_import_summary.json",
        "new_certificates": out_dir / "new_certificates.jsonl",
        "residual_queue": out_dir / "residual_queue.jsonl",
        "task_outcome_ledger": out_dir / "task_outcome_ledger.jsonl",
        "duplicate_certificates": out_dir / "duplicate_certificates.jsonl",
        "residual_obstruction_candidates": out_dir / "residual_obstruction_candidates.jsonl",
        "episode_diagnostics_json": out_dir / "assimilation_episode_diagnostics.json",
        "episode_diagnostics_md": out_dir / "assimilation_episode_diagnostics.md",
        "oracle_probe": out_dir / "oracle_probe.json",
        "summary_json": out_dir / "certificate_assimilation_summary.json",
        "report_json": out_dir / "certificate_assimilation_report.json",
        "report_md": out_dir / "certificate_assimilation_report.md",
    }


def _write_result_reports(result: CertificateAssimilationResult, paths: dict[str, Path]) -> None:
    _write_json(result.summary.to_dict(), paths["summary_json"])
    _write_json(result.to_dict(), paths["report_json"])
    summary = result.summary
    lines = [
        "# Certificate Processing and Assimilation Pipeline",
        "",
        f"- ok: `{summary.ok}`",
        f"- real asset mode: `{summary.real_asset_mode}`",
        f"- synthetic fallback used: `{summary.synthetic_fallback_used}`",
        f"- primitive certificates: `{summary.primitive_count_before}` -> `{summary.primitive_count_after}`",
        f"- derived certificates: `{summary.derived_count_before}` -> `{summary.derived_count_after}`",
        f"- outcome rows: `{summary.outcome_row_count_before}` -> `{summary.outcome_row_count_after}`",
        f"- frontier/scheduled/tasks: `{summary.frontier_count}` / `{summary.scheduled_count}` / `{summary.task_count}`",
        f"- finite verified/imported: `{summary.finite_executor_verified_count}` / `{summary.imported_count}`",
        f"- duplicates: `{summary.duplicate_count}`",
        f"- residual count: `{summary.residual_count}`",
        f"- import rate: `{summary.import_rate:.3f}`",
        f"- frontier known-pair skipped: `{summary.frontier_known_pair_skipped_count}`",
        f"- frontier episode-duplicate skipped: `{summary.frontier_episode_duplicate_skipped_count}`",
        f"- elapsed seconds: `{summary.elapsed_sec:.2f}`",
        "",
        "## Warnings",
        "",
        *(f"- {warning}" for warning in summary.warnings),
        "",
        "## Errors",
        "",
        *(f"- {error}" for error in summary.errors),
        "",
        "## Truth Boundary",
        "",
        TRUTH_BOUNDARY_NOTE,
    ]
    paths["report_md"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_diagnostics_markdown(diagnostics: dict[str, Any], path: Path) -> None:
    summary = diagnostics.get("summary", {})
    lines = [
        "# Assimilation Episode Diagnostics",
        "",
        "## Episode Summary",
        "",
        f"- task_count: `{summary.get('task_count', 0)}`",
        f"- verified_count: `{summary.get('verified_count', 0)}`",
        f"- imported_count: `{summary.get('imported_count', 0)}`",
        f"- duplicate_count: `{summary.get('duplicate_count', 0)}`",
        f"- residual_count: `{summary.get('residual_count', 0)}`",
        f"- import_rate: `{summary.get('import_rate', 0.0):.3f}`",
        f"- unique_import_rate: `{summary.get('unique_import_rate', 0.0):.3f}`",
        f"- duplicate_rate: `{summary.get('duplicate_rate', 0.0):.3f}`",
        "",
        "## Outcome Ledger",
        "",
        "Every scheduled task has one final outcome row in `task_outcome_ledger.jsonl`.",
        "",
        "## Imported Certificates",
        "",
        f"- imported_count: `{summary.get('imported_count', 0)}`",
        "",
        "## Duplicate Certificates",
        "",
        f"- duplicate_count: `{summary.get('duplicate_count', 0)}`",
        "",
        "## Residual / Obstruction Candidates",
        "",
        f"- residual_count: `{summary.get('residual_count', 0)}`",
        f"- not_found_count: `{summary.get('not_found_count', 0)}`",
        f"- verification_failed_count: `{summary.get('verification_failed_count', 0)}`",
        "",
        "## Consistency Checks",
        "",
        *(
            f"- {key}: `{value}`"
            for key, value in diagnostics.get("consistency_checks", {}).items()
        ),
        "",
        "## Safety Notes",
        "",
        "Duplicates are not promoted. Finite search misses are residual evidence only. Scheduler/advisory rows are not truth.",
        "",
        "## Which Residuals Should Be Tried Next?",
        "",
        *(
            f"- `{row.get('task_id')}` {row.get('route')} priority={row.get('priority')} reason={row.get('reason')}"
            for row in diagnostics.get("try_next", [])[:5]
        ),
        "",
        "## Which Route/Constructor Had The Best Yield?",
        "",
        f"- best_yield_route: `{summary.get('best_yield_route')}`",
        "",
        "## Truth Boundary",
        "",
        TRUTH_BOUNDARY_NOTE,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_empty_episode_artifacts(paths: dict[str, Path]) -> None:
    _write_jsonl([], paths["task_outcome_ledger"])
    _write_jsonl([], paths["duplicate_certificates"])
    _write_jsonl([], paths["residual_obstruction_candidates"])
    _write_jsonl([], paths["residual_queue"])
    _write_jsonl([], paths["new_certificates"])
    diagnostics = _episode_diagnostics([])
    _write_json(diagnostics, paths["episode_diagnostics_json"])
    _write_diagnostics_markdown(diagnostics, paths["episode_diagnostics_md"])


def _read_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(payload: Any, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "none")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

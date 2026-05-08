"""Episode Runner v2: bounded execution over Frontier v2 task queues.

The runner executes only certificate-capable ``finite_countermodel_search``
tasks. Every other Frontier v2 task kind is preserved as advisory trace memory.
Replay, route policy, residual atlas, and next frontier artifacts are
regenerated as scheduling pressure only; they do not cross the terminal truth
boundary.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.continuation_traces import ContinuationTrace, ContinuationTraceStore, make_trace_id
from mathgraph.countermodel_importer import import_finite_countermodel_results
from mathgraph.finite_countermodel_executor import run_finite_countermodel_tasks
from mathgraph.frontier_v2 import build_frontier_v2_from_atlas
from mathgraph.hashing import content_id
from mathgraph.lawbook_store import LawbookStore
from mathgraph.m0_audit import audit_m0_store
from mathgraph.replay_engine import ReplayReport, replay_continuation_traces
from mathgraph.residual_atlas import ResidualAtlasReport, build_residual_atlas_from_traces
from mathgraph.route_policy_v2 import (
    RoutePolicyV2Report,
    build_route_policy_v2_from_replay,
    write_route_policy_v2,
)
from mathgraph.terminal_contract import ProvenanceType, TerminalForm, TrustLevel, VerifierBoundary

EPISODE_V2_WARNINGS = [
    "Only finite_countermodel_search is executable in Episode Runner v2.",
    "Advisory task kinds are not certificates.",
    "Finite search failure is not proof.",
    "Importer/revalidation decides finite refutation promotion.",
    "Replay, route policy, residual atlas, and frontier outputs are advisory.",
]

EXECUTABLE_TASK_KIND = "finite_countermodel_search"


@dataclass(frozen=True)
class EpisodeRunnerV2Config:
    frontier_task_queue_jsonl: str
    out_dir: str
    store_path: str
    episode_id: str | None = None
    max_tasks: int = 100
    max_countermodel_order: int = 3
    exhaustive_order_limit: int = 3
    random_tables_per_order: int = 0
    audit_after_import: bool = True
    build_replay: bool = True
    build_route_policy: bool = True
    build_residual_atlas: bool = True
    build_next_frontier: bool = True
    next_frontier_max_tasks: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeRunnerV2Config":
        return cls(**dict(data))


@dataclass(frozen=True)
class EpisodeTaskResult:
    task_id: str
    task_kind: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    status: str
    executable: bool
    promoted: bool
    certificate_id: str | None
    terminal_form: str | None
    trust_level: str | None
    verifier_boundary: str | None
    root_label: str | None
    constructor_family: str | None
    route_key: str | None
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeTaskResult":
        return cls(**dict(data))


@dataclass(frozen=True)
class EpisodeRunnerV2Report:
    episode_id: str
    status: str
    attempted_tasks: int
    executable_tasks: int
    advisory_tasks: int
    promoted_certificates: int
    verified_false: int
    constructor_failed: int
    residual_count: int
    outputs: dict[str, str]
    summary: dict[str, Any]
    task_results: list[EpisodeTaskResult]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "status": self.status,
            "attempted_tasks": self.attempted_tasks,
            "executable_tasks": self.executable_tasks,
            "advisory_tasks": self.advisory_tasks,
            "promoted_certificates": self.promoted_certificates,
            "verified_false": self.verified_false,
            "constructor_failed": self.constructor_failed,
            "residual_count": self.residual_count,
            "outputs": dict(self.outputs),
            "summary": dict(self.summary),
            "task_results": [result.to_dict() for result in self.task_results],
            "warnings": list(self.warnings),
            "advisory_outputs": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeRunnerV2Report":
        return cls(
            episode_id=str(data.get("episode_id") or ""),
            status=str(data.get("status") or ""),
            attempted_tasks=int(data.get("attempted_tasks", 0) or 0),
            executable_tasks=int(data.get("executable_tasks", 0) or 0),
            advisory_tasks=int(data.get("advisory_tasks", 0) or 0),
            promoted_certificates=int(data.get("promoted_certificates", 0) or 0),
            verified_false=int(data.get("verified_false", 0) or 0),
            constructor_failed=int(data.get("constructor_failed", 0) or 0),
            residual_count=int(data.get("residual_count", 0) or 0),
            outputs=dict(data.get("outputs") or {}),
            summary=dict(data.get("summary") or {}),
            task_results=[EpisodeTaskResult.from_dict(row) for row in data.get("task_results", [])],
            warnings=list(data.get("warnings") or []),
        )


def run_episode_v2(config: EpisodeRunnerV2Config | dict[str, Any]) -> EpisodeRunnerV2Report:
    config = config if isinstance(config, EpisodeRunnerV2Config) else EpisodeRunnerV2Config.from_dict(config)
    started = time.perf_counter()
    episode_id = config.episode_id or f"episode_v2_{int(time.time() * 1000)}"
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _ensure_store(config.store_path)
    input_rows = _read_jsonl(config.frontier_task_queue_jsonl)[: max(0, config.max_tasks)]
    executable_rows = [row for row in input_rows if str(row.get("task_kind")) == EXECUTABLE_TASK_KIND]
    advisory_rows = [row for row in input_rows if str(row.get("task_kind")) != EXECUTABLE_TASK_KIND]

    outputs = _base_outputs(out_dir)
    _write_jsonl(input_rows, Path(outputs["input_frontier_tasks_jsonl"]))
    _write_jsonl(executable_rows, Path(outputs["executable_tasks_jsonl"]))
    _write_jsonl(advisory_rows, Path(outputs["advisory_tasks_jsonl"]))

    executor_by_task: dict[str, dict[str, Any]] = {}
    importer_by_task: dict[str, dict[str, Any]] = {}
    import_summary: dict[str, Any] = {"results": [], "summary": {"imported": 0}, "config": {}, "created_ts": _now()}
    finite_results_path = Path(outputs["finite_countermodel_results_jsonl"])
    import_summary_path = Path(outputs["countermodel_import_summary_json"])

    if executable_rows:
        run_finite_countermodel_tasks(
            {
                "task_queue_jsonl": outputs["executable_tasks_jsonl"],
                "out_jsonl": str(finite_results_path),
                "max_tasks": len(executable_rows),
                "max_order": config.max_countermodel_order,
                "random_tables_per_order": config.random_tables_per_order,
                "exhaustive_order_limit": config.exhaustive_order_limit,
                "stop_after_first": True,
            }
        )
        executor_rows = _read_jsonl(str(finite_results_path))
        executor_by_task = {str(row.get("task_id")): row for row in executor_rows}
        import_run = import_finite_countermodel_results(
            {
                "results_jsonl": str(finite_results_path),
                "store_path": config.store_path,
                "out_json": str(import_summary_path),
                "revalidate": True,
                "allow_duplicate_certificates": False,
            }
        )
        import_summary = import_run.to_dict()
        importer_by_task = {str(row.task_id): row.to_dict() for row in import_run.results}
    else:
        _write_jsonl([], finite_results_path)
        _write_json(import_summary, import_summary_path)

    task_results: list[EpisodeTaskResult] = []
    traces: list[ContinuationTrace] = []
    for row in executable_rows:
        result = _executable_result(row, executor_by_task.get(str(row.get("task_id")), {}), importer_by_task)
        task_results.append(result)
        traces.append(_trace_from_result(episode_id, row, result, attempted=True))
    for row in advisory_rows:
        result = _advisory_result(row)
        task_results.append(result)
        traces.append(_trace_from_result(episode_id, row, result, attempted=False))

    trace_store_path = outputs["continuation_traces_jsonl"]
    ContinuationTraceStore(trace_store_path).append_many(traces)

    audit_payload = None
    if config.audit_after_import:
        audit_payload = audit_m0_store(config.store_path).to_dict()
        outputs["audit_report_json"] = str(out_dir / "audit_report.json")
        _write_json(audit_payload, Path(outputs["audit_report_json"]))

    replay: ReplayReport | None = None
    policy: RoutePolicyV2Report | None = None
    atlas: ResidualAtlasReport | None = None
    if config.build_replay or config.build_route_policy or config.build_residual_atlas or config.build_next_frontier:
        replay_dir = str(out_dir / "replay") if config.build_replay else None
        replay = replay_continuation_traces(trace_store_path, replay_dir)
        outputs.update(replay.outputs)
    if config.build_route_policy or config.build_residual_atlas or config.build_next_frontier:
        policy = build_route_policy_v2_from_replay(replay)
        if config.build_route_policy:
            outputs.update(write_route_policy_v2(policy, str(out_dir / "route_policy_v2")))
    if config.build_residual_atlas or config.build_next_frontier:
        atlas = build_residual_atlas_from_traces(
            trace_store_path,
            route_policy=policy,
            out_dir=str(out_dir / "residual_atlas") if config.build_residual_atlas else None,
            run_id=f"{episode_id}_residual_atlas",
        )
        outputs.update(atlas.outputs)
    if config.build_next_frontier:
        frontier = build_frontier_v2_from_atlas(
            atlas,
            max_tasks=config.next_frontier_max_tasks,
            out_dir=str(out_dir / "next_frontier_v2"),
            run_id=f"{episode_id}_next_frontier_v2",
        )
        outputs.update(frontier.outputs)

    elapsed = time.perf_counter() - started
    summary = _summary(
        task_results,
        elapsed=elapsed,
        audit=audit_payload,
        import_summary=import_summary.get("summary", {}),
        replay=replay,
        policy=policy,
        atlas=atlas,
    )
    report = EpisodeRunnerV2Report(
        episode_id=episode_id,
        status="completed",
        attempted_tasks=len(input_rows),
        executable_tasks=len(executable_rows),
        advisory_tasks=len(advisory_rows),
        promoted_certificates=sum(1 for result in task_results if result.promoted),
        verified_false=sum(1 for result in task_results if result.status == "verified_false"),
        constructor_failed=sum(1 for result in task_results if result.status == "constructor_failed"),
        residual_count=sum(1 for result in task_results if result.status in {"residual", "skipped"}),
        outputs=outputs,
        summary=summary,
        task_results=task_results,
        warnings=list(EPISODE_V2_WARNINGS),
    )
    _write_json(report.to_dict(), Path(outputs["episode_v2_report_json"]))
    _write_markdown(report, Path(outputs["episode_v2_report_md"]))
    return report


def _executable_result(
    task: dict[str, Any],
    executor_row: dict[str, Any],
    importer_by_task: dict[str, dict[str, Any]],
) -> EpisodeTaskResult:
    task_id = str(task.get("task_id") or _task_id(task))
    import_row = importer_by_task.get(task_id, {})
    certificate_id = import_row.get("certificate_id") or executor_row.get("certificate_id")
    if import_row.get("imported"):
        status = "verified_false"
        promoted = True
        terminal = TerminalForm.REFUTATION_CERTIFICATE
        trust = TrustLevel.FINITE_VERIFIED
        boundary = VerifierBoundary.IMPORTER_REVALIDATED
    elif executor_row.get("status") == "finite_countermodel_found":
        status = "verification_failed"
        promoted = False
        terminal = TerminalForm.NONE
        trust = TrustLevel.ADVISORY_ROUTE
        boundary = VerifierBoundary.NOT_VERIFIED
        certificate_id = None
    elif executor_row.get("status") == "parse_failed":
        status = "parse_failed"
        promoted = False
        terminal = TerminalForm.NONE
        trust = TrustLevel.ADVISORY_ROUTE
        boundary = VerifierBoundary.NOT_VERIFIED
        certificate_id = None
    elif executor_row.get("status") == "error":
        status = "error"
        promoted = False
        terminal = TerminalForm.NONE
        trust = TrustLevel.ERROR
        boundary = VerifierBoundary.ERROR
        certificate_id = None
    elif executor_row.get("status") == "no_countermodel_found":
        status = "constructor_failed"
        promoted = False
        terminal = TerminalForm.NONE
        trust = TrustLevel.ADVISORY_ROUTE
        boundary = VerifierBoundary.NOT_VERIFIED
        certificate_id = None
    else:
        status = "residual"
        promoted = False
        terminal = TerminalForm.NONE
        trust = TrustLevel.ADVISORY_ROUTE
        boundary = VerifierBoundary.NOT_VERIFIED
        certificate_id = None
    return EpisodeTaskResult(
        task_id=task_id,
        task_kind=EXECUTABLE_TASK_KIND,
        source=str(task.get("source") or ""),
        target=str(task.get("target") or ""),
        source_idx=_optional_int(task.get("source_idx")),
        target_idx=_optional_int(task.get("target_idx")),
        status=status,
        executable=True,
        promoted=promoted,
        certificate_id=certificate_id if promoted else None,
        terminal_form=terminal,
        trust_level=trust,
        verifier_boundary=boundary,
        root_label=_optional_str(task.get("root_label")),
        constructor_family=_optional_str(task.get("constructor_family")),
        route_key=_optional_str(task.get("route_key") or task.get("route")),
        warnings=list(EPISODE_V2_WARNINGS),
        evidence={
            "executor": dict(executor_row),
            "importer": dict(import_row),
            "frontier_task": dict(task),
            "finite_search_failure_is_not_proof": True,
        },
    )


def _advisory_result(task: dict[str, Any]) -> EpisodeTaskResult:
    task_kind = str(task.get("task_kind") or "unknown_advisory_task")
    evidence = dict(task.get("evidence") or {})
    evidence.update(
        {
            "advisory_task_kind": task_kind,
            "reason": task.get("reason"),
            "not_executed_by_episode_runner_v2": True,
            "frontier_task": dict(task),
        }
    )
    return EpisodeTaskResult(
        task_id=str(task.get("task_id") or _task_id(task)),
        task_kind=task_kind,
        source=str(task.get("source") or ""),
        target=str(task.get("target") or ""),
        source_idx=_optional_int(task.get("source_idx")),
        target_idx=_optional_int(task.get("target_idx")),
        status="skipped",
        executable=False,
        promoted=False,
        certificate_id=None,
        terminal_form=TerminalForm.NONE,
        trust_level=TrustLevel.ADVISORY_ROUTE,
        verifier_boundary=VerifierBoundary.NOT_VERIFIED,
        root_label=_optional_str(task.get("root_label")),
        constructor_family=_optional_str(task.get("constructor_family")),
        route_key=_optional_str(task.get("route_key") or task.get("route")),
        warnings=list(EPISODE_V2_WARNINGS),
        evidence=evidence,
    )


def _trace_from_result(
    episode_id: str,
    task: dict[str, Any],
    result: EpisodeTaskResult,
    *,
    attempted: bool,
) -> ContinuationTrace:
    frontier_evidence = dict(task.get("evidence") or {})
    claim_id = str(task.get("claim_id") or content_id("claim", {"source": result.source, "target": result.target}, n=20))
    status = result.status if result.status in {"verified_false", "constructor_failed", "parse_failed", "verification_failed", "residual", "skipped", "error"} else "residual"
    near = float(frontier_evidence.get("best_near_miss_score") or frontier_evidence.get("near_miss_score") or 0.0)
    compression = float(frontier_evidence.get("residual_compression_delta") or 0.0)
    route_type = result.route_key or str(task.get("route") or result.task_kind)
    payload = {
        "episode_id": episode_id,
        "claim_id": claim_id,
        "source": result.source,
        "target": result.target,
        "source_idx": result.source_idx,
        "target_idx": result.target_idx,
        "root_label": result.root_label,
        "root_score": _optional_float(task.get("root_score")),
        "basin_label": result.root_label or task.get("basin_label"),
        "detector_evidence": dict(task.get("detector_evidence") or {}),
        "route_type": route_type,
        "constructor_family": result.constructor_family,
        "constructor_config": {
            "task_kind": result.task_kind,
            "max_order_source": "episode_runner_v2",
        },
        "status": status,
        "terminal_form": result.terminal_form,
        "trust_level": result.trust_level,
        "provenance_type": ProvenanceType.PRIMITIVE if result.promoted else ProvenanceType.SYSTEM,
        "verifier_boundary": result.verifier_boundary,
        "certificate_id": result.certificate_id,
        "obstruction_label": _optional_str(task.get("obstruction_label")),
        "attempted": attempted,
        "verified": result.status == "verified_false",
        "promoted": result.promoted,
        "known_skipped": False,
        "near_miss_score": near,
        "residual_compression_delta": compression,
        "novelty_score": float(frontier_evidence.get("novelty_score") or task.get("novelty_score") or 0.0),
        "elapsed_sec": float(result.evidence.get("executor", {}).get("elapsed_sec") or 0.0),
        "warnings": list(result.warnings),
        "evidence": {
            "episode_runner_v2": True,
            "task_result": result.to_dict(),
            "frontier_task": dict(task),
            "advisory_only_unless_promoted_certificate": not result.promoted,
        },
    }
    payload["trace_id"] = make_trace_id(payload)
    return ContinuationTrace.from_dict(payload)


def _summary(
    results: list[EpisodeTaskResult],
    *,
    elapsed: float,
    audit: dict[str, Any] | None,
    import_summary: dict[str, Any],
    replay: ReplayReport | None,
    policy: RoutePolicyV2Report | None,
    atlas: ResidualAtlasReport | None,
) -> dict[str, Any]:
    by_status = Counter(result.status for result in results)
    by_kind = Counter(result.task_kind for result in results)
    return {
        "elapsed_sec": round(elapsed, 6),
        "task_status_counts": dict(sorted(by_status.items())),
        "task_kind_counts": dict(sorted(by_kind.items())),
        "import_summary": dict(import_summary or {}),
        "audit": _audit_summary(audit),
        "replay_trace_count": replay.trace_count if replay else 0,
        "route_policy_card_count": policy.card_count if policy else 0,
        "residual_atlas_case_count": atlas.case_count if atlas else 0,
        "advisory_outputs": True,
        "trust_boundary": {
            "only_executable_task_kind": EXECUTABLE_TASK_KIND,
            "finite_search_failure_is_not_proof": True,
            "importer_revalidation_promotes_refutations": True,
        },
    }


def _audit_summary(audit: dict[str, Any] | None) -> dict[str, Any] | None:
    if audit is None:
        return None
    return {
        "passed": bool(audit.get("passed")),
        "critical_count": int(audit.get("critical_count", 0) or 0),
        "warning_count": int(audit.get("warning_count", 0) or 0),
        "finding_count": int(audit.get("finding_count", 0) or 0),
    }


def _base_outputs(out_dir: Path) -> dict[str, str]:
    return {
        "episode_v2_report_json": str(out_dir / "episode_v2_report.json"),
        "episode_v2_report_md": str(out_dir / "episode_v2_report.md"),
        "input_frontier_tasks_jsonl": str(out_dir / "input_frontier_tasks.jsonl"),
        "executable_tasks_jsonl": str(out_dir / "executable_tasks.jsonl"),
        "advisory_tasks_jsonl": str(out_dir / "advisory_tasks.jsonl"),
        "finite_countermodel_results_jsonl": str(out_dir / "finite_countermodel_results.jsonl"),
        "countermodel_import_summary_json": str(out_dir / "countermodel_import_summary.json"),
        "continuation_traces_jsonl": str(out_dir / "continuation_traces.jsonl"),
    }


def _ensure_store(store_path: str) -> None:
    store = LawbookStore(store_path)
    try:
        store.init_schema()
    finally:
        store.close()


def _task_id(row: dict[str, Any]) -> str:
    return content_id(
        "episode_v2_task",
        {
            "task_kind": row.get("task_kind"),
            "source": row.get("source"),
            "target": row.get("target"),
            "source_idx": row.get("source_idx"),
            "target_idx": row.get("target_idx"),
            "route": row.get("route") or row.get("route_key"),
        },
        n=20,
    )


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return rows
    with p.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(report: EpisodeRunnerV2Report, path: Path) -> None:
    lines = [
        "# Episode Runner v2 Report",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| attempted_tasks | {report.attempted_tasks} |",
        f"| executable_tasks | {report.executable_tasks} |",
        f"| advisory_tasks | {report.advisory_tasks} |",
        f"| promoted_certificates | {report.promoted_certificates} |",
        f"| verified_false | {report.verified_false} |",
        f"| constructor_failed | {report.constructor_failed} |",
        f"| residual_count | {report.residual_count} |",
        "",
        "## Task Results",
        "",
        "| task_kind | executable | status | promoted | certificate_id |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in report.task_results:
        lines.append(
            f"| {result.task_kind} | {str(result.executable).lower()} | {result.status} | "
            f"{str(result.promoted).lower()} | {result.certificate_id or ''} |"
        )
    lines.extend(["", "## Outputs", ""])
    for key, value in sorted(report.outputs.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "- only finite_countermodel_search is executable",
            "- advisory task kinds are not certificates",
            "- finite search failure is not proof",
            "- importer/revalidation decides finite refutation promotion",
            "- replay/policy/atlas/frontier are advisory",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


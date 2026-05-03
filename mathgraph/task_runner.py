"""Mock-safe execution shell for planned certificate tasks."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from mathgraph.certificates import TerminalForm, VerificationStatus
from mathgraph.hashing import sha256_hex
from mathgraph.task_planner import CertificateTask


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    task_kind: str
    claim: str | None
    source: str | None
    target: str | None
    source_idx: int | str | None
    target_idx: int | str | None
    route: str | None
    status: str
    terminal_form: str
    verification_status: str
    executor: str
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_kind": self.task_kind,
            "claim": self.claim,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "route": self.route,
            "status": self.status,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "executor": self.executor,
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskOutcome":
        return cls(
            task_id=str(data.get("task_id", "malformed_task")),
            task_kind=str(data.get("task_kind", "unknown")),
            claim=data.get("claim"),
            source=data.get("source"),
            target=data.get("target"),
            source_idx=data.get("source_idx"),
            target_idx=data.get("target_idx"),
            route=data.get("route"),
            status=str(data.get("status", "malformed_task")),
            terminal_form=str(data.get("terminal_form", TerminalForm.NAMED_OBSTRUCTION.value)),
            verification_status=str(data.get("verification_status", "UNKNOWN")),
            executor=str(data.get("executor", "mathgraph.task_runner.mock")),
            evidence=dict(data.get("evidence", {})),
            warnings=list(data.get("warnings", [])),
            errors=list(data.get("errors", [])),
            created=data.get("created") or datetime.now(timezone.utc).isoformat(),
        )


@dataclass(frozen=True)
class TaskRunSummary:
    task_count: int
    outcome_count: int
    status_counts: dict[str, int]
    task_kind_counts: dict[str, int]
    terminal_form_counts: dict[str, int]
    verification_status_counts: dict[str, int]
    route_counts: dict[str, int]
    executor_counts: dict[str, int]
    known_certificate_count: int
    mock_proof_template_count: int
    mock_countermodel_queue_count: int
    obstruction_count: int
    failed_count: int
    malformed_count: int
    warnings_count: int
    errors_count: int
    residual_count: int
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_count": self.task_count,
            "outcome_count": self.outcome_count,
            "status_counts": dict(self.status_counts),
            "task_kind_counts": dict(self.task_kind_counts),
            "terminal_form_counts": dict(self.terminal_form_counts),
            "verification_status_counts": dict(self.verification_status_counts),
            "route_counts": dict(self.route_counts),
            "executor_counts": dict(self.executor_counts),
            "known_certificate_count": self.known_certificate_count,
            "mock_proof_template_count": self.mock_proof_template_count,
            "mock_countermodel_queue_count": self.mock_countermodel_queue_count,
            "obstruction_count": self.obstruction_count,
            "failed_count": self.failed_count,
            "malformed_count": self.malformed_count,
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "residual_count": self.residual_count,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskRunSummary":
        return cls(
            task_count=int(data.get("task_count", 0)),
            outcome_count=int(data.get("outcome_count", 0)),
            status_counts=dict(data.get("status_counts", {})),
            task_kind_counts=dict(data.get("task_kind_counts", {})),
            terminal_form_counts=dict(data.get("terminal_form_counts", {})),
            verification_status_counts=dict(data.get("verification_status_counts", {})),
            route_counts=dict(data.get("route_counts", {})),
            executor_counts=dict(data.get("executor_counts", {})),
            known_certificate_count=int(data.get("known_certificate_count", 0)),
            mock_proof_template_count=int(data.get("mock_proof_template_count", 0)),
            mock_countermodel_queue_count=int(data.get("mock_countermodel_queue_count", 0)),
            obstruction_count=int(data.get("obstruction_count", 0)),
            failed_count=int(data.get("failed_count", 0)),
            malformed_count=int(data.get("malformed_count", 0)),
            warnings_count=int(data.get("warnings_count", 0)),
            errors_count=int(data.get("errors_count", 0)),
            residual_count=int(data.get("residual_count", 0)),
            created=data.get("created") or datetime.now(timezone.utc).isoformat(),
        )


def execute_certificate_task(task: CertificateTask | dict[str, Any], *, mode: str = "mock") -> TaskOutcome:
    if mode != "mock":
        raise ValueError("only mock task execution mode is currently supported")

    try:
        normalized = _coerce_task(task)
    except (KeyError, TypeError, ValueError) as exc:
        return _malformed_outcome(task, str(exc))

    if normalized.task_kind == "known_certificate" or normalized.status == "not_needed":
        advice = normalized.advice
        verification = str(advice.get("verification_status") or _known_status(normalized.terminal_goal))
        return _outcome(
            normalized,
            status="known_certificate" if verification in {"VERIFIED", "REFUTED"} else "skipped_known",
            terminal_form=normalized.terminal_goal,
            verification_status=verification,
            evidence={
                "known_claim": normalized.evidence.get("known_claim"),
                "exact_match": normalized.evidence.get("exact_match", True),
                "note": "Existing lawbook certificate; no mock execution performed.",
            },
            warnings=["No new task required unless re-verification is requested."],
        )

    if normalized.task_kind == "proof_template":
        return _outcome(
            normalized,
            status="mock_proof_template_generated",
            terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
            verification_status="UNKNOWN",
            evidence={
                "proposed_route": normalized.route,
                "task": _compact_task(normalized),
                "note": "No proof was generated and no verifier was invoked.",
            },
            warnings=[*normalized.warnings, "Mock proof template is not VERIFIED_PROOF."],
        )

    if normalized.task_kind == "finite_countermodel_search":
        return _outcome(
            normalized,
            status="mock_countermodel_search_queued",
            terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
            verification_status="UNKNOWN",
            evidence={
                "proposed_route": normalized.route,
                "search_placeholder": True,
                "task": _compact_task(normalized),
                "note": "No finite model was searched.",
            },
            warnings=[*normalized.warnings, "Mock countermodel queue is not FINITE_COUNTERMODEL."],
        )

    if normalized.task_kind == "obstruction_analysis":
        return _outcome(
            normalized,
            status="mock_obstruction_recorded",
            terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
            verification_status=VerificationStatus.OBSTRUCTED.value,
            evidence={
                "blockers": normalized.failure_modes,
                "residual": True,
                "task": _compact_task(normalized),
            },
            warnings=[*normalized.warnings, "Obstruction analysis is not a truth claim."],
        )

    return _outcome(
        normalized,
        status="malformed_task",
        terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
        verification_status="UNKNOWN",
        evidence={"task": _compact_task(normalized)},
        warnings=["Unknown task kind; no execution performed."],
        errors=[f"unsupported task_kind: {normalized.task_kind}"],
    )


def execute_many_certificate_tasks(
    tasks: Iterable[CertificateTask | dict[str, Any]],
    *,
    mode: str = "mock",
    limit: int | None = None,
) -> list[TaskOutcome]:
    selected = list(tasks)
    if limit is not None:
        selected = selected[:limit]
    return [execute_certificate_task(task, mode=mode) for task in selected]


def summarize_task_outcomes(outcomes: Iterable[TaskOutcome | dict[str, Any]]) -> TaskRunSummary:
    normalized = [_coerce_outcome(outcome) for outcome in outcomes]
    status_counts = Counter(outcome.status for outcome in normalized)
    return TaskRunSummary(
        task_count=len(normalized),
        outcome_count=len(normalized),
        status_counts=dict(status_counts),
        task_kind_counts=dict(Counter(outcome.task_kind for outcome in normalized)),
        terminal_form_counts=dict(Counter(outcome.terminal_form for outcome in normalized)),
        verification_status_counts=dict(Counter(outcome.verification_status for outcome in normalized)),
        route_counts=dict(Counter(outcome.route for outcome in normalized if outcome.route)),
        executor_counts=dict(Counter(outcome.executor for outcome in normalized)),
        known_certificate_count=status_counts.get("known_certificate", 0)
        + status_counts.get("skipped_known", 0),
        mock_proof_template_count=status_counts.get("mock_proof_template_generated", 0),
        mock_countermodel_queue_count=status_counts.get("mock_countermodel_search_queued", 0),
        obstruction_count=status_counts.get("mock_obstruction_recorded", 0),
        failed_count=status_counts.get("failed", 0),
        malformed_count=status_counts.get("malformed_task", 0),
        warnings_count=sum(len(outcome.warnings) for outcome in normalized),
        errors_count=sum(len(outcome.errors) for outcome in normalized),
        residual_count=len(residual_outcomes(normalized)),
    )


def residual_outcomes(outcomes: Iterable[TaskOutcome | dict[str, Any]]) -> list[TaskOutcome]:
    return [
        outcome
        for outcome in (_coerce_outcome(item) for item in outcomes)
        if outcome.status not in {"known_certificate", "skipped_known"}
    ]


def write_outcomes_jsonl(outcomes: Iterable[TaskOutcome | dict[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for outcome in outcomes:
            handle.write(json.dumps(_coerce_outcome(outcome).to_dict(), sort_keys=True) + "\n")


def read_outcomes_jsonl(path: str | Path) -> list[TaskOutcome]:
    outcomes: list[TaskOutcome] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                outcomes.append(TaskOutcome.from_dict(json.loads(stripped)))
    return outcomes


def write_outcomes_json(outcomes: Iterable[TaskOutcome | dict[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = [_coerce_outcome(outcome).to_dict() for outcome in outcomes]
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_outcomes_json(path: str | Path) -> list[TaskOutcome]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("outcomes", [])
    return [TaskOutcome.from_dict(item) for item in data]


def task_outcome_hash(outcome: TaskOutcome | dict[str, Any]) -> str:
    return sha256_hex(_coerce_outcome(outcome).to_dict())


def load_tasks_json(path: str | Path) -> list[CertificateTask]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [CertificateTask.from_dict(data)]
    return [CertificateTask.from_dict(item) for item in data]


def load_tasks_jsonl(path: str | Path) -> list[CertificateTask]:
    tasks: list[CertificateTask] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                tasks.append(CertificateTask.from_dict(json.loads(stripped)))
    return tasks


def _coerce_task(task: CertificateTask | dict[str, Any]) -> CertificateTask:
    if isinstance(task, CertificateTask):
        return task
    if isinstance(task, dict):
        return CertificateTask.from_dict(task)
    raise TypeError("task must be a CertificateTask or dict")


def _coerce_outcome(outcome: TaskOutcome | dict[str, Any]) -> TaskOutcome:
    return outcome if isinstance(outcome, TaskOutcome) else TaskOutcome.from_dict(outcome)


def _outcome(
    task: CertificateTask,
    *,
    status: str,
    terminal_form: str,
    verification_status: str,
    evidence: dict[str, Any],
    warnings: list[str],
    errors: list[str] | None = None,
) -> TaskOutcome:
    return TaskOutcome(
        task_id=task.task_id,
        task_kind=task.task_kind,
        claim=task.advice.get("known_claim") or f"{task.source} => {task.target}",
        source=task.source,
        target=task.target,
        source_idx=task.advice.get("source_idx"),
        target_idx=task.advice.get("target_idx"),
        route=task.route,
        status=status,
        terminal_form=terminal_form,
        verification_status=verification_status,
        executor="mathgraph.task_runner.mock",
        evidence=evidence,
        warnings=_unique(warnings),
        errors=errors or [],
    )


def _malformed_outcome(task: Any, error: str) -> TaskOutcome:
    return TaskOutcome(
        task_id="malformed_task",
        task_kind="unknown",
        claim=None,
        source=None,
        target=None,
        source_idx=None,
        target_idx=None,
        route=None,
        status="malformed_task",
        terminal_form=TerminalForm.NAMED_OBSTRUCTION.value,
        verification_status="UNKNOWN",
        executor="mathgraph.task_runner.mock",
        evidence={"raw_task_type": type(task).__name__},
        warnings=["Malformed task was not executed."],
        errors=[error],
    )


def _known_status(terminal_form: str) -> str:
    if terminal_form == TerminalForm.VERIFIED_PROOF.value:
        return VerificationStatus.VERIFIED.value
    if terminal_form == TerminalForm.FINITE_COUNTERMODEL.value:
        return VerificationStatus.REFUTED.value
    return VerificationStatus.OBSTRUCTED.value


def _compact_task(task: CertificateTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "task_kind": task.task_kind,
        "terminal_goal": task.terminal_goal,
        "route": task.route,
        "priority": task.priority,
        "status": task.status,
    }


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

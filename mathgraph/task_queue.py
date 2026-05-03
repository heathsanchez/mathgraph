"""Build constructor-ready task queue rows from scheduled candidates."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id


PROOF_ROUTE_MARKERS = {
    "variable_identification",
    "skeleton_preserving_relabel",
    "direct_substitution_instance",
    "proof_template",
    "broad_split_to_skeleton_preserving_relabel",
}

QUEUE_WARNINGS = [
    "This task is not a proof or refutation until verified.",
    "Do not promote without a verified proof or finite countermodel.",
    "Finite search failure is obstruction evidence only.",
]


@dataclass(frozen=True)
class TaskQueueItem:
    task_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    route: str
    task_kind: str
    terminal_goal: str
    priority: float
    schedule_rank: int
    candidate_origin: str | None
    label: str | None
    required_inputs: list[str]
    steps: list[str]
    success_criteria: list[str]
    failure_modes: list[str]
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "route": self.route,
            "task_kind": self.task_kind,
            "terminal_goal": self.terminal_goal,
            "priority": self.priority,
            "schedule_rank": self.schedule_rank,
            "candidate_origin": self.candidate_origin,
            "label": self.label,
            "required_inputs": list(self.required_inputs),
            "steps": list(self.steps),
            "success_criteria": list(self.success_criteria),
            "failure_modes": list(self.failure_modes),
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskQueueItem":
        return cls(
            task_id=str(data["task_id"]),
            source=str(data["source"]),
            target=str(data["target"]),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            route=str(data["route"]),
            task_kind=str(data["task_kind"]),
            terminal_goal=str(data["terminal_goal"]),
            priority=float(data.get("priority", 0.0)),
            schedule_rank=int(data.get("schedule_rank", 0)),
            candidate_origin=data.get("candidate_origin"),
            label=data.get("label"),
            required_inputs=[str(item) for item in data.get("required_inputs", [])],
            steps=[str(item) for item in data.get("steps", [])],
            success_criteria=[str(item) for item in data.get("success_criteria", [])],
            failure_modes=[str(item) for item in data.get("failure_modes", [])],
            evidence=dict(data.get("evidence", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


@dataclass(frozen=True)
class TaskQueueConfig:
    schedule_jsonl: str
    out_jsonl: str
    max_tasks: int = 1000
    min_priority: float = 0.0
    include_known: bool = False
    default_countermodel_route: str = "finite_countermodel"
    default_proof_route: str = "proof_template"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_jsonl": self.schedule_jsonl,
            "out_jsonl": self.out_jsonl,
            "max_tasks": self.max_tasks,
            "min_priority": self.min_priority,
            "include_known": self.include_known,
            "default_countermodel_route": self.default_countermodel_route,
            "default_proof_route": self.default_proof_route,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskQueueConfig":
        return cls(
            schedule_jsonl=str(data["schedule_jsonl"]),
            out_jsonl=str(data["out_jsonl"]),
            max_tasks=int(data.get("max_tasks", 1000)),
            min_priority=float(data.get("min_priority", 0.0)),
            include_known=bool(data.get("include_known", False)),
            default_countermodel_route=str(data.get("default_countermodel_route", "finite_countermodel")),
            default_proof_route=str(data.get("default_proof_route", "proof_template")),
        )


@dataclass(frozen=True)
class TaskQueueResult:
    tasks: list[dict[str, Any]]
    summary: dict[str, Any]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": list(self.tasks),
            "summary": dict(self.summary),
            "outputs": dict(self.outputs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskQueueResult":
        return cls(
            tasks=list(data.get("tasks", [])),
            summary=dict(data.get("summary", {})),
            outputs=dict(data.get("outputs", {})),
        )


def build_task_queue(config: TaskQueueConfig | dict[str, Any]) -> TaskQueueResult:
    config = config if isinstance(config, TaskQueueConfig) else TaskQueueConfig.from_dict(config)
    rows = _read_jsonl(config.schedule_jsonl)
    tasks: list[TaskQueueItem] = []
    skipped = 0
    for row in rows:
        priority = _priority(row)
        if priority < config.min_priority:
            skipped += 1
            continue
        if not config.include_known and _is_known(row):
            skipped += 1
            continue
        tasks.append(_task_from_row(row, priority, len(tasks) + 1, config))
        if len(tasks) >= config.max_tasks:
            break
    tasks.sort(key=lambda item: (-item.priority, item.schedule_rank, item.source, item.target))
    tasks = [
        TaskQueueItem(**{**task.to_dict(), "schedule_rank": index + 1})
        for index, task in enumerate(tasks)
    ]
    _write_jsonl(tasks, config.out_jsonl)
    summary_path = str(Path(config.out_jsonl).with_name("task_queue_summary.json"))
    summary = _summary(tasks, skipped)
    _write_json(summary, summary_path)
    return TaskQueueResult(
        tasks=[task.to_dict() for task in tasks],
        summary=summary,
        outputs={"jsonl": str(config.out_jsonl), "summary": summary_path},
    )


def _task_from_row(
    row: dict[str, Any],
    priority: float,
    schedule_rank: int,
    config: TaskQueueConfig,
) -> TaskQueueItem:
    route = _route(row, config)
    task_kind, terminal_goal = _task_kind(route)
    candidate_origin = _candidate_origin(row)
    label = row.get("label")
    evidence = {
        "schedule_row": _compact_row(row),
        "score_breakdown": row.get("score_breakdown"),
        "frontier_reason_codes": row.get("frontier_reason_codes") or row.get("metadata", {}).get("frontier_reason_codes"),
        "features": row.get("features") or row.get("metadata", {}).get("features"),
        "candidate_origin": candidate_origin,
        "label": label,
    }
    source = str(row.get("source", ""))
    target = str(row.get("target", ""))
    return TaskQueueItem(
        task_id=content_id(
            "queue_task",
            {"source": source, "target": target, "route": route, "rank": schedule_rank},
        ),
        source=source,
        target=target,
        source_idx=_optional_int(row.get("source_idx")),
        target_idx=_optional_int(row.get("target_idx")),
        route=route,
        task_kind=task_kind,
        terminal_goal=terminal_goal,
        priority=priority,
        schedule_rank=schedule_rank,
        candidate_origin=candidate_origin,
        label=label,
        required_inputs=_required_inputs(task_kind),
        steps=_steps(task_kind),
        success_criteria=_success_criteria(task_kind),
        failure_modes=_failure_modes(task_kind),
        evidence=evidence,
        warnings=list(QUEUE_WARNINGS),
    )


def _route(row: dict[str, Any], config: TaskQueueConfig) -> str:
    for key in ("route", "recommended_route", "top_route", "selected_route"):
        value = row.get(key)
        if value:
            return str(value)
    task_kind = str(row.get("recommended_task_kind", ""))
    if "countermodel" in task_kind:
        return config.default_countermodel_route
    if "proof" in task_kind:
        return config.default_proof_route
    return "obstruction_analysis"


def _priority(row: dict[str, Any]) -> float:
    for key in ("priority", "normalized_priority", "htilt_priority", "frontier_score"):
        value = row.get(key)
        if value is not None:
            return float(value)
    return 0.0


def _task_kind(route: str) -> tuple[str, str]:
    if "finite_countermodel" in route:
        return "finite_countermodel_search", "FINITE_COUNTERMODEL"
    if any(marker in route for marker in PROOF_ROUTE_MARKERS):
        return "proof_template", "VERIFIED_PROOF"
    return "obstruction_analysis", "NAMED_OBSTRUCTION"


def _required_inputs(task_kind: str) -> list[str]:
    if task_kind == "finite_countermodel_search":
        return ["source equation", "target equation", "finite magma constructor family"]
    if task_kind == "proof_template":
        return ["source equation", "target equation", "route-specific transformation map"]
    return ["source equation", "target equation", "structural invariants"]


def _steps(task_kind: str) -> list[str]:
    if task_kind == "finite_countermodel_search":
        return [
            "Parse source and target equations.",
            "Build or select finite magma constructor family.",
            "Search only tables satisfying source.",
            "Check whether target is violated.",
            "Emit finite countermodel certificate if found.",
            "Promote only after finite checker verifies source satisfaction and target violation.",
        ]
    if task_kind == "proof_template":
        return [
            "Parse source and target equations.",
            "Construct route-specific substitution/relabel/collapse map.",
            "Emit proof skeleton.",
            "Run verifier.",
            "Promote only if verifier accepts exact source/target claim.",
        ]
    return [
        "Parse source and target equations.",
        "Extract invariant and structural deltas.",
        "Compare against known obstruction families.",
        "Name obstruction if no certificate is produced.",
        "Do not promote obstruction as truth/refutation.",
    ]


def _success_criteria(task_kind: str) -> list[str]:
    if task_kind == "finite_countermodel_search":
        return [
            "Finite model satisfies source equation.",
            "Same finite model violates target equation.",
            "Finite checker validates the witness.",
        ]
    if task_kind == "proof_template":
        return [
            "Proof artifact addresses the exact source/target claim.",
            "Verifier accepts the exact claim.",
        ]
    return ["Named obstruction record explains why no certificate was produced."]


def _failure_modes(task_kind: str) -> list[str]:
    if task_kind == "finite_countermodel_search":
        return [
            "Finite search fails within selected bounds.",
            "Candidate table fails source satisfaction.",
            "Candidate table does not violate target.",
        ]
    if task_kind == "proof_template":
        return [
            "Transformation map is invalid.",
            "Proof skeleton does not match exact claim.",
            "Verifier rejects artifact.",
        ]
    return [
        "Obstruction family does not fit.",
        "Residual requires a narrower constructor task.",
    ]


def _is_known(row: dict[str, Any]) -> bool:
    return row.get("oracle_status") in {"VERIFIED", "REFUTED"} or row.get("recommended_task_kind") == "known_certificate_review"


def _candidate_origin(row: dict[str, Any]) -> str | None:
    return row.get("candidate_origin") or row.get("metadata", {}).get("candidate_origin")


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "task_id",
        "source",
        "target",
        "source_idx",
        "target_idx",
        "recommended_route",
        "recommended_task_kind",
        "priority",
        "htilt_score",
        "frontier_score",
        "label",
        "candidate_origin",
        "oracle_status",
    ]
    return {key: row.get(key) for key in keys if key in row}


def _summary(tasks: list[TaskQueueItem], skipped: int) -> dict[str, Any]:
    priorities = [task.priority for task in tasks]
    return {
        "task_count": len(tasks),
        "skipped_count": skipped,
        "by_task_kind": dict(Counter(task.task_kind for task in tasks)),
        "by_route": dict(Counter(task.route for task in tasks)),
        "by_terminal_goal": dict(Counter(task.terminal_goal for task in tasks)),
        "priority_min": min(priorities) if priorities else 0.0,
        "priority_max": max(priorities) if priorities else 0.0,
        "priority_mean": sum(priorities) / len(priorities) if priorities else 0.0,
        "warnings": list(QUEUE_WARNINGS),
    }


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(tasks: list[TaskQueueItem], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for task in tasks:
            handle.write(json.dumps(task.to_dict(), sort_keys=True) + "\n")


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

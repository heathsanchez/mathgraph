"""Frontier Builder v2: atlas-guided advisory next-episode tasks."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.residual_atlas import ResidualAtlasReport, ResidualCase

FRONTIER_WARNINGS = [
    "Frontier tasks are advisory work proposals, not truth.",
    "A scheduled task never verifies or refutes a claim.",
    "Finite search failure is not proof.",
    "Only verifier/importer promotes terminal certificates.",
]


@dataclass(frozen=True)
class FrontierTaskV2:
    task_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    task_kind: str
    root_label: str | None
    obstruction_label: str | None
    constructor_family: str | None
    route_key: str | None
    residual_id: str | None
    cluster_id: str | None
    htilt_priority: float
    membrane_pressure: float
    saturation_score: float
    representation_shift_score: float
    expected_value: float
    novelty_score: float
    replay_priority: float
    final_priority: float
    reason: str
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrontierTaskV2":
        return cls(**dict(data))


@dataclass(frozen=True)
class FrontierV2Report:
    run_id: str
    task_count: int
    summary: dict[str, Any]
    tasks: list[FrontierTaskV2]
    outputs: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_count": self.task_count,
            "summary": dict(self.summary),
            "tasks": [task.to_dict() for task in self.tasks],
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
            "advisory_only": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrontierV2Report":
        return cls(
            run_id=str(data.get("run_id") or ""),
            task_count=int(data.get("task_count", len(data.get("tasks", []))) or 0),
            summary=dict(data.get("summary") or {}),
            tasks=[FrontierTaskV2.from_dict(row) for row in data.get("tasks", [])],
            outputs=dict(data.get("outputs") or {}),
            warnings=list(data.get("warnings") or []),
        )


def build_frontier_v2_from_atlas(
    atlas: ResidualAtlasReport | dict[str, Any],
    *,
    max_tasks: int = 100,
    include_suppressed: bool = False,
    run_id: str | None = None,
    out_dir: str | None = None,
) -> FrontierV2Report:
    atlas_obj = atlas if isinstance(atlas, ResidualAtlasReport) else ResidualAtlasReport.from_dict(atlas)
    run_id = run_id or f"frontier_v2_{int(time.time() * 1000)}"
    cluster_by_case = _cluster_by_case(atlas_obj)
    combo_counts = _combo_counts(atlas_obj.cases)
    tasks: list[FrontierTaskV2] = []
    for case in atlas_obj.cases:
        kind, reason = _task_kind_and_reason(case)
        if kind == "suppress_or_hold" and not include_suppressed:
            continue
        task = _task_from_case(case, kind, reason, cluster_by_case.get(case.residual_id), combo_counts)
        tasks.append(task)
    tasks = sorted(
        tasks,
        key=lambda item: (
            -item.final_priority,
            -item.membrane_pressure,
            -item.representation_shift_score,
            item.residual_id or "",
        ),
    )[: max(0, max_tasks)]
    summary = {
        "task_count": len(tasks),
        "task_kind_counts": dict(sorted(Counter(task.task_kind for task in tasks).items())),
        "top_priority": tasks[0].final_priority if tasks else 0.0,
        "top_task_id": tasks[0].task_id if tasks else None,
        "advisory_only": True,
    }
    report = FrontierV2Report(
        run_id=run_id,
        task_count=len(tasks),
        summary=summary,
        tasks=tasks,
        outputs={},
        warnings=list(FRONTIER_WARNINGS),
    )
    if out_dir:
        outputs = write_frontier_v2(report, out_dir)
        report = FrontierV2Report(
            run_id=report.run_id,
            task_count=report.task_count,
            summary=report.summary,
            tasks=report.tasks,
            outputs=outputs,
            warnings=report.warnings,
        )
    return report


def frontier_v2_to_task_queue_rows(report: FrontierV2Report | dict[str, Any]) -> list[dict[str, Any]]:
    frontier = report if isinstance(report, FrontierV2Report) else FrontierV2Report.from_dict(report)
    rows = []
    for task in frontier.tasks:
        route = task.route_key or task.task_kind
        rows.append(
            {
                "task_id": task.task_id,
                "task_kind": task.task_kind,
                "source": task.source,
                "target": task.target,
                "source_idx": task.source_idx,
                "target_idx": task.target_idx,
                "route": route,
                "constructor_family": task.constructor_family,
                "root_label": task.root_label,
                "priority": task.final_priority,
                "candidate_origin": "frontier_v2",
                "warnings": list(task.warnings),
                "evidence": dict(task.evidence),
            }
        )
    return rows


def write_frontier_v2(report: FrontierV2Report | dict[str, Any], out_dir: str) -> dict[str, str]:
    frontier = report if isinstance(report, FrontierV2Report) else FrontierV2Report.from_dict(report)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "frontier_v2_report_json": str(out / "frontier_v2_report.json"),
        "frontier_v2_tasks_jsonl": str(out / "frontier_v2_tasks.jsonl"),
        "frontier_v2_task_queue_jsonl": str(out / "frontier_v2_task_queue.jsonl"),
        "frontier_v2_report_md": str(out / "frontier_v2_report.md"),
    }
    persisted = FrontierV2Report(
        run_id=frontier.run_id,
        task_count=frontier.task_count,
        summary=frontier.summary,
        tasks=frontier.tasks,
        outputs=outputs,
        warnings=frontier.warnings,
    )
    _write_json(persisted.to_dict(), out / "frontier_v2_report.json")
    _write_jsonl([task.to_dict() for task in frontier.tasks], out / "frontier_v2_tasks.jsonl")
    _write_jsonl(frontier_v2_to_task_queue_rows(frontier), out / "frontier_v2_task_queue.jsonl")
    _write_markdown(persisted, out / "frontier_v2_report.md")
    return outputs


def _task_from_case(
    case: ResidualCase,
    task_kind: str,
    reason: str,
    cluster_id: str | None,
    combo_counts: dict[tuple[str | None, str | None, str | None], int],
) -> FrontierTaskV2:
    combo = (case.root_label, case.obstruction_label, case.constructor_family)
    novelty = 1.0 / max(1, combo_counts.get(combo, 1))
    replay_priority = max(case.best_near_miss_score, 0.5 if case.failures + case.residuals >= 2 else 0.0)
    expected = (
        0.35 * case.membrane_pressure
        + 0.25 * case.htilt_priority
        + 0.20 * case.representation_shift_score
        + 0.10 * novelty
        + 0.10 * replay_priority
    )
    penalty = 0.25 * case.saturation_score if task_kind == "suppress_or_hold" else 0.10 * case.saturation_score
    final = _clamp01(expected - penalty)
    payload = {
        "residual_id": case.residual_id,
        "task_kind": task_kind,
        "route_key": case.route_key,
        "source": case.source,
        "target": case.target,
        "source_idx": case.source_idx,
        "target_idx": case.target_idx,
    }
    return FrontierTaskV2(
        task_id=content_id("frontier_v2_task", payload, n=20),
        source=case.source,
        target=case.target,
        source_idx=case.source_idx,
        target_idx=case.target_idx,
        task_kind=task_kind,
        root_label=case.root_label,
        obstruction_label=case.obstruction_label,
        constructor_family=case.constructor_family,
        route_key=case.route_key,
        residual_id=case.residual_id,
        cluster_id=cluster_id,
        htilt_priority=case.htilt_priority,
        membrane_pressure=case.membrane_pressure,
        saturation_score=case.saturation_score,
        representation_shift_score=case.representation_shift_score,
        expected_value=round(expected, 6),
        novelty_score=round(novelty, 6),
        replay_priority=round(replay_priority, 6),
        final_priority=round(final, 6),
        reason=reason,
        warnings=list(FRONTIER_WARNINGS),
        evidence={
            "advisory_only": True,
            "case_next_action": case.next_action,
            "case_status": case.status,
            "priority_formula": "expected_value - saturation penalty",
        },
    )


def _task_kind_and_reason(case: ResidualCase) -> tuple[str, str]:
    if case.next_action == "schedule_next_attempt":
        return "finite_countermodel_search", "High membrane pressure / near-miss / route-policy priority."
    if case.next_action == "name_obstruction":
        return "obstruction_analysis", "Repeated structured failure should be named."
    if case.next_action == "seek_representation_shift":
        return "representation_shift_probe", "Saturated high-pressure membrane suggests representation shift."
    if case.near_misses > 0 and case.best_near_miss_score >= 0.6:
        return "near_miss_replay", "Near miss should be replayed and preserved."
    if case.next_action == "suppress_saturated_region":
        return "suppress_or_hold", "Saturated low-priority region should be held unless explicitly included."
    return "suppress_or_hold", "Insufficient evidence for active continuation."


def _cluster_by_case(atlas: ResidualAtlasReport) -> dict[str, str]:
    output: dict[str, str] = {}
    for cluster in atlas.clusters:
        for case_id in cluster.top_cases:
            output.setdefault(case_id, cluster.cluster_id)
        for case_id in cluster.evidence.get("case_ids", []):
            output.setdefault(case_id, cluster.cluster_id)
    return output


def _combo_counts(cases: list[ResidualCase]) -> dict[tuple[str | None, str | None, str | None], int]:
    counts: dict[tuple[str | None, str | None, str | None], int] = defaultdict(int)
    for case in cases:
        counts[(case.root_label, case.obstruction_label, case.constructor_family)] += 1
    return dict(counts)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(report: FrontierV2Report, path: Path) -> None:
    lines = [
        "# Frontier Builder v2 Report",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| task_count | {report.task_count} |",
        f"| top_priority | {report.summary.get('top_priority', 0.0)} |",
        "",
        "## Top Tasks",
        "",
        "| rank | task_kind | root | constructor | priority | reason |",
        "| ---: | --- | --- | --- | ---: | --- |",
    ]
    for idx, task in enumerate(report.tasks[:20], start=1):
        lines.append(
            f"| {idx} | {task.task_kind} | {task.root_label or ''} | {task.constructor_family or ''} | "
            f"{task.final_priority:.3f} | {task.reason} |"
        )
    lines.extend(["", "## Task Kind Counts", ""])
    for kind, count in sorted(report.summary.get("task_kind_counts", {}).items()):
        lines.append(f"- `{kind}`: {count}")
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "- frontier tasks are proposals",
            "- scheduling pressure is not truth",
            "- only verifier/importer promotes terminal certificates",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

"""Task planning from advisory certificate memory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id
from mathgraph.pair_advisor import PairAdvice, advise_pair, advise_many


PROOF_ROUTES = {
    "variable_identification",
    "direct_substitution_instance",
    "skeleton_preserving_relabel",
    "broad_split_to_skeleton_preserving_relabel",
}


@dataclass(frozen=True)
class CertificateTask:
    task_id: str
    source: str
    target: str
    task_kind: str
    terminal_goal: str
    route: str | None
    priority: float
    status: str
    required_inputs: list[str]
    steps: list[str]
    success_criteria: list[str]
    failure_modes: list[str]
    warnings: list[str]
    evidence: dict[str, Any]
    advice: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "target": self.target,
            "task_kind": self.task_kind,
            "terminal_goal": self.terminal_goal,
            "route": self.route,
            "priority": self.priority,
            "status": self.status,
            "required_inputs": list(self.required_inputs),
            "steps": list(self.steps),
            "success_criteria": list(self.success_criteria),
            "failure_modes": list(self.failure_modes),
            "warnings": list(self.warnings),
            "evidence": dict(self.evidence),
            "advice": dict(self.advice),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateTask":
        return cls(
            task_id=str(data["task_id"]),
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            task_kind=str(data["task_kind"]),
            terminal_goal=str(data["terminal_goal"]),
            route=data.get("route"),
            priority=float(data.get("priority", 0.0)),
            status=str(data.get("status", "planned")),
            required_inputs=list(data.get("required_inputs", [])),
            steps=list(data.get("steps", [])),
            success_criteria=list(data.get("success_criteria", [])),
            failure_modes=list(data.get("failure_modes", [])),
            warnings=list(data.get("warnings", [])),
            evidence=dict(data.get("evidence", {})),
            advice=dict(data.get("advice", {})),
        )


def plan_certificate_task(
    lawbook: Any,
    source: str,
    target: str,
    max_routes: int = 5,
) -> CertificateTask:
    advice = advise_pair(lawbook, source, target, max_routes=max_routes)
    return _task_from_advice(advice)


def plan_many_certificate_tasks(
    lawbook: Any,
    pairs: Iterable[Any],
    max_routes: int = 5,
) -> list[CertificateTask]:
    return [_task_from_advice(advice) for advice in advise_many(lawbook, pairs, max_routes=max_routes)]


def save_certificate_task(path: str | Path, task_or_tasks: CertificateTask | list[CertificateTask]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(task_or_tasks, list):
        payload: Any = [task.to_dict() for task in task_or_tasks]
    else:
        payload = task_or_tasks.to_dict()
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _task_from_advice(advice: PairAdvice) -> CertificateTask:
    if advice.status == "known_certificate":
        route = _top_route(advice)
        return _build_task(
            advice=advice,
            task_kind="known_certificate",
            terminal_goal=advice.terminal_form,
            route=route,
            priority=0.0,
            status="not_needed",
            required_inputs=[],
            steps=[],
            success_criteria=["Existing verified lawbook trace found."],
            failure_modes=[],
            warnings=["No new task required unless re-verification is requested."],
            evidence={"known_claim": advice.known_claim, "exact_match": True},
        )

    top = advice.candidate_routes[0] if advice.candidate_routes else None
    route = top.get("route") if top else None
    priority = _priority(top)
    if route == "finite_countermodel":
        return _build_task(
            advice=advice,
            task_kind="finite_countermodel_search",
            terminal_goal=TerminalForm.FINITE_COUNTERMODEL.value,
            route=route,
            priority=priority,
            status="planned",
            required_inputs=["source equation", "target equation", "finite magma search bounds"],
            steps=[
                "Parse source and target equations.",
                "Search small finite magmas for a model satisfying source.",
                "Test target violation on the same model.",
                "If found, emit table + assignment witness.",
                "Generate Lean/Python replay artifact.",
                "Verify artifact and only then promote.",
            ],
            success_criteria=[
                "Explicit finite model satisfies the source equation.",
                "The same finite model violates the target equation.",
                "Replay artifact verifies before promotion.",
            ],
            failure_modes=[
                "Finite-search failure is residual only, not proof.",
                "Candidate table does not satisfy source.",
                "Candidate table does not violate target.",
            ],
            warnings=advice.warnings,
            evidence={"candidate_route": top, "features": advice.features},
        )

    if route in PROOF_ROUTES:
        return _build_task(
            advice=advice,
            task_kind="proof_template",
            terminal_goal=TerminalForm.VERIFIED_PROOF.value,
            route=route,
            priority=priority,
            status="planned",
            required_inputs=["source equation", "target equation", "route-specific transformation map"],
            steps=[
                "Parse source and target equations.",
                "Construct route-specific substitution/relabel/collapse map.",
                "Check that every target term is obtained by lawful continuation from source.",
                "Emit proof skeleton.",
                "Run Lean verification.",
                "Promote only if Lean verifies.",
            ],
            success_criteria=[
                "A verified proof artifact is produced.",
                "Lean verification succeeds for the exact source/target claim.",
            ],
            failure_modes=[
                "Route blocked by new variables.",
                "Variable role mismatch.",
                "Skeleton mismatch.",
                "Lean failure.",
            ],
            warnings=advice.warnings,
            evidence={"candidate_route": top, "features": advice.features},
        )

    return _build_task(
        advice=advice,
        task_kind="obstruction_analysis",
        terminal_goal=TerminalForm.NAMED_OBSTRUCTION.value,
        route=route,
        priority=priority,
        status="planned" if advice.status != "malformed_input" else "blocked",
        required_inputs=["source equation", "target equation", "pair features"],
        steps=[
            "Extract pair features.",
            "Compare against lawbook route basins.",
            "Identify blocked routes.",
            "Produce named obstruction or split into narrower basin.",
        ],
        success_criteria=["Named obstruction card or new subtask."],
        failure_modes=["Advisory analysis is mistaken for a truth claim."],
        warnings=[*advice.warnings, "Planner output is not a proof or refutation."],
        evidence={"candidate_route": top, "features": advice.features},
    )


def _build_task(
    *,
    advice: PairAdvice,
    task_kind: str,
    terminal_goal: str,
    route: str | None,
    priority: float,
    status: str,
    required_inputs: list[str],
    steps: list[str],
    success_criteria: list[str],
    failure_modes: list[str],
    warnings: list[str],
    evidence: dict[str, Any],
) -> CertificateTask:
    payload = {
        "source": advice.source,
        "target": advice.target,
        "task_kind": task_kind,
        "route": route,
        "terminal_goal": terminal_goal,
    }
    return CertificateTask(
        task_id=content_id("task", payload, n=24),
        source=advice.source,
        target=advice.target,
        task_kind=task_kind,
        terminal_goal=terminal_goal,
        route=route,
        priority=max(0.0, min(1.0, float(priority))),
        status=status,
        required_inputs=required_inputs,
        steps=steps,
        success_criteria=success_criteria,
        failure_modes=failure_modes,
        warnings=_unique(warnings),
        evidence=evidence,
        advice=advice.to_dict(),
    )


def _top_route(advice: PairAdvice) -> str | None:
    if not advice.candidate_routes:
        return None
    return advice.candidate_routes[0].get("route")


def _priority(candidate: dict[str, Any] | None) -> float:
    if not candidate:
        return 0.0
    return max(0.0, min(1.0, float(candidate.get("score", 0.0))))


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

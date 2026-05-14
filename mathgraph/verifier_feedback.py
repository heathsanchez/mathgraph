"""Verifier feedback classification and advisory repair planning.

Verifier feedback turns failed checks into repair pressure, obstruction
pressure, or residual structure. It is not verification and cannot promote
claims across the verifier boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import (
    ContinuationActionOutput,
    ContinuationActionStatus,
    ContinuationOutputKind,
    make_continuation_output_id,
)
from mathgraph.hashing import content_id
from mathgraph.lean_adapter import LeanAdapterTrace, LeanArtifactStatus
from mathgraph.proof_verification import ProofVerificationResult, ProofVerificationStatus, ProofVerificationTrace
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind, make_projection_candidate_id
from mathgraph.root_constructors import RootConstructorStatus
from mathgraph.verification_episode import VerificationEpisodeTrace


class VerifierFeedbackStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_RUN = "NOT_RUN"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class FlawSeverity(str, Enum):
    NONE = "NONE"
    MINOR_REPAIRABLE = "MINOR_REPAIRABLE"
    STRUCTURAL_GAP = "STRUCTURAL_GAP"
    CRITICAL_INVALIDATION = "CRITICAL_INVALIDATION"
    UNKNOWN = "UNKNOWN"


class RepairActionKind(str, Enum):
    NO_ACTION = "NO_ACTION"
    LOCAL_REVISE = "LOCAL_REVISE"
    REGENERATE_ARTIFACT = "REGENERATE_ARTIFACT"
    REROUTE = "REROUTE"
    EMIT_PROOF_TASK = "EMIT_PROOF_TASK"
    EMIT_COUNTERMODEL_TASK = "EMIT_COUNTERMODEL_TASK"
    EMIT_PROJECTION_TASK = "EMIT_PROJECTION_TASK"
    EMIT_OBSTRUCTION_TASK = "EMIT_OBSTRUCTION_TASK"
    HOLD_IN_CHORA = "HOLD_IN_CHORA"
    MARK_RESIDUAL = "MARK_RESIDUAL"
    UNKNOWN = "UNKNOWN"


class RepairLoopStatus(str, Enum):
    EMPTY = "EMPTY"
    PLANNED = "PLANNED"
    REPAIR_TASKS_EMITTED = "REPAIR_TASKS_EMITTED"
    REROUTE_RECOMMENDED = "REROUTE_RECOMMENDED"
    OBSTRUCTION_RECOMMENDED = "OBSTRUCTION_RECOMMENDED"
    RESIDUALIZED = "RESIDUALIZED"
    VERIFIED_AFTER_REPAIR = "VERIFIED_AFTER_REPAIR"
    FAILED = "FAILED"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class VerifierFeedback:
    feedback_id: str
    artifact_id: str | None = None
    claim_id: str | None = None
    episode_id: str | None = None
    verifier_kind: str | None = None
    status: VerifierFeedbackStatus = VerifierFeedbackStatus.UNKNOWN
    flaw_severity: FlawSeverity = FlawSeverity.UNKNOWN
    flaw_location: str | None = None
    repair_hint: str | None = None
    regeneration_required: bool = False
    revision_allowed: bool = False
    terminal_blocked: bool = True
    raw_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def is_passed(self) -> bool:
        return self.status == VerifierFeedbackStatus.PASSED and self.flaw_severity == FlawSeverity.NONE

    def is_failed(self) -> bool:
        return self.status in {VerifierFeedbackStatus.FAILED, VerifierFeedbackStatus.UNAVAILABLE, VerifierFeedbackStatus.NOT_RUN}

    def is_repairable(self) -> bool:
        return self.flaw_severity == FlawSeverity.MINOR_REPAIRABLE or self.revision_allowed

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "artifact_id": self.artifact_id,
            "claim_id": self.claim_id,
            "episode_id": self.episode_id,
            "verifier_kind": self.verifier_kind,
            "status": self.status.value,
            "flaw_severity": self.flaw_severity.value,
            "flaw_location": self.flaw_location,
            "repair_hint": self.repair_hint,
            "regeneration_required": self.regeneration_required,
            "revision_allowed": self.revision_allowed,
            "terminal_blocked": self.terminal_blocked,
            "raw_message": self.raw_message,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerifierFeedback":
        return cls(
            feedback_id=str(data["feedback_id"]),
            artifact_id=_optional_str(data.get("artifact_id")),
            claim_id=_optional_str(data.get("claim_id")),
            episode_id=_optional_str(data.get("episode_id")),
            verifier_kind=_optional_str(data.get("verifier_kind")),
            status=VerifierFeedbackStatus(str(data.get("status", VerifierFeedbackStatus.UNKNOWN.value))),
            flaw_severity=FlawSeverity(str(data.get("flaw_severity", FlawSeverity.UNKNOWN.value))),
            flaw_location=_optional_str(data.get("flaw_location")),
            repair_hint=_optional_str(data.get("repair_hint")),
            regeneration_required=bool(data.get("regeneration_required", False)),
            revision_allowed=bool(data.get("revision_allowed", False)),
            terminal_blocked=bool(data.get("terminal_blocked", True)),
            raw_message=_optional_str(data.get("raw_message")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "VerifierFeedback":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "VerifierFeedback":
        return cls.from_json(line.strip())


@dataclass
class RepairPlan:
    repair_plan_id: str
    feedback_id: str
    action_kind: RepairActionKind
    priority: float = 0.0
    reason: str | None = None
    task_payload: dict[str, Any] = field(default_factory=dict)
    continuation_output: ContinuationActionOutput | None = None
    projection_candidate: ProjectionCandidate | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "repair_plan_id": self.repair_plan_id,
            "feedback_id": self.feedback_id,
            "action_kind": self.action_kind.value,
            "priority": self.priority,
            "reason": self.reason,
            "task_payload": dict(self.task_payload),
            "continuation_output": self.continuation_output.to_dict() if self.continuation_output else None,
            "projection_candidate": self.projection_candidate.to_dict() if self.projection_candidate else None,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RepairPlan":
        return cls(
            repair_plan_id=str(data["repair_plan_id"]),
            feedback_id=str(data["feedback_id"]),
            action_kind=RepairActionKind(str(data.get("action_kind", RepairActionKind.UNKNOWN.value))),
            priority=float(data.get("priority", 0.0) or 0.0),
            reason=_optional_str(data.get("reason")),
            task_payload=dict(data.get("task_payload", {})),
            continuation_output=ContinuationActionOutput.from_dict(data["continuation_output"]) if data.get("continuation_output") else None,
            projection_candidate=ProjectionCandidate.from_dict(data["projection_candidate"]) if data.get("projection_candidate") else None,
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "RepairPlan":
        return cls.from_dict(json.loads(text))


@dataclass
class RepairLoopTrace:
    trace_id: str
    feedback_items: list[VerifierFeedback] = field(default_factory=list)
    repair_plans: list[RepairPlan] = field(default_factory=list)
    continuation_outputs: list[ContinuationActionOutput] = field(default_factory=list)
    projection_candidates: list[ProjectionCandidate] = field(default_factory=list)
    status: RepairLoopStatus = RepairLoopStatus.EMPTY
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def feedback_count(self) -> int:
        return len(self.feedback_items)

    def repair_plan_count(self) -> int:
        return len(self.repair_plans)

    def output_count(self) -> int:
        return len(self.continuation_outputs) + len(self.projection_candidates)

    def is_terminal(self) -> bool:
        return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "feedback_items": [item.to_dict() for item in self.feedback_items],
            "repair_plans": [plan.to_dict() for plan in self.repair_plans],
            "continuation_outputs": [item.to_dict() for item in self.continuation_outputs],
            "projection_candidates": [item.to_dict() for item in self.projection_candidates],
            "status": self.status.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RepairLoopTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            feedback_items=[VerifierFeedback.from_dict(item) for item in data.get("feedback_items", [])],
            repair_plans=[RepairPlan.from_dict(item) for item in data.get("repair_plans", [])],
            continuation_outputs=[ContinuationActionOutput.from_dict(item) for item in data.get("continuation_outputs", [])],
            projection_candidates=[ProjectionCandidate.from_dict(item) for item in data.get("projection_candidates", [])],
            status=RepairLoopStatus(str(data.get("status", RepairLoopStatus.EMPTY.value))),
            terminal_form=_optional_terminal(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "RepairLoopTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "RepairLoopTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["RepairLoopTrace"]:
        source = Path(path)
        if not source.exists():
            return []
        return [cls.from_json(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


def classify_flaw_from_message(message: str | None) -> FlawSeverity:
    text = (message or "").lower()
    if not text.strip():
        return FlawSeverity.UNKNOWN
    if any(token in text for token in ("passed", "success", "verified")):
        return FlawSeverity.NONE
    if any(token in text for token in ("counterexample", "source violated", "target not violated", "invalid certificate", "false theorem", "contradiction")):
        return FlawSeverity.CRITICAL_INVALIDATION
    if any(token in text for token in ("type mismatch", "failed to synthesize", "unsolved goals", "incomplete proof", "sorry")):
        return FlawSeverity.STRUCTURAL_GAP
    if any(token in text for token in ("syntax", "parse", "unknown identifier", "unknown constant", "missing import")):
        return FlawSeverity.MINOR_REPAIRABLE
    if any(token in text for token in ("timeout", "not run", "unavailable", "missing executable")):
        return FlawSeverity.UNKNOWN
    return FlawSeverity.UNKNOWN


def feedback_from_proof_verification_result(result: ProofVerificationResult) -> VerifierFeedback:
    message = " ".join(
        part
        for part in [result.failure_reason, result.stderr_excerpt, result.stdout_excerpt, json.dumps(result.metadata, sort_keys=True)]
        if part
    )
    if result.is_terminal():
        status = VerifierFeedbackStatus.PASSED
        severity = FlawSeverity.NONE
    elif result.status == ProofVerificationStatus.VERIFIER_FAILED:
        status = VerifierFeedbackStatus.FAILED
        severity = classify_flaw_from_message(message)
    elif result.status == ProofVerificationStatus.VERIFIER_NOT_RUN:
        status = VerifierFeedbackStatus.NOT_RUN
        severity = FlawSeverity.UNKNOWN
    elif result.status in {ProofVerificationStatus.REJECTED, ProofVerificationStatus.RESIDUAL}:
        status = VerifierFeedbackStatus.FAILED
        severity = classify_flaw_from_message(message)
    else:
        status = VerifierFeedbackStatus.UNKNOWN
        severity = classify_flaw_from_message(message)
    return _feedback(
        artifact_id=result.artifact_id,
        verifier_kind=result.verifier_kind.value,
        status=status,
        severity=severity,
        raw_message=message,
        metadata={"proof_verification_result": result.to_dict(), "advisory_only": True},
    )


def feedback_from_proof_verification_trace(trace: ProofVerificationTrace) -> list[VerifierFeedback]:
    rows = []
    for result in trace.results:
        feedback = feedback_from_proof_verification_result(result)
        feedback.episode_id = trace.episode_id
        rows.append(feedback)
    return rows


def feedback_from_lean_adapter_trace(trace: LeanAdapterTrace) -> list[VerifierFeedback]:
    rows: list[VerifierFeedback] = []
    for result in trace.results:
        if result.proof_verification_result is not None:
            feedback = feedback_from_proof_verification_result(result.proof_verification_result)
            feedback.metadata["lean_check_result"] = result.to_dict()
        else:
            message = " ".join(part for part in [result.stderr_excerpt, result.stdout_excerpt, json.dumps(result.metadata, sort_keys=True)] if part)
            status = VerifierFeedbackStatus.UNAVAILABLE if result.status == LeanArtifactStatus.LEAN_NOT_AVAILABLE else (
                VerifierFeedbackStatus.NOT_RUN if result.status == LeanArtifactStatus.CHECK_NOT_RUN else VerifierFeedbackStatus.FAILED
            )
            feedback = _feedback(
                artifact_id=result.lean_file_id,
                verifier_kind="LEAN",
                status=status,
                severity=classify_flaw_from_message(message),
                raw_message=message,
                metadata={"lean_check_result": result.to_dict(), "advisory_only": True},
            )
        rows.append(feedback)
    return rows


def feedback_from_verification_episode_trace(trace: VerificationEpisodeTrace) -> list[VerifierFeedback]:
    rows: list[VerifierFeedback] = []
    if trace.proof_verification_trace is not None:
        rows.extend(feedback_from_proof_verification_trace(trace.proof_verification_trace))
    if trace.root_constructor_trace is not None:
        for attempt in trace.root_constructor_trace.attempts:
            if attempt.is_terminal():
                rows.append(_feedback(artifact_id=attempt.attempt_id, claim_id=None, episode_id=trace.episode_id, verifier_kind="FINITE_COUNTERMODEL_IMPORTER", status=VerifierFeedbackStatus.PASSED, severity=FlawSeverity.NONE, raw_message="importer verified finite countermodel", metadata={"constructor_attempt": attempt.to_dict()}))
            elif attempt.status in {RootConstructorStatus.SEARCH_MISS, RootConstructorStatus.IMPORTER_REJECTED, RootConstructorStatus.RESIDUAL}:
                rows.append(_feedback(artifact_id=attempt.attempt_id, claim_id=None, episode_id=trace.episode_id, verifier_kind="FINITE_COUNTERMODEL_IMPORTER", status=VerifierFeedbackStatus.FAILED, severity=FlawSeverity.STRUCTURAL_GAP if attempt.status == RootConstructorStatus.SEARCH_MISS else classify_flaw_from_message(attempt.failure_reason), raw_message=attempt.failure_reason or attempt.status.value, metadata={"constructor_attempt": attempt.to_dict(), "search_miss_not_proof": True}))
    if trace.is_terminal():
        rows.append(_feedback(artifact_id=trace.episode_id, claim_id=trace.input.claim_id, episode_id=trace.episode_id, verifier_kind="EPISODE", status=VerifierFeedbackStatus.PASSED, severity=FlawSeverity.NONE, raw_message="episode terminal boundary crossed", metadata={"episode": trace.to_dict()}))
    return rows


def feedback_from_text(
    *,
    raw_message: str,
    artifact_id: str | None = None,
    claim_id: str | None = None,
    verifier_kind: str | None = None,
) -> VerifierFeedback:
    severity = classify_flaw_from_message(raw_message)
    if severity == FlawSeverity.NONE:
        status = VerifierFeedbackStatus.PASSED
    elif "unavailable" in raw_message.lower() or "missing executable" in raw_message.lower():
        status = VerifierFeedbackStatus.UNAVAILABLE
    elif "not run" in raw_message.lower():
        status = VerifierFeedbackStatus.NOT_RUN
    else:
        status = VerifierFeedbackStatus.FAILED if raw_message else VerifierFeedbackStatus.UNKNOWN
    return _feedback(
        artifact_id=artifact_id,
        claim_id=claim_id,
        verifier_kind=verifier_kind,
        status=status,
        severity=severity,
        raw_message=raw_message,
        metadata={"source": "text", "advisory_only": True, "natural_language_feedback_not_verification": True},
    )


def plan_repair_from_feedback(feedback: VerifierFeedback) -> list[RepairPlan]:
    if feedback.is_passed():
        return [_plan(feedback, RepairActionKind.NO_ACTION, 0.0, "Verifier passed; no repair needed.")]
    if feedback.flaw_severity == FlawSeverity.MINOR_REPAIRABLE:
        return [_plan(feedback, RepairActionKind.LOCAL_REVISE, 0.9, "Minor verifier flaw appears locally repairable.")]
    if feedback.flaw_severity == FlawSeverity.STRUCTURAL_GAP:
        return [
            _plan(feedback, RepairActionKind.REROUTE, 0.8, "Structural gap should reroute or change proof strategy."),
            _plan(feedback, RepairActionKind.EMIT_PROOF_TASK, 0.7, "Emit a fresh proof task addressing the structural gap."),
        ]
    if feedback.flaw_severity == FlawSeverity.CRITICAL_INVALIDATION:
        return [
            _plan(feedback, RepairActionKind.EMIT_OBSTRUCTION_TASK, 0.9, "Critical invalidation should become obstruction pressure."),
            _plan(feedback, RepairActionKind.MARK_RESIDUAL, 0.8, "Critical invalidation should residualize this route."),
        ]
    if feedback.status in {VerifierFeedbackStatus.UNAVAILABLE, VerifierFeedbackStatus.NOT_RUN}:
        return [
            _plan(feedback, RepairActionKind.HOLD_IN_CHORA, 0.5, "Verifier unavailable or not run; hold advisory artifact in Chora."),
            _plan(feedback, RepairActionKind.MARK_RESIDUAL, 0.4, "Record residual status until verifier can run."),
        ]
    return [
        _plan(feedback, RepairActionKind.REROUTE, 0.4, "Unknown verifier failure; reroute conservatively."),
        _plan(feedback, RepairActionKind.MARK_RESIDUAL, 0.3, "Unknown verifier failure remains residual."),
    ]


def run_repair_loop(
    feedback_items: Sequence[VerifierFeedback],
    *,
    max_plans: int | None = None,
) -> RepairLoopTrace:
    plans: list[RepairPlan] = []
    for feedback in feedback_items:
        plans.extend(plan_repair_from_feedback(feedback))
    if max_plans is not None:
        plans = plans[:max_plans]
    outputs = [plan.continuation_output for plan in plans if plan.continuation_output is not None]
    projections = [plan.projection_candidate for plan in plans if plan.projection_candidate is not None]
    trace = RepairLoopTrace(
        trace_id=make_repair_loop_trace_id([item.to_dict() for item in feedback_items], [plan.to_dict() for plan in plans]),
        feedback_items=list(feedback_items),
        repair_plans=plans,
        continuation_outputs=outputs,
        projection_candidates=projections,
        status=_loop_status(feedback_items, plans),
    )
    trace.summary.update(_summary(trace))
    return trace


def repair_loop_trace_to_alchemical_trace(trace: RepairLoopTrace) -> AlchemicalTrace:
    alchemy = AlchemicalTrace(trace_id=make_alchemical_trace_id("verifier_feedback", trace.trace_id))
    alchemy.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if trace.feedback_items:
        alchemy.add_step(phase=AlchemicalPhase.DISTILLATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.continuation_outputs:
        alchemy.add_step(phase=AlchemicalPhase.DESCENSION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(plan.action_kind in {RepairActionKind.EMIT_OBSTRUCTION_TASK, RepairActionKind.MARK_RESIDUAL} for plan in trace.repair_plans):
        alchemy.add_step(phase=AlchemicalPhase.COAGULATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.projection_candidates:
        alchemy.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.ADVISORY_ONLY)
    if trace.is_terminal():
        alchemy.terminal_form = trace.terminal_form
        alchemy.promoted_certificate_id = trace.certificate_id
        alchemy.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary="INHERITED_REPAIR_RESULT")
    return alchemy


def repair_loop_trace_to_agent_experiences(trace: RepairLoopTrace, agent_id: str | None = None) -> list[AgentExperience]:
    actor = agent_id or "verifier-feedback"
    experiences: list[AgentExperience] = []
    for feedback in trace.feedback_items:
        experiences.append(
            AgentExperience(
                experience_id=content_id("verifier_feedback_exp", feedback.to_dict(), n=24),
                agent_id=actor,
                episode_id=feedback.episode_id,
                claim_id=feedback.claim_id or feedback.artifact_id,
                route=f"verifier_feedback:{feedback.flaw_severity.value.lower()}",
                phase=AlchemicalPhase.DISTILLATION.value,
                outcome=AgentExperienceOutcome.VERIFIED_PROOF if feedback.is_passed() else AgentExperienceOutcome.RESIDUAL,
                scar_tags=() if feedback.is_passed() else (feedback.flaw_severity.value,),
                metadata={"verifier_feedback": feedback.to_dict(), "repair_loop_advisory": True},
            )
        )
    return experiences


def repair_loop_trace_to_continuation_outputs(trace: RepairLoopTrace) -> list[ContinuationActionOutput]:
    return list(trace.continuation_outputs)


def repair_loop_trace_to_projection_candidates(trace: RepairLoopTrace) -> list[ProjectionCandidate]:
    return list(trace.projection_candidates)


def repair_loop_trace_to_route_telemetry_events(trace: RepairLoopTrace) -> list[dict[str, Any]]:
    events = []
    for feedback in trace.feedback_items:
        events.append(
            {
                "episode_id": feedback.episode_id,
                "claim_id": feedback.claim_id,
                "route_kind": "PROOF_VERIFICATION",
                "outcome": "ADVISORY_ONLY" if feedback.is_passed() else "VERIFIER_FAILED",
                "from_state": "verifier",
                "to_state": "repair" if feedback.is_failed() else "terminal",
                "killed": feedback.is_failed(),
                "kill_reason": feedback.flaw_severity.value if feedback.is_failed() else None,
                "advisory": True,
                "metadata": {"feedback_id": feedback.feedback_id},
            }
        )
    return events


def make_verifier_feedback_id(*parts: Any) -> str:
    return content_id("verifier_feedback", parts, n=24)


def make_repair_plan_id(*parts: Any) -> str:
    return content_id("repair_plan", parts, n=24)


def make_repair_loop_trace_id(*parts: Any) -> str:
    return content_id("repair_loop_trace", parts, n=24)


def _feedback(
    *,
    artifact_id: str | None = None,
    claim_id: str | None = None,
    episode_id: str | None = None,
    verifier_kind: str | None = None,
    status: VerifierFeedbackStatus,
    severity: FlawSeverity,
    raw_message: str | None,
    metadata: Mapping[str, Any],
) -> VerifierFeedback:
    return VerifierFeedback(
        feedback_id=make_verifier_feedback_id(artifact_id, claim_id, episode_id, verifier_kind, status.value, severity.value, raw_message),
        artifact_id=artifact_id,
        claim_id=claim_id,
        episode_id=episode_id,
        verifier_kind=verifier_kind,
        status=status,
        flaw_severity=severity,
        repair_hint=_repair_hint(severity),
        regeneration_required=severity in {FlawSeverity.STRUCTURAL_GAP, FlawSeverity.CRITICAL_INVALIDATION},
        revision_allowed=severity == FlawSeverity.MINOR_REPAIRABLE,
        terminal_blocked=status != VerifierFeedbackStatus.PASSED,
        raw_message=raw_message,
        metadata={**dict(metadata), "advisory_only": True},
    )


def _plan(feedback: VerifierFeedback, kind: RepairActionKind, priority: float, reason: str) -> RepairPlan:
    payload = {
        "feedback_id": feedback.feedback_id,
        "artifact_id": feedback.artifact_id,
        "claim_id": feedback.claim_id,
        "repair_hint": feedback.repair_hint,
        "action_kind": kind.value,
        "advisory_only": True,
    }
    output = None if kind == RepairActionKind.NO_ACTION else _continuation_output(feedback, kind, payload, reason)
    projection = _projection_candidate(feedback, kind) if kind == RepairActionKind.EMIT_PROJECTION_TASK else None
    return RepairPlan(
        repair_plan_id=make_repair_plan_id(feedback.feedback_id, kind.value, payload),
        feedback_id=feedback.feedback_id,
        action_kind=kind,
        priority=priority,
        reason=reason,
        task_payload=payload,
        continuation_output=output,
        projection_candidate=projection,
        metadata={"advisory_only": True, "repair_plan_not_truth": True},
    )


def _continuation_output(feedback: VerifierFeedback, kind: RepairActionKind, payload: Mapping[str, Any], reason: str) -> ContinuationActionOutput:
    if kind == RepairActionKind.EMIT_OBSTRUCTION_TASK:
        output_kind = ContinuationOutputKind.OBSTRUCTION_CANDIDATE
        obstruction_name = f"candidate_obstruction_{feedback.feedback_id}"
    else:
        output_kind = ContinuationOutputKind.TASK
        obstruction_name = None
    return ContinuationActionOutput(
        output_id=make_continuation_output_id({"feedback": feedback.to_dict(), "kind": kind.value}),
        action_id="verifier_feedback_repair",
        kind=output_kind,
        status=ContinuationActionStatus.PRODUCED_TASK if output_kind == ContinuationOutputKind.TASK else ContinuationActionStatus.PRODUCED_CANDIDATE,
        obstruction_name=obstruction_name,
        task_payload=dict(payload),
        note=reason,
        metadata={"advisory_only": True, "repair_output_not_truth": True, "repair_action_kind": kind.value},
    )


def _projection_candidate(feedback: VerifierFeedback, kind: RepairActionKind) -> ProjectionCandidate:
    return ProjectionCandidate(
        candidate_id=make_projection_candidate_id({"feedback": feedback.to_dict(), "kind": kind.value}),
        source_claim_id=feedback.claim_id,
        target_claim_id=None,
        rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY,
        confidence=0.1,
        advisory=True,
        reason="Verifier feedback suggests advisory projection repair pressure.",
        metadata={"advisory_only": True, "feedback_id": feedback.feedback_id},
    )


def _loop_status(feedback_items: Sequence[VerifierFeedback], plans: Sequence[RepairPlan]) -> RepairLoopStatus:
    if not feedback_items:
        return RepairLoopStatus.EMPTY
    kinds = {plan.action_kind for plan in plans}
    if RepairActionKind.EMIT_OBSTRUCTION_TASK in kinds:
        return RepairLoopStatus.OBSTRUCTION_RECOMMENDED
    if RepairActionKind.REROUTE in kinds:
        return RepairLoopStatus.REROUTE_RECOMMENDED
    if any(plan.continuation_output for plan in plans):
        return RepairLoopStatus.REPAIR_TASKS_EMITTED
    if kinds == {RepairActionKind.MARK_RESIDUAL}:
        return RepairLoopStatus.RESIDUALIZED
    if plans:
        return RepairLoopStatus.PLANNED
    return RepairLoopStatus.ADVISORY_ONLY


def _summary(trace: RepairLoopTrace) -> dict[str, Any]:
    return {
        "feedback_total": len(trace.feedback_items),
        "passed_count": sum(1 for item in trace.feedback_items if item.status == VerifierFeedbackStatus.PASSED),
        "failed_count": sum(1 for item in trace.feedback_items if item.is_failed()),
        "minor_repairable_count": sum(1 for item in trace.feedback_items if item.flaw_severity == FlawSeverity.MINOR_REPAIRABLE),
        "structural_gap_count": sum(1 for item in trace.feedback_items if item.flaw_severity == FlawSeverity.STRUCTURAL_GAP),
        "critical_invalidation_count": sum(1 for item in trace.feedback_items if item.flaw_severity == FlawSeverity.CRITICAL_INVALIDATION),
        "unknown_count": sum(1 for item in trace.feedback_items if item.flaw_severity == FlawSeverity.UNKNOWN),
        "repair_plan_count": len(trace.repair_plans),
        "continuation_output_count": len(trace.continuation_outputs),
        "projection_candidate_count": len(trace.projection_candidates),
        "terminal_outputs": int(trace.is_terminal()),
        "advisory_outputs": len(trace.continuation_outputs) + len(trace.projection_candidates),
        "advisory_only": not trace.is_terminal(),
    }


def _repair_hint(severity: FlawSeverity) -> str | None:
    return {
        FlawSeverity.NONE: "No repair needed.",
        FlawSeverity.MINOR_REPAIRABLE: "Try local syntax/import/name repair.",
        FlawSeverity.STRUCTURAL_GAP: "Reroute or emit a new proof task.",
        FlawSeverity.CRITICAL_INVALIDATION: "Residualize or name obstruction candidate.",
        FlawSeverity.UNKNOWN: "Hold in Chora or mark residual until more evidence exists.",
    }.get(severity)


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_terminal(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    return TerminalForm(str(value))

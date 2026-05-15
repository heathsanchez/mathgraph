"""Advisory discovery-value scoring for MathGraph route selection.

Discovery value ranks what may be worth trying next. It is scheduling pressure,
not truth, and it never crosses verifier/importer/finite-validation boundaries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import ContinuationActionOutput, ContinuationActionStatus, ContinuationOutputKind, make_continuation_output_id
from mathgraph.continuation_curriculum import (
    ContinuationCurriculum,
    CurriculumStage,
    CurriculumStageKind,
    build_continuation_curriculum,
)
from mathgraph.hashing import content_id
from mathgraph.proof_digestion import LawbookAssimilationCandidate, ProofDigestionTrace, make_lawbook_assimilation_candidate
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind
from mathgraph.verifier_feedback import FlawSeverity, RepairActionKind, RepairLoopTrace, RepairPlan, VerifierFeedback


class DiscoveryValueObjectKind(str, Enum):
    CURRICULUM = "CURRICULUM"
    CURRICULUM_STAGE = "CURRICULUM_STAGE"
    PROOF_DIGESTION_TRACE = "PROOF_DIGESTION_TRACE"
    LAWBOOK_ASSIMILATION_CANDIDATE = "LAWBOOK_ASSIMILATION_CANDIDATE"
    VERIFIER_FEEDBACK = "VERIFIER_FEEDBACK"
    REPAIR_LOOP_TRACE = "REPAIR_LOOP_TRACE"
    REPAIR_PLAN = "REPAIR_PLAN"
    PROJECTION_CANDIDATE = "PROJECTION_CANDIDATE"
    CONTINUATION_OUTPUT = "CONTINUATION_OUTPUT"
    ROUTE_TELEMETRY_EVENT = "ROUTE_TELEMETRY_EVENT"
    ALCHEMICAL_TRACE = "ALCHEMICAL_TRACE"
    AGENT_EXPERIENCE = "AGENT_EXPERIENCE"
    RAW_TASK = "RAW_TASK"
    UNKNOWN = "UNKNOWN"


class DiscoveryValueSignalKind(str, Enum):
    CERTIFICATE_POTENTIAL = "CERTIFICATE_POTENTIAL"
    COUNTERMODEL_POTENTIAL = "COUNTERMODEL_POTENTIAL"
    PROOF_POTENTIAL = "PROOF_POTENTIAL"
    OBSTRUCTION_POTENTIAL = "OBSTRUCTION_POTENTIAL"
    DIGESTION_VALUE = "DIGESTION_VALUE"
    PROJECTION_VALUE = "PROJECTION_VALUE"
    REPAIR_VALUE = "REPAIR_VALUE"
    CURRICULUM_VALUE = "CURRICULUM_VALUE"
    ROUTE_SURVIVAL_VALUE = "ROUTE_SURVIVAL_VALUE"
    RESIDUAL_COMPRESSION_VALUE = "RESIDUAL_COMPRESSION_VALUE"
    ROOT_LIKENESS = "ROOT_LIKENESS"
    REUSE_VALUE = "REUSE_VALUE"
    NOVELTY_VALUE = "NOVELTY_VALUE"
    COST_PENALTY = "COST_PENALTY"
    RISK_PENALTY = "RISK_PENALTY"
    OVERFIT_PENALTY = "OVERFIT_PENALTY"
    UNKNOWN = "UNKNOWN"


class DiscoveryValueDecision(str, Enum):
    RUN_NOW = "RUN_NOW"
    QUEUE_SOON = "QUEUE_SOON"
    HOLD_IN_CHORA = "HOLD_IN_CHORA"
    NEEDS_REPAIR = "NEEDS_REPAIR"
    NEEDS_DIGESTION = "NEEDS_DIGESTION"
    NEEDS_VERIFIER = "NEEDS_VERIFIER"
    PROJECT = "PROJECT"
    RESIDUALIZE = "RESIDUALIZE"
    DROP = "DROP"
    UNKNOWN = "UNKNOWN"


class DiscoveryValueStatus(str, Enum):
    EMPTY = "EMPTY"
    SCORED = "SCORED"
    RANKED = "RANKED"
    BLOCKED = "BLOCKED"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class DiscoveryValueSignal:
    signal_id: str
    kind: DiscoveryValueSignalKind
    value: float
    weight: float = 1.0
    reason: str | None = None
    source_object_id: str | None = None
    source_object_kind: DiscoveryValueObjectKind = DiscoveryValueObjectKind.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def contribution(self) -> float:
        return self.value * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "kind": self.kind.value,
            "value": self.value,
            "weight": self.weight,
            "reason": self.reason,
            "source_object_id": self.source_object_id,
            "source_object_kind": self.source_object_kind.value,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryValueSignal":
        return cls(
            signal_id=str(data["signal_id"]),
            kind=DiscoveryValueSignalKind(str(data.get("kind", DiscoveryValueSignalKind.UNKNOWN.value))),
            value=float(data.get("value", 0.0) or 0.0),
            weight=float(data.get("weight", 1.0) or 1.0),
            reason=_optional_str(data.get("reason")),
            source_object_id=_optional_str(data.get("source_object_id")),
            source_object_kind=DiscoveryValueObjectKind(str(data.get("source_object_kind", DiscoveryValueObjectKind.UNKNOWN.value))),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "DiscoveryValueSignal":
        return cls.from_dict(json.loads(text))


@dataclass
class DiscoveryValueScore:
    score_id: str
    object_id: str
    object_kind: DiscoveryValueObjectKind
    label: str | None = None
    signals: list[DiscoveryValueSignal] = field(default_factory=list)
    raw_score: float = 0.0
    normalized_score: float = 0.0
    cost_estimate: float = 0.0
    risk_estimate: float = 0.0
    expected_gain: float = 0.0
    decision: DiscoveryValueDecision = DiscoveryValueDecision.UNKNOWN
    rank: int | None = None
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def recompute(self) -> float:
        self.raw_score = sum(signal.contribution() for signal in self.signals)
        self.expected_gain = sum(signal.contribution() for signal in self.signals if signal.value > 0)
        self.risk_estimate = abs(sum(signal.contribution() for signal in self.signals if signal.kind in {DiscoveryValueSignalKind.RISK_PENALTY, DiscoveryValueSignalKind.OVERFIT_PENALTY}))
        return self.raw_score

    def is_terminal(self) -> bool:
        return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed

    def to_dict(self) -> dict[str, Any]:
        return {
            "score_id": self.score_id,
            "object_id": self.object_id,
            "object_kind": self.object_kind.value,
            "label": self.label,
            "signals": [signal.to_dict() for signal in self.signals],
            "raw_score": self.raw_score,
            "normalized_score": self.normalized_score,
            "cost_estimate": self.cost_estimate,
            "risk_estimate": self.risk_estimate,
            "expected_gain": self.expected_gain,
            "decision": self.decision.value,
            "rank": self.rank,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryValueScore":
        return cls(
            score_id=str(data["score_id"]),
            object_id=str(data["object_id"]),
            object_kind=DiscoveryValueObjectKind(str(data.get("object_kind", DiscoveryValueObjectKind.UNKNOWN.value))),
            label=_optional_str(data.get("label")),
            signals=[DiscoveryValueSignal.from_dict(item) for item in data.get("signals", [])],
            raw_score=float(data.get("raw_score", 0.0) or 0.0),
            normalized_score=float(data.get("normalized_score", 0.0) or 0.0),
            cost_estimate=float(data.get("cost_estimate", 0.0) or 0.0),
            risk_estimate=float(data.get("risk_estimate", 0.0) or 0.0),
            expected_gain=float(data.get("expected_gain", 0.0) or 0.0),
            decision=DiscoveryValueDecision(str(data.get("decision", DiscoveryValueDecision.UNKNOWN.value))),
            rank=int(data["rank"]) if data.get("rank") is not None else None,
            terminal_form=_optional_terminal(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "DiscoveryValueScore":
        return cls.from_dict(json.loads(text))


@dataclass
class DiscoveryValueReport:
    report_id: str
    scores: list[DiscoveryValueScore] = field(default_factory=list)
    status: DiscoveryValueStatus = DiscoveryValueStatus.EMPTY
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def score_count(self) -> int:
        return len(self.scores)

    def top(self, n: int = 10) -> list[DiscoveryValueScore]:
        return self.scores[:n]

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "scores": [score.to_dict() for score in self.scores],
            "status": self.status.value,
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryValueReport":
        return cls(
            report_id=str(data["report_id"]),
            scores=[DiscoveryValueScore.from_dict(item) for item in data.get("scores", [])],
            status=DiscoveryValueStatus(str(data.get("status", DiscoveryValueStatus.EMPTY.value))),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "DiscoveryValueReport":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "DiscoveryValueReport":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(score.to_json() + "\n" for score in self.scores), encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "DiscoveryValueReport":
        scores = [DiscoveryValueScore.from_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
        return _report(scores)


def make_discovery_value_signal_id(*parts: Any) -> str:
    return content_id("discovery_value_signal", parts, n=24)


def make_discovery_value_score_id(*parts: Any) -> str:
    return content_id("discovery_value_score", parts, n=24)


def make_discovery_value_report_id(*parts: Any) -> str:
    return content_id("discovery_value_report", parts, n=24)


def score_curriculum(curriculum: ContinuationCurriculum) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    kinds = [stage.kind for stage in curriculum.stages]
    _add(signals, DiscoveryValueSignalKind.CURRICULUM_VALUE, 1.0 if CurriculumStageKind.WARMUP_CLAIM in kinds else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.CURRICULUM_VALUE, 1.0 if CurriculumStageKind.SIMPLIFIED_CASE in kinds else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.CURRICULUM_VALUE, 1.0 if CurriculumStageKind.FINITE_EXAMPLE in kinds else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL, 2.0 if curriculum.episode_inputs else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.PROOF_POTENTIAL, 2.0 if CurriculumStageKind.PROOF_TASK in kinds else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 2.0 if CurriculumStageKind.COUNTERMODEL_TASK in kinds else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 2.0 if curriculum.projection_candidates else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 1.0 if any(kind in {CurriculumStageKind.RESIDUAL_REVIEW, CurriculumStageKind.HELD_IN_CHORA} for kind in kinds) else 0.0, curriculum)
    _add(signals, DiscoveryValueSignalKind.ROOT_LIKENESS, 2.0 if len(curriculum.stages) >= 5 else 0.0, curriculum)
    if (curriculum.target_claim_id or curriculum.target_source or curriculum.target_raw) and not curriculum.stages:
        _add(signals, DiscoveryValueSignalKind.CURRICULUM_VALUE, -1.0, curriculum, "target without stages")
    unknown_count = sum(1 for kind in kinds if kind == CurriculumStageKind.UNKNOWN)
    if unknown_count > max(1, len(kinds) // 2):
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -1.0, curriculum, "many unknown stages")
    _risk_from_terminal(signals, curriculum)
    return _score(curriculum.curriculum_id, DiscoveryValueObjectKind.CURRICULUM, signals, label=curriculum.target_claim_id or curriculum.target_raw, metadata={"advisory_only": True, "source": "curriculum"})


def score_curriculum_stage(stage: CurriculumStage) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    mapping = {
        CurriculumStageKind.WARMUP_CLAIM: (DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL, 0.5),
        CurriculumStageKind.FINITE_EXAMPLE: (DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 1.0),
        CurriculumStageKind.PREREQUISITE_LEMMA: (DiscoveryValueSignalKind.PROOF_POTENTIAL, 1.5),
        CurriculumStageKind.PROOF_TASK: (DiscoveryValueSignalKind.PROOF_POTENTIAL, 2.0),
        CurriculumStageKind.COUNTERMODEL_TASK: (DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 2.0),
        CurriculumStageKind.PROJECTION_TASK: (DiscoveryValueSignalKind.PROJECTION_VALUE, 2.0 if stage.projection_candidate else 1.0),
        CurriculumStageKind.REPAIR_TASK: (DiscoveryValueSignalKind.REPAIR_VALUE, 1.5),
        CurriculumStageKind.RESIDUAL_REVIEW: (DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 1.0),
    }
    if stage.kind in mapping:
        kind, value = mapping[stage.kind]
        _add(signals, kind, value, stage)
    if stage.source and stage.target:
        _add(signals, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 0.5, stage)
    if stage.metadata.get("terminal_form") or stage.metadata.get("certificate_id"):
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -3.0, stage, "stage claims truth")
    return _score(stage.stage_id, DiscoveryValueObjectKind.CURRICULUM_STAGE, signals, label=stage.title, metadata={"advisory_only": True, "stage_kind": stage.kind.value})


def score_proof_digestion_trace(trace: ProofDigestionTrace) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    _add(signals, DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL, 3.0 if trace.is_truth_terminal() else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.DIGESTION_VALUE, 1.0 if trace.dependency_maps else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.DIGESTION_VALUE, 1.5 if trace.key_ideas else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.DIGESTION_VALUE, 1.5 if trace.reusable_schemas else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.DIGESTION_VALUE, 0.5 if trace.exposition_notes else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.0 if trace.reusable_schemas else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 2.0 if trace.projection_candidates else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.ROOT_LIKENESS, 1.5 if trace.reusable_schemas else 0.0, trace)
    _risk_from_terminal(signals, trace)
    score = _score(trace.trace_id, DiscoveryValueObjectKind.PROOF_DIGESTION_TRACE, signals, metadata={"advisory_only": True, "proof_like": True, "digested": trace.is_digested()})
    score.metadata["lawbook_assimilation_candidate"] = make_lawbook_assimilation_candidate(trace).to_dict()
    return score


def score_verifier_feedback(feedback: VerifierFeedback) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    if feedback.flaw_severity == FlawSeverity.MINOR_REPAIRABLE:
        _add(signals, DiscoveryValueSignalKind.REPAIR_VALUE, 1.5, feedback)
    if feedback.flaw_severity == FlawSeverity.STRUCTURAL_GAP:
        _add(signals, DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 1.5, feedback)
        _add(signals, DiscoveryValueSignalKind.PROOF_POTENTIAL, 1.0, feedback)
    if feedback.flaw_severity == FlawSeverity.CRITICAL_INVALIDATION:
        _add(signals, DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 2.0, feedback)
        _add(signals, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 1.0, feedback)
    if feedback.metadata.get("source") == "text" and feedback.metadata.get("verifier_boundary"):
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -2.0, feedback, "natural-language feedback claims verification")
    return _score(feedback.feedback_id, DiscoveryValueObjectKind.VERIFIER_FEEDBACK, signals, label=feedback.flaw_severity.value, metadata={"advisory_only": True, "repairable": feedback.is_repairable(), "flaw_severity": feedback.flaw_severity.value})


def score_repair_loop(trace: RepairLoopTrace) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    _add(signals, DiscoveryValueSignalKind.REPAIR_VALUE, 1.5 if any(item.flaw_severity == FlawSeverity.MINOR_REPAIRABLE for item in trace.feedback_items) else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.REPAIR_VALUE, 1.0 if any(item.flaw_severity == FlawSeverity.STRUCTURAL_GAP for item in trace.feedback_items) and trace.repair_plans else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 2.0 if any(item.flaw_severity == FlawSeverity.CRITICAL_INVALIDATION for item in trace.feedback_items) else 0.0, trace)
    if any(item.flaw_severity == FlawSeverity.CRITICAL_INVALIDATION for item in trace.feedback_items) and any(plan.action_kind == RepairActionKind.LOCAL_REVISE for plan in trace.repair_plans):
        _add(signals, DiscoveryValueSignalKind.REPAIR_VALUE, -2.0, trace, "critical invalidation locally revised")
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.0 if trace.projection_candidates else 0.0, trace)
    _risk_from_terminal(signals, trace)
    return _score(trace.trace_id, DiscoveryValueObjectKind.REPAIR_LOOP_TRACE, signals, metadata={"advisory_only": True, "has_repair_plans": bool(trace.repair_plans)})


def score_repair_plan(plan: RepairPlan) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    if plan.action_kind == RepairActionKind.LOCAL_REVISE:
        _add(signals, DiscoveryValueSignalKind.REPAIR_VALUE, 1.5, plan)
    if plan.action_kind in {RepairActionKind.REROUTE, RepairActionKind.EMIT_PROOF_TASK}:
        _add(signals, DiscoveryValueSignalKind.PROOF_POTENTIAL, 1.0, plan)
    if plan.action_kind == RepairActionKind.EMIT_COUNTERMODEL_TASK:
        _add(signals, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 1.0, plan)
    if plan.action_kind == RepairActionKind.EMIT_OBSTRUCTION_TASK:
        _add(signals, DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 1.0, plan)
    return _score(plan.repair_plan_id, DiscoveryValueObjectKind.REPAIR_PLAN, signals, label=plan.action_kind.value, metadata={"advisory_only": True})


def score_lawbook_assimilation_candidate(candidate: LawbookAssimilationCandidate) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.5 if candidate.ready else 0.5, candidate)
    _add(signals, DiscoveryValueSignalKind.REUSE_VALUE, 1.0 if candidate.schema_ids else 0.0, candidate)
    _add(signals, DiscoveryValueSignalKind.DIGESTION_VALUE, 1.0 if candidate.key_idea_ids or candidate.exposition_note_ids else 0.0, candidate)
    if not candidate.certificate_id:
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -1.0, candidate, "assimilation candidate without certificate")
    return _score(candidate.assimilation_id, DiscoveryValueObjectKind.LAWBOOK_ASSIMILATION_CANDIDATE, signals, metadata={"advisory_only": True, "projection_like": True})


def score_projection_candidate(candidate: ProjectionCandidate) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 2.0 * max(candidate.confidence, 0.1), candidate)
    _add(signals, DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL, 0.5 if candidate.source_claim_id and candidate.target_claim_id else 0.0, candidate)
    _add(signals, DiscoveryValueSignalKind.REUSE_VALUE, 1.0 if candidate.rule_kind != ProjectionRuleKind.ADVISORY_SIMILARITY else 0.0, candidate)
    if not candidate.advisory:
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -1.0, candidate, "projection candidate not marked advisory")
    return _score(candidate.candidate_id, DiscoveryValueObjectKind.PROJECTION_CANDIDATE, signals, label=candidate.rule_kind.value, metadata={"advisory_only": True, "projection_like": True})


def score_continuation_output(output: ContinuationActionOutput) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    if output.kind == ContinuationOutputKind.EPISODE_INPUT:
        _add(signals, DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL, 2.0, output)
    if output.kind == ContinuationOutputKind.PROOF_ARTIFACT or "proof" in str(output.task_payload).lower():
        _add(signals, DiscoveryValueSignalKind.PROOF_POTENTIAL, 1.0, output)
    if "countermodel" in str(output.task_payload).lower():
        _add(signals, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, 2.0, output)
    if output.projection_candidate is not None:
        _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 2.0, output)
    _risk_from_terminal(signals, output)
    return _score(output.output_id, DiscoveryValueObjectKind.CONTINUATION_OUTPUT, signals, label=output.kind.value, metadata={"advisory_only": True, "proof_like": output.kind == ContinuationOutputKind.PROOF_ARTIFACT})


def score_alchemical_trace(trace: AlchemicalTrace) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.0 if trace.has_phase(AlchemicalPhase.PROJECTION) else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.RESIDUAL_COMPRESSION_VALUE, 1.5 if trace.total_compression_gain() > 0 else 0.0, trace)
    _add(signals, DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL, 3.0 if trace.is_promoted() else 0.0, trace)
    if trace.has_phase(AlchemicalPhase.FIXATION) and not trace.is_promoted():
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -3.0, trace, "fixation without verifier")
    return _score(trace.trace_id, DiscoveryValueObjectKind.ALCHEMICAL_TRACE, signals, cost_estimate=trace.total_cost(), metadata={"advisory_only": True})


def score_agent_experience(exp: AgentExperience) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    _add(signals, DiscoveryValueSignalKind.RESIDUAL_COMPRESSION_VALUE, 2.0 if exp.residual_delta < 0 else 0.0, exp)
    _add(signals, DiscoveryValueSignalKind.RESIDUAL_COMPRESSION_VALUE, 1.5 if exp.compression_gain > 0 else 0.0, exp)
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.0 if exp.projection_gain > 0 else 0.0, exp)
    _add(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.0 if exp.derived_amplification > 0 else 0.0, exp)
    if exp.outcome in {AgentExperienceOutcome.RESIDUAL, AgentExperienceOutcome.NAMED_OBSTRUCTION}:
        _add(signals, DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, 1.0, exp)
    _add(signals, DiscoveryValueSignalKind.COST_PENALTY, -min(exp.cost_units / 10.0, 5.0), exp)
    if exp.terminal_form and not exp.verifier_boundary_crossed:
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -3.0, exp)
    return _score(exp.experience_id, DiscoveryValueObjectKind.AGENT_EXPERIENCE, signals, cost_estimate=exp.cost_units, metadata={"advisory_only": True})


def score_route_telemetry_event(event: Mapping[str, Any]) -> DiscoveryValueScore:
    signals: list[DiscoveryValueSignal] = []
    object_id = str(event.get("event_id") or content_id("route_event", dict(event), n=24))
    killed = bool(event.get("killed", False))
    _add_raw(signals, DiscoveryValueSignalKind.ROUTE_SURVIVAL_VALUE, 2.0 if float(event.get("survival_weight", 0.0) or 0.0) >= 0.5 else 0.0, object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT)
    _add_raw(signals, DiscoveryValueSignalKind.ROUTE_SURVIVAL_VALUE, -2.0 if killed else 0.0, object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT)
    _add_raw(signals, DiscoveryValueSignalKind.RESIDUAL_COMPRESSION_VALUE, 2.0 if int(event.get("residual_delta", 0) or 0) < 0 else 0.0, object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT)
    _add_raw(signals, DiscoveryValueSignalKind.RESIDUAL_COMPRESSION_VALUE, 1.5 if float(event.get("compression_gain", 0.0) or 0.0) > 0 else 0.0, object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT)
    _add_raw(signals, DiscoveryValueSignalKind.PROJECTION_VALUE, 1.0 if float(event.get("projection_gain", 0.0) or 0.0) > 0 else 0.0, object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT)
    cost = float(event.get("cost_units", 0.0) or 0.0)
    _add_raw(signals, DiscoveryValueSignalKind.COST_PENALTY, -min(cost / 10.0, 5.0), object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT)
    return _score(object_id, DiscoveryValueObjectKind.ROUTE_TELEMETRY_EVENT, signals, cost_estimate=cost, metadata={"advisory_only": True, "killed": killed})


def score_object(obj: Any) -> DiscoveryValueScore:
    if isinstance(obj, ContinuationCurriculum):
        return score_curriculum(obj)
    if isinstance(obj, CurriculumStage):
        return score_curriculum_stage(obj)
    if isinstance(obj, ProofDigestionTrace):
        return score_proof_digestion_trace(obj)
    if isinstance(obj, VerifierFeedback):
        return score_verifier_feedback(obj)
    if isinstance(obj, RepairLoopTrace):
        return score_repair_loop(obj)
    if isinstance(obj, RepairPlan):
        return score_repair_plan(obj)
    if isinstance(obj, LawbookAssimilationCandidate):
        return score_lawbook_assimilation_candidate(obj)
    if isinstance(obj, ProjectionCandidate):
        return score_projection_candidate(obj)
    if isinstance(obj, ContinuationActionOutput):
        return score_continuation_output(obj)
    if isinstance(obj, AlchemicalTrace):
        return score_alchemical_trace(obj)
    if isinstance(obj, AgentExperience):
        return score_agent_experience(obj)
    if isinstance(obj, Mapping):
        if "route_kind" in obj or "killed" in obj:
            return score_route_telemetry_event(obj)
        return _unknown_score(obj, DiscoveryValueObjectKind.RAW_TASK)
    return _unknown_score(obj, DiscoveryValueObjectKind.UNKNOWN)


def build_discovery_value_report(
    *,
    curricula: Sequence[ContinuationCurriculum] = (),
    curriculum_stages: Sequence[CurriculumStage] = (),
    proof_digestion_traces: Sequence[ProofDigestionTrace] = (),
    lawbook_assimilation_candidates: Sequence[LawbookAssimilationCandidate] = (),
    verifier_feedback_items: Sequence[VerifierFeedback] = (),
    repair_loop_traces: Sequence[RepairLoopTrace] = (),
    repair_plans: Sequence[RepairPlan] = (),
    projection_candidates: Sequence[ProjectionCandidate] = (),
    continuation_outputs: Sequence[ContinuationActionOutput] = (),
    alchemical_traces: Sequence[AlchemicalTrace] = (),
    agent_experiences: Sequence[AgentExperience] = (),
    route_telemetry_events: Sequence[Mapping[str, Any]] = (),
    raw_tasks: Sequence[Mapping[str, Any]] = (),
    top_n: int | None = None,
) -> DiscoveryValueReport:
    objects = [
        *curricula,
        *curriculum_stages,
        *proof_digestion_traces,
        *lawbook_assimilation_candidates,
        *verifier_feedback_items,
        *repair_loop_traces,
        *repair_plans,
        *projection_candidates,
        *continuation_outputs,
        *alchemical_traces,
        *agent_experiences,
        *route_telemetry_events,
        *raw_tasks,
    ]
    scores = [score_object(obj) for obj in objects]
    _normalize(scores)
    for score in scores:
        score.decision = _decision(score)
    scores.sort(key=lambda score: (-score.normalized_score, -score.expected_gain, -score.raw_score, score.object_id))
    if top_n is not None:
        scores = scores[:top_n]
    for index, score in enumerate(scores, start=1):
        score.rank = index
    return _report(scores)


def discovery_value_report_to_continuation_outputs(report: DiscoveryValueReport) -> list[ContinuationActionOutput]:
    outputs = []
    for score in report.scores:
        if score.decision in {DiscoveryValueDecision.RUN_NOW, DiscoveryValueDecision.QUEUE_SOON, DiscoveryValueDecision.NEEDS_VERIFIER, DiscoveryValueDecision.NEEDS_REPAIR, DiscoveryValueDecision.PROJECT}:
            outputs.append(
                ContinuationActionOutput(
                    output_id=make_continuation_output_id({"discovery_value": score.to_dict()}),
                    action_id="discovery_value",
                    kind=ContinuationOutputKind.TASK,
                    status=ContinuationActionStatus.PRODUCED_TASK,
                    task_payload={"object_id": score.object_id, "decision": score.decision.value, "advisory_only": True},
                    note=f"Discovery value decision: {score.decision.value}",
                    score=score.normalized_score,
                    metadata={"advisory_only": True, "value_is_not_truth": True},
                )
            )
    return outputs


def discovery_value_report_to_curriculum(report: DiscoveryValueReport) -> ContinuationCurriculum:
    stages = []
    for score in report.scores:
        kind = {
            DiscoveryValueDecision.PROJECT: CurriculumStageKind.PROJECTION_TASK,
            DiscoveryValueDecision.NEEDS_REPAIR: CurriculumStageKind.REPAIR_TASK,
            DiscoveryValueDecision.NEEDS_DIGESTION: CurriculumStageKind.DIGESTION_TASK,
            DiscoveryValueDecision.HOLD_IN_CHORA: CurriculumStageKind.HELD_IN_CHORA,
            DiscoveryValueDecision.RESIDUALIZE: CurriculumStageKind.RESIDUAL_REVIEW,
            DiscoveryValueDecision.RUN_NOW: CurriculumStageKind.EPISODE_INPUT,
            DiscoveryValueDecision.QUEUE_SOON: CurriculumStageKind.PROOF_TASK,
            DiscoveryValueDecision.NEEDS_VERIFIER: CurriculumStageKind.PROOF_TASK,
        }.get(score.decision)
        if kind is None:
            continue
        from mathgraph.continuation_curriculum import CurriculumStage, CurriculumStageStatus, make_curriculum_stage_id

        stages.append(
            CurriculumStage(
                stage_id=make_curriculum_stage_id("discovery_value", score.to_dict()),
                kind=kind,
                status=CurriculumStageStatus.READY,
                title=f"Discovery value: {score.decision.value}",
                priority=score.normalized_score,
                metadata={"advisory_only": True, "discovery_value_score_id": score.score_id},
            )
        )
    return build_continuation_curriculum(action_outputs=(), max_stages=max(len(stages), 1)) if not stages else _curriculum_from_value_stages(stages)


def discovery_value_report_to_alchemical_trace(report: DiscoveryValueReport) -> AlchemicalTrace:
    trace = AlchemicalTrace(trace_id=make_alchemical_trace_id("discovery_value", report.report_id))
    trace.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if report.scores:
        trace.add_step(phase=AlchemicalPhase.SUBLIMATION, status=AlchemicalStatus.ADVISORY_ONLY)
        trace.add_step(phase=AlchemicalPhase.DISTILLATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(score.decision in {DiscoveryValueDecision.RUN_NOW, DiscoveryValueDecision.QUEUE_SOON, DiscoveryValueDecision.NEEDS_REPAIR, DiscoveryValueDecision.NEEDS_VERIFIER} for score in report.scores):
        trace.add_step(phase=AlchemicalPhase.DESCENSION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(score.decision == DiscoveryValueDecision.PROJECT for score in report.scores):
        trace.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.ADVISORY_ONLY)
    return trace


def discovery_value_report_to_agent_experiences(report: DiscoveryValueReport, agent_id: str | None = None) -> list[AgentExperience]:
    return [
        AgentExperience(
            experience_id=content_id("discovery_value_exp", score.to_dict(), n=24),
            agent_id=agent_id or "discovery-value",
            episode_id=None,
            claim_id=score.object_id,
            route="discovery_value",
            phase=AlchemicalPhase.DISTILLATION.value,
            outcome=AgentExperienceOutcome.RESIDUAL if score.decision == DiscoveryValueDecision.RESIDUALIZE else AgentExperienceOutcome.ADVISORY_ONLY,
            compression_gain=max(score.raw_score, 0.0),
            verifier_boundary_crossed=False,
            metadata={"discovery_value_score": score.to_dict(), "value_is_not_truth": True},
        )
        for score in report.scores
    ]


def discovery_value_report_to_route_telemetry_events(report: DiscoveryValueReport) -> list[dict[str, Any]]:
    return [
        {
            "event_id": content_id("discovery_value_event", score.to_dict(), n=24),
            "episode_id": None,
            "claim_id": score.object_id,
            "route_kind": "ADVISORY_ONLY",
            "outcome": "ADVISORY_ONLY",
            "from_state": "discovery_value",
            "to_state": score.decision.value.lower(),
            "cost_units": score.cost_estimate,
            "compression_gain": max(score.raw_score, 0.0),
            "killed": score.decision == DiscoveryValueDecision.DROP,
            "advisory": True,
            "metadata": {"score_id": score.score_id},
        }
        for score in report.scores
    ]


def _score(object_id: str, object_kind: DiscoveryValueObjectKind, signals: list[DiscoveryValueSignal], *, label: str | None = None, cost_estimate: float = 0.0, metadata: Mapping[str, Any] | None = None) -> DiscoveryValueScore:
    score = DiscoveryValueScore(
        score_id=make_discovery_value_score_id(object_id, object_kind.value, [signal.to_dict() for signal in signals]),
        object_id=object_id,
        object_kind=object_kind,
        label=label,
        signals=signals,
        cost_estimate=cost_estimate,
        metadata={"advisory_only": True, "value_is_not_truth": True, **dict(metadata or {})},
    )
    score.recompute()
    return score


def _unknown_score(obj: Any, kind: DiscoveryValueObjectKind) -> DiscoveryValueScore:
    object_id = content_id("unknown_discovery_object", repr(obj), n=24)
    signals: list[DiscoveryValueSignal] = []
    _add_raw(signals, DiscoveryValueSignalKind.RISK_PENALTY, -1.0, object_id, kind, "unknown object kind")
    return _score(object_id, kind, signals, metadata={"advisory_only": True, "unknown_object": True})


def _add(signals: list[DiscoveryValueSignal], kind: DiscoveryValueSignalKind, value: float, obj: Any, reason: str | None = None) -> None:
    if value:
        object_id, object_kind = _identity(obj)
        _add_raw(signals, kind, value, object_id, object_kind, reason)


def _add_raw(signals: list[DiscoveryValueSignal], kind: DiscoveryValueSignalKind, value: float, object_id: str, object_kind: DiscoveryValueObjectKind, reason: str | None = None) -> None:
    if value:
        signals.append(
            DiscoveryValueSignal(
                signal_id=make_discovery_value_signal_id(kind.value, value, object_id, reason),
                kind=kind,
                value=value,
                reason=reason,
                source_object_id=object_id,
                source_object_kind=object_kind,
                metadata={"advisory_only": True},
            )
        )


def _identity(obj: Any) -> tuple[str, DiscoveryValueObjectKind]:
    mapping = [
        (ContinuationCurriculum, "curriculum_id", DiscoveryValueObjectKind.CURRICULUM),
        (CurriculumStage, "stage_id", DiscoveryValueObjectKind.CURRICULUM_STAGE),
        (ProofDigestionTrace, "trace_id", DiscoveryValueObjectKind.PROOF_DIGESTION_TRACE),
        (VerifierFeedback, "feedback_id", DiscoveryValueObjectKind.VERIFIER_FEEDBACK),
        (RepairLoopTrace, "trace_id", DiscoveryValueObjectKind.REPAIR_LOOP_TRACE),
        (RepairPlan, "repair_plan_id", DiscoveryValueObjectKind.REPAIR_PLAN),
        (LawbookAssimilationCandidate, "assimilation_id", DiscoveryValueObjectKind.LAWBOOK_ASSIMILATION_CANDIDATE),
        (ProjectionCandidate, "candidate_id", DiscoveryValueObjectKind.PROJECTION_CANDIDATE),
        (ContinuationActionOutput, "output_id", DiscoveryValueObjectKind.CONTINUATION_OUTPUT),
        (AlchemicalTrace, "trace_id", DiscoveryValueObjectKind.ALCHEMICAL_TRACE),
        (AgentExperience, "experience_id", DiscoveryValueObjectKind.AGENT_EXPERIENCE),
    ]
    for cls, attr, kind in mapping:
        if isinstance(obj, cls):
            return str(getattr(obj, attr)), kind
    return content_id("discovery_object", repr(obj), n=24), DiscoveryValueObjectKind.UNKNOWN


def _risk_from_terminal(signals: list[DiscoveryValueSignal], obj: Any) -> None:
    if (getattr(obj, "terminal_form", None) or getattr(obj, "certificate_id", None)) and not getattr(obj, "verifier_boundary_crossed", False):
        _add(signals, DiscoveryValueSignalKind.RISK_PENALTY, -3.0, obj, "truth-boundary misuse")


def _normalize(scores: list[DiscoveryValueScore]) -> None:
    if not scores:
        return
    values = [score.raw_score for score in scores]
    low, high = min(values), max(values)
    for score in scores:
        if low == high:
            score.normalized_score = 1.0 if score.raw_score > 0 else 0.0
        else:
            score.normalized_score = (score.raw_score - low) / (high - low)


def _decision(score: DiscoveryValueScore) -> DiscoveryValueDecision:
    if score.raw_score < 0:
        return DiscoveryValueDecision.DROP
    if score.object_kind == DiscoveryValueObjectKind.VERIFIER_FEEDBACK and score.metadata.get("repairable"):
        return DiscoveryValueDecision.NEEDS_REPAIR
    if score.object_kind == DiscoveryValueObjectKind.PROJECTION_CANDIDATE and score.raw_score > 0:
        return DiscoveryValueDecision.PROJECT
    if score.object_kind == DiscoveryValueObjectKind.PROOF_DIGESTION_TRACE and score.metadata.get("proof_like") and not score.metadata.get("digested"):
        return DiscoveryValueDecision.NEEDS_DIGESTION
    if score.metadata.get("proof_like") and not score.is_terminal():
        return DiscoveryValueDecision.NEEDS_VERIFIER
    if score.risk_estimate >= 2.0 and score.raw_score > 0:
        return DiscoveryValueDecision.HOLD_IN_CHORA
    if score.object_kind == DiscoveryValueObjectKind.REPAIR_LOOP_TRACE and any(signal.kind == DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL for signal in score.signals):
        return DiscoveryValueDecision.RESIDUALIZE
    if score.normalized_score >= 0.80:
        return DiscoveryValueDecision.RUN_NOW
    if score.normalized_score >= 0.55:
        return DiscoveryValueDecision.QUEUE_SOON
    if score.raw_score > 0:
        return DiscoveryValueDecision.HOLD_IN_CHORA
    return DiscoveryValueDecision.UNKNOWN


def _report(scores: list[DiscoveryValueScore]) -> DiscoveryValueReport:
    summary = {
        "score_total": len(scores),
        "run_now_count": sum(score.decision == DiscoveryValueDecision.RUN_NOW for score in scores),
        "queue_soon_count": sum(score.decision == DiscoveryValueDecision.QUEUE_SOON for score in scores),
        "hold_count": sum(score.decision == DiscoveryValueDecision.HOLD_IN_CHORA for score in scores),
        "repair_count": sum(score.decision == DiscoveryValueDecision.NEEDS_REPAIR for score in scores),
        "digestion_count": sum(score.decision == DiscoveryValueDecision.NEEDS_DIGESTION for score in scores),
        "verifier_count": sum(score.decision == DiscoveryValueDecision.NEEDS_VERIFIER for score in scores),
        "project_count": sum(score.decision == DiscoveryValueDecision.PROJECT for score in scores),
        "residual_count": sum(score.decision == DiscoveryValueDecision.RESIDUALIZE for score in scores),
        "drop_count": sum(score.decision == DiscoveryValueDecision.DROP for score in scores),
        "top_score": scores[0].normalized_score if scores else 0.0,
        "mean_score": mean([score.normalized_score for score in scores]) if scores else 0.0,
        "advisory_count": sum(score.advisory for score in scores),
        "terminal_count": sum(score.is_terminal() for score in scores),
        "risk_count": sum(score.risk_estimate > 0 for score in scores),
    }
    return DiscoveryValueReport(
        report_id=make_discovery_value_report_id([score.to_dict() for score in scores]),
        scores=scores,
        status=DiscoveryValueStatus.RANKED if scores else DiscoveryValueStatus.EMPTY,
        summary=summary,
        metadata={"advisory_only": True, "value_is_not_truth": True},
    )


def _curriculum_from_value_stages(stages: list[CurriculumStage]) -> ContinuationCurriculum:
    from mathgraph.continuation_curriculum import ContinuationCurriculum, CurriculumBuildStrategy, CurriculumTraceStatus, make_curriculum_id

    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("discovery_value", [stage.to_dict() for stage in stages]),
        strategy=CurriculumBuildStrategy.MIXED,
        stages=stages,
        status=CurriculumTraceStatus.TASKS_EMITTED,
        metadata={"advisory_only": True, "from_discovery_value": True, "curriculum_is_not_verification": True},
    )
    curriculum.summary.update(
        {
            "stage_total": len(stages),
            "advisory_count": len(stages),
            "terminal_count": 0,
            "advisory_only": True,
        }
    )
    return curriculum


def _optional_str(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


def _optional_terminal(value: Any) -> TerminalForm | None:
    return None if value in (None, "") else TerminalForm(str(value))

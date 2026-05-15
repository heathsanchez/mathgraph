"""Advisory continuation curricula for staged verification work.

Curricula turn hard targets into smaller route plans. They do not verify claims,
promote warm-ups into target proofs, or turn finite examples into truth.
"""

from __future__ import annotations

import json
import re
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
from mathgraph.projection import ProjectionCandidate


class CurriculumStageKind(str, Enum):
    TARGET = "TARGET"
    WARMUP_CLAIM = "WARMUP_CLAIM"
    SIMPLIFIED_CASE = "SIMPLIFIED_CASE"
    FINITE_EXAMPLE = "FINITE_EXAMPLE"
    PREREQUISITE_LEMMA = "PREREQUISITE_LEMMA"
    PROOF_TASK = "PROOF_TASK"
    COUNTERMODEL_TASK = "COUNTERMODEL_TASK"
    PROJECTION_TASK = "PROJECTION_TASK"
    REPAIR_TASK = "REPAIR_TASK"
    DIGESTION_TASK = "DIGESTION_TASK"
    EPISODE_INPUT = "EPISODE_INPUT"
    RESIDUAL_REVIEW = "RESIDUAL_REVIEW"
    HELD_IN_CHORA = "HELD_IN_CHORA"
    UNKNOWN = "UNKNOWN"


class CurriculumStageStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    SKIPPED = "SKIPPED"
    EMITTED = "EMITTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    UNKNOWN = "UNKNOWN"


class CurriculumBuildStrategy(str, Enum):
    EMPTY = "EMPTY"
    ACTION_EXPANSION = "ACTION_EXPANSION"
    MAGMA_EQUATIONAL = "MAGMA_EQUATIONAL"
    PROOF_DIGESTION = "PROOF_DIGESTION"
    VERIFIER_FEEDBACK = "VERIFIER_FEEDBACK"
    REPAIR_LOOP = "REPAIR_LOOP"
    PROJECTION = "PROJECTION"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class CurriculumTraceStatus(str, Enum):
    EMPTY = "EMPTY"
    BUILT = "BUILT"
    TASKS_EMITTED = "TASKS_EMITTED"
    EPISODE_INPUTS_EMITTED = "EPISODE_INPUTS_EMITTED"
    BLOCKED = "BLOCKED"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class CurriculumStage:
    stage_id: str
    kind: CurriculumStageKind
    status: CurriculumStageStatus = CurriculumStageStatus.PENDING
    title: str | None = None
    claim_id: str | None = None
    source: str | None = None
    target: str | None = None
    raw: str | None = None
    world: str | None = None
    priority: float = 0.0
    difficulty: float = 0.0
    depends_on: tuple[str, ...] = ()
    action_output: ContinuationActionOutput | None = None
    projection_candidate: ProjectionCandidate | None = None
    verifier_feedback_id: str | None = None
    repair_plan_id: str | None = None
    proof_digestion_trace_id: str | None = None
    episode_payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def is_terminal(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "title": self.title,
            "claim_id": self.claim_id,
            "source": self.source,
            "target": self.target,
            "raw": self.raw,
            "world": self.world,
            "priority": self.priority,
            "difficulty": self.difficulty,
            "depends_on": list(self.depends_on),
            "action_output": self.action_output.to_dict() if self.action_output else None,
            "projection_candidate": self.projection_candidate.to_dict() if self.projection_candidate else None,
            "verifier_feedback_id": self.verifier_feedback_id,
            "repair_plan_id": self.repair_plan_id,
            "proof_digestion_trace_id": self.proof_digestion_trace_id,
            "episode_payload": dict(self.episode_payload),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CurriculumStage":
        return cls(
            stage_id=str(data["stage_id"]),
            kind=CurriculumStageKind(str(data.get("kind", CurriculumStageKind.UNKNOWN.value))),
            status=CurriculumStageStatus(str(data.get("status", CurriculumStageStatus.PENDING.value))),
            title=_optional_str(data.get("title")),
            claim_id=_optional_str(data.get("claim_id")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            raw=_optional_str(data.get("raw")),
            world=_optional_str(data.get("world")),
            priority=float(data.get("priority", 0.0) or 0.0),
            difficulty=float(data.get("difficulty", 0.0) or 0.0),
            depends_on=tuple(str(x) for x in data.get("depends_on", ())),
            action_output=ContinuationActionOutput.from_dict(data["action_output"]) if data.get("action_output") else None,
            projection_candidate=ProjectionCandidate.from_dict(data["projection_candidate"]) if data.get("projection_candidate") else None,
            verifier_feedback_id=_optional_str(data.get("verifier_feedback_id")),
            repair_plan_id=_optional_str(data.get("repair_plan_id")),
            proof_digestion_trace_id=_optional_str(data.get("proof_digestion_trace_id")),
            episode_payload=dict(data.get("episode_payload", {})),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "CurriculumStage":
        return cls.from_dict(json.loads(text))


@dataclass
class ContinuationCurriculum:
    curriculum_id: str
    target_claim_id: str | None = None
    target_raw: str | None = None
    target_source: str | None = None
    target_target: str | None = None
    world: str | None = None
    strategy: CurriculumBuildStrategy = CurriculumBuildStrategy.UNKNOWN
    stages: list[CurriculumStage] = field(default_factory=list)
    continuation_outputs: list[ContinuationActionOutput] = field(default_factory=list)
    projection_candidates: list[ProjectionCandidate] = field(default_factory=list)
    episode_inputs: list[dict[str, Any]] = field(default_factory=list)
    status: CurriculumTraceStatus = CurriculumTraceStatus.EMPTY
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def stage_count(self) -> int:
        return len(self.stages)

    def output_count(self) -> int:
        return len(self.continuation_outputs)

    def episode_input_count(self) -> int:
        return len(self.episode_inputs)

    def is_terminal(self) -> bool:
        return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed

    def to_dict(self) -> dict[str, Any]:
        return {
            "curriculum_id": self.curriculum_id,
            "target_claim_id": self.target_claim_id,
            "target_raw": self.target_raw,
            "target_source": self.target_source,
            "target_target": self.target_target,
            "world": self.world,
            "strategy": self.strategy.value,
            "stages": [stage.to_dict() for stage in self.stages],
            "continuation_outputs": [output.to_dict() for output in self.continuation_outputs],
            "projection_candidates": [candidate.to_dict() for candidate in self.projection_candidates],
            "episode_inputs": [dict(item) for item in self.episode_inputs],
            "status": self.status.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuationCurriculum":
        return cls(
            curriculum_id=str(data["curriculum_id"]),
            target_claim_id=_optional_str(data.get("target_claim_id")),
            target_raw=_optional_str(data.get("target_raw")),
            target_source=_optional_str(data.get("target_source")),
            target_target=_optional_str(data.get("target_target")),
            world=_optional_str(data.get("world")),
            strategy=CurriculumBuildStrategy(str(data.get("strategy", CurriculumBuildStrategy.UNKNOWN.value))),
            stages=[CurriculumStage.from_dict(item) for item in data.get("stages", [])],
            continuation_outputs=[ContinuationActionOutput.from_dict(item) for item in data.get("continuation_outputs", [])],
            projection_candidates=[ProjectionCandidate.from_dict(item) for item in data.get("projection_candidates", [])],
            episode_inputs=[dict(item) for item in data.get("episode_inputs", [])],
            status=CurriculumTraceStatus(str(data.get("status", CurriculumTraceStatus.EMPTY.value))),
            terminal_form=_optional_terminal(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", True)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ContinuationCurriculum":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "ContinuationCurriculum":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(json.dumps(stage.to_dict(), sort_keys=True, separators=(",", ":")) + "\n" for stage in self.stages), encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "ContinuationCurriculum":
        stages = [
            CurriculumStage.from_dict(json.loads(line))
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        curriculum = build_empty_curriculum()
        curriculum.stages = stages
        curriculum.status = _status_for(stages, [])
        curriculum.summary.update(_summary(curriculum))
        return curriculum


def make_curriculum_stage_id(*parts: Any) -> str:
    return content_id("curriculum_stage", parts, n=24)


def make_curriculum_id(*parts: Any) -> str:
    return content_id("continuation_curriculum", parts, n=24)


def normalize_curriculum_target(
    *,
    raw: str | None = None,
    source: str | None = None,
    target: str | None = None,
    claim_id: str | None = None,
    world: str | None = None,
    domain_claim: Any | None = None,
) -> dict[str, Any]:
    data = domain_claim.to_dict() if hasattr(domain_claim, "to_dict") else dict(domain_claim or {})
    inferred_world = world or _enum_value(data.get("world"))
    if inferred_world is None and (source or data.get("source")) and (target or data.get("target")):
        inferred_world = "MAGMA_EQUATIONAL"
    return {
        "claim_id": claim_id or _optional_str(data.get("claim_id")),
        "raw": raw or _optional_str(data.get("raw")),
        "source": source or _optional_str(data.get("source")),
        "target": target or _optional_str(data.get("target")),
        "world": inferred_world,
        "normalized": _optional_str(data.get("normalized")),
        "advisory": True,
    }


def build_empty_curriculum(
    *,
    target_claim_id: str | None = None,
    target_raw: str | None = None,
    target_source: str | None = None,
    target_target: str | None = None,
    world: str | None = None,
) -> ContinuationCurriculum:
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("empty", target_claim_id, target_raw, target_source, target_target, world),
        target_claim_id=target_claim_id,
        target_raw=target_raw,
        target_source=target_source,
        target_target=target_target,
        world=world,
        strategy=CurriculumBuildStrategy.EMPTY,
        metadata={"advisory_only": True, "curriculum_is_not_verification": True},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_curriculum_from_actions(
    action_outputs: Sequence[ContinuationActionOutput],
    *,
    target_claim_id: str | None = None,
    target_raw: str | None = None,
    world: str | None = None,
    max_stages: int | None = None,
) -> ContinuationCurriculum:
    stages = [_stage_from_output(output, world=world) for output in action_outputs]
    stages = stages[:max_stages] if max_stages is not None else stages
    episodes = [stage.episode_payload for stage in stages if stage.episode_payload]
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("actions", [output.to_dict() for output in action_outputs], target_claim_id),
        target_claim_id=target_claim_id,
        target_raw=target_raw,
        world=world,
        strategy=CurriculumBuildStrategy.ACTION_EXPANSION,
        stages=stages,
        continuation_outputs=list(action_outputs),
        projection_candidates=[output.projection_candidate for output in action_outputs if output.projection_candidate is not None],
        episode_inputs=episodes,
        status=_status_for(stages, episodes),
        metadata={"advisory_only": True},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_magma_equational_curriculum(
    *,
    source: str,
    target: str,
    claim_id: str | None = None,
    max_stages: int = 24,
) -> ContinuationCurriculum:
    world = "MAGMA_EQUATIONAL"
    complexity = float(source.count("*") + target.count("*") + source.count("(") + target.count("("))
    repeated = sorted({var for var in _variables(source + " " + target) if (source + target).count(var) > 1})
    canonical_source = _canonicalize_variables(source)
    canonical_target = _canonicalize_variables(target)
    specs: list[tuple[CurriculumStageKind, str, str | None, str | None, dict[str, Any]]] = [
        (CurriculumStageKind.TARGET, "Target implication", source, target, {}),
        (CurriculumStageKind.WARMUP_CLAIM, "Warm-up: source reflexivity", source, source, {"warmup_not_target_proof": True}),
        (CurriculumStageKind.WARMUP_CLAIM, "Warm-up: target reflexivity", target, target, {"warmup_not_target_proof": True}),
    ]
    if repeated:
        specs.append((CurriculumStageKind.SIMPLIFIED_CASE, "Simplified repeated-variable case", source, target, {"repeated_variables": repeated}))
    if canonical_source != source or canonical_target != target:
        specs.append((CurriculumStageKind.SIMPLIFIED_CASE, "Canonical variable renaming", canonical_source, canonical_target, {"canonicalized": True}))
    specs.extend(
        [
            (CurriculumStageKind.FINITE_EXAMPLE, "Finite example search: carrier size 2", source, target, {"carrier_size": 2, "finite_example_not_proof": True}),
            (CurriculumStageKind.FINITE_EXAMPLE, "Finite example search: carrier size 3", source, target, {"carrier_size": 3, "finite_example_not_proof": True}),
            (CurriculumStageKind.COUNTERMODEL_TASK, "Countermodel task: source true / target false", source, target, {"task_kind": "countermodel_search"}),
            (CurriculumStageKind.PROOF_TASK, "Proof task: source closure / target absorption", source, target, {"task_kind": "proof_task"}),
            (CurriculumStageKind.PROJECTION_TASK, "Projection task: known closures", source, target, {"task_kind": "projection_lookup"}),
            (CurriculumStageKind.RESIDUAL_REVIEW, "Residual review if no route closes", source, target, {"residual_fallback": True}),
        ]
    )
    stages = [
        _make_stage(kind, title, claim_id=claim_id, source=src, target=tgt, world=world, priority=max(0.0, 10.0 - index), difficulty=complexity + index / 10.0, metadata=metadata)
        for index, (kind, title, src, tgt, metadata) in enumerate(specs)
    ][:max_stages]
    episodes = [stage.episode_payload for stage in stages if stage.episode_payload]
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("magma", claim_id, source, target, [stage.to_dict() for stage in stages]),
        target_claim_id=claim_id,
        target_source=source,
        target_target=target,
        world=world,
        strategy=CurriculumBuildStrategy.MAGMA_EQUATIONAL,
        stages=stages,
        episode_inputs=episodes,
        status=_status_for(stages, episodes),
        metadata={"advisory_only": True, "curriculum_is_not_verification": True},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_curriculum_from_proof_digestion(digestion_trace: Any, *, max_stages: int | None = None) -> ContinuationCurriculum:
    stages: list[CurriculumStage] = []
    for dep in digestion_trace.dependency_maps:
        stages.append(_make_stage(CurriculumStageKind.PREREQUISITE_LEMMA, "Review proof dependencies", raw=",".join(dep.raw_dependency_names), proof_digestion_trace_id=digestion_trace.trace_id))
    for idea in digestion_trace.key_ideas:
        stages.append(_make_stage(CurriculumStageKind.PROOF_TASK, "Use key idea candidate", raw=idea.statement, proof_digestion_trace_id=digestion_trace.trace_id))
    for schema in digestion_trace.reusable_schemas:
        stages.append(_make_stage(CurriculumStageKind.PROJECTION_TASK, f"Project schema {schema.name}", raw=schema.pattern, proof_digestion_trace_id=digestion_trace.trace_id))
    if digestion_trace.exposition_notes:
        stages.append(_make_stage(CurriculumStageKind.DIGESTION_TASK, "Review exposition before assimilation", proof_digestion_trace_id=digestion_trace.trace_id))
    stages = stages[:max_stages] if max_stages is not None else stages
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("digestion", digestion_trace.trace_id, [stage.to_dict() for stage in stages]),
        strategy=CurriculumBuildStrategy.PROOF_DIGESTION,
        stages=stages,
        status=_status_for(stages, []),
        metadata={"advisory_only": True},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_curriculum_from_verifier_feedback(feedback_items: Sequence[Any], *, max_stages: int | None = None) -> ContinuationCurriculum:
    from mathgraph.verifier_feedback import FlawSeverity, RepairActionKind, plan_repair_from_feedback

    stages: list[CurriculumStage] = []
    for feedback in feedback_items:
        for plan in plan_repair_from_feedback(feedback):
            if feedback.flaw_severity == FlawSeverity.MINOR_REPAIRABLE:
                kind = CurriculumStageKind.REPAIR_TASK
            elif feedback.flaw_severity == FlawSeverity.STRUCTURAL_GAP:
                kind = CurriculumStageKind.PREREQUISITE_LEMMA if plan.action_kind == RepairActionKind.REROUTE else CurriculumStageKind.PROOF_TASK
            elif feedback.flaw_severity == FlawSeverity.CRITICAL_INVALIDATION:
                kind = CurriculumStageKind.COUNTERMODEL_TASK if plan.action_kind == RepairActionKind.EMIT_OBSTRUCTION_TASK else CurriculumStageKind.RESIDUAL_REVIEW
            else:
                kind = CurriculumStageKind.HELD_IN_CHORA if plan.action_kind == RepairActionKind.HOLD_IN_CHORA else CurriculumStageKind.RESIDUAL_REVIEW
            stages.append(_stage_from_repair_plan(plan, feedback, kind))
    stages = stages[:max_stages] if max_stages is not None else stages
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("feedback", [item.to_dict() for item in feedback_items], [stage.to_dict() for stage in stages]),
        strategy=CurriculumBuildStrategy.VERIFIER_FEEDBACK,
        stages=stages,
        continuation_outputs=[stage.action_output for stage in stages if stage.action_output],
        episode_inputs=[stage.episode_payload for stage in stages if stage.episode_payload],
        status=_status_for(stages, [stage.episode_payload for stage in stages if stage.episode_payload]),
        metadata={"advisory_only": True, "from_verifier_feedback": bool(feedback_items)},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_curriculum_from_repair_loop(repair_trace: Any, *, max_stages: int | None = None) -> ContinuationCurriculum:
    stages = []
    feedback_by_id = {item.feedback_id: item for item in repair_trace.feedback_items}
    for plan in repair_trace.repair_plans:
        feedback = feedback_by_id.get(plan.feedback_id)
        kind = _stage_kind_from_repair_action(plan.action_kind.value)
        stages.append(_stage_from_repair_plan(plan, feedback, kind))
    for output in repair_trace.continuation_outputs:
        stages.append(_stage_from_output(output))
    stages = stages[:max_stages] if max_stages is not None else stages
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("repair_loop", repair_trace.trace_id, [stage.to_dict() for stage in stages]),
        strategy=CurriculumBuildStrategy.REPAIR_LOOP,
        stages=stages,
        continuation_outputs=list(repair_trace.continuation_outputs),
        projection_candidates=list(repair_trace.projection_candidates),
        episode_inputs=[stage.episode_payload for stage in stages if stage.episode_payload],
        status=_status_for(stages, [stage.episode_payload for stage in stages if stage.episode_payload]),
        metadata={"advisory_only": True, "repair_trace_id": repair_trace.trace_id},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_curriculum_from_projection_candidates(
    projection_candidates: Sequence[ProjectionCandidate],
    *,
    target_claim_id: str | None = None,
    max_stages: int | None = None,
) -> ContinuationCurriculum:
    stages = [
        _make_stage(
            CurriculumStageKind.PROJECTION_TASK,
            "Projection candidate review",
            claim_id=target_claim_id or candidate.target_claim_id,
            source=candidate.source,
            target=candidate.target,
            priority=float(candidate.confidence),
            projection_candidate=candidate,
            metadata={"projection_candidate_id": candidate.candidate_id},
        )
        for candidate in projection_candidates
    ]
    stages = stages[:max_stages] if max_stages is not None else stages
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id("projection", [candidate.to_dict() for candidate in projection_candidates]),
        target_claim_id=target_claim_id,
        strategy=CurriculumBuildStrategy.PROJECTION,
        stages=stages,
        projection_candidates=list(projection_candidates),
        status=_status_for(stages, []),
        metadata={"advisory_only": True},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def build_continuation_curriculum(
    *,
    raw: str | None = None,
    source: str | None = None,
    target: str | None = None,
    claim_id: str | None = None,
    world: str | None = None,
    domain_claim: Any | None = None,
    action_outputs: Sequence[ContinuationActionOutput] = (),
    proof_digestion_traces: Sequence[Any] = (),
    verifier_feedback_items: Sequence[Any] = (),
    repair_loop_traces: Sequence[Any] = (),
    projection_candidates: Sequence[ProjectionCandidate] = (),
    max_stages: int = 50,
) -> ContinuationCurriculum:
    normalized = normalize_curriculum_target(raw=raw, source=source, target=target, claim_id=claim_id, world=world, domain_claim=domain_claim)
    pieces: list[ContinuationCurriculum] = []
    if normalized["source"] and normalized["target"]:
        pieces.append(build_magma_equational_curriculum(source=normalized["source"], target=normalized["target"], claim_id=normalized["claim_id"], max_stages=max_stages))
    if action_outputs:
        pieces.append(build_curriculum_from_actions(action_outputs, target_claim_id=normalized["claim_id"], target_raw=normalized["raw"], world=normalized["world"]))
    pieces.extend(build_curriculum_from_proof_digestion(trace) for trace in proof_digestion_traces)
    if verifier_feedback_items:
        pieces.append(build_curriculum_from_verifier_feedback(verifier_feedback_items))
    pieces.extend(build_curriculum_from_repair_loop(trace) for trace in repair_loop_traces)
    if projection_candidates:
        pieces.append(build_curriculum_from_projection_candidates(projection_candidates, target_claim_id=normalized["claim_id"]))
    if not pieces:
        return build_empty_curriculum(
            target_claim_id=normalized["claim_id"],
            target_raw=normalized["raw"],
            target_source=normalized["source"],
            target_target=normalized["target"],
            world=normalized["world"],
        )
    stages = _dedupe_stages(stage for piece in pieces for stage in piece.stages)
    stages.sort(key=lambda stage: (-stage.priority, stage.difficulty, stage.kind.value, stage.stage_id))
    stages = stages[:max_stages]
    outputs = _dedupe_by_id(output for piece in pieces for output in piece.continuation_outputs)
    projections = _dedupe_by_id(candidate for piece in pieces for candidate in piece.projection_candidates)
    episodes = _dedupe_dicts([stage.episode_payload for stage in stages if stage.episode_payload] + [item for piece in pieces for item in piece.episode_inputs])
    strategies = {piece.strategy for piece in pieces if piece.strategy != CurriculumBuildStrategy.EMPTY}
    strategy = next(iter(strategies)) if len(strategies) == 1 else CurriculumBuildStrategy.MIXED
    curriculum = ContinuationCurriculum(
        curriculum_id=make_curriculum_id(normalized, [stage.to_dict() for stage in stages]),
        target_claim_id=normalized["claim_id"],
        target_raw=normalized["raw"],
        target_source=normalized["source"],
        target_target=normalized["target"],
        world=normalized["world"],
        strategy=strategy,
        stages=stages,
        continuation_outputs=outputs,
        projection_candidates=projections,
        episode_inputs=episodes,
        status=_status_for(stages, episodes),
        metadata={"advisory_only": True, "curriculum_is_not_verification": True},
    )
    curriculum.summary.update(_summary(curriculum))
    return curriculum


def curriculum_to_continuation_outputs(curriculum: ContinuationCurriculum) -> list[ContinuationActionOutput]:
    outputs = [_advisory_output(output) for output in curriculum.continuation_outputs]
    existing = {output.output_id for output in outputs}
    for stage in curriculum.stages:
        if stage.action_output is not None or stage.kind in {CurriculumStageKind.TARGET, CurriculumStageKind.WARMUP_CLAIM}:
            continue
        output = ContinuationActionOutput(
            output_id=make_continuation_output_id({"curriculum": curriculum.curriculum_id, "stage": stage.to_dict()}),
            action_id="continuation_curriculum",
            kind=ContinuationOutputKind.TASK,
            status=ContinuationActionStatus.PRODUCED_TASK,
            task_payload={"stage_id": stage.stage_id, "stage_kind": stage.kind.value, **dict(stage.episode_payload)},
            note=stage.title,
            metadata={"advisory_only": True, "curriculum_output_not_truth": True},
        )
        if output.output_id not in existing:
            outputs.append(output)
            existing.add(output.output_id)
    return outputs


def curriculum_to_episode_inputs(curriculum: ContinuationCurriculum) -> list[dict[str, Any]]:
    rows = list(curriculum.episode_inputs)
    for stage in curriculum.stages:
        if stage.kind in {
            CurriculumStageKind.TARGET,
            CurriculumStageKind.PROOF_TASK,
            CurriculumStageKind.COUNTERMODEL_TASK,
            CurriculumStageKind.PROJECTION_TASK,
            CurriculumStageKind.EPISODE_INPUT,
        } and stage.source and stage.target:
            rows.append(
                {
                    "claim_id": stage.claim_id,
                    "source": stage.source,
                    "target": stage.target,
                    "route_hint": _route_hint(stage.kind),
                    "metadata": {"curriculum_stage_id": stage.stage_id, "advisory_only": True},
                }
            )
    return _dedupe_dicts(rows)


def curriculum_to_projection_candidates(curriculum: ContinuationCurriculum) -> list[ProjectionCandidate]:
    candidates = list(curriculum.projection_candidates)
    candidates.extend(stage.projection_candidate for stage in curriculum.stages if stage.projection_candidate is not None)
    return _dedupe_by_id(candidates)


def curriculum_to_alchemical_trace(curriculum: ContinuationCurriculum) -> AlchemicalTrace:
    trace = AlchemicalTrace(trace_id=make_alchemical_trace_id("continuation_curriculum", curriculum.curriculum_id), claim_id=curriculum.target_claim_id)
    trace.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if any(stage.kind == CurriculumStageKind.SIMPLIFIED_CASE for stage in curriculum.stages):
        trace.add_step(phase=AlchemicalPhase.CALCINATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(stage.kind in {CurriculumStageKind.PREREQUISITE_LEMMA, CurriculumStageKind.WARMUP_CLAIM} for stage in curriculum.stages):
        trace.add_step(phase=AlchemicalPhase.SOLUTION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(stage.kind in {CurriculumStageKind.PROOF_TASK, CurriculumStageKind.COUNTERMODEL_TASK, CurriculumStageKind.FINITE_EXAMPLE, CurriculumStageKind.EPISODE_INPUT} for stage in curriculum.stages):
        trace.add_step(phase=AlchemicalPhase.DESCENSION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(stage.kind == CurriculumStageKind.REPAIR_TASK for stage in curriculum.stages):
        trace.add_step(phase=AlchemicalPhase.DISTILLATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(stage.kind == CurriculumStageKind.PROJECTION_TASK for stage in curriculum.stages):
        trace.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.ADVISORY_ONLY)
    if curriculum.is_terminal():
        trace.terminal_form = curriculum.terminal_form
        trace.promoted_certificate_id = curriculum.certificate_id
        trace.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary="INHERITED_CURRICULUM_BOUNDARY")
    return trace


def curriculum_to_agent_experiences(curriculum: ContinuationCurriculum, agent_id: str | None = None) -> list[AgentExperience]:
    actor = agent_id or "continuation-curriculum"
    return [
        AgentExperience(
            experience_id=content_id("continuation_curriculum_exp", stage.to_dict(), n=24),
            agent_id=actor,
            episode_id=None,
            claim_id=stage.claim_id or curriculum.target_claim_id,
            route=f"curriculum:{stage.kind.value.lower()}",
            phase=AlchemicalPhase.DESCENSION.value,
            outcome=AgentExperienceOutcome.RESIDUAL if stage.kind in {CurriculumStageKind.RESIDUAL_REVIEW, CurriculumStageKind.HELD_IN_CHORA} else AgentExperienceOutcome.ADVISORY_ONLY,
            verifier_boundary_crossed=False,
            metadata={"curriculum_stage": stage.to_dict(), "curriculum_is_not_proof": True},
        )
        for stage in curriculum.stages
    ]


def curriculum_to_route_telemetry_events(curriculum: ContinuationCurriculum) -> list[dict[str, Any]]:
    return [
        {
            "episode_id": None,
            "claim_id": stage.claim_id or curriculum.target_claim_id,
            "route_kind": _route_hint(stage.kind),
            "outcome": "ADVISORY_ONLY",
            "from_state": "curriculum",
            "to_state": stage.kind.value.lower(),
            "killed": False,
            "advisory": True,
            "metadata": {"curriculum_id": curriculum.curriculum_id, "stage_id": stage.stage_id},
        }
        for stage in curriculum.stages
    ]


def _make_stage(
    kind: CurriculumStageKind,
    title: str,
    *,
    claim_id: str | None = None,
    source: str | None = None,
    target: str | None = None,
    raw: str | None = None,
    world: str | None = None,
    priority: float = 0.0,
    difficulty: float = 0.0,
    projection_candidate: ProjectionCandidate | None = None,
    verifier_feedback_id: str | None = None,
    repair_plan_id: str | None = None,
    proof_digestion_trace_id: str | None = None,
    action_output: ContinuationActionOutput | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CurriculumStage:
    episode_payload = {}
    if kind in {CurriculumStageKind.PROOF_TASK, CurriculumStageKind.COUNTERMODEL_TASK, CurriculumStageKind.PROJECTION_TASK, CurriculumStageKind.EPISODE_INPUT} and source and target:
        episode_payload = {"claim_id": claim_id, "source": source, "target": target, "route_hint": _route_hint(kind), "metadata": {"advisory_only": True}}
    payload = {
        "kind": kind.value,
        "title": title,
        "claim_id": claim_id,
        "source": source,
        "target": target,
        "raw": raw,
        "world": world,
        "projection_candidate": projection_candidate.candidate_id if projection_candidate else None,
        "feedback": verifier_feedback_id,
        "repair": repair_plan_id,
        "digestion": proof_digestion_trace_id,
    }
    return CurriculumStage(
        stage_id=make_curriculum_stage_id(payload),
        kind=kind,
        status=CurriculumStageStatus.READY,
        title=title,
        claim_id=claim_id,
        source=source,
        target=target,
        raw=raw,
        world=world,
        priority=priority,
        difficulty=difficulty,
        action_output=action_output,
        projection_candidate=projection_candidate,
        verifier_feedback_id=verifier_feedback_id,
        repair_plan_id=repair_plan_id,
        proof_digestion_trace_id=proof_digestion_trace_id,
        episode_payload=episode_payload,
        metadata={"advisory_only": True, **dict(metadata or {})},
    )


def _stage_from_output(output: ContinuationActionOutput, *, world: str | None = None) -> CurriculumStage:
    task_kind = str(output.task_payload.get("task_kind") or output.metadata.get("repair_action_kind") or "")
    if output.kind == ContinuationOutputKind.DOMAIN_CLAIM:
        kind = CurriculumStageKind.WARMUP_CLAIM
    elif output.kind == ContinuationOutputKind.EPISODE_INPUT:
        kind = CurriculumStageKind.EPISODE_INPUT
    elif output.kind == ContinuationOutputKind.PROJECTION_CANDIDATE:
        kind = CurriculumStageKind.PROJECTION_TASK
    elif output.kind == ContinuationOutputKind.OBSTRUCTION_CANDIDATE:
        kind = CurriculumStageKind.RESIDUAL_REVIEW
    elif "countermodel" in task_kind:
        kind = CurriculumStageKind.COUNTERMODEL_TASK
    elif "projection" in task_kind:
        kind = CurriculumStageKind.PROJECTION_TASK
    elif "repair" in task_kind or "local_revise" in task_kind:
        kind = CurriculumStageKind.REPAIR_TASK
    elif output.kind in {ContinuationOutputKind.PROOF_ARTIFACT, ContinuationOutputKind.THEOREM_SCHEMA_CANDIDATE} or "proof" in task_kind:
        kind = CurriculumStageKind.PROOF_TASK
    elif output.kind == ContinuationOutputKind.TASK:
        kind = CurriculumStageKind.REPAIR_TASK if output.metadata.get("repair_action_kind") else CurriculumStageKind.PROOF_TASK
    else:
        kind = CurriculumStageKind.UNKNOWN
    episode = output.episode_input.to_dict() if output.episode_input is not None else {}
    claim = output.domain_claim
    return CurriculumStage(
        stage_id=make_curriculum_stage_id("output", output.to_dict()),
        kind=kind,
        status=CurriculumStageStatus.EMITTED,
        title=output.note or f"Continuation output {output.kind.value}",
        claim_id=claim.claim_id if claim else (episode.get("claim_id") if episode else None),
        source=claim.source if claim else episode.get("source"),
        target=claim.target if claim else episode.get("target"),
        raw=claim.raw if claim else None,
        world=world or (_enum_value(claim.world) if claim else None),
        priority=float(output.score),
        action_output=output,
        projection_candidate=output.projection_candidate,
        episode_payload=episode,
        metadata={"advisory_only": True, "from_action_output": output.output_id},
    )


def _stage_from_repair_plan(plan: Any, feedback: Any | None, kind: CurriculumStageKind) -> CurriculumStage:
    return _make_stage(
        kind,
        plan.reason or "Repair plan",
        claim_id=getattr(feedback, "claim_id", None),
        priority=float(plan.priority),
        verifier_feedback_id=getattr(feedback, "feedback_id", None) or plan.feedback_id,
        repair_plan_id=plan.repair_plan_id,
        action_output=plan.continuation_output,
        metadata={"repair_action_kind": plan.action_kind.value, "from_verifier_feedback": True},
    )


def _stage_kind_from_repair_action(action: str) -> CurriculumStageKind:
    mapping = {
        "LOCAL_REVISE": CurriculumStageKind.REPAIR_TASK,
        "REGENERATE_ARTIFACT": CurriculumStageKind.REPAIR_TASK,
        "REROUTE": CurriculumStageKind.PREREQUISITE_LEMMA,
        "EMIT_PROOF_TASK": CurriculumStageKind.PROOF_TASK,
        "EMIT_COUNTERMODEL_TASK": CurriculumStageKind.COUNTERMODEL_TASK,
        "EMIT_PROJECTION_TASK": CurriculumStageKind.PROJECTION_TASK,
        "EMIT_OBSTRUCTION_TASK": CurriculumStageKind.RESIDUAL_REVIEW,
        "HOLD_IN_CHORA": CurriculumStageKind.HELD_IN_CHORA,
        "MARK_RESIDUAL": CurriculumStageKind.RESIDUAL_REVIEW,
    }
    return mapping.get(action, CurriculumStageKind.UNKNOWN)


def _status_for(stages: Sequence[CurriculumStage], episodes: Sequence[Mapping[str, Any]]) -> CurriculumTraceStatus:
    if not stages:
        return CurriculumTraceStatus.EMPTY
    if episodes:
        return CurriculumTraceStatus.EPISODE_INPUTS_EMITTED
    if any(stage.kind not in {CurriculumStageKind.TARGET, CurriculumStageKind.WARMUP_CLAIM, CurriculumStageKind.SIMPLIFIED_CASE} for stage in stages):
        return CurriculumTraceStatus.TASKS_EMITTED
    return CurriculumTraceStatus.BUILT


def _summary(curriculum: ContinuationCurriculum) -> dict[str, Any]:
    counts = {kind.value: sum(1 for stage in curriculum.stages if stage.kind == kind) for kind in CurriculumStageKind}
    return {
        "stage_total": len(curriculum.stages),
        "warmup_count": counts[CurriculumStageKind.WARMUP_CLAIM.value],
        "simplified_count": counts[CurriculumStageKind.SIMPLIFIED_CASE.value],
        "finite_example_count": counts[CurriculumStageKind.FINITE_EXAMPLE.value],
        "proof_task_count": counts[CurriculumStageKind.PROOF_TASK.value] + counts[CurriculumStageKind.PREREQUISITE_LEMMA.value],
        "countermodel_task_count": counts[CurriculumStageKind.COUNTERMODEL_TASK.value],
        "projection_task_count": counts[CurriculumStageKind.PROJECTION_TASK.value],
        "repair_task_count": counts[CurriculumStageKind.REPAIR_TASK.value],
        "episode_input_count": len(curriculum.episode_inputs),
        "residual_review_count": counts[CurriculumStageKind.RESIDUAL_REVIEW.value] + counts[CurriculumStageKind.HELD_IN_CHORA.value],
        "advisory_count": sum(1 for stage in curriculum.stages if stage.advisory),
        "terminal_count": sum(1 for stage in curriculum.stages if stage.is_terminal()),
        "advisory_only": True,
    }


def _variables(expr: str) -> list[str]:
    return re.findall(r"\b[a-z]\b", expr)


def _canonicalize_variables(expr: str) -> str:
    mapping: dict[str, str] = {}
    alphabet = iter("xyzuvwabcdefghijklmnopqrst")
    for var in _variables(expr):
        mapping.setdefault(var, next(alphabet, var))
    result = expr
    for old, new in mapping.items():
        result = re.sub(rf"\b{re.escape(old)}\b", new, result)
    return result


def _dedupe_stages(stages: Sequence[CurriculumStage] | Any) -> list[CurriculumStage]:
    result: list[CurriculumStage] = []
    seen: set[tuple[Any, ...]] = set()
    for stage in stages:
        signature = (stage.kind.value, stage.claim_id, stage.source, stage.target, stage.raw, stage.title, stage.repair_plan_id, stage.proof_digestion_trace_id)
        if signature not in seen:
            result.append(stage)
            seen.add(signature)
    return result


def _dedupe_by_id(items: Sequence[Any] | Any) -> list[Any]:
    result = []
    seen = set()
    for item in items:
        if item is None:
            continue
        item_id = getattr(item, "output_id", None) or getattr(item, "candidate_id", None) or json.dumps(item.to_dict(), sort_keys=True)
        if item_id not in seen:
            result.append(item)
            seen.add(item_id)
    return result


def _dedupe_dicts(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        encoded = json.dumps(dict(row), sort_keys=True, separators=(",", ":"))
        if encoded not in seen:
            result.append(dict(row))
            seen.add(encoded)
    return result


def _route_hint(kind: CurriculumStageKind) -> str:
    if kind == CurriculumStageKind.COUNTERMODEL_TASK:
        return "ROOT_CONSTRUCTOR"
    if kind == CurriculumStageKind.PROJECTION_TASK:
        return "PROJECTION"
    if kind == CurriculumStageKind.PROOF_TASK:
        return "PROOF_VERIFICATION"
    return "RESIDUAL_ONLY"


def _advisory_output(output: ContinuationActionOutput) -> ContinuationActionOutput:
    data = output.to_dict()
    data["terminal_form"] = None
    data["certificate_id"] = None
    data["verifier_boundary_crossed"] = False
    data["advisory"] = True
    data["metadata"] = {
        **dict(data.get("metadata", {})),
        "advisory_only": True,
        "curriculum_output_not_truth": True,
    }
    return ContinuationActionOutput.from_dict(data)


def _enum_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value.value if hasattr(value, "value") else value)


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_terminal(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    return TerminalForm(str(value))

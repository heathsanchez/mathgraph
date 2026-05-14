"""Unified verification episode orchestration for MathGraph M1-M4 traces."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentBiography, AgentExperience, AgentProfile, score_route_htilt_lite
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id
from mathgraph.proof_verification import (
    ProofArtifact,
    ProofVerificationTrace,
    ProofVerifierKind,
    make_lean_skeleton,
    proof_verification_trace_to_agent_experiences,
    run_proof_verification_pipeline,
)
from mathgraph.projection import (
    ProjectionTrace,
    projection_trace_to_agent_experiences,
    run_projection_engine,
)
from mathgraph.root_constructors import (
    RootConstructorTrace,
    RootSignal,
    root_constructor_trace_to_agent_experiences,
    run_root_aware_constructors,
)


class VerificationEpisodeStatus(str, Enum):
    EMPTY = "EMPTY"
    PLANNED = "PLANNED"
    KNOWN_SKIP = "KNOWN_SKIP"
    PROJECTION_ONLY = "PROJECTION_ONLY"
    CONSTRUCTOR_ATTEMPTED = "CONSTRUCTOR_ATTEMPTED"
    PROOF_ATTEMPTED = "PROOF_ATTEMPTED"
    TERMINAL_VERIFIED_PROOF = "TERMINAL_VERIFIED_PROOF"
    TERMINAL_FINITE_COUNTERMODEL = "TERMINAL_FINITE_COUNTERMODEL"
    TERMINAL_NAMED_OBSTRUCTION = "TERMINAL_NAMED_OBSTRUCTION"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    ALIGNMENT_FAILED = "ALIGNMENT_FAILED"


class VerificationRouteKind(str, Enum):
    LAWBOOK_LOOKUP = "LAWBOOK_LOOKUP"
    PROJECTION = "PROJECTION"
    ROOT_CONSTRUCTOR = "ROOT_CONSTRUCTOR"
    PROOF_VERIFICATION = "PROOF_VERIFICATION"
    BOTH_SIDES = "BOTH_SIDES"
    RESIDUAL_ONLY = "RESIDUAL_ONLY"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class VerificationEpisodeInput:
    claim_id: str | None = None
    source: str | None = None
    target: str | None = None
    source_idx: int | None = None
    target_idx: int | None = None
    route_hint: VerificationRouteKind | None = None
    agent_id: str | None = None
    episode_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "route_hint": self.route_hint.value if self.route_hint else None,
            "agent_id": self.agent_id,
            "episode_id": self.episode_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerificationEpisodeInput":
        return cls(
            claim_id=_optional_str(data.get("claim_id")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            route_hint=_optional_route(data.get("route_hint")),
            agent_id=_optional_str(data.get("agent_id")),
            episode_id=_optional_str(data.get("episode_id")),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "VerificationEpisodeInput":
        return cls.from_dict(json.loads(text))


@dataclass
class VerificationEpisodeRouteDecision:
    decision_id: str
    route_kind: VerificationRouteKind
    reason: str
    htilt_score: float = 0.0
    advisory: bool = True
    selected: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "route_kind": self.route_kind.value,
            "reason": self.reason,
            "htilt_score": self.htilt_score,
            "advisory": self.advisory,
            "selected": self.selected,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerificationEpisodeRouteDecision":
        return cls(
            decision_id=str(data["decision_id"]),
            route_kind=VerificationRouteKind(str(data["route_kind"])),
            reason=str(data["reason"]),
            htilt_score=float(data.get("htilt_score", 0.0) or 0.0),
            advisory=bool(data.get("advisory", True)),
            selected=bool(data.get("selected", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class VerificationEpisodeTrace:
    episode_id: str
    input: VerificationEpisodeInput
    status: VerificationEpisodeStatus
    route_decisions: list[VerificationEpisodeRouteDecision] = field(default_factory=list)
    projection_trace: ProjectionTrace | None = None
    root_constructor_trace: RootConstructorTrace | None = None
    proof_verification_trace: ProofVerificationTrace | None = None
    alchemical_trace: AlchemicalTrace | None = None
    agent_experiences: list[AgentExperience] = field(default_factory=list)
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed

    def is_advisory(self) -> bool:
        return not self.is_terminal()

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "input": self.input.to_dict(),
            "status": self.status.value,
            "route_decisions": [decision.to_dict() for decision in self.route_decisions],
            "projection_trace": self.projection_trace.to_dict() if self.projection_trace else None,
            "root_constructor_trace": self.root_constructor_trace.to_dict() if self.root_constructor_trace else None,
            "proof_verification_trace": self.proof_verification_trace.to_dict() if self.proof_verification_trace else None,
            "alchemical_trace": self.alchemical_trace.to_dict() if self.alchemical_trace else None,
            "agent_experiences": [experience.to_dict() for experience in self.agent_experiences],
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "created_at": self.created_at,
            "summary": dict(self.summary),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerificationEpisodeTrace":
        return cls(
            episode_id=str(data["episode_id"]),
            input=VerificationEpisodeInput.from_dict(dict(data["input"])),
            status=VerificationEpisodeStatus(str(data["status"])),
            route_decisions=[
                VerificationEpisodeRouteDecision.from_dict(item) for item in data.get("route_decisions", [])
            ],
            projection_trace=ProjectionTrace.from_dict(data["projection_trace"]) if data.get("projection_trace") else None,
            root_constructor_trace=RootConstructorTrace.from_dict(data["root_constructor_trace"]) if data.get("root_constructor_trace") else None,
            proof_verification_trace=ProofVerificationTrace.from_dict(data["proof_verification_trace"]) if data.get("proof_verification_trace") else None,
            alchemical_trace=AlchemicalTrace.from_dict(data["alchemical_trace"]) if data.get("alchemical_trace") else None,
            agent_experiences=[AgentExperience.from_dict(item) for item in data.get("agent_experiences", [])],
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "VerificationEpisodeTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "VerificationEpisodeTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["VerificationEpisodeTrace"]:
        if not Path(path).exists():
            return []
        traces: list[VerificationEpisodeTrace] = []
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    traces.append(cls.from_json(line))
        return traces


def choose_episode_routes(
    episode_input: VerificationEpisodeInput,
    *,
    agent: AgentProfile | AgentBiography | None = None,
    lawbook_entries: Sequence[Mapping[str, Any]] = (),
    root_signals: Sequence[RootSignal] = (),
    proof_artifacts: Sequence[ProofArtifact] = (),
    route_hint: VerificationRouteKind | None = None,
) -> list[VerificationEpisodeRouteDecision]:
    route_hint = route_hint or episode_input.route_hint
    ordered: list[tuple[VerificationRouteKind, str]] = []
    if route_hint is not None:
        ordered.append((route_hint, "explicit route hint"))
    if lawbook_entries:
        ordered.append((VerificationRouteKind.LAWBOOK_LOOKUP, "lawbook entries supplied"))
        ordered.append((VerificationRouteKind.PROJECTION, "lawbook projection pressure available"))
    if root_signals or episode_input.source or episode_input.target:
        ordered.append((VerificationRouteKind.ROOT_CONSTRUCTOR, "root/residual FALSE-side pressure available"))
    if proof_artifacts or episode_input.source or episode_input.target:
        ordered.append((VerificationRouteKind.PROOF_VERIFICATION, "TRUE-side proof route available"))
    if not ordered:
        ordered.append((VerificationRouteKind.ADVISORY_ONLY, "empty episode has advisory-only route"))
        ordered.append((VerificationRouteKind.RESIDUAL_ONLY, "no verifier-bound work selected"))

    decisions: list[VerificationEpisodeRouteDecision] = []
    seen: set[VerificationRouteKind] = set()
    for route_kind, reason in _ordered_unique(ordered):
        if route_kind in seen:
            continue
        seen.add(route_kind)
        score = score_route_htilt_lite(route_kind.value.lower(), agent=agent).final_score if agent else 0.0
        payload = {"input": episode_input.to_dict(), "route_kind": route_kind.value, "reason": reason, "score": score}
        decisions.append(
            VerificationEpisodeRouteDecision(
                decision_id=content_id("episode_route", payload, n=24),
                route_kind=route_kind,
                reason=reason,
                htilt_score=score,
                advisory=True,
                selected=True,
                metadata={"advisory_only": True, "route_is_not_truth": True},
            )
        )
    return decisions


def run_verification_episode(
    *,
    episode_input: VerificationEpisodeInput,
    lawbook_entries: Sequence[Mapping[str, Any]] = (),
    residual_pairs: Sequence[Mapping[str, Any]] = (),
    root_signals: Sequence[RootSignal] = (),
    proof_artifacts: Sequence[ProofArtifact] = (),
    agent: AgentProfile | AgentBiography | None = None,
    max_projection_candidates: int | None = None,
    max_constructor_plans: int | None = None,
    max_constructor_attempts: int | None = None,
    constructor_dry_run: bool = True,
    proof_verifier_kind: ProofVerifierKind = ProofVerifierKind.NONE,
    proof_command: Sequence[str] | None = None,
    proof_timeout_seconds: float = 10.0,
    allow_mock_verifier: bool = False,
    run_alignment: bool = True,
) -> VerificationEpisodeTrace:
    episode_id = episode_input.episode_id or make_verification_episode_id(episode_input.to_dict())
    if episode_input.episode_id != episode_id:
        episode_input = VerificationEpisodeInput.from_dict({**episode_input.to_dict(), "episode_id": episode_id})
    decisions = choose_episode_routes(
        episode_input,
        agent=agent,
        lawbook_entries=lawbook_entries,
        root_signals=root_signals,
        proof_artifacts=proof_artifacts,
    )
    selected = {decision.route_kind for decision in decisions if decision.selected}
    pair_rows = _episode_pairs(episode_input, residual_pairs)

    projection_trace = None
    if lawbook_entries or residual_pairs or VerificationRouteKind.PROJECTION in selected or VerificationRouteKind.LAWBOOK_LOOKUP in selected:
        projection_trace = run_projection_engine(
            lawbook_entries=lawbook_entries,
            residual_pairs=pair_rows,
            agent_id=episode_input.agent_id,
            episode_id=episode_id,
            max_candidates=max_projection_candidates,
        )

    root_trace = None
    if pair_rows or root_signals or VerificationRouteKind.ROOT_CONSTRUCTOR in selected:
        root_trace = run_root_aware_constructors(
            root_signals=root_signals,
            residual_pairs=pair_rows,
            projection_traces=[projection_trace] if projection_trace else (),
            agent_id=episode_input.agent_id,
            episode_id=episode_id,
            max_plans=max_constructor_plans,
            max_attempts=max_constructor_attempts,
            dry_run=constructor_dry_run,
        )

    proof_inputs = list(proof_artifacts)
    if not proof_inputs and (episode_input.source or episode_input.target) and VerificationRouteKind.PROOF_VERIFICATION in selected:
        proof_inputs.append(
            make_lean_skeleton(
                claim_id=episode_input.claim_id,
                source=episode_input.source,
                target=episode_input.target,
                theorem_name=None,
            )
        )
    proof_trace = None
    if proof_inputs or VerificationRouteKind.PROOF_VERIFICATION in selected:
        proof_trace = run_proof_verification_pipeline(
            artifacts=proof_inputs,
            agent_id=episode_input.agent_id,
            episode_id=episode_id,
            verifier_kind=proof_verifier_kind,
            command=proof_command,
            timeout_seconds=proof_timeout_seconds,
            allow_mock_verifier=allow_mock_verifier,
        )

    terminal_form, certificate_id, boundary = _terminal_from_subtraces(projection_trace, root_trace, proof_trace)
    status = _episode_status(terminal_form, projection_trace, root_trace, proof_trace, decisions)
    alchemical = combine_episode_alchemical_trace(
        episode_id=episode_id,
        agent_id=episode_input.agent_id,
        projection_trace=projection_trace,
        root_constructor_trace=root_trace,
        proof_verification_trace=proof_trace,
        terminal_form=terminal_form,
        certificate_id=certificate_id,
        verifier_boundary_crossed=boundary,
    )
    experiences: list[AgentExperience] = []
    if projection_trace:
        experiences.extend(projection_trace_to_agent_experiences(projection_trace))
    if root_trace:
        experiences.extend(root_constructor_trace_to_agent_experiences(root_trace))
    if proof_trace:
        experiences.extend(proof_verification_trace_to_agent_experiences(proof_trace))

    summary = _summary(
        projection_trace=projection_trace,
        root_constructor_trace=root_trace,
        proof_verification_trace=proof_trace,
        route_decisions=decisions,
        agent_experiences=experiences,
    )
    trace = VerificationEpisodeTrace(
        episode_id=episode_id,
        input=episode_input,
        status=status,
        route_decisions=decisions,
        projection_trace=projection_trace,
        root_constructor_trace=root_trace,
        proof_verification_trace=proof_trace,
        alchemical_trace=alchemical,
        agent_experiences=experiences,
        terminal_form=terminal_form,
        certificate_id=certificate_id,
        verifier_boundary_crossed=boundary,
        summary=summary,
    )
    if run_alignment:
        from mathgraph.roadmap_alignment import check_roadmap_alignment

        report = check_roadmap_alignment(
            alchemical_traces=[alchemical],
            agent_experiences=experiences,
            projection_traces=[projection_trace] if projection_trace else (),
            root_constructor_traces=[root_trace] if root_trace else (),
            proof_verification_traces=[proof_trace] if proof_trace else (),
            verification_episode_traces=[trace],
            summary={"metadata": {"verification_episode": "advisory routes are not truth"}},
        )
        trace.summary.update(
            {
                "alignment_critical_count": report.critical_count(),
                "alignment_warning_count": report.warning_count(),
                "alignment_info_count": report.info_count(),
                "alignment_is_aligned": report.is_aligned(),
            }
        )
        if report.critical_count() > 0:
            trace.status = VerificationEpisodeStatus.ALIGNMENT_FAILED
    return trace


def combine_episode_alchemical_trace(
    *,
    episode_id: str,
    agent_id: str | None,
    projection_trace: ProjectionTrace | None = None,
    root_constructor_trace: RootConstructorTrace | None = None,
    proof_verification_trace: ProofVerificationTrace | None = None,
    terminal_form: TerminalForm | None = None,
    certificate_id: str | None = None,
    verifier_boundary_crossed: bool = False,
) -> AlchemicalTrace:
    trace = AlchemicalTrace(
        trace_id=make_alchemical_trace_id("verification_episode", episode_id),
        claim_id=episode_id,
        agent_id=agent_id,
        episode_id=episode_id,
    )
    trace.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    if projection_trace is not None:
        trace.add_step(
            phase=AlchemicalPhase.MULTIPLICATION,
            status=AlchemicalStatus.SUCCEEDED if projection_trace.results else AlchemicalStatus.ADVISORY_ONLY,
            residual_delta=projection_trace.residual_delta_total(),
            compression_gain=projection_trace.compression_gain_total(),
        )
        trace.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.SUCCEEDED if projection_trace.results else AlchemicalStatus.ADVISORY_ONLY)
    if root_constructor_trace is not None:
        if root_constructor_trace.plans:
            trace.add_step(phase=AlchemicalPhase.CALCINATION, status=AlchemicalStatus.SUCCEEDED)
            trace.add_step(phase=AlchemicalPhase.SOLUTION, status=AlchemicalStatus.SUCCEEDED)
        if root_constructor_trace.attempts:
            trace.add_step(
                phase=AlchemicalPhase.DESCENSION,
                status=AlchemicalStatus.SUCCEEDED,
                residual_delta=root_constructor_trace.residual_delta_total(),
                compression_gain=root_constructor_trace.compression_gain_total(),
            )
    if proof_verification_trace is not None:
        if proof_verification_trace.artifacts:
            trace.add_step(phase=AlchemicalPhase.SUBLIMATION, status=AlchemicalStatus.ADVISORY_ONLY)
            trace.add_step(phase=AlchemicalPhase.DESCENSION, status=AlchemicalStatus.ADVISORY_ONLY)
        if proof_verification_trace.results:
            trace.add_step(
                phase=AlchemicalPhase.DISTILLATION,
                status=AlchemicalStatus.SUCCEEDED,
                residual_delta=proof_verification_trace.residual_delta_total(),
                compression_gain=proof_verification_trace.compression_gain_total(),
            )
    if terminal_form and certificate_id and verifier_boundary_crossed:
        trace.terminal_form = terminal_form
        trace.promoted_certificate_id = certificate_id
        trace.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary="EPISODE_SUBTRACE_BOUNDARY")
        trace.add_step(phase=AlchemicalPhase.CERATION, status=AlchemicalStatus.SUCCEEDED)
    if _total_gain(projection_trace, root_constructor_trace, proof_verification_trace) > 0:
        trace.add_step(phase=AlchemicalPhase.PERFECTION, status=AlchemicalStatus.SUCCEEDED)
    return trace


def make_verification_episode_id(payload: Mapping[str, Any]) -> str:
    return content_id("verification_episode", payload, n=24)


def _terminal_from_subtraces(
    projection_trace: ProjectionTrace | None,
    root_trace: RootConstructorTrace | None,
    proof_trace: ProofVerificationTrace | None,
) -> tuple[TerminalForm | None, str | None, bool]:
    if proof_trace:
        for result in proof_trace.results:
            if result.is_terminal() and result.terminal_form == TerminalForm.VERIFIED_PROOF:
                return result.terminal_form, result.certificate_id, True
    if root_trace:
        for attempt in root_trace.attempts:
            if attempt.is_terminal() and attempt.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
                return attempt.terminal_form, attempt.certificate_id, True
            if attempt.is_terminal() and attempt.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
                return attempt.terminal_form, attempt.certificate_id, True
    if projection_trace:
        for result in projection_trace.results:
            if result.is_terminal():
                return result.terminal_form, result.derived_certificate_id or result.lawbook_entry_id, True
    return None, None, False


def _episode_status(
    terminal_form: TerminalForm | None,
    projection_trace: ProjectionTrace | None,
    root_trace: RootConstructorTrace | None,
    proof_trace: ProofVerificationTrace | None,
    decisions: Sequence[VerificationEpisodeRouteDecision],
) -> VerificationEpisodeStatus:
    if terminal_form == TerminalForm.VERIFIED_PROOF:
        return VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF
    if terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return VerificationEpisodeStatus.TERMINAL_FINITE_COUNTERMODEL
    if terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        return VerificationEpisodeStatus.TERMINAL_NAMED_OBSTRUCTION
    if projection_trace and any(result.is_terminal() for result in projection_trace.results):
        return VerificationEpisodeStatus.KNOWN_SKIP
    if root_trace and root_trace.attempts:
        return VerificationEpisodeStatus.CONSTRUCTOR_ATTEMPTED if any(not attempt.is_residual() for attempt in root_trace.attempts) else VerificationEpisodeStatus.RESIDUAL
    if proof_trace and proof_trace.results:
        return VerificationEpisodeStatus.PROOF_ATTEMPTED
    if projection_trace and projection_trace.results:
        return VerificationEpisodeStatus.PROJECTION_ONLY
    selected = {decision.route_kind for decision in decisions if decision.selected}
    if selected and selected <= {VerificationRouteKind.ADVISORY_ONLY, VerificationRouteKind.RESIDUAL_ONLY}:
        return VerificationEpisodeStatus.ADVISORY_ONLY
    if decisions and any(decision.route_kind != VerificationRouteKind.ADVISORY_ONLY for decision in decisions):
        return VerificationEpisodeStatus.PLANNED
    return VerificationEpisodeStatus.EMPTY


def _summary(
    *,
    projection_trace: ProjectionTrace | None,
    root_constructor_trace: RootConstructorTrace | None,
    proof_verification_trace: ProofVerificationTrace | None,
    route_decisions: Sequence[VerificationEpisodeRouteDecision],
    agent_experiences: Sequence[AgentExperience],
) -> dict[str, Any]:
    return {
        "route_decisions": len(route_decisions),
        "projection_ran": projection_trace is not None,
        "root_constructor_ran": root_constructor_trace is not None,
        "proof_verification_ran": proof_verification_trace is not None,
        "agent_experience_count": len(agent_experiences),
        "projection_gain_total": _projection_gain(projection_trace, root_constructor_trace, proof_verification_trace),
        "residual_delta_total": _residual_delta(projection_trace, root_constructor_trace, proof_verification_trace),
        "terminal_subtrace_count": sum(
            count
            for count in [
                projection_trace.terminal_count() if projection_trace else 0,
                root_constructor_trace.terminal_count() if root_constructor_trace else 0,
                proof_verification_trace.terminal_count() if proof_verification_trace else 0,
            ]
        ),
    }


def _episode_pairs(episode_input: VerificationEpisodeInput, residual_pairs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(pair) for pair in residual_pairs]
    if not rows and (episode_input.source or episode_input.target or episode_input.source_idx is not None or episode_input.target_idx is not None):
        rows.append(
            {
                "claim_id": episode_input.claim_id,
                "source": episode_input.source,
                "target": episode_input.target,
                "source_idx": episode_input.source_idx,
                "target_idx": episode_input.target_idx,
            }
        )
    return rows


def _ordered_unique(items: Sequence[tuple[VerificationRouteKind, str]]) -> list[tuple[VerificationRouteKind, str]]:
    priority = {
        VerificationRouteKind.LAWBOOK_LOOKUP: 0,
        VerificationRouteKind.PROJECTION: 1,
        VerificationRouteKind.ROOT_CONSTRUCTOR: 2,
        VerificationRouteKind.PROOF_VERIFICATION: 3,
        VerificationRouteKind.RESIDUAL_ONLY: 4,
        VerificationRouteKind.ADVISORY_ONLY: 5,
        VerificationRouteKind.BOTH_SIDES: 2,
    }
    seen: set[VerificationRouteKind] = set()
    unique = []
    for item in items:
        if item[0] not in seen:
            seen.add(item[0])
            unique.append(item)
    return sorted(unique, key=lambda item: (priority.get(item[0], 99), item[0].value))


def _projection_gain(*traces: Any) -> float:
    return sum(trace.projection_gain_total() for trace in traces if trace is not None)


def _residual_delta(*traces: Any) -> int:
    return sum(trace.residual_delta_total() for trace in traces if trace is not None)


def _total_gain(*traces: Any) -> float:
    return _projection_gain(*traces) + sum(trace.compression_gain_total() for trace in traces if trace is not None) + abs(_residual_delta(*traces))


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_route(value: Any) -> VerificationRouteKind | None:
    if value in (None, ""):
        return None
    if isinstance(value, VerificationRouteKind):
        return value
    return VerificationRouteKind(str(value))


def _optional_terminal_form(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    if isinstance(value, TerminalForm):
        return value
    return TerminalForm(str(value))

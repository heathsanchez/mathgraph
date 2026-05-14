"""Root-aware constructor planning and safe attempt traces.

Root signals, obstruction surfaces, residual basins, and projection pressure are
advisory inputs. Constructor attempts may find candidate tables, but only an
importer/revalidator boundary can promote a candidate into a terminal finite
countermodel certificate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace, make_alchemical_trace_id
from mathgraph.certificates import TerminalForm
from mathgraph.finite_countermodel_executor import run_finite_countermodel_tasks
from mathgraph.hashing import content_id
from mathgraph.projection import (
    ProjectionCandidate,
    ProjectionRuleKind,
    ProjectionStatus,
    ProjectionTrace,
    make_projection_candidate_id,
)


class RootConstructorStatus(str, Enum):
    PLANNED = "PLANNED"
    ATTEMPTED = "ATTEMPTED"
    CANDIDATE_TABLE_FOUND = "CANDIDATE_TABLE_FOUND"
    IMPORTER_VERIFIED = "IMPORTER_VERIFIED"
    IMPORTER_REJECTED = "IMPORTER_REJECTED"
    SEARCH_MISS = "SEARCH_MISS"
    RESIDUAL = "RESIDUAL"
    OBSTRUCTION_NAMED = "OBSTRUCTION_NAMED"
    ADVISORY_ONLY = "ADVISORY_ONLY"


class RootConstructorKind(str, Enum):
    EXACT_REPLAY = "EXACT_REPLAY"
    TABLE_REPLAY = "TABLE_REPLAY"
    PROJECTION_GUIDED = "PROJECTION_GUIDED"
    OBSTRUCTION_GUIDED = "OBSTRUCTION_GUIDED"
    BASIN_TEMPLATE = "BASIN_TEMPLATE"
    QUOTIENT_GEOMETRY = "QUOTIENT_GEOMETRY"
    DIAGONAL_PRESSURE = "DIAGONAL_PRESSURE"
    ROLE_PERMUTATION = "ROLE_PERMUTATION"
    TAILDROP = "TAILDROP"
    SAME_SKELETON_COLLAPSE = "SAME_SKELETON_COLLAPSE"
    UNKNOWN = "UNKNOWN"


@dataclass
class RootSignal:
    root_id: str
    name: str | None = None
    basin: str | None = None
    micro_basin: str | None = None
    obstruction_id: str | None = None
    reason_id: str | None = None
    support: int = 0
    confidence: float = 0.0
    advisory: bool = True
    features: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_id": self.root_id,
            "name": self.name,
            "basin": self.basin,
            "micro_basin": self.micro_basin,
            "obstruction_id": self.obstruction_id,
            "reason_id": self.reason_id,
            "support": self.support,
            "confidence": self.confidence,
            "advisory": self.advisory,
            "features": dict(self.features),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RootSignal":
        features = dict(data.get("features") or data.get("detector_evidence") or {})
        metadata = dict(data.get("metadata") or {})
        return cls(
            root_id=str(
                data.get("root_id")
                or data.get("root_node_id")
                or data.get("root_label")
                or data.get("canonical_name")
                or content_id("root_signal", dict(data), n=16)
            ),
            name=_optional_str(data.get("name") or data.get("root_label") or data.get("canonical_name")),
            basin=_optional_str(data.get("basin") or data.get("source_target_basin")),
            micro_basin=_optional_str(data.get("micro_basin") or data.get("forced_transition")),
            obstruction_id=_optional_str(data.get("obstruction_id")),
            reason_id=_optional_str(data.get("reason_id") or data.get("reason_node_id")),
            support=int(data.get("support", data.get("support_count", 0)) or 0),
            confidence=float(data.get("confidence", data.get("detector_score", data.get("load_bearing_score", 0.0))) or 0.0),
            advisory=bool(data.get("advisory", data.get("advisory_only", True))),
            features=features,
            metadata=metadata,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "RootSignal":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "RootSignal":
        return cls.from_json(line.strip())


@dataclass
class ConstructorPlan:
    plan_id: str
    root_id: str | None
    source: str | None
    target: str | None
    source_idx: int | None = None
    target_idx: int | None = None
    kind: RootConstructorKind = RootConstructorKind.UNKNOWN
    route: str | None = None
    max_order: int = 3
    expected_gain: float = 0.0
    advisory: bool = True
    reason: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "root_id": self.root_id,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "kind": self.kind.value,
            "route": self.route,
            "max_order": self.max_order,
            "expected_gain": self.expected_gain,
            "advisory": self.advisory,
            "reason": self.reason,
            "constraints": dict(self.constraints),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConstructorPlan":
        return cls(
            plan_id=str(data["plan_id"]),
            root_id=_optional_str(data.get("root_id")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            kind=RootConstructorKind(str(data.get("kind", RootConstructorKind.UNKNOWN.value))),
            route=_optional_str(data.get("route")),
            max_order=int(data.get("max_order", 3) or 3),
            expected_gain=float(data.get("expected_gain", 0.0) or 0.0),
            advisory=bool(data.get("advisory", True)),
            reason=_optional_str(data.get("reason")),
            constraints=dict(data.get("constraints", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ConstructorPlan":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ConstructorPlan":
        return cls.from_json(line.strip())


@dataclass
class ConstructorAttempt:
    attempt_id: str
    plan_id: str
    status: RootConstructorStatus
    candidate_artifact_id: str | None = None
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    table_order: int | None = None
    witness: dict[str, Any] = field(default_factory=dict)
    cost_units: float = 0.0
    residual_delta: int = 0
    compression_gain: float = 0.0
    projection_gain: float = 0.0
    failure_reason: str | None = None
    obstruction_name: str | None = None
    advisory_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        if (
            self.terminal_form == TerminalForm.FINITE_COUNTERMODEL
            and self.certificate_id
            and self.verifier_boundary_crossed
            and self.status == RootConstructorStatus.IMPORTER_VERIFIED
        ):
            return True
        return (
            self.terminal_form == TerminalForm.NAMED_OBSTRUCTION
            and self.certificate_id
            and self.verifier_boundary_crossed
            and self.status == RootConstructorStatus.OBSTRUCTION_NAMED
            and bool(self.metadata.get("naming_boundary"))
        )

    def is_candidate_only(self) -> bool:
        return self.status == RootConstructorStatus.CANDIDATE_TABLE_FOUND and not self.is_terminal()

    def is_residual(self) -> bool:
        return self.status in {RootConstructorStatus.SEARCH_MISS, RootConstructorStatus.RESIDUAL}

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "candidate_artifact_id": self.candidate_artifact_id,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "table_order": self.table_order,
            "witness": dict(self.witness),
            "cost_units": self.cost_units,
            "residual_delta": self.residual_delta,
            "compression_gain": self.compression_gain,
            "projection_gain": self.projection_gain,
            "failure_reason": self.failure_reason,
            "obstruction_name": self.obstruction_name,
            "advisory_notes": list(self.advisory_notes),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConstructorAttempt":
        return cls(
            attempt_id=str(data["attempt_id"]),
            plan_id=str(data["plan_id"]),
            status=RootConstructorStatus(str(data["status"])),
            candidate_artifact_id=_optional_str(data.get("candidate_artifact_id")),
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            table_order=_optional_int(data.get("table_order")),
            witness=dict(data.get("witness", {})),
            cost_units=float(data.get("cost_units", 0.0) or 0.0),
            residual_delta=int(data.get("residual_delta", 0) or 0),
            compression_gain=float(data.get("compression_gain", 0.0) or 0.0),
            projection_gain=float(data.get("projection_gain", 0.0) or 0.0),
            failure_reason=_optional_str(data.get("failure_reason")),
            obstruction_name=_optional_str(data.get("obstruction_name")),
            advisory_notes=tuple(str(x) for x in data.get("advisory_notes", ())),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ConstructorAttempt":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "ConstructorAttempt":
        return cls.from_json(line.strip())


@dataclass
class RootConstructorTrace:
    trace_id: str
    episode_id: str | None
    agent_id: str | None
    root_signals: list[RootSignal] = field(default_factory=list)
    plans: list[ConstructorPlan] = field(default_factory=list)
    attempts: list[ConstructorAttempt] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)

    def terminal_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.is_terminal())

    def candidate_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.status == RootConstructorStatus.CANDIDATE_TABLE_FOUND)

    def residual_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.status == RootConstructorStatus.RESIDUAL)

    def search_miss_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.status == RootConstructorStatus.SEARCH_MISS)

    def residual_delta_total(self) -> int:
        return sum(attempt.residual_delta for attempt in self.attempts)

    def compression_gain_total(self) -> float:
        return sum(attempt.compression_gain for attempt in self.attempts)

    def projection_gain_total(self) -> float:
        return sum(attempt.projection_gain for attempt in self.attempts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "episode_id": self.episode_id,
            "agent_id": self.agent_id,
            "root_signals": [signal.to_dict() for signal in self.root_signals],
            "plans": [plan.to_dict() for plan in self.plans],
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "created_at": self.created_at,
            "summary": dict(self.summary),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RootConstructorTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            episode_id=_optional_str(data.get("episode_id")),
            agent_id=_optional_str(data.get("agent_id")),
            root_signals=[RootSignal.from_dict(item) for item in data.get("root_signals", [])],
            plans=[ConstructorPlan.from_dict(item) for item in data.get("plans", [])],
            attempts=[ConstructorAttempt.from_dict(item) for item in data.get("attempts", [])],
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "RootConstructorTrace":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "RootConstructorTrace":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["RootConstructorTrace"]:
        if not Path(path).exists():
            return []
        traces: list[RootConstructorTrace] = []
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    traces.append(cls.from_json(line))
        return traces


def load_root_signals_json(path: str | Path) -> list[RootSignal]:
    return [RootSignal.from_dict(item) for item in _read_records(path)]


def load_root_signals_jsonl(path: str | Path) -> list[RootSignal]:
    return [RootSignal.from_dict(item) for item in _read_jsonl(path)]


def load_constructor_plans_jsonl(path: str | Path) -> list[ConstructorPlan]:
    return [ConstructorPlan.from_dict(item) for item in _read_jsonl(path)]


def compile_constructor_plans(
    *,
    root_signals: Sequence[RootSignal] = (),
    residual_pairs: Sequence[Mapping[str, Any]] = (),
    projection_traces: Sequence[ProjectionTrace] = (),
    max_order: int = 3,
    max_plans: int | None = None,
) -> list[ConstructorPlan]:
    signals = list(root_signals)
    residuals = [dict(pair) for pair in residual_pairs]
    projection_hints = _projection_hints(projection_traces)
    if not residuals:
        residuals = [
            {
                "source": hint.get("source"),
                "target": hint.get("target"),
                "source_idx": hint.get("source_idx"),
                "target_idx": hint.get("target_idx"),
                "projection_hint": hint,
            }
            for hint in projection_hints
            if hint.get("source") or hint.get("target")
        ]

    plans: list[ConstructorPlan] = []
    for pair in residuals:
        matching = _match_signals(pair, signals)
        if not matching:
            matching = [None]
        for signal in matching:
            hint = _best_projection_hint(pair, projection_hints)
            kind = _choose_kind(signal, hint)
            plan = _make_plan(pair, signal, hint, kind, max_order)
            plans.append(plan)
    plans.sort(key=_plan_rank)
    if max_plans is not None:
        plans = plans[:max_plans]
    return plans


def run_constructor_attempts(
    *,
    plans: Sequence[ConstructorPlan],
    max_attempts: int | None = None,
    dry_run: bool = False,
) -> list[ConstructorAttempt]:
    selected = list(plans)[:max_attempts] if max_attempts is not None else list(plans)
    if dry_run:
        return [_dry_run_attempt(plan) for plan in selected]
    return [_bounded_attempt(plan) for plan in selected]


def run_root_aware_constructors(
    *,
    root_signals: Sequence[RootSignal] = (),
    residual_pairs: Sequence[Mapping[str, Any]] = (),
    projection_traces: Sequence[ProjectionTrace] = (),
    agent_id: str | None = None,
    episode_id: str | None = None,
    max_order: int = 3,
    max_plans: int | None = None,
    max_attempts: int | None = None,
    dry_run: bool = False,
) -> RootConstructorTrace:
    signals = list(root_signals)
    projections = list(projection_traces)
    plans = compile_constructor_plans(
        root_signals=signals,
        residual_pairs=residual_pairs,
        projection_traces=projections,
        max_order=max_order,
        max_plans=max_plans,
    )
    attempts = run_constructor_attempts(plans=plans, max_attempts=max_attempts, dry_run=dry_run)
    trace = RootConstructorTrace(
        trace_id=make_root_constructor_trace_id(episode_id, agent_id, [plan.to_dict() for plan in plans]),
        episode_id=episode_id,
        agent_id=agent_id,
        root_signals=signals,
        plans=plans,
        attempts=attempts,
    )
    trace.summary.update(_summary(trace, dry_run=dry_run, projection_traces=projections))
    return trace


def root_constructor_trace_to_alchemical_trace(trace: RootConstructorTrace) -> AlchemicalTrace:
    alchemical = AlchemicalTrace(
        trace_id=make_alchemical_trace_id("root_constructor", trace.trace_id),
        agent_id=trace.agent_id,
        episode_id=trace.episode_id,
    )
    alchemical.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.SUCCEEDED)
    alchemical.add_step(
        phase=AlchemicalPhase.CALCINATION,
        status=AlchemicalStatus.SUCCEEDED if trace.root_signals else AlchemicalStatus.ADVISORY_ONLY,
        advisory_notes=("root signals are advisory SAT/UNSAT boundary pressure",),
    )
    alchemical.add_step(
        phase=AlchemicalPhase.SOLUTION,
        status=AlchemicalStatus.SUCCEEDED if trace.plans else AlchemicalStatus.ADVISORY_ONLY,
        output_artifact_ids=tuple(plan.plan_id for plan in trace.plans),
    )
    alchemical.add_step(
        phase=AlchemicalPhase.DESCENSION,
        status=AlchemicalStatus.SUCCEEDED if trace.attempts else AlchemicalStatus.ADVISORY_ONLY,
        output_artifact_ids=tuple(attempt.attempt_id for attempt in trace.attempts),
        residual_delta=trace.residual_delta_total(),
        compression_gain=trace.compression_gain_total(),
    )
    alchemical.add_step(phase=AlchemicalPhase.DISTILLATION, status=AlchemicalStatus.ADVISORY_ONLY)
    if any(attempt.is_terminal() for attempt in trace.attempts):
        first = next(attempt for attempt in trace.attempts if attempt.is_terminal())
        alchemical.terminal_form = first.terminal_form
        alchemical.promoted_certificate_id = first.certificate_id
        alchemical.add_step(
            phase=AlchemicalPhase.FIXATION,
            status=AlchemicalStatus.PROMOTED_BY_VERIFIER,
            verifier_boundary="IMPORTER_REVALIDATED",
        )
    if any(attempt.status == RootConstructorStatus.OBSTRUCTION_NAMED for attempt in trace.attempts):
        alchemical.add_step(phase=AlchemicalPhase.COAGULATION, status=AlchemicalStatus.SUCCEEDED)
    if trace.summary.get("projection_influenced"):
        alchemical.add_step(
            phase=AlchemicalPhase.PROJECTION,
            status=AlchemicalStatus.SUCCEEDED,
            residual_delta=trace.residual_delta_total(),
            compression_gain=trace.compression_gain_total(),
        )
    return alchemical


def root_constructor_trace_to_agent_experiences(trace: RootConstructorTrace) -> list[AgentExperience]:
    agent_id = trace.agent_id or "root-constructor"
    experiences: list[AgentExperience] = []
    plans_by_id = {plan.plan_id: plan for plan in trace.plans}
    for attempt in trace.attempts:
        plan = plans_by_id.get(attempt.plan_id)
        experiences.append(
            AgentExperience(
                experience_id=content_id("root_constructor_exp", attempt.to_dict(), n=24),
                agent_id=agent_id,
                episode_id=trace.episode_id,
                claim_id=attempt.plan_id,
                route=plan.route if plan else "root_constructor",
                phase=AlchemicalPhase.DESCENSION.value,
                outcome=_experience_outcome(attempt),
                terminal_form=attempt.terminal_form if attempt.is_terminal() else None,
                certificate_id=attempt.certificate_id if attempt.is_terminal() else None,
                cost_units=attempt.cost_units,
                residual_delta=attempt.residual_delta,
                compression_gain=attempt.compression_gain,
                projection_gain=attempt.projection_gain,
                verifier_boundary_crossed=attempt.is_terminal(),
                scar_tags=_scar_tags(attempt),
                metadata={"constructor_attempt": attempt.to_dict(), "boundary_preserved": True},
            )
        )
    return experiences


def root_constructor_trace_to_projection_candidates(trace: RootConstructorTrace) -> list[ProjectionCandidate]:
    plans_by_id = {plan.plan_id: plan for plan in trace.plans}
    candidates: list[ProjectionCandidate] = []
    for attempt in trace.attempts:
        plan = plans_by_id.get(attempt.plan_id)
        source = plan.source if plan else None
        target = plan.target if plan else None
        if attempt.is_terminal():
            rule_kind = ProjectionRuleKind.EXACT_KNOWN
            confidence = 1.0
            advisory = False
            reason = "Importer-verified constructor result can seed lawbook projection."
        else:
            rule_kind = ProjectionRuleKind.CONSTRUCTOR_REPLAY
            confidence = 0.2
            advisory = True
            reason = "Constructor attempt produced advisory replay or obstruction pressure only."
        payload = {
            "attempt_id": attempt.attempt_id,
            "plan_id": attempt.plan_id,
            "source": source,
            "target": target,
            "rule_kind": rule_kind.value,
        }
        candidates.append(
            ProjectionCandidate(
                candidate_id=make_projection_candidate_id(payload),
                source_claim_id=attempt.plan_id,
                target_claim_id=None,
                source_idx=plan.source_idx if plan else None,
                target_idx=plan.target_idx if plan else None,
                source=source,
                target=target,
                rule_kind=rule_kind,
                originating_certificate_id=attempt.certificate_id if attempt.is_terminal() else None,
                confidence=confidence,
                advisory=advisory,
                reason=reason,
                metadata={"constructor_attempt": attempt.to_dict(), "status": ProjectionStatus.CANDIDATE.value},
            )
        )
    return candidates


def make_root_signal_id(payload: Mapping[str, Any]) -> str:
    return content_id("root_signal", payload, n=24)


def make_constructor_plan_id(payload: Mapping[str, Any]) -> str:
    return content_id("constructor_plan", payload, n=24)


def make_constructor_attempt_id(payload: Mapping[str, Any]) -> str:
    return content_id("constructor_attempt", payload, n=24)


def make_root_constructor_trace_id(*parts: Any) -> str:
    return content_id("root_constructor_trace", parts, n=24)


def _make_plan(
    pair: Mapping[str, Any],
    signal: RootSignal | None,
    hint: Mapping[str, Any] | None,
    kind: RootConstructorKind,
    max_order: int,
) -> ConstructorPlan:
    source = _optional_str(pair.get("source") or pair.get("equation1"))
    target = _optional_str(pair.get("target") or pair.get("equation2"))
    source_idx = _optional_int(pair.get("source_idx", pair.get("eq1_id")))
    target_idx = _optional_int(pair.get("target_idx", pair.get("eq2_id")))
    expected_gain = _expected_gain(signal, hint, pair)
    payload = {
        "root_id": signal.root_id if signal else None,
        "source": source,
        "target": target,
        "source_idx": source_idx,
        "target_idx": target_idx,
        "kind": kind.value,
        "max_order": max_order,
        "hint": dict(hint or {}),
    }
    return ConstructorPlan(
        plan_id=make_constructor_plan_id(payload),
        root_id=signal.root_id if signal else None,
        source=source,
        target=target,
        source_idx=source_idx,
        target_idx=target_idx,
        kind=kind,
        route=f"root_constructor:{kind.value.lower()}",
        max_order=max_order,
        expected_gain=expected_gain,
        advisory=True,
        reason="Root/residual/projection pressure compiled into a narrow constructor attempt.",
        constraints={"max_order": max_order},
        metadata={
            "root_signal": signal.to_dict() if signal else None,
            "projection_hint": dict(hint or {}),
            "advisory_only": True,
            "rank_score": _rank_score(signal, hint, expected_gain),
        },
    )


def _dry_run_attempt(plan: ConstructorPlan) -> ConstructorAttempt:
    return ConstructorAttempt(
        attempt_id=make_constructor_attempt_id({"plan_id": plan.plan_id, "dry_run": True}),
        plan_id=plan.plan_id,
        status=RootConstructorStatus.ADVISORY_ONLY,
        residual_delta=0,
        compression_gain=0.0,
        projection_gain=plan.expected_gain,
        advisory_notes=("dry-run only", "constructor plans are advisory", "no verifier boundary crossed"),
        metadata={"plan": plan.to_dict(), "dry_run": True, "advisory_only": True},
    )


def _bounded_attempt(plan: ConstructorPlan) -> ConstructorAttempt:
    if not plan.source or not plan.target:
        return _residual_attempt(plan, "plan lacks source or target")
    with TemporaryDirectory(prefix="root_constructor_") as tmp:
        queue_path = Path(tmp) / "queue.jsonl"
        out_path = Path(tmp) / "finite_results.jsonl"
        row = {
            "task_id": plan.plan_id,
            "source": plan.source,
            "target": plan.target,
            "source_idx": plan.source_idx,
            "target_idx": plan.target_idx,
            "route": plan.route or "root_constructor",
            "task_kind": "finite_countermodel_search",
        }
        _write_jsonl([row], queue_path)
        try:
            run = run_finite_countermodel_tasks(
                {
                    "task_queue_jsonl": str(queue_path),
                    "out_jsonl": str(out_path),
                    "max_tasks": 1,
                    "max_order": plan.max_order,
                    "random_tables_per_order": 0,
                    "exhaustive_order_limit": min(plan.max_order, 3),
                    "include_deterministic_tables": True,
                    "stop_after_first": True,
                }
            )
        except Exception as exc:
            return _residual_attempt(plan, f"constructor backend unavailable: {exc}")
    result = run.results[0] if run.results else {}
    status = str(result.get("status", ""))
    if status == "finite_countermodel_found":
        countermodel = dict(result.get("countermodel") or {})
        return ConstructorAttempt(
            attempt_id=make_constructor_attempt_id({"plan_id": plan.plan_id, "candidate": countermodel}),
            plan_id=plan.plan_id,
            status=RootConstructorStatus.CANDIDATE_TABLE_FOUND,
            candidate_artifact_id=content_id("candidate_table", countermodel, n=24),
            table_order=_optional_int(countermodel.get("order")),
            witness=dict(result.get("witness") or {}),
            cost_units=float(result.get("tables_tried", 0) or 0),
            residual_delta=-1,
            compression_gain=0.25,
            projection_gain=plan.expected_gain,
            advisory_notes=(
                "candidate finite table found",
                "not a certificate until importer/revalidator promotes it",
            ),
            metadata={"plan": plan.to_dict(), "finite_executor_result": result, "advisory_only": True},
        )
    if status in {"no_countermodel_found", "search_miss"}:
        return ConstructorAttempt(
            attempt_id=make_constructor_attempt_id({"plan_id": plan.plan_id, "search_miss": True}),
            plan_id=plan.plan_id,
            status=RootConstructorStatus.SEARCH_MISS,
            cost_units=float(result.get("tables_tried", 0) or 0),
            residual_delta=0,
            failure_reason="bounded finite search found no countermodel",
            advisory_notes=("finite-search miss is not proof",),
            metadata={"plan": plan.to_dict(), "finite_executor_result": result, "advisory_only": True},
        )
    return _residual_attempt(plan, str(result.get("failure_reason") or status or "constructor residual"))


def _residual_attempt(plan: ConstructorPlan, reason: str) -> ConstructorAttempt:
    return ConstructorAttempt(
        attempt_id=make_constructor_attempt_id({"plan_id": plan.plan_id, "residual": reason}),
        plan_id=plan.plan_id,
        status=RootConstructorStatus.RESIDUAL,
        residual_delta=0,
        failure_reason=reason,
        advisory_notes=("constructor attempt remained residual", "not terminal truth"),
        metadata={"plan": plan.to_dict(), "advisory_only": True},
    )


def _summary(
    trace: RootConstructorTrace,
    *,
    dry_run: bool,
    projection_traces: Sequence[ProjectionTrace],
) -> dict[str, Any]:
    return {
        "root_signals_total": len(trace.root_signals),
        "plans_total": len(trace.plans),
        "attempts_total": len(trace.attempts),
        "terminal_attempts": trace.terminal_count(),
        "candidate_tables": trace.candidate_count(),
        "importer_verified": sum(1 for attempt in trace.attempts if attempt.status == RootConstructorStatus.IMPORTER_VERIFIED),
        "importer_rejected": sum(1 for attempt in trace.attempts if attempt.status == RootConstructorStatus.IMPORTER_REJECTED),
        "search_misses": trace.search_miss_count(),
        "residuals": trace.residual_count(),
        "obstructions_named": sum(1 for attempt in trace.attempts if attempt.status == RootConstructorStatus.OBSTRUCTION_NAMED),
        "residual_delta_total": trace.residual_delta_total(),
        "compression_gain_total": trace.compression_gain_total(),
        "projection_gain_total": trace.projection_gain_total(),
        "dry_run": dry_run,
        "advisory_only": dry_run,
        "projection_influenced": bool(projection_traces),
    }


def _projection_hints(projection_traces: Sequence[ProjectionTrace]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for trace in projection_traces:
        candidates_by_id = {candidate.candidate_id: candidate for candidate in trace.candidates}
        for result in trace.results:
            candidate = candidates_by_id.get(result.candidate_id)
            if candidate is None:
                raw_candidate = result.metadata.get("candidate")
                candidate = ProjectionCandidate.from_dict(raw_candidate) if isinstance(raw_candidate, dict) else None
            if candidate is None:
                continue
            if result.status in {
                ProjectionStatus.RESIDUAL_SPLIT,
                ProjectionStatus.OBSTRUCTION_PRESSURE,
                ProjectionStatus.ADVISORY_ONLY,
                ProjectionStatus.CANDIDATE,
            }:
                hints.append(
                    {
                        "source": candidate.source,
                        "target": candidate.target,
                        "source_idx": candidate.source_idx,
                        "target_idx": candidate.target_idx,
                        "projection_gain": result.projection_gain,
                        "residual_delta": result.residual_delta,
                        "status": result.status.value,
                        "candidate_id": candidate.candidate_id,
                    }
                )
    return hints


def _match_signals(pair: Mapping[str, Any], signals: Sequence[RootSignal]) -> list[RootSignal]:
    pair_text = json.dumps(pair, sort_keys=True).lower()
    matches: list[RootSignal] = []
    for signal in signals:
        keys = [signal.basin, signal.micro_basin, signal.name, signal.obstruction_id]
        feature_values = [str(value) for value in signal.features.values() if isinstance(value, (str, int, float))]
        needles = [str(value).lower() for value in keys + feature_values if value not in (None, "")]
        if not needles or any(needle in pair_text for needle in needles):
            matches.append(signal)
    return matches


def _best_projection_hint(pair: Mapping[str, Any], hints: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    source = _optional_str(pair.get("source") or pair.get("equation1"))
    target = _optional_str(pair.get("target") or pair.get("equation2"))
    for hint in hints:
        if hint.get("source") == source and hint.get("target") == target:
            return hint
    for hint in hints:
        if hint.get("source") == source or hint.get("target") == target:
            return hint
    return None


def _choose_kind(signal: RootSignal | None, hint: Mapping[str, Any] | None) -> RootConstructorKind:
    text = ""
    if signal is not None:
        text = json.dumps({"features": signal.features, "metadata": signal.metadata, "name": signal.name}, sort_keys=True).lower()
    if "diagonal" in text:
        return RootConstructorKind.DIAGONAL_PRESSURE
    if "taildrop" in text:
        return RootConstructorKind.TAILDROP
    if "same_skeleton" in text or "same skeleton" in text:
        return RootConstructorKind.SAME_SKELETON_COLLAPSE
    if "role_permutation" in text or "role permutation" in text:
        return RootConstructorKind.ROLE_PERMUTATION
    if hint:
        return RootConstructorKind.PROJECTION_GUIDED
    if signal and signal.obstruction_id:
        return RootConstructorKind.OBSTRUCTION_GUIDED
    if signal:
        return RootConstructorKind.BASIN_TEMPLATE
    return RootConstructorKind.UNKNOWN


def _expected_gain(signal: RootSignal | None, hint: Mapping[str, Any] | None, pair: Mapping[str, Any]) -> float:
    confidence = signal.confidence if signal else 0.0
    support = min(float(signal.support if signal else 0), 100.0) / 100.0
    projection_gain = float(hint.get("projection_gain", 0.0) or 0.0) if hint else 0.0
    residual_hint = abs(float(hint.get("residual_delta", 0.0) or 0.0)) if hint else 0.0
    pair_gain = float(pair.get("expected_gain", 0.0) or 0.0)
    return confidence + support + projection_gain + residual_hint + pair_gain


def _rank_score(signal: RootSignal | None, hint: Mapping[str, Any] | None, expected_gain: float) -> float:
    return expected_gain + (signal.confidence if signal else 0.0) + (0.01 * (signal.support if signal else 0))


def _plan_rank(plan: ConstructorPlan) -> tuple[float, str]:
    return (-float(plan.metadata.get("rank_score", plan.expected_gain)), plan.plan_id)


def _experience_outcome(attempt: ConstructorAttempt) -> AgentExperienceOutcome:
    if attempt.is_terminal() and attempt.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return AgentExperienceOutcome.FINITE_COUNTERMODEL
    if attempt.is_terminal() and attempt.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        return AgentExperienceOutcome.NAMED_OBSTRUCTION
    if attempt.status == RootConstructorStatus.IMPORTER_REJECTED:
        return AgentExperienceOutcome.INVALID_CANDIDATE
    if attempt.status == RootConstructorStatus.SEARCH_MISS:
        return AgentExperienceOutcome.FAILED_SEARCH
    if attempt.status in {RootConstructorStatus.RESIDUAL, RootConstructorStatus.CANDIDATE_TABLE_FOUND}:
        return AgentExperienceOutcome.RESIDUAL
    return AgentExperienceOutcome.ADVISORY_ONLY


def _scar_tags(attempt: ConstructorAttempt) -> tuple[str, ...]:
    if attempt.status == RootConstructorStatus.SEARCH_MISS:
        return ("finite_search_miss",)
    if attempt.status == RootConstructorStatus.IMPORTER_REJECTED:
        return ("importer_rejected",)
    if attempt.status == RootConstructorStatus.RESIDUAL:
        return ("constructor_residual",)
    return ()


def _read_records(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [dict(item) for item in data]
    if isinstance(data, dict):
        for key in ("root_signals", "signals", "items", "results", "pairs"):
            if isinstance(data.get(key), list):
                return [dict(item) for item in data[key]]
        return [dict(data)]
    return []


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(dict(json.loads(line)))
    return rows


def _write_jsonl(rows: Sequence[Mapping[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _optional_terminal_form(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    if isinstance(value, TerminalForm):
        return value
    return TerminalForm(str(value))


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

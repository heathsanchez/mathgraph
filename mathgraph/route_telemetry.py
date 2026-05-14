"""Route telemetry ledger for future spectral H-tilt.

This module records route choices, transitions, killing pressure, costs, gains,
and outcomes from unified verification episodes. The records are advisory
telemetry only: they prepare data for future spectral H-tilt, but they do not
decide truth and cannot promote claims across the verifier boundary.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id
from mathgraph.proof_verification import ProofArtifactKind, ProofVerificationStatus
from mathgraph.projection import ProjectionStatus
from mathgraph.root_constructors import RootConstructorStatus
from mathgraph.verification_episode import (
    VerificationEpisodeStatus,
    VerificationEpisodeTrace,
    VerificationRouteKind,
)


class RouteTelemetryOutcome(str, Enum):
    TERMINAL_VERIFIED_PROOF = "TERMINAL_VERIFIED_PROOF"
    TERMINAL_FINITE_COUNTERMODEL = "TERMINAL_FINITE_COUNTERMODEL"
    TERMINAL_NAMED_OBSTRUCTION = "TERMINAL_NAMED_OBSTRUCTION"
    KNOWN_SKIP = "KNOWN_SKIP"
    DERIVED_CERTIFICATE = "DERIVED_CERTIFICATE"
    CANDIDATE_TABLE = "CANDIDATE_TABLE"
    PROOF_SKELETON = "PROOF_SKELETON"
    VERIFIER_FAILED = "VERIFIER_FAILED"
    IMPORTER_REJECTED = "IMPORTER_REJECTED"
    SEARCH_MISS = "SEARCH_MISS"
    RESIDUAL = "RESIDUAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    ALIGNMENT_FAILED = "ALIGNMENT_FAILED"


class RouteTelemetryKind(str, Enum):
    LAWBOOK_LOOKUP = "LAWBOOK_LOOKUP"
    PROJECTION = "PROJECTION"
    ROOT_CONSTRUCTOR = "ROOT_CONSTRUCTOR"
    PROOF_VERIFICATION = "PROOF_VERIFICATION"
    BOTH_SIDES = "BOTH_SIDES"
    RESIDUAL_ONLY = "RESIDUAL_ONLY"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass
class RouteTelemetryEvent:
    event_id: str
    episode_id: str | None
    claim_id: str | None
    route_kind: RouteTelemetryKind
    outcome: RouteTelemetryOutcome
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    from_state: str | None = None
    to_state: str | None = None
    cost_units: float = 0.0
    residual_delta: int = 0
    compression_gain: float = 0.0
    projection_gain: float = 0.0
    derived_amplification: float = 0.0
    killed: bool = False
    kill_reason: str | None = None
    support_weight: float = 0.0
    survival_weight: float = 0.0
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.terminal_form is not None and bool(self.certificate_id) and self.verifier_boundary_crossed

    def is_kill(self) -> bool:
        return self.killed

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "episode_id": self.episode_id,
            "claim_id": self.claim_id,
            "route_kind": self.route_kind.value,
            "outcome": self.outcome.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "cost_units": self.cost_units,
            "residual_delta": self.residual_delta,
            "compression_gain": self.compression_gain,
            "projection_gain": self.projection_gain,
            "derived_amplification": self.derived_amplification,
            "killed": self.killed,
            "kill_reason": self.kill_reason,
            "support_weight": self.support_weight,
            "survival_weight": self.survival_weight,
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RouteTelemetryEvent":
        return cls(
            event_id=str(data["event_id"]),
            episode_id=_optional_str(data.get("episode_id")),
            claim_id=_optional_str(data.get("claim_id")),
            route_kind=RouteTelemetryKind(str(data.get("route_kind", RouteTelemetryKind.UNKNOWN.value))),
            outcome=RouteTelemetryOutcome(str(data["outcome"])),
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            from_state=_optional_str(data.get("from_state")),
            to_state=_optional_str(data.get("to_state")),
            cost_units=float(data.get("cost_units", 0.0) or 0.0),
            residual_delta=int(data.get("residual_delta", 0) or 0),
            compression_gain=float(data.get("compression_gain", 0.0) or 0.0),
            projection_gain=float(data.get("projection_gain", 0.0) or 0.0),
            derived_amplification=float(data.get("derived_amplification", 0.0) or 0.0),
            killed=bool(data.get("killed", False)),
            kill_reason=_optional_str(data.get("kill_reason")),
            support_weight=float(data.get("support_weight", 0.0) or 0.0),
            survival_weight=float(data.get("survival_weight", 0.0) or 0.0),
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "RouteTelemetryEvent":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "RouteTelemetryEvent":
        return cls.from_json(line.strip())


@dataclass
class RouteTelemetryLedger:
    ledger_id: str
    events: list[RouteTelemetryEvent] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: RouteTelemetryEvent) -> None:
        self.events.append(event)
        self.summary = _ledger_summary(self)

    def terminal_count(self) -> int:
        return sum(1 for event in self.events if event.is_terminal())

    def kill_count(self) -> int:
        return sum(1 for event in self.events if event.is_kill())

    def advisory_count(self) -> int:
        return sum(1 for event in self.events if not event.is_terminal())

    def route_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.route_kind.value] = counts.get(event.route_kind.value, 0) + 1
        return counts

    def outcome_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.outcome.value] = counts.get(event.outcome.value, 0) + 1
        return counts

    def transition_counts(self) -> dict[str, int]:
        return transition_table(self)

    def killing_counts(self) -> dict[str, int]:
        return killing_table(self)

    def total_cost(self) -> float:
        return sum(event.cost_units for event in self.events)

    def total_residual_delta(self) -> int:
        return sum(event.residual_delta for event in self.events)

    def total_compression_gain(self) -> float:
        return sum(event.compression_gain for event in self.events)

    def total_projection_gain(self) -> float:
        return sum(event.projection_gain for event in self.events)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "events": [event.to_dict() for event in self.events],
            "created_at": self.created_at,
            "summary": dict(self.summary),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RouteTelemetryLedger":
        return cls(
            ledger_id=str(data["ledger_id"]),
            events=[RouteTelemetryEvent.from_dict(item) for item in data.get("events", [])],
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "RouteTelemetryLedger":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "RouteTelemetryLedger":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(event.to_jsonl_line() for event in self.events), encoding="utf-8")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "RouteTelemetryLedger":
        source = Path(path)
        events: list[RouteTelemetryEvent] = []
        if source.exists():
            with source.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        events.append(RouteTelemetryEvent.from_jsonl_line(line))
        return build_route_telemetry_ledger(events=events)


@dataclass
class HTiltTelemetrySummary:
    summary_id: str
    route_scores: dict[str, float]
    route_survival_rates: dict[str, float]
    route_kill_rates: dict[str, float]
    route_average_gain: dict[str, float]
    route_average_cost: dict[str, float]
    transition_counts: dict[str, int]
    killing_counts: dict[str, int]
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "route_scores": dict(self.route_scores),
            "route_survival_rates": dict(self.route_survival_rates),
            "route_kill_rates": dict(self.route_kill_rates),
            "route_average_gain": dict(self.route_average_gain),
            "route_average_cost": dict(self.route_average_cost),
            "transition_counts": dict(self.transition_counts),
            "killing_counts": dict(self.killing_counts),
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HTiltTelemetrySummary":
        return cls(
            summary_id=str(data["summary_id"]),
            route_scores={str(k): float(v) for k, v in dict(data.get("route_scores", {})).items()},
            route_survival_rates={str(k): float(v) for k, v in dict(data.get("route_survival_rates", {})).items()},
            route_kill_rates={str(k): float(v) for k, v in dict(data.get("route_kill_rates", {})).items()},
            route_average_gain={str(k): float(v) for k, v in dict(data.get("route_average_gain", {})).items()},
            route_average_cost={str(k): float(v) for k, v in dict(data.get("route_average_cost", {})).items()},
            transition_counts={str(k): int(v) for k, v in dict(data.get("transition_counts", {})).items()},
            killing_counts={str(k): int(v) for k, v in dict(data.get("killing_counts", {})).items()},
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "HTiltTelemetrySummary":
        return cls.from_dict(json.loads(text))


def telemetry_events_from_episode(episode: VerificationEpisodeTrace) -> list[RouteTelemetryEvent]:
    events: list[RouteTelemetryEvent] = []
    claim_id = episode.input.claim_id
    for decision in episode.route_decisions:
        events.append(
            _event(
                episode_id=episode.episode_id,
                claim_id=claim_id,
                route_kind=_route_kind(decision.route_kind),
                outcome=RouteTelemetryOutcome.ADVISORY_ONLY,
                from_state="input",
                to_state="route_selected",
                support_weight=float(decision.htilt_score or 0.0),
                survival_weight=1.0,
                metadata={
                    "route_decision": decision.to_dict(),
                    "advisory_only": True,
                    "route_telemetry_is_not_truth": True,
                },
            )
        )

    if episode.projection_trace is not None:
        for result in episode.projection_trace.results:
            outcome = _projection_outcome(result.status, result.is_terminal())
            events.append(
                _event(
                    episode_id=episode.episode_id,
                    claim_id=claim_id,
                    route_kind=RouteTelemetryKind.PROJECTION,
                    outcome=outcome,
                    terminal_form=result.terminal_form if result.is_terminal() else None,
                    certificate_id=(result.derived_certificate_id or result.lawbook_entry_id) if result.is_terminal() else None,
                    verifier_boundary_crossed=result.is_terminal(),
                    from_state="route_selected",
                    to_state="terminal" if result.is_terminal() else "residual",
                    residual_delta=result.residual_delta,
                    compression_gain=result.compression_gain,
                    projection_gain=result.projection_gain,
                    support_weight=1.0 if result.is_terminal() else 0.25,
                    survival_weight=1.0 if not result.is_advisory() else 0.5,
                    advisory=not result.is_terminal(),
                    metadata={"projection_result": result.to_dict(), "advisory_telemetry": True},
                )
            )

    if episode.root_constructor_trace is not None:
        for attempt in episode.root_constructor_trace.attempts:
            outcome = _constructor_outcome(attempt.status, attempt.is_terminal())
            killed = attempt.status in {
                RootConstructorStatus.SEARCH_MISS,
                RootConstructorStatus.IMPORTER_REJECTED,
                RootConstructorStatus.RESIDUAL,
            }
            events.append(
                _event(
                    episode_id=episode.episode_id,
                    claim_id=claim_id,
                    route_kind=RouteTelemetryKind.ROOT_CONSTRUCTOR,
                    outcome=outcome,
                    terminal_form=attempt.terminal_form if attempt.is_terminal() else None,
                    certificate_id=attempt.certificate_id if attempt.is_terminal() else None,
                    verifier_boundary_crossed=attempt.is_terminal(),
                    from_state="root_constructor",
                    to_state="terminal" if attempt.is_terminal() else ("killed" if killed else "candidate"),
                    cost_units=attempt.cost_units,
                    residual_delta=attempt.residual_delta,
                    compression_gain=attempt.compression_gain,
                    projection_gain=attempt.projection_gain,
                    killed=killed,
                    kill_reason=attempt.failure_reason if killed else None,
                    support_weight=1.0 if attempt.is_terminal() else 0.25,
                    survival_weight=0.0 if killed else 1.0,
                    advisory=not attempt.is_terminal(),
                    metadata={"constructor_attempt": attempt.to_dict(), "advisory_telemetry": True},
                )
            )

    if episode.proof_verification_trace is not None:
        for artifact in episode.proof_verification_trace.artifacts:
            if artifact.kind in {
                ProofArtifactKind.LEAN_SKELETON,
                ProofArtifactKind.ISABELLE_SKELETON,
                ProofArtifactKind.PROOF_MOTIF,
                ProofArtifactKind.LEMMA_CANDIDATE,
                ProofArtifactKind.CUT_CANDIDATE,
            }:
                events.append(
                    _event(
                        episode_id=episode.episode_id,
                        claim_id=artifact.claim_id or claim_id,
                        route_kind=RouteTelemetryKind.PROOF_VERIFICATION,
                        outcome=RouteTelemetryOutcome.PROOF_SKELETON,
                        from_state="proof_verification",
                        to_state="candidate",
                        survival_weight=0.5,
                        metadata={"proof_artifact": artifact.to_dict(), "advisory_telemetry": True},
                    )
                )
        for result in episode.proof_verification_trace.results:
            killed = result.status == ProofVerificationStatus.VERIFIER_FAILED
            events.append(
                _event(
                    episode_id=episode.episode_id,
                    claim_id=claim_id,
                    route_kind=RouteTelemetryKind.PROOF_VERIFICATION,
                    outcome=_proof_outcome(result.status, result.is_terminal()),
                    terminal_form=result.terminal_form if result.is_terminal() else None,
                    certificate_id=result.certificate_id if result.is_terminal() else None,
                    verifier_boundary_crossed=result.is_terminal(),
                    from_state="verifier",
                    to_state="terminal" if result.is_terminal() else ("killed" if killed else "residual"),
                    residual_delta=result.residual_delta,
                    compression_gain=result.compression_gain,
                    projection_gain=result.projection_gain,
                    killed=killed,
                    kill_reason=result.failure_reason if killed else None,
                    support_weight=1.0 if result.is_terminal() else 0.25,
                    survival_weight=0.0 if killed else 1.0,
                    advisory=not result.is_terminal(),
                    metadata={"proof_result": result.to_dict(), "advisory_telemetry": True},
                )
            )

    for exp in episode.agent_experiences:
        events.append(
            _event(
                episode_id=episode.episode_id,
                claim_id=exp.claim_id or claim_id,
                route_kind=_route_from_string(exp.route),
                outcome=_agent_experience_outcome(exp),
                terminal_form=exp.terminal_form if exp.verifier_boundary_crossed else None,
                certificate_id=exp.certificate_id if exp.verifier_boundary_crossed else None,
                verifier_boundary_crossed=exp.verifier_boundary_crossed,
                from_state=exp.phase or "agent_experience",
                to_state="terminal" if exp.verifier_boundary_crossed else "residual",
                cost_units=exp.cost_units,
                residual_delta=exp.residual_delta,
                compression_gain=exp.compression_gain,
                projection_gain=exp.projection_gain,
                derived_amplification=exp.derived_amplification,
                killed=bool(exp.scar_tags),
                kill_reason=",".join(exp.scar_tags) if exp.scar_tags else None,
                support_weight=0.5,
                survival_weight=1.0 if exp.verifier_boundary_crossed else 0.5,
                advisory=not exp.verifier_boundary_crossed,
                metadata={"agent_experience": exp.to_dict(), "advisory_telemetry": True},
            )
        )

    if episode.status == VerificationEpisodeStatus.ALIGNMENT_FAILED:
        events.append(
            _event(
                episode_id=episode.episode_id,
                claim_id=claim_id,
                route_kind=RouteTelemetryKind.UNKNOWN,
                outcome=RouteTelemetryOutcome.ALIGNMENT_FAILED,
                from_state="alignment",
                to_state="killed",
                killed=True,
                kill_reason="roadmap alignment critical finding",
                metadata={"episode_status": episode.status.value, "advisory_telemetry": True},
            )
        )
    elif episode.is_terminal():
        events.append(
            _event(
                episode_id=episode.episode_id,
                claim_id=claim_id,
                route_kind=_terminal_route_kind(episode),
                outcome=_terminal_outcome(episode.terminal_form),
                terminal_form=episode.terminal_form,
                certificate_id=episode.certificate_id,
                verifier_boundary_crossed=True,
                from_state="verifier",
                to_state="terminal",
                compression_gain=float(episode.summary.get("residual_delta_total", 0) or 0),
                projection_gain=float(episode.summary.get("projection_gain_total", 0.0) or 0.0),
                support_weight=1.0,
                survival_weight=1.0,
                advisory=False,
                metadata={"episode_terminal": True, "advisory_telemetry": True},
            )
        )
    elif not events:
        events.append(
            _event(
                episode_id=episode.episode_id,
                claim_id=claim_id,
                route_kind=RouteTelemetryKind.ADVISORY_ONLY,
                outcome=RouteTelemetryOutcome.ADVISORY_ONLY,
                from_state="input",
                to_state="residual",
                metadata={"empty_episode": True, "advisory_telemetry": True},
            )
        )
    return events


def build_route_telemetry_ledger(
    *,
    episodes: Sequence[VerificationEpisodeTrace] = (),
    events: Sequence[RouteTelemetryEvent] = (),
) -> RouteTelemetryLedger:
    all_events = [event for episode in episodes for event in telemetry_events_from_episode(episode)]
    all_events.extend(events)
    ledger = RouteTelemetryLedger(
        ledger_id=make_route_telemetry_ledger_id([event.to_dict() for event in all_events]),
        events=list(all_events),
    )
    ledger.summary.update(_ledger_summary(ledger))
    return ledger


def summarize_h_tilt_telemetry(
    ledger: RouteTelemetryLedger,
    *,
    beta: float = 1.0,
) -> HTiltTelemetrySummary:
    """Create advisory route scores from telemetry.

    This is telemetry preparation only, not full spectral H-tilt. Full spectral
    H-tilt requires estimating L, V, K=L-V, h, q, and pi*.
    """

    buckets: dict[str, list[RouteTelemetryEvent]] = {}
    for event in ledger.events:
        buckets.setdefault(event.route_kind.value, []).append(event)

    route_scores: dict[str, float] = {}
    survival_rates: dict[str, float] = {}
    kill_rates: dict[str, float] = {}
    average_gain: dict[str, float] = {}
    average_cost: dict[str, float] = {}
    for route, route_events in sorted(buckets.items()):
        count = len(route_events)
        killed = sum(1 for event in route_events if event.killed)
        survival_rate = (count - killed) / count if count else 0.0
        kill_rate = killed / count if count else 0.0
        total_gain = sum(
            event.compression_gain
            + event.projection_gain
            + event.derived_amplification
            + (1.0 if event.is_terminal() else 0.0)
            for event in route_events
        )
        total_cost = sum(event.cost_units for event in route_events)
        avg_gain = total_gain / count if count else 0.0
        avg_cost = total_cost / count if count else 0.0
        route_scores[route] = beta * (survival_rate + avg_gain - kill_rate - 0.1 * avg_cost)
        survival_rates[route] = survival_rate
        kill_rates[route] = kill_rate
        average_gain[route] = avg_gain
        average_cost[route] = avg_cost

    payload = {
        "ledger_id": ledger.ledger_id,
        "beta": beta,
        "route_scores": route_scores,
        "transition_counts": ledger.transition_counts(),
        "killing_counts": ledger.killing_counts(),
    }
    return HTiltTelemetrySummary(
        summary_id=content_id("htilt_telemetry_summary", payload, n=24),
        route_scores=route_scores,
        route_survival_rates=survival_rates,
        route_kill_rates=kill_rates,
        route_average_gain=average_gain,
        route_average_cost=average_cost,
        transition_counts=ledger.transition_counts(),
        killing_counts=ledger.killing_counts(),
        advisory=True,
        metadata={
            "advisory_only": True,
            "full_spectral_h_tilt_future_work": True,
            "spectral_terms_not_estimated": ["L", "V", "K=L-V", "h", "q", "pi*"],
        },
    )


def transition_table(ledger: RouteTelemetryLedger) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in ledger.events:
        if event.from_state and event.to_state:
            key = f"{event.from_state}->{event.to_state}"
            counts[key] = counts.get(key, 0) + 1
    return counts


def killing_table(ledger: RouteTelemetryLedger) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in ledger.events:
        if event.killed:
            key = event.kill_reason or event.outcome.value
            counts[key] = counts.get(key, 0) + 1
    return counts


def route_outcome_table(ledger: RouteTelemetryLedger) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in ledger.events:
        key = f"{event.route_kind.value}::{event.outcome.value}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def make_route_telemetry_event_id(payload: Mapping[str, Any]) -> str:
    return content_id("route_telemetry_event", payload, n=24)


def make_route_telemetry_ledger_id(payload: Any) -> str:
    return content_id("route_telemetry_ledger", payload, n=24)


def _event(**kwargs: Any) -> RouteTelemetryEvent:
    payload = {key: value for key, value in kwargs.items() if key != "event_id"}
    return RouteTelemetryEvent(event_id=make_route_telemetry_event_id(payload), **kwargs)


def _ledger_summary(ledger: RouteTelemetryLedger) -> dict[str, Any]:
    total_cost = ledger.total_cost()
    terminal_count = ledger.terminal_count()
    total_compression = ledger.total_compression_gain()
    total_projection = ledger.total_projection_gain()
    residual_compression = total_compression + abs(ledger.total_residual_delta())
    return {
        "events_total": len(ledger.events),
        "terminal_count": terminal_count,
        "kill_count": ledger.kill_count(),
        "advisory_count": ledger.advisory_count(),
        "route_counts": ledger.route_counts(),
        "outcome_counts": ledger.outcome_counts(),
        "transition_counts": ledger.transition_counts(),
        "killing_counts": ledger.killing_counts(),
        "route_outcome_counts": route_outcome_table(ledger),
        "total_cost": total_cost,
        "total_residual_delta": ledger.total_residual_delta(),
        "total_compression_gain": total_compression,
        "total_projection_gain": total_projection,
        "certificate_yield_per_cost": _safe_div(float(terminal_count), total_cost),
        "residual_compression_per_cost": _safe_div(residual_compression, total_cost),
        "projection_gain_per_cost": _safe_div(total_projection, total_cost),
        "metadata": {
            "advisory_only": True,
            "telemetry_is_not_truth": True,
            "full_spectral_h_tilt_future_work": True,
        },
    }


def _projection_outcome(status: ProjectionStatus, terminal: bool) -> RouteTelemetryOutcome:
    if status == ProjectionStatus.KNOWN_SKIP:
        return RouteTelemetryOutcome.KNOWN_SKIP
    if status == ProjectionStatus.DERIVED_CERTIFICATE and terminal:
        return RouteTelemetryOutcome.DERIVED_CERTIFICATE
    if status == ProjectionStatus.REJECTED:
        return RouteTelemetryOutcome.IMPORTER_REJECTED
    if status == ProjectionStatus.RESIDUAL_SPLIT:
        return RouteTelemetryOutcome.RESIDUAL
    return RouteTelemetryOutcome.ADVISORY_ONLY


def _constructor_outcome(status: RootConstructorStatus, terminal: bool) -> RouteTelemetryOutcome:
    if terminal:
        return RouteTelemetryOutcome.TERMINAL_FINITE_COUNTERMODEL
    if status == RootConstructorStatus.CANDIDATE_TABLE_FOUND:
        return RouteTelemetryOutcome.CANDIDATE_TABLE
    if status == RootConstructorStatus.IMPORTER_REJECTED:
        return RouteTelemetryOutcome.IMPORTER_REJECTED
    if status == RootConstructorStatus.SEARCH_MISS:
        return RouteTelemetryOutcome.SEARCH_MISS
    if status == RootConstructorStatus.OBSTRUCTION_NAMED:
        return RouteTelemetryOutcome.TERMINAL_NAMED_OBSTRUCTION if terminal else RouteTelemetryOutcome.RESIDUAL
    if status == RootConstructorStatus.RESIDUAL:
        return RouteTelemetryOutcome.RESIDUAL
    return RouteTelemetryOutcome.ADVISORY_ONLY


def _proof_outcome(status: ProofVerificationStatus, terminal: bool) -> RouteTelemetryOutcome:
    if terminal:
        return RouteTelemetryOutcome.TERMINAL_VERIFIED_PROOF
    if status == ProofVerificationStatus.VERIFIER_FAILED:
        return RouteTelemetryOutcome.VERIFIER_FAILED
    if status in {ProofVerificationStatus.SKELETON_GENERATED, ProofVerificationStatus.VERIFIER_NOT_RUN}:
        return RouteTelemetryOutcome.PROOF_SKELETON
    if status == ProofVerificationStatus.REJECTED:
        return RouteTelemetryOutcome.IMPORTER_REJECTED
    if status == ProofVerificationStatus.RESIDUAL:
        return RouteTelemetryOutcome.RESIDUAL
    return RouteTelemetryOutcome.ADVISORY_ONLY


def _agent_experience_outcome(exp: Any) -> RouteTelemetryOutcome:
    if exp.verifier_boundary_crossed and exp.terminal_form == TerminalForm.VERIFIED_PROOF:
        return RouteTelemetryOutcome.TERMINAL_VERIFIED_PROOF
    if exp.verifier_boundary_crossed and exp.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return RouteTelemetryOutcome.TERMINAL_FINITE_COUNTERMODEL
    if exp.verifier_boundary_crossed and exp.terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        return RouteTelemetryOutcome.TERMINAL_NAMED_OBSTRUCTION
    value = getattr(exp.outcome, "value", str(exp.outcome))
    if value == "FAILED_SEARCH":
        return RouteTelemetryOutcome.SEARCH_MISS
    if value == "INVALID_CANDIDATE":
        return RouteTelemetryOutcome.IMPORTER_REJECTED
    if value == "KNOWN_SKIPPED":
        return RouteTelemetryOutcome.KNOWN_SKIP
    if value == "RESIDUAL":
        return RouteTelemetryOutcome.RESIDUAL
    return RouteTelemetryOutcome.ADVISORY_ONLY


def _terminal_outcome(terminal_form: TerminalForm | None) -> RouteTelemetryOutcome:
    if terminal_form == TerminalForm.VERIFIED_PROOF:
        return RouteTelemetryOutcome.TERMINAL_VERIFIED_PROOF
    if terminal_form == TerminalForm.FINITE_COUNTERMODEL:
        return RouteTelemetryOutcome.TERMINAL_FINITE_COUNTERMODEL
    if terminal_form == TerminalForm.NAMED_OBSTRUCTION:
        return RouteTelemetryOutcome.TERMINAL_NAMED_OBSTRUCTION
    return RouteTelemetryOutcome.ADVISORY_ONLY


def _terminal_route_kind(episode: VerificationEpisodeTrace) -> RouteTelemetryKind:
    if episode.terminal_form == TerminalForm.VERIFIED_PROOF:
        return RouteTelemetryKind.PROOF_VERIFICATION
    if episode.terminal_form in {TerminalForm.FINITE_COUNTERMODEL, TerminalForm.NAMED_OBSTRUCTION}:
        return RouteTelemetryKind.ROOT_CONSTRUCTOR
    return RouteTelemetryKind.UNKNOWN


def _route_kind(route: VerificationRouteKind) -> RouteTelemetryKind:
    try:
        return RouteTelemetryKind(route.value)
    except ValueError:
        return RouteTelemetryKind.UNKNOWN


def _route_from_string(route: str | None) -> RouteTelemetryKind:
    if not route:
        return RouteTelemetryKind.UNKNOWN
    lowered = route.lower()
    if "projection" in lowered:
        return RouteTelemetryKind.PROJECTION
    if "constructor" in lowered or "root" in lowered:
        return RouteTelemetryKind.ROOT_CONSTRUCTOR
    if "proof" in lowered or "verifier" in lowered:
        return RouteTelemetryKind.PROOF_VERIFICATION
    return RouteTelemetryKind.UNKNOWN


def _safe_div(numerator: float, denominator: float) -> float:
    if math.isclose(denominator, 0.0):
        return 0.0
    return numerator / denominator


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_terminal_form(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    return TerminalForm(str(value))


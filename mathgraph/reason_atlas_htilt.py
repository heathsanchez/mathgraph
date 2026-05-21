"""Spectral H-Tilt wiring for persistent advisory Reason Atlas entries."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.reason_atlas_store import (
    ReasonAtlasEntry,
    ReasonAtlasEntryStatus,
    ReasonAtlasFeedbackOutcome,
    ReasonAtlasQuery,
    ReasonAtlasStore,
)
from mathgraph.route_telemetry import (
    RouteTelemetryEvent,
    RouteTelemetryKind,
    RouteTelemetryLedger,
    RouteTelemetryOutcome,
    build_route_telemetry_ledger,
)
from mathgraph.spectral_htilt import SpectralHTiltConfig, SpectralHTiltEstimate, SpectralStateEstimate, estimate_spectral_htilt


@dataclass(frozen=True)
class ReasonAtlasHTiltConfig:
    beta: float = 1.0
    base_priority_weight: float = 1.0
    survivor_weight: float = 8.0
    survival_weight: float = 4.0
    support_weight: float = 3.0
    mu_weight: float = 5.0
    kill_weight: float = 6.0
    novelty_weight: float = 0.25
    limit: int = 1000


@dataclass(frozen=True)
class ReasonAtlasHTiltScore:
    entry_id: str
    entry_kind: str
    old_priority_score: float
    new_priority_score: float
    htilt_score: float
    survivor_pi: float
    survival_h: float
    support_q: float
    tilted_mu_beta: float
    kill_pressure: float
    advisory_only: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_kind": self.entry_kind,
            "old_priority_score": self.old_priority_score,
            "new_priority_score": self.new_priority_score,
            "htilt_score": self.htilt_score,
            "survivor_pi": self.survivor_pi,
            "survival_h": self.survival_h,
            "support_q": self.support_q,
            "tilted_mu_beta": self.tilted_mu_beta,
            "kill_pressure": self.kill_pressure,
            "advisory_only": True,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ReasonAtlasHTiltReport:
    estimate_id: str
    entry_count: int
    feedback_event_count: int
    scored_entry_count: int
    converged: bool
    top_states: list[dict[str, Any]]
    advisory_boundary_ok: bool
    scores: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def build_route_telemetry_from_reason_atlas(store: ReasonAtlasStore, limit: int = 1000) -> RouteTelemetryLedger:
    """Build advisory route telemetry from Reason Atlas entries and feedback."""

    entries = store.query(ReasonAtlasQuery(status=ReasonAtlasEntryStatus.ACTIVE, limit=limit)).entries
    events: list[RouteTelemetryEvent] = []
    for entry in entries:
        events.append(
            RouteTelemetryEvent(
                event_id=content_id("reason-atlas-htilt-entry", [entry.entry_id, entry.updated_at]),
                episode_id="reason_atlas",
                claim_id=entry.entry_id,
                route_kind=RouteTelemetryKind.ROOT_CONSTRUCTOR,
                outcome=RouteTelemetryOutcome.ADVISORY_ONLY,
                from_state="reason_atlas",
                to_state=entry.entry_id,
                support_weight=float(max(entry.support, 1)),
                survival_weight=1.0,
                compression_gain=float(entry.residual_compression_total),
                advisory=True,
                metadata={"entry": entry.to_dict(), "advisory_only": True, "htilt_telemetry": True},
            )
        )
        for feedback in store.feedback_for_entry(entry.entry_id):
            outcome, killed, target = _feedback_to_telemetry(feedback.outcome)
            events.append(
                RouteTelemetryEvent(
                    event_id=content_id("reason-atlas-htilt-feedback", feedback.to_dict()),
                    episode_id="reason_atlas",
                    claim_id=entry.entry_id,
                    route_kind=RouteTelemetryKind.ROOT_CONSTRUCTOR,
                    outcome=outcome,
                    from_state=entry.entry_id,
                    to_state=target,
                    residual_delta=int(feedback.residual_delta),
                    compression_gain=max(float(feedback.residual_delta), 0.0),
                    killed=killed,
                    kill_reason=feedback.outcome.value if killed else None,
                    support_weight=1.0 if not killed else 0.1,
                    survival_weight=1.0 if not killed else 0.0,
                    advisory=True,
                    metadata={"feedback": feedback.to_dict(), "advisory_only": True, "htilt_telemetry": True},
                )
            )
    return build_route_telemetry_ledger(events=events)


def estimate_htilt_for_reason_atlas(store: ReasonAtlasStore, config: ReasonAtlasHTiltConfig | None = None) -> SpectralHTiltEstimate:
    cfg = config or ReasonAtlasHTiltConfig()
    ledger = build_route_telemetry_from_reason_atlas(store, cfg.limit)
    return estimate_spectral_htilt(ledger, config=SpectralHTiltConfig(beta=cfg.beta, metadata={"source": "reason_atlas"}))


def map_htilt_state_to_reason_entry(entry: ReasonAtlasEntry, estimate: SpectralHTiltEstimate) -> SpectralStateEstimate | None:
    for state in estimate.state_estimates:
        if state.state == entry.entry_id:
            return state
    return None


def score_reason_entry_with_htilt(entry: ReasonAtlasEntry, estimate: SpectralHTiltEstimate, config: ReasonAtlasHTiltConfig | None = None) -> ReasonAtlasHTiltScore:
    cfg = config or ReasonAtlasHTiltConfig()
    state = map_htilt_state_to_reason_entry(entry, estimate)
    if state is None:
        htilt_score = 0.0
        survivor_pi = survival_h = support_q = tilted_mu_beta = kill_pressure = 0.0
    else:
        survivor_pi = state.survivor_pi
        survival_h = state.survival_h
        support_q = state.support_q
        tilted_mu_beta = state.tilted_mu_beta
        kill_pressure = state.kill_pressure
        htilt_score = (
            cfg.survivor_weight * survivor_pi
            + cfg.survival_weight * survival_h
            + cfg.support_weight * support_q
            + cfg.mu_weight * tilted_mu_beta
            - cfg.kill_weight * kill_pressure
        )
    novelty = cfg.novelty_weight / (1.0 + max(entry.transfer_successes + entry.verifier_successes, 0))
    new_priority = max(0.0, cfg.base_priority_weight * float(entry.priority_score) + htilt_score + novelty)
    return ReasonAtlasHTiltScore(
        entry_id=entry.entry_id,
        entry_kind=entry.kind.value,
        old_priority_score=float(entry.priority_score),
        new_priority_score=new_priority,
        htilt_score=htilt_score,
        survivor_pi=survivor_pi,
        survival_h=survival_h,
        support_q=support_q,
        tilted_mu_beta=tilted_mu_beta,
        kill_pressure=kill_pressure,
        metadata={"estimate_id": estimate.estimate_id, "advisory_only": True},
    )


def apply_htilt_scores_to_reason_atlas(store: ReasonAtlasStore, estimate: SpectralHTiltEstimate, config: ReasonAtlasHTiltConfig | None = None) -> ReasonAtlasHTiltReport:
    cfg = config or ReasonAtlasHTiltConfig()
    entries = store.query(ReasonAtlasQuery(status=ReasonAtlasEntryStatus.ACTIVE, limit=cfg.limit)).entries
    scores: list[ReasonAtlasHTiltScore] = []
    applied_at = datetime.now(timezone.utc).isoformat()
    for entry in entries:
        score = score_reason_entry_with_htilt(entry, estimate, cfg)
        scores.append(score)
        state_meta = {
            "previous_priority_score": entry.priority_score,
            "htilt_score": score.htilt_score,
            "htilt_survivor_pi": score.survivor_pi,
            "htilt_survival_h": score.survival_h,
            "htilt_support_q": score.support_q,
            "htilt_mu_beta": score.tilted_mu_beta,
            "htilt_kill_pressure": score.kill_pressure,
            "htilt_estimate_id": estimate.estimate_id,
            "htilt_applied_at": applied_at,
            "advisory_only": True,
        }
        store.upsert_entry(replace(entry, priority_score=score.new_priority_score, metadata={**entry.metadata, **state_meta}))
    return reason_atlas_htilt_summary(store, estimate, scores)


def export_htilt_augmented_queue(store: ReasonAtlasStore, estimate: SpectralHTiltEstimate, path: str | Path, limit: int = 100) -> list[dict[str, Any]]:
    rows = store.export_next_queue_rows(path, limit=limit)
    for row in rows:
        state = next((item for item in estimate.state_estimates if item.state == row["entry_id"]), None)
        row["advisory_only"] = True
        row["htilt_estimate_id"] = estimate.estimate_id
        if state:
            row["htilt_score"] = state.score
            row["htilt_survivor_pi"] = state.survivor_pi
            row["htilt_survival_h"] = state.survival_h
            row["htilt_support_q"] = state.support_q
            row["htilt_mu_beta"] = state.tilted_mu_beta
            row["htilt_kill_pressure"] = state.kill_pressure
    output = Path(path)
    if output.suffix.lower() == ".csv":
        fields = sorted({key for row in rows for key in row})
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})
    else:
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def reason_atlas_htilt_summary(store: ReasonAtlasStore, estimate: SpectralHTiltEstimate, scores: list[ReasonAtlasHTiltScore] | None = None) -> ReasonAtlasHTiltReport:
    stats = store.stats()
    score_rows = [score.to_dict() for score in scores or []]
    return ReasonAtlasHTiltReport(
        estimate_id=estimate.estimate_id,
        entry_count=stats.entry_count,
        feedback_event_count=stats.feedback_count,
        scored_entry_count=len(score_rows),
        converged=estimate.converged,
        top_states=[state.to_dict() for state in estimate.top_states(10)],
        advisory_boundary_ok=stats.advisory_boundary_ok and estimate.advisory,
        scores=score_rows,
        metadata={"advisory_only": True, "not_truth_authority": True},
    )


def write_htilt_score_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _feedback_to_telemetry(outcome: ReasonAtlasFeedbackOutcome) -> tuple[RouteTelemetryOutcome, bool, str]:
    if outcome in {
        ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS,
        ReasonAtlasFeedbackOutcome.VERIFIER_SUCCESS,
        ReasonAtlasFeedbackOutcome.RESIDUAL_COMPRESSED,
        ReasonAtlasFeedbackOutcome.DELETION_HURT,
    }:
        return RouteTelemetryOutcome.DERIVED_CERTIFICATE, False, "survived"
    if outcome in {
        ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE,
        ReasonAtlasFeedbackOutcome.VERIFIER_FAILURE,
        ReasonAtlasFeedbackOutcome.OBSTRUCTION_FOUND,
        ReasonAtlasFeedbackOutcome.RESIDUAL_EXPANDED,
        ReasonAtlasFeedbackOutcome.DELETION_SAFE,
    }:
        return RouteTelemetryOutcome.SEARCH_MISS, True, "killed"
    return RouteTelemetryOutcome.ADVISORY_ONLY, False, "review"

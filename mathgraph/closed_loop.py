"""Closed advisory scheduling loop over MathGraph route outcomes."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from mathgraph.hashing import content_id
from mathgraph.htilt_scheduler import HTiltScheduler, ScheduledTask, SchedulerInputPair
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.outcome_dataset import PairOutcome, extract_pair_features
from mathgraph.route_learner import RouteLearner
from mathgraph.route_priors import build_smoothed_route_prior
from mathgraph.terminal_schema import terminal_form_from_legacy


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LoopEventKind(str, Enum):
    PENDING_SUBMITTED = "PENDING_SUBMITTED"
    TASK_SCHEDULED = "TASK_SCHEDULED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"
    ROUTE_PRIOR_UPDATED = "ROUTE_PRIOR_UPDATED"
    QUEUE_RESCORED = "QUEUE_RESCORED"
    LAWBOOK_CANDIDATE_EMITTED = "LAWBOOK_CANDIDATE_EMITTED"
    OBSTRUCTION_RECORDED = "OBSTRUCTION_RECORDED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class LoopEvent:
    event_id: str
    kind: str
    timestamp: str
    source: str | None = None
    target: str | None = None
    route: str | None = None
    terminal_form: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "timestamp": self.timestamp,
            "source": self.source,
            "target": self.target,
            "route": self.route,
            "terminal_form": self.terminal_form,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PendingPair:
    source: str
    target: str
    source_idx: int | None = None
    target_idx: int | None = None
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_scheduler_pair(self) -> SchedulerInputPair:
        return SchedulerInputPair(
            source=self.source,
            target=self.target,
            source_idx=self.source_idx,
            target_idx=self.target_idx,
            label=self.label,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "label": self.label,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_any(cls, value: "PendingPair | dict[str, Any] | tuple[str, str]") -> "PendingPair":
        if isinstance(value, PendingPair):
            return value
        if isinstance(value, tuple):
            return cls(source=str(value[0]), target=str(value[1]))
        return cls(
            source=str(value.get("source", "")),
            target=str(value.get("target", "")),
            source_idx=value.get("source_idx"),
            target_idx=value.get("target_idx"),
            label=value.get("label"),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class ClosedLoopStats:
    iteration: int
    pending_count: int
    outcome_count: int
    event_count: int
    terminal_form_distribution: dict[str, int]
    route_distribution: dict[str, int]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "pending_count": self.pending_count,
            "outcome_count": self.outcome_count,
            "event_count": self.event_count,
            "terminal_form_distribution": dict(self.terminal_form_distribution),
            "route_distribution": dict(self.route_distribution),
            "warnings": list(self.warnings),
        }


class ClosedVerificationLoop:
    def __init__(self, beta: float = 1.0, oracle: KernelOracle | None = None) -> None:
        self.beta = float(beta)
        self.oracle = oracle
        self.pending: list[PendingPair] = []
        self.outcomes: list[PairOutcome] = []
        self.events: list[LoopEvent] = []
        self.iteration = 0
        self._last_tasks: list[ScheduledTask] = []

    def submit_pending(self, pair: PendingPair | dict[str, Any] | tuple[str, str]) -> None:
        pending = PendingPair.from_any(pair)
        self.pending.append(pending)
        self._event(LoopEventKind.PENDING_SUBMITTED, source=pending.source, target=pending.target)

    def submit_many(self, pairs: Sequence[PendingPair | dict[str, Any] | tuple[str, str]]) -> None:
        for pair in pairs:
            self.submit_pending(pair)

    def record_outcome(
        self,
        source: str,
        target: str,
        terminal_form: str,
        route: str,
        verification_status: str = "VERIFIED",
        trust_level: str = "HIGH",
        origin: str = "closed_loop",
        features: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        warnings: Sequence[str] = (),
    ) -> PairOutcome:
        canonical = terminal_form_from_legacy(terminal_form)
        labels = {
            "is_verified_true": canonical.value == "VERIFIED_PROOF",
            "is_verified_false": canonical.value == "REFUTATION_CERTIFICATE",
            "is_obstruction": canonical.value == "NAMED_OBSTRUCTION",
        }
        outcome = PairOutcome(
            pair_id=content_id("closed_loop_pair_outcome", [source, target, terminal_form, route, len(self.outcomes)]),
            source=source,
            target=target,
            source_idx=None,
            target_idx=None,
            claim_id=None,
            terminal_form=terminal_form,
            verification_status=verification_status,
            trust_level=trust_level,
            origin=origin,
            route=route,
            derivation_rule=route,
            parent_claims=[],
            features=features or extract_pair_features(source, target),
            labels=labels,
            evidence=dict(evidence or {}),
            warnings=list(warnings),
        )
        self.outcomes.append(outcome)
        self.pending = [p for p in self.pending if not (p.source == source and p.target == target)]
        self._event(
            LoopEventKind.OUTCOME_RECORDED,
            source=source,
            target=target,
            route=route,
            terminal_form=terminal_form,
        )
        if canonical.value == "NAMED_OBSTRUCTION":
            self._event(LoopEventKind.OBSTRUCTION_RECORDED, source=source, target=target, route=route)
        return outcome

    def build_route_learner(self) -> RouteLearner | None:
        if not self.outcomes:
            return None
        learner = RouteLearner(self.outcomes)
        learner.build_policy_cards()
        return learner

    def schedule(self, top_k: int = 10, skip_known: bool = False) -> list[ScheduledTask]:
        self.iteration += 1
        learner = self.build_route_learner()
        prior = build_smoothed_route_prior(self.outcomes)
        scheduler = HTiltScheduler(
            oracle=self.oracle,
            route_learner=learner,
            outcomes=self.outcomes if learner is None and self.outcomes else None,
            beta=self.beta,
        )
        pairs = [p.to_scheduler_pair() for p in self.pending]
        tasks = scheduler.schedule(pairs, top_k=top_k, skip_known=skip_known)
        enriched: list[ScheduledTask] = []
        for task in tasks:
            metadata = {
                **task.metadata,
                "prior_from_outcome_count": len(self.outcomes),
                "smoothed_route_prior": prior.to_dict(),
                "advisory": True,
            }
            enriched_task = _replace_task_metadata(task, metadata)
            enriched.append(enriched_task)
            self._event(
                LoopEventKind.TASK_SCHEDULED,
                source=task.source,
                target=task.target,
                route=task.recommended_route,
                metadata={"priority": task.priority, "prior_from_outcome_count": len(self.outcomes)},
            )
        self._last_tasks = enriched
        self._event(LoopEventKind.ROUTE_PRIOR_UPDATED, metadata=prior.to_dict())
        self._event(LoopEventKind.QUEUE_RESCORED, metadata={"scheduled_count": len(enriched)})
        return enriched

    def next_tasks(self, top_k: int = 10) -> list[dict[str, Any]]:
        return [task.to_dict() for task in self.schedule(top_k=top_k)]

    def stats(self) -> ClosedLoopStats:
        warnings = ["Closed loop scheduling is advisory; verifier-bound components supply outcomes."]
        return ClosedLoopStats(
            iteration=self.iteration,
            pending_count=len(self.pending),
            outcome_count=len(self.outcomes),
            event_count=len(self.events),
            terminal_form_distribution=dict(Counter(o.terminal_form for o in self.outcomes)),
            route_distribution=dict(Counter(o.route for o in self.outcomes if o.route)),
            warnings=warnings,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "beta": self.beta,
            "iteration": self.iteration,
            "pending": [p.to_dict() for p in self.pending],
            "outcomes": [o.to_dict() for o in self.outcomes],
            "events": [e.to_dict() for e in self.events],
            "last_tasks": [t.to_dict() for t in self._last_tasks],
            "stats": self.stats().to_dict(),
            "advisory": True,
        }

    def save_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def _event(
        self,
        kind: str | LoopEventKind,
        source: str | None = None,
        target: str | None = None,
        route: str | None = None,
        terminal_form: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        kind_value = kind.value if isinstance(kind, LoopEventKind) else str(kind)
        payload = [kind_value, source, target, route, terminal_form, len(self.events)]
        self.events.append(
            LoopEvent(
                event_id=content_id("closed_loop_event", payload),
                kind=kind_value,
                timestamp=_utc_now(),
                source=source,
                target=target,
                route=route,
                terminal_form=terminal_form,
                metadata=dict(metadata or {}),
            )
        )


def _replace_task_metadata(task: ScheduledTask, metadata: dict[str, Any]) -> ScheduledTask:
    data = task.to_dict()
    data["metadata"] = metadata
    return ScheduledTask(**data)

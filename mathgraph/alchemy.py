"""Alchemical process traces for advisory MathGraph discovery episodes.

An alchemical trace records transformation pressure around a claim. It is not a
certificate and it is not truth. A trace crosses the verifier boundary only when
it carries a canonical terminal form, a promoted certificate id, and an explicit
``PROMOTED_BY_VERIFIER`` step.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id


class AlchemicalPhase(str, Enum):
    RAW_MATTER = "RAW_MATTER"
    CALCINATION = "CALCINATION"
    SOLUTION = "SOLUTION"
    SUBLIMATION = "SUBLIMATION"
    DESCENSION = "DESCENSION"
    DISTILLATION = "DISTILLATION"
    COAGULATION = "COAGULATION"
    FIXATION = "FIXATION"
    CERATION = "CERATION"
    CONJUNCTION = "CONJUNCTION"
    MULTIPLICATION = "MULTIPLICATION"
    PROJECTION = "PROJECTION"
    PERFECTION = "PERFECTION"


class AlchemicalStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    PROMOTED_BY_VERIFIER = "PROMOTED_BY_VERIFIER"


@dataclass
class AlchemicalStep:
    phase: AlchemicalPhase
    status: AlchemicalStatus
    input_artifact_ids: tuple[str, ...] = ()
    output_artifact_ids: tuple[str, ...] = ()
    route: str | None = None
    verifier_boundary: str | None = None
    cost_units: float = 0.0
    residual_delta: int = 0
    compression_gain: float = 0.0
    failure_reason: str | None = None
    advisory_notes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "status": self.status.value,
            "input_artifact_ids": list(self.input_artifact_ids),
            "output_artifact_ids": list(self.output_artifact_ids),
            "route": self.route,
            "verifier_boundary": self.verifier_boundary,
            "cost_units": self.cost_units,
            "residual_delta": self.residual_delta,
            "compression_gain": self.compression_gain,
            "failure_reason": self.failure_reason,
            "advisory_notes": list(self.advisory_notes),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlchemicalStep":
        return cls(
            phase=AlchemicalPhase(str(data["phase"])),
            status=AlchemicalStatus(str(data["status"])),
            input_artifact_ids=tuple(str(x) for x in data.get("input_artifact_ids", ())),
            output_artifact_ids=tuple(str(x) for x in data.get("output_artifact_ids", ())),
            route=_optional_str(data.get("route")),
            verifier_boundary=_optional_str(data.get("verifier_boundary")),
            cost_units=float(data.get("cost_units", 0.0) or 0.0),
            residual_delta=int(data.get("residual_delta", 0) or 0),
            compression_gain=float(data.get("compression_gain", 0.0) or 0.0),
            failure_reason=_optional_str(data.get("failure_reason")),
            advisory_notes=tuple(str(x) for x in data.get("advisory_notes", ())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class AlchemicalTrace:
    trace_id: str
    claim_id: str | None = None
    agent_id: str | None = None
    episode_id: str | None = None
    steps: list[AlchemicalStep] = field(default_factory=list)
    terminal_form: TerminalForm | None = None
    promoted_certificate_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_step(self, step: AlchemicalStep | None = None, **kwargs: Any) -> AlchemicalStep:
        if step is None:
            step = AlchemicalStep(**kwargs)
        self.steps.append(step)
        return step

    def phases_seen(self) -> tuple[AlchemicalPhase, ...]:
        return tuple(step.phase for step in self.steps)

    def last_status(self) -> AlchemicalStatus | None:
        return self.steps[-1].status if self.steps else None

    def has_phase(self, phase: AlchemicalPhase | str) -> bool:
        phase_value = phase if isinstance(phase, AlchemicalPhase) else AlchemicalPhase(str(phase))
        return any(step.phase == phase_value for step in self.steps)

    def is_fixed(self) -> bool:
        return self.has_phase(AlchemicalPhase.FIXATION)

    def is_promoted(self) -> bool:
        return (
            self.terminal_form in set(TerminalForm)
            and bool(self.promoted_certificate_id)
            and any(step.status == AlchemicalStatus.PROMOTED_BY_VERIFIER for step in self.steps)
        )

    def advisory_only_steps(self) -> list[AlchemicalStep]:
        return [
            step
            for step in self.steps
            if step.status == AlchemicalStatus.ADVISORY_ONLY
            or step.status != AlchemicalStatus.PROMOTED_BY_VERIFIER
        ]

    def total_cost(self) -> float:
        return sum(step.cost_units for step in self.steps)

    def total_residual_delta(self) -> int:
        return sum(step.residual_delta for step in self.steps)

    def total_compression_gain(self) -> float:
        return sum(step.compression_gain for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "claim_id": self.claim_id,
            "agent_id": self.agent_id,
            "episode_id": self.episode_id,
            "steps": [step.to_dict() for step in self.steps],
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "promoted_certificate_id": self.promoted_certificate_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlchemicalTrace":
        return cls(
            trace_id=str(data["trace_id"]),
            claim_id=_optional_str(data.get("claim_id")),
            agent_id=_optional_str(data.get("agent_id")),
            episode_id=_optional_str(data.get("episode_id")),
            steps=[AlchemicalStep.from_dict(step) for step in data.get("steps", [])],
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            promoted_certificate_id=_optional_str(data.get("promoted_certificate_id")),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "AlchemicalTrace":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "AlchemicalTrace":
        return cls.from_json(line.strip())


def make_alchemical_trace_id(*parts: Any, **metadata: Any) -> str:
    """Return a deterministic content-hash id for an alchemical trace seed."""

    payload = {"parts": parts, "metadata": metadata}
    return content_id("alchemy_trace", payload, n=24)


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_terminal_form(value: Any) -> TerminalForm | None:
    if value in (None, ""):
        return None
    if isinstance(value, TerminalForm):
        return value
    return TerminalForm(str(value))

"""Lightweight agent policy memory and advisory H-tilt-lite scoring."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from mathgraph.certificates import TerminalForm


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"
    PRUNED = "PRUNED"


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    status: AgentStatus = AgentStatus.ACTIVE
    parent_agent_id: str | None = None
    policy_name: str = "default"
    resource_budget: float = 0.0
    preferred_routes: tuple[str, ...] = ()
    phase_strengths: dict[str, float] = field(default_factory=dict)
    taste_weights: dict[str, float] = field(default_factory=dict)
    scar_counts: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "parent_agent_id": self.parent_agent_id,
            "policy_name": self.policy_name,
            "resource_budget": self.resource_budget,
            "preferred_routes": list(self.preferred_routes),
            "phase_strengths": dict(self.phase_strengths),
            "taste_weights": dict(self.taste_weights),
            "scar_counts": dict(self.scar_counts),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentProfile":
        return cls(
            agent_id=str(data["agent_id"]),
            name=str(data["name"]),
            status=AgentStatus(str(data.get("status", AgentStatus.ACTIVE.value))),
            parent_agent_id=_optional_str(data.get("parent_agent_id")),
            policy_name=str(data.get("policy_name", "default")),
            resource_budget=float(data.get("resource_budget", 0.0) or 0.0),
            preferred_routes=tuple(str(x) for x in data.get("preferred_routes", ())),
            phase_strengths={str(k): float(v) for k, v in dict(data.get("phase_strengths", {})).items()},
            taste_weights={str(k): float(v) for k, v in dict(data.get("taste_weights", {})).items()},
            scar_counts={str(k): int(v) for k, v in dict(data.get("scar_counts", {})).items()},
            metadata=dict(data.get("metadata", {})),
        )


class AgentExperienceOutcome(str, Enum):
    VERIFIED_PROOF = "VERIFIED_PROOF"
    FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"
    RESIDUAL = "RESIDUAL"
    FAILED_SEARCH = "FAILED_SEARCH"
    INVALID_CANDIDATE = "INVALID_CANDIDATE"
    KNOWN_SKIPPED = "KNOWN_SKIPPED"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass
class AgentExperience:
    experience_id: str
    agent_id: str
    episode_id: str | None
    claim_id: str | None
    route: str | None
    phase: str | None
    outcome: AgentExperienceOutcome
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    obstruction_id: str | None = None
    cost_units: float = 0.0
    residual_delta: int = 0
    compression_gain: float = 0.0
    projection_gain: float = 0.0
    derived_amplification: float = 0.0
    verifier_boundary_crossed: bool = False
    scar_tags: tuple[str, ...] = ()
    taste_delta: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "agent_id": self.agent_id,
            "episode_id": self.episode_id,
            "claim_id": self.claim_id,
            "route": self.route,
            "phase": self.phase,
            "outcome": self.outcome.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "obstruction_id": self.obstruction_id,
            "cost_units": self.cost_units,
            "residual_delta": self.residual_delta,
            "compression_gain": self.compression_gain,
            "projection_gain": self.projection_gain,
            "derived_amplification": self.derived_amplification,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "scar_tags": list(self.scar_tags),
            "taste_delta": dict(self.taste_delta),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentExperience":
        return cls(
            experience_id=str(data["experience_id"]),
            agent_id=str(data["agent_id"]),
            episode_id=_optional_str(data.get("episode_id")),
            claim_id=_optional_str(data.get("claim_id")),
            route=_optional_str(data.get("route")),
            phase=_optional_str(data.get("phase")),
            outcome=AgentExperienceOutcome(str(data["outcome"])),
            terminal_form=_optional_terminal_form(data.get("terminal_form")),
            certificate_id=_optional_str(data.get("certificate_id")),
            obstruction_id=_optional_str(data.get("obstruction_id")),
            cost_units=float(data.get("cost_units", 0.0) or 0.0),
            residual_delta=int(data.get("residual_delta", 0) or 0),
            compression_gain=float(data.get("compression_gain", 0.0) or 0.0),
            projection_gain=float(data.get("projection_gain", 0.0) or 0.0),
            derived_amplification=float(data.get("derived_amplification", 0.0) or 0.0),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            scar_tags=tuple(str(x) for x in data.get("scar_tags", ())),
            taste_delta={str(k): float(v) for k, v in dict(data.get("taste_delta", {})).items()},
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "AgentExperience":
        return cls.from_dict(json.loads(text))

    def to_jsonl_line(self) -> str:
        return self.to_json() + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> "AgentExperience":
        return cls.from_json(line.strip())


@dataclass
class AgentBiography:
    profile: AgentProfile
    experiences: list[AgentExperience] = field(default_factory=list)

    def add_experience(self, exp: AgentExperience) -> None:
        if exp.agent_id != self.profile.agent_id:
            raise ValueError("experience agent_id does not match biography profile")
        self.experiences.append(exp)

    def total_cost(self) -> float:
        return sum(exp.cost_units for exp in self.experiences)

    def terminal_counts(self) -> dict[str, int]:
        return dict(Counter(exp.terminal_form.value for exp in self.experiences if exp.terminal_form))

    def route_yields(self) -> dict[str, dict[str, float]]:
        return _yield_summary(self.experiences, "route")

    def phase_yields(self) -> dict[str, dict[str, float]]:
        return _yield_summary(self.experiences, "phase")

    def scar_summary(self) -> dict[str, int]:
        counts = Counter(self.profile.scar_counts)
        for exp in self.experiences:
            counts.update(exp.scar_tags)
            if exp.outcome in {AgentExperienceOutcome.FAILED_SEARCH, AgentExperienceOutcome.INVALID_CANDIDATE}:
                counts[exp.outcome.value] += 1
                if exp.route:
                    counts[f"route:{exp.route}"] += 1
        return dict(sorted(counts.items()))

    def update_taste_from_experience(self, exp: AgentExperience, learning_rate: float = 0.1) -> dict[str, float]:
        signal = _experience_signal(exp)
        updates: dict[str, float] = {}
        for key in _taste_keys(exp):
            delta = float(learning_rate) * signal
            self.profile.taste_weights[key] = self.profile.taste_weights.get(key, 0.0) + delta
            updates[key] = delta
        for tag in exp.scar_tags:
            self.profile.scar_counts[tag] = self.profile.scar_counts.get(tag, 0) + 1
        if exp.outcome in {AgentExperienceOutcome.FAILED_SEARCH, AgentExperienceOutcome.INVALID_CANDIDATE}:
            self.profile.scar_counts[exp.outcome.value] = self.profile.scar_counts.get(exp.outcome.value, 0) + 1
            if exp.route:
                route_key = f"route:{exp.route}"
                self.profile.scar_counts[route_key] = self.profile.scar_counts.get(route_key, 0) + 1
        exp.taste_delta.update(updates)
        return updates

    def apply_budget_delta(self, delta: float) -> float:
        self.profile.resource_budget += float(delta)
        return self.profile.resource_budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "experiences": [exp.to_dict() for exp in self.experiences],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentBiography":
        return cls(
            profile=AgentProfile.from_dict(dict(data["profile"])),
            experiences=[AgentExperience.from_dict(exp) for exp in data.get("experiences", [])],
        )

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "AgentBiography":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for exp in self.experiences:
                handle.write(exp.to_jsonl_line())

    @classmethod
    def read_jsonl(cls, profile: AgentProfile, path: str | Path) -> "AgentBiography":
        experiences: list[AgentExperience] = []
        source = Path(path)
        if source.exists():
            with source.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        experiences.append(AgentExperience.from_jsonl_line(line))
        return cls(profile=profile, experiences=experiences)


@dataclass(frozen=True)
class HTiltLiteScore:
    route: str
    base_score: float
    taste_score: float
    scar_penalty: float
    cost_penalty: float
    projection_bonus: float
    compression_bonus: float
    final_score: float
    beta: float = 1.0
    explanation: tuple[str, ...] = ()


def score_route_htilt_lite(
    route: str,
    agent: AgentProfile | AgentBiography | None = None,
    base_score: float = 0.0,
    expected_cost: float = 0.0,
    expected_projection_gain: float = 0.0,
    expected_compression_gain: float = 0.0,
    beta: float = 1.0,
) -> HTiltLiteScore:
    """Score advisory route pressure from taste, scars, cost, and gains.

    This is scheduling pressure only. It does not promote claims, decide truth,
    or implement full spectral H-tilt; the spectral ``K = L - V`` formulation
    remains future work.
    """

    profile = agent.profile if isinstance(agent, AgentBiography) else agent
    route_key = f"route:{route}"
    taste_score = profile.taste_weights.get(route_key, 0.0) if profile else 0.0
    scar_count = profile.scar_counts.get(route_key, 0) if profile else 0
    scar_penalty = 0.25 * scar_count
    viability = (
        float(base_score)
        + taste_score
        + float(expected_projection_gain)
        + float(expected_compression_gain)
        - float(expected_cost)
        - scar_penalty
    )
    final_score = math.exp(max(-50.0, min(50.0, float(beta) * viability)))
    explanation = (
        "advisory_only",
        f"route_key={route_key}",
        f"scar_count={scar_count}",
        "full_spectral_h_tilt_future_work",
    )
    return HTiltLiteScore(
        route=route,
        base_score=float(base_score),
        taste_score=taste_score,
        scar_penalty=scar_penalty,
        cost_penalty=float(expected_cost),
        projection_bonus=float(expected_projection_gain),
        compression_bonus=float(expected_compression_gain),
        final_score=final_score,
        beta=float(beta),
        explanation=explanation,
    )


def _experience_signal(exp: AgentExperience) -> float:
    signal = 0.0
    if exp.outcome in {AgentExperienceOutcome.VERIFIED_PROOF, AgentExperienceOutcome.FINITE_COUNTERMODEL}:
        signal += 3.0
    elif exp.outcome == AgentExperienceOutcome.NAMED_OBSTRUCTION:
        signal += 1.5
    elif exp.outcome == AgentExperienceOutcome.KNOWN_SKIPPED:
        signal += 0.5
    elif exp.outcome == AgentExperienceOutcome.FAILED_SEARCH:
        signal -= 1.0
    elif exp.outcome == AgentExperienceOutcome.INVALID_CANDIDATE:
        signal -= 2.0
    signal += exp.compression_gain + exp.projection_gain + exp.derived_amplification
    signal -= 0.1 * exp.cost_units
    return signal


def _taste_keys(exp: AgentExperience) -> tuple[str, ...]:
    keys: list[str] = []
    if exp.route:
        keys.append(f"route:{exp.route}")
    if exp.phase:
        keys.append(f"phase:{exp.phase}")
    return tuple(keys)


def _yield_summary(experiences: list[AgentExperience], attr: str) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0.0, "verified": 0.0, "cost": 0.0})
    for exp in experiences:
        key = getattr(exp, attr)
        if not key:
            continue
        rows[str(key)]["count"] += 1.0
        rows[str(key)]["cost"] += exp.cost_units
        if exp.verifier_boundary_crossed:
            rows[str(key)]["verified"] += 1.0
    return {key: dict(value) for key, value in sorted(rows.items())}


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

"""Lightweight spectral H-tilt estimator over route telemetry.

The estimator turns advisory route telemetry into lightweight estimates of
transition structure L, killing pressure V, K=L-V, forward survival h,
structural support q, survivor distribution pi*, and multiplicative bridge
mu_beta. It is route pressure only: it is not a verifier, not a proof system,
and not authority for terminal truth.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.hashing import content_id
from mathgraph.route_telemetry import RouteTelemetryLedger, RouteTelemetryOutcome


BAD_OUTCOMES = {
    RouteTelemetryOutcome.VERIFIER_FAILED,
    RouteTelemetryOutcome.IMPORTER_REJECTED,
    RouteTelemetryOutcome.SEARCH_MISS,
    RouteTelemetryOutcome.ALIGNMENT_FAILED,
}


@dataclass
class SpectralHTiltConfig:
    beta: float = 1.0
    damping: float = 0.85
    kill_weight: float = 1.0
    support_smoothing: float = 1e-6
    max_iterations: int = 100
    tolerance: float = 1e-9
    normalize_each_step: bool = True
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "beta": self.beta,
            "damping": self.damping,
            "kill_weight": self.kill_weight,
            "support_smoothing": self.support_smoothing,
            "max_iterations": self.max_iterations,
            "tolerance": self.tolerance,
            "normalize_each_step": self.normalize_each_step,
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SpectralHTiltConfig":
        return cls(
            beta=float(data.get("beta", 1.0) or 1.0),
            damping=float(data.get("damping", 0.85) or 0.85),
            kill_weight=float(data.get("kill_weight", 1.0) or 1.0),
            support_smoothing=float(data.get("support_smoothing", 1e-6) or 1e-6),
            max_iterations=int(data.get("max_iterations", 100) or 100),
            tolerance=float(data.get("tolerance", 1e-9) or 1e-9),
            normalize_each_step=bool(data.get("normalize_each_step", True)),
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class SpectralStateEstimate:
    state: str
    support_q: float
    survival_h: float
    survivor_pi: float
    tilted_mu_beta: float
    kill_pressure: float
    outgoing_mass: float
    incoming_mass: float
    score: float
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "support_q": self.support_q,
            "survival_h": self.survival_h,
            "survivor_pi": self.survivor_pi,
            "tilted_mu_beta": self.tilted_mu_beta,
            "kill_pressure": self.kill_pressure,
            "outgoing_mass": self.outgoing_mass,
            "incoming_mass": self.incoming_mass,
            "score": self.score,
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SpectralStateEstimate":
        return cls(
            state=str(data["state"]),
            support_q=float(data.get("support_q", 0.0) or 0.0),
            survival_h=float(data.get("survival_h", 0.0) or 0.0),
            survivor_pi=float(data.get("survivor_pi", 0.0) or 0.0),
            tilted_mu_beta=float(data.get("tilted_mu_beta", 0.0) or 0.0),
            kill_pressure=float(data.get("kill_pressure", 0.0) or 0.0),
            outgoing_mass=float(data.get("outgoing_mass", 0.0) or 0.0),
            incoming_mass=float(data.get("incoming_mass", 0.0) or 0.0),
            score=float(data.get("score", 0.0) or 0.0),
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class SpectralHTiltEstimate:
    estimate_id: str
    config: SpectralHTiltConfig
    states: tuple[str, ...]
    transition_L: dict[str, dict[str, float]]
    killing_V: dict[str, float]
    generator_K: dict[str, dict[str, float]]
    state_estimates: list[SpectralStateEstimate]
    iterations: int
    converged: bool
    residual_error: float
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def top_states(self, n: int = 10) -> list[SpectralStateEstimate]:
        return sorted(self.state_estimates, key=lambda item: (-item.score, item.state))[:n]

    def state_score(self, state: str) -> float:
        for estimate in self.state_estimates:
            if estimate.state == state:
                return estimate.score
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimate_id": self.estimate_id,
            "config": self.config.to_dict(),
            "states": list(self.states),
            "transition_L": _copy_matrix(self.transition_L),
            "killing_V": dict(self.killing_V),
            "generator_K": _copy_matrix(self.generator_K),
            "state_estimates": [estimate.to_dict() for estimate in self.state_estimates],
            "iterations": self.iterations,
            "converged": self.converged,
            "residual_error": self.residual_error,
            "created_at": self.created_at,
            "advisory": self.advisory,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SpectralHTiltEstimate":
        return cls(
            estimate_id=str(data["estimate_id"]),
            config=SpectralHTiltConfig.from_dict(data.get("config", {})),
            states=tuple(str(state) for state in data.get("states", ())),
            transition_L=_matrix_from_dict(data.get("transition_L", {})),
            killing_V={str(k): float(v) for k, v in dict(data.get("killing_V", {})).items()},
            generator_K=_matrix_from_dict(data.get("generator_K", {})),
            state_estimates=[SpectralStateEstimate.from_dict(item) for item in data.get("state_estimates", [])],
            iterations=int(data.get("iterations", 0) or 0),
            converged=bool(data.get("converged", False)),
            residual_error=float(data.get("residual_error", 0.0) or 0.0),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            advisory=bool(data.get("advisory", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "SpectralHTiltEstimate":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "SpectralHTiltEstimate":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


def build_transition_matrix_from_ledger(
    ledger: RouteTelemetryLedger,
    *,
    smoothing: float = 1e-6,
) -> dict[str, dict[str, float]]:
    counts: dict[str, dict[str, float]] = {}
    states: set[str] = set()
    for event in ledger.events:
        source = event.from_state or event.route_kind.value
        target = event.to_state or event.outcome.value
        states.update({source, target})
        counts.setdefault(source, {})
        counts[source][target] = counts[source].get(target, 0.0) + 1.0
    if not states:
        return {}
    ordered_states = sorted(states)
    matrix: dict[str, dict[str, float]] = {}
    for source in ordered_states:
        row_counts = counts.get(source, {})
        row = {target: row_counts.get(target, 0.0) + smoothing for target in ordered_states}
        total = sum(row.values())
        if math.isclose(total, 0.0):
            matrix[source] = {target: 1.0 if target == source else 0.0 for target in ordered_states}
            continue
        matrix[source] = {target: value / total for target, value in row.items()}
    return matrix


def build_killing_pressure_from_ledger(
    ledger: RouteTelemetryLedger,
    *,
    kill_weight: float = 1.0,
    smoothing: float = 1e-6,
) -> dict[str, float]:
    totals: dict[str, float] = {}
    kills: dict[str, float] = {}
    for event in ledger.events:
        state = event.from_state or event.route_kind.value
        totals[state] = totals.get(state, 0.0) + 1.0
        if event.killed or event.outcome in BAD_OUTCOMES:
            kills[state] = kills.get(state, 0.0) + 1.0
    return {
        state: kill_weight * (kills.get(state, 0.0) + smoothing) / (total + smoothing)
        for state, total in sorted(totals.items())
    }


def build_generator_K(
    L: Mapping[str, Mapping[str, float]],
    V: Mapping[str, float],
) -> dict[str, dict[str, float]]:
    """Build a discrete approximation of K=L-V from telemetry estimates."""

    states = sorted(set(L) | {target for row in L.values() for target in row} | set(V))
    K: dict[str, dict[str, float]] = {}
    for source in states:
        row = {target: float(L.get(source, {}).get(target, 0.0)) for target in states}
        row[source] = row.get(source, 0.0) - float(V.get(source, 0.0))
        K[source] = row
    return K


def normalize_vector(v: Mapping[str, float]) -> dict[str, float]:
    if not v:
        return {}
    positives = {str(key): max(float(value), 0.0) for key, value in v.items()}
    total = sum(positives.values())
    if math.isclose(total, 0.0):
        uniform = 1.0 / len(positives)
        return {key: uniform for key in sorted(positives)}
    return {key: positives[key] / total for key in sorted(positives)}


def l1_error(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    keys = set(a) | set(b)
    return sum(abs(float(a.get(key, 0.0)) - float(b.get(key, 0.0))) for key in keys)


def multiply_matrix_vector(M: Mapping[str, Mapping[str, float]], v: Mapping[str, float]) -> dict[str, float]:
    states = sorted(set(M) | set(v) | {target for row in M.values() for target in row})
    return {
        source: sum(float(M.get(source, {}).get(target, 0.0)) * float(v.get(target, 0.0)) for target in states)
        for source in states
    }


def multiply_transpose_matrix_vector(M: Mapping[str, Mapping[str, float]], v: Mapping[str, float]) -> dict[str, float]:
    states = sorted(set(M) | set(v) | {target for row in M.values() for target in row})
    result = {state: 0.0 for state in states}
    for source in states:
        for target in states:
            result[target] += float(M.get(source, {}).get(target, 0.0)) * float(v.get(source, 0.0))
    return result


def estimate_right_survival_h(
    K: Mapping[str, Mapping[str, float]],
    states: Sequence[str],
    *,
    max_iterations: int,
    tolerance: float,
    damping: float,
) -> tuple[dict[str, float], int, bool, float]:
    """Estimate forward survival h from telemetry-derived K.

    This is an advisory estimator over telemetry-derived transition/killing
    data, not a formal spectral theorem.
    """

    return _iterate_positive(K, states, max_iterations=max_iterations, tolerance=tolerance, damping=damping, transpose=False)


def estimate_left_support_q(
    K: Mapping[str, Mapping[str, float]],
    states: Sequence[str],
    *,
    max_iterations: int,
    tolerance: float,
    damping: float,
) -> tuple[dict[str, float], int, bool, float]:
    """Estimate structural support q from telemetry-derived K.

    This is an advisory estimator over telemetry-derived transition/killing
    data, not a formal spectral theorem.
    """

    return _iterate_positive(K, states, max_iterations=max_iterations, tolerance=tolerance, damping=damping, transpose=True)


def compute_survivor_distribution(q: Mapping[str, float], h: Mapping[str, float]) -> dict[str, float]:
    states = sorted(set(q) | set(h))
    return normalize_vector({state: max(float(q.get(state, 0.0)), 0.0) * max(float(h.get(state, 0.0)), 0.0) for state in states})


def compute_multiplicative_bridge(q: Mapping[str, float], h: Mapping[str, float], beta: float) -> dict[str, float]:
    states = sorted(set(q) | set(h))
    return normalize_vector(
        {
            state: max(float(q.get(state, 0.0)), 0.0) * (max(float(h.get(state, 0.0)), 0.0) ** beta)
            for state in states
        }
    )


def estimate_spectral_htilt(
    ledger: RouteTelemetryLedger,
    *,
    config: SpectralHTiltConfig | None = None,
) -> SpectralHTiltEstimate:
    config = config or SpectralHTiltConfig()
    L = build_transition_matrix_from_ledger(ledger, smoothing=config.support_smoothing)
    V = build_killing_pressure_from_ledger(
        ledger,
        kill_weight=config.kill_weight,
        smoothing=config.support_smoothing,
    )
    K = build_generator_K(L, V)
    states = tuple(sorted(set(K) | {target for row in K.values() for target in row}))
    h, h_iterations, h_converged, h_error = estimate_right_survival_h(
        K,
        states,
        max_iterations=config.max_iterations,
        tolerance=config.tolerance,
        damping=config.damping,
    )
    q, q_iterations, q_converged, q_error = estimate_left_support_q(
        K,
        states,
        max_iterations=config.max_iterations,
        tolerance=config.tolerance,
        damping=config.damping,
    )
    pi_star = compute_survivor_distribution(q, h)
    mu_beta = compute_multiplicative_bridge(q, h, config.beta)
    estimates = [
        SpectralStateEstimate(
            state=state,
            support_q=q.get(state, 0.0),
            survival_h=h.get(state, 0.0),
            survivor_pi=pi_star.get(state, 0.0),
            tilted_mu_beta=mu_beta.get(state, 0.0),
            kill_pressure=V.get(state, 0.0),
            outgoing_mass=sum(L.get(state, {}).values()),
            incoming_mass=sum(row.get(state, 0.0) for row in L.values()),
            score=mu_beta.get(state, 0.0) + pi_star.get(state, 0.0) + h.get(state, 0.0) + q.get(state, 0.0) - V.get(state, 0.0),
            advisory=True,
            metadata={"advisory_only": True, "not_truth_authority": True},
        )
        for state in states
    ]
    estimates.sort(key=lambda item: (-item.score, item.state))
    payload = {
        "ledger_id": ledger.ledger_id,
        "config": config.to_dict(),
        "states": states,
        "L": L,
        "V": V,
        "K": K,
        "state_estimates": [estimate.to_dict() for estimate in estimates],
    }
    return SpectralHTiltEstimate(
        estimate_id=content_id("spectral_htilt_estimate", payload, n=24),
        config=config,
        states=states,
        transition_L=L,
        killing_V=V,
        generator_K=K,
        state_estimates=estimates,
        iterations=max(h_iterations, q_iterations),
        converged=h_converged and q_converged,
        residual_error=max(h_error, q_error),
        advisory=True,
        metadata={
            "full_spectral_h_tilt_estimated": True,
            "advisory_only": True,
            "not_truth_authority": True,
            "telemetry_based": True,
            "no_verifier_authority": True,
            "approximation": "pure_python_positive_iteration",
        },
    )


def route_priorities_from_estimate(
    estimate: SpectralHTiltEstimate,
    *,
    route_prefixes: Sequence[str] = (),
    top_n: int | None = None,
) -> list[tuple[str, float]]:
    prefixes = tuple(route_prefixes)
    rows = [
        (state.state, state.score)
        for state in estimate.state_estimates
        if not prefixes or state.state.startswith(prefixes)
    ]
    rows.sort(key=lambda item: (-item[1], item[0]))
    if top_n is not None:
        return rows[:top_n]
    return rows


def _iterate_positive(
    K: Mapping[str, Mapping[str, float]],
    states: Sequence[str],
    *,
    max_iterations: int,
    tolerance: float,
    damping: float,
    transpose: bool,
) -> tuple[dict[str, float], int, bool, float]:
    ordered = tuple(sorted(str(state) for state in states))
    if not ordered:
        return {}, 0, True, 0.0
    uniform = {state: 1.0 / len(ordered) for state in ordered}
    current = dict(uniform)
    error = 0.0
    for iteration in range(1, max_iterations + 1):
        multiplied = multiply_transpose_matrix_vector(K, current) if transpose else multiply_matrix_vector(K, current)
        positive = {state: max(multiplied.get(state, 0.0), 0.0) for state in ordered}
        next_vector = {
            state: damping * positive.get(state, 0.0) + (1.0 - damping) * uniform[state]
            for state in ordered
        }
        next_vector = normalize_vector(next_vector)
        error = l1_error(current, next_vector)
        current = next_vector
        if error <= tolerance:
            return current, iteration, True, error
    return current, max_iterations, False, error


def _copy_matrix(matrix: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]:
    return {str(row): {str(col): float(value) for col, value in cols.items()} for row, cols in matrix.items()}


def _matrix_from_dict(data: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    return {str(row): {str(col): float(value) for col, value in dict(cols).items()} for row, cols in dict(data).items()}

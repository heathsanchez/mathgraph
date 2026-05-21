"""Smoothed advisory route priors for sparse MathGraph outcome data."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Sequence

from mathgraph.outcome_dataset import PairOutcome, extract_pair_features
from mathgraph.route_learner import ROUTE_FAMILIES
from mathgraph.terminal_schema import terminal_form_from_legacy


@dataclass(frozen=True)
class SmoothedRoutePriorConfig:
    alpha: float = 1.0
    min_entropy: float = 0.50
    exploration_weight: float = 0.15
    failure_penalty: float = 0.10
    diversity_floor: float = 0.05


@dataclass(frozen=True)
class SmoothedRoutePrior:
    route_scores: dict[str, float]
    route_probabilities: dict[str, float]
    route_counts: dict[str, int]
    route_successes: dict[str, int]
    route_failures: dict[str, int]
    entropy: float
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_scores": dict(self.route_scores),
            "route_probabilities": dict(self.route_probabilities),
            "route_counts": dict(self.route_counts),
            "route_successes": dict(self.route_successes),
            "route_failures": dict(self.route_failures),
            "entropy": self.entropy,
            "warnings": list(self.warnings),
            "advisory": True,
        }


def _outcome_route(outcome: PairOutcome | dict[str, Any]) -> str | None:
    if isinstance(outcome, PairOutcome):
        return outcome.route
    return outcome.get("route")


def _outcome_terminal(outcome: PairOutcome | dict[str, Any]) -> str:
    if isinstance(outcome, PairOutcome):
        return outcome.terminal_form
    return str(outcome.get("terminal_form", "NONE"))


def _outcome_status(outcome: PairOutcome | dict[str, Any]) -> str:
    if isinstance(outcome, PairOutcome):
        return outcome.verification_status
    return str(outcome.get("verification_status", ""))


def _is_success(outcome: PairOutcome | dict[str, Any]) -> bool:
    form = terminal_form_from_legacy(_outcome_terminal(outcome))
    status = _outcome_status(outcome).upper()
    return form.value in {"VERIFIED_PROOF", "REFUTATION_CERTIFICATE"} and (
        "VERIFIED" in status or "REFUTED" in status
    )


def _is_failure(outcome: PairOutcome | dict[str, Any]) -> bool:
    status = _outcome_status(outcome).upper()
    form = terminal_form_from_legacy(_outcome_terminal(outcome))
    return form.value == "NAMED_OBSTRUCTION" or "FAILED" in status or "REJECTED" in status


def _normalized_entropy(probabilities: dict[str, float]) -> float:
    if len(probabilities) <= 1:
        return 0.0
    entropy = -sum(p * math.log(p) for p in probabilities.values() if p > 0)
    return entropy / math.log(len(probabilities))


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    total = sum(max(score, 0.0) for score in scores.values())
    if total <= 0:
        n = max(len(scores), 1)
        return {route: 1.0 / n for route in scores}
    return {route: max(score, 0.0) / total for route, score in scores.items()}


def build_smoothed_route_prior(
    outcomes: Sequence[PairOutcome | dict[str, Any]],
    route_families: Sequence[str] | None = None,
    config: SmoothedRoutePriorConfig | None = None,
) -> SmoothedRoutePrior:
    cfg = config or SmoothedRoutePriorConfig()
    routes = list(route_families or ROUTE_FAMILIES)
    if not routes:
        routes = ["route_probe"]
    counts: Counter[str] = Counter({route: 0 for route in routes})
    successes: Counter[str] = Counter({route: 0 for route in routes})
    failures: Counter[str] = Counter({route: 0 for route in routes})
    for outcome in outcomes:
        route = _outcome_route(outcome)
        if not route:
            continue
        if route not in counts:
            routes.append(route)
            counts[route] = 0
            successes[route] = 0
            failures[route] = 0
        counts[route] += 1
        if _is_success(outcome):
            successes[route] += 1
        elif _is_failure(outcome):
            failures[route] += 1
    scores: dict[str, float] = {}
    for route in routes:
        count = counts[route]
        success = successes[route]
        failure = failures[route]
        base = (success + cfg.alpha) / (count + 2.0 * cfg.alpha)
        exploration = cfg.exploration_weight / (1.0 + count)
        score = max(base - cfg.failure_penalty * failure + exploration, cfg.diversity_floor)
        scores[route] = score
    probabilities = _normalize(scores)
    entropy = _normalized_entropy(probabilities)
    warnings: list[str] = ["Route prior is advisory scheduling pressure, not truth."]
    if entropy < cfg.min_entropy and len(routes) > 1:
        uniform = {route: 1.0 / len(routes) for route in routes}
        for _ in range(20):
            probabilities = {
                route: 0.9 * probabilities[route] + 0.1 * uniform[route]
                for route in routes
            }
            entropy = _normalized_entropy(probabilities)
            if entropy >= cfg.min_entropy:
                break
        warnings.append("Route probabilities were mixed with uniform mass to avoid sparse-data collapse.")
    return SmoothedRoutePrior(
        route_scores=scores,
        route_probabilities=probabilities,
        route_counts=dict(counts),
        route_successes=dict(successes),
        route_failures=dict(failures),
        entropy=entropy,
        warnings=warnings,
    )


def recommend_route_with_prior(
    source: str,
    target: str,
    outcomes: Sequence[PairOutcome | dict[str, Any]],
    route_families: Sequence[str] | None = None,
    config: SmoothedRoutePriorConfig | None = None,
) -> dict[str, Any]:
    prior = build_smoothed_route_prior(outcomes, route_families=route_families, config=config)
    route, probability = max(
        prior.route_probabilities.items(),
        key=lambda item: (item[1], item[0]),
    )
    return {
        "source": source,
        "target": target,
        "features": extract_pair_features(source, target),
        "recommended_route": route,
        "probability": probability,
        "entropy": prior.entropy,
        "route_probabilities": dict(prior.route_probabilities),
        "warnings": list(prior.warnings),
        "advisory": True,
    }

"""Deterministic route success model over MathGraph pair outcomes."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.outcome_dataset import PairOutcome, extract_pair_features


ROUTE_FAMILIES = [
    "finite_countermodel",
    "variable_identification",
    "skeleton_preserving_relabel",
    "broad_split_to_skeleton_preserving_relabel",
    "direct_substitution_instance",
]

SUCCESS_STATUSES = {"VERIFIED", "REFUTED", "LEAN_VERIFIED", "FINITE_VERIFIED"}
SUCCESS_TRUST = {"lean_verified", "finite_verified", "derived_from_verified_traces"}


@dataclass(frozen=True)
class RouteBasinKey:
    route: str
    source_var_bucket: str
    target_var_bucket: str
    op_delta_bucket: str
    len_delta_bucket: str
    new_target_vars_bucket: str
    skeleton_bucket: str
    repeat_bucket: str

    def to_dict(self) -> dict[str, str]:
        return {
            "route": self.route,
            "source_var_bucket": self.source_var_bucket,
            "target_var_bucket": self.target_var_bucket,
            "op_delta_bucket": self.op_delta_bucket,
            "len_delta_bucket": self.len_delta_bucket,
            "new_target_vars_bucket": self.new_target_vars_bucket,
            "skeleton_bucket": self.skeleton_bucket,
            "repeat_bucket": self.repeat_bucket,
        }


@dataclass(frozen=True)
class RoutePolicyCard:
    basin_key: dict[str, str]
    support_count: int
    route: str
    success_count: int
    failure_count: int
    unknown_count: int
    verified_true_count: int
    verified_false_count: int
    derived_count: int
    primitive_count: int
    success_rate: float
    false_rate: float
    true_rate: float
    derived_rate: float
    confidence: float
    recommended_task_kind: str
    warnings: list[str]
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "basin_key": dict(self.basin_key),
            "support_count": self.support_count,
            "route": self.route,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "unknown_count": self.unknown_count,
            "verified_true_count": self.verified_true_count,
            "verified_false_count": self.verified_false_count,
            "derived_count": self.derived_count,
            "primitive_count": self.primitive_count,
            "success_rate": self.success_rate,
            "false_rate": self.false_rate,
            "true_rate": self.true_rate,
            "derived_rate": self.derived_rate,
            "confidence": self.confidence,
            "recommended_task_kind": self.recommended_task_kind,
            "warnings": list(self.warnings),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class RouteLearnerStats:
    outcome_count: int
    usable_outcome_count: int
    route_count: int
    basin_count: int
    policy_card_count: int
    by_route: dict[str, dict[str, int]]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_count": self.outcome_count,
            "usable_outcome_count": self.usable_outcome_count,
            "route_count": self.route_count,
            "basin_count": self.basin_count,
            "policy_card_count": self.policy_card_count,
            "by_route": self.by_route,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class RouteRecommendation:
    source: str
    target: str
    features: dict[str, Any]
    candidate_cards: list[dict[str, Any]]
    recommended_route: str | None
    recommended_task_kind: str
    confidence: float
    reason_codes: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "features": dict(self.features),
            "candidate_cards": list(self.candidate_cards),
            "recommended_route": self.recommended_route,
            "recommended_task_kind": self.recommended_task_kind,
            "confidence": self.confidence,
            "reason_codes": list(self.reason_codes),
            "warnings": list(self.warnings),
        }


def make_basin_key(route: str, features: dict[str, Any]) -> RouteBasinKey:
    return RouteBasinKey(
        route=route,
        source_var_bucket=_var_bucket(features.get("source_var_count", 0)),
        target_var_bucket=_var_bucket(features.get("target_var_count", 0)),
        op_delta_bucket=_op_delta_bucket(features.get("op_delta", 0)),
        len_delta_bucket=_len_delta_bucket(features.get("len_delta", 0)),
        new_target_vars_bucket=_new_vars_bucket(features.get("new_target_vars", [])),
        skeleton_bucket=_skeleton_bucket(features),
        repeat_bucket=_repeat_bucket(features),
    )


class RouteLearner:
    def __init__(self, outcomes: list[PairOutcome] | list[dict[str, Any]]) -> None:
        self.outcomes = [_coerce_outcome(outcome) for outcome in outcomes]
        self._policy_cards: list[RoutePolicyCard] | None = None

    def build_policy_cards(self, min_support: int = 1) -> list[RoutePolicyCard]:
        buckets: dict[tuple[str, ...], list[PairOutcome]] = defaultdict(list)
        for outcome in self._usable_outcomes():
            key = make_basin_key(str(outcome.route), outcome.features)
            buckets[tuple(key.to_dict().values())].append(outcome)
        cards = [
            _policy_card(make_basin_key(outcomes[0].route or "", outcomes[0].features), outcomes)
            for outcomes in buckets.values()
            if len(outcomes) >= min_support
        ]
        cards.sort(key=lambda card: (-card.confidence, -card.support_count, card.route))
        self._policy_cards = cards
        return cards

    def stats(self) -> RouteLearnerStats:
        usable = self._usable_outcomes()
        by_route: dict[str, Counter[str]] = defaultdict(Counter)
        basins = set()
        for outcome in usable:
            route = str(outcome.route)
            by_route[route]["count"] += 1
            if _is_success(outcome):
                by_route[route]["success"] += 1
            elif _is_unknown(outcome):
                by_route[route]["unknown"] += 1
            else:
                by_route[route]["failure"] += 1
            basins.add(tuple(make_basin_key(route, outcome.features).to_dict().values()))
        cards = self._policy_cards if self._policy_cards is not None else self.build_policy_cards()
        warnings = []
        if not usable:
            warnings.append("No routed outcomes available for route learning.")
        return RouteLearnerStats(
            outcome_count=len(self.outcomes),
            usable_outcome_count=len(usable),
            route_count=len(by_route),
            basin_count=len(basins),
            policy_card_count=len(cards),
            by_route={route: dict(counts) for route, counts in by_route.items()},
            warnings=warnings,
        )

    def recommend(self, source: str, target: str, top_k: int = 5) -> RouteRecommendation:
        features = extract_pair_features(source, target)
        cards = self._policy_cards if self._policy_cards is not None else self.build_policy_cards()
        exact = []
        for route in ROUTE_FAMILIES:
            basin = make_basin_key(route, features).to_dict()
            exact.extend(card for card in cards if card.basin_key == basin)
        reason_codes = ["exact_basin_match"] if exact else []
        candidates = exact
        if not candidates:
            aggregates = self._route_aggregate_cards()
            candidates = list(aggregates.values())
            if candidates:
                reason_codes.append("route_level_fallback")
        candidates.sort(key=lambda card: (-card.confidence, -card.support_count, card.route))
        top = candidates[:top_k]
        if not top:
            return RouteRecommendation(
                source=source,
                target=target,
                features=features,
                candidate_cards=[],
                recommended_route=None,
                recommended_task_kind="route_probe",
                confidence=0.0,
                reason_codes=["no_policy_card_available"],
                warnings=_recommendation_warnings(),
            )
        best = top[0]
        return RouteRecommendation(
            source=source,
            target=target,
            features=features,
            candidate_cards=[card.to_dict() for card in top],
            recommended_route=best.route,
            recommended_task_kind=best.recommended_task_kind,
            confidence=best.confidence,
            reason_codes=reason_codes,
            warnings=_recommendation_warnings(),
        )

    def save_policy_cards_json(self, path: str | Path) -> None:
        cards = self._policy_cards if self._policy_cards is not None else self.build_policy_cards()
        _write_json([card.to_dict() for card in cards], path)

    def save_policy_cards_jsonl(self, path: str | Path) -> None:
        cards = self._policy_cards if self._policy_cards is not None else self.build_policy_cards()
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for card in cards:
                handle.write(json.dumps(card.to_dict(), sort_keys=True) + "\n")

    def save_stats_json(self, path: str | Path) -> None:
        _write_json(self.stats().to_dict(), path)

    def _usable_outcomes(self) -> list[PairOutcome]:
        return [outcome for outcome in self.outcomes if outcome.route]

    def _route_aggregate_cards(self) -> dict[str, RoutePolicyCard]:
        grouped: dict[str, list[PairOutcome]] = defaultdict(list)
        for outcome in self._usable_outcomes():
            grouped[str(outcome.route)].append(outcome)
        cards = {}
        for route, outcomes in grouped.items():
            basin = RouteBasinKey(
                route=route,
                source_var_bucket="any",
                target_var_bucket="any",
                op_delta_bucket="any",
                len_delta_bucket="any",
                new_target_vars_bucket="any",
                skeleton_bucket="any",
                repeat_bucket="any",
            )
            cards[route] = _policy_card(basin, outcomes)
        return cards


def _policy_card(key: RouteBasinKey, outcomes: list[PairOutcome]) -> RoutePolicyCard:
    support = len(outcomes)
    success = sum(1 for outcome in outcomes if _is_success(outcome))
    unknown = sum(1 for outcome in outcomes if _is_unknown(outcome))
    failure = support - success - unknown
    true_count = sum(1 for outcome in outcomes if outcome.terminal_form == "VERIFIED_PROOF")
    false_count = sum(1 for outcome in outcomes if outcome.terminal_form == "FINITE_COUNTERMODEL")
    derived = sum(1 for outcome in outcomes if outcome.origin == "derived_certificate")
    primitive = sum(1 for outcome in outcomes if outcome.origin == "primitive_trace")
    success_rate = success / support if support else 0.0
    false_rate = false_count / support if support else 0.0
    true_rate = true_count / support if support else 0.0
    derived_rate = derived / support if support else 0.0
    confidence = success_rate * (support / (support + 5)) if support else 0.0
    return RoutePolicyCard(
        basin_key=key.to_dict(),
        support_count=support,
        route=key.route,
        success_count=success,
        failure_count=failure,
        unknown_count=unknown,
        verified_true_count=true_count,
        verified_false_count=false_count,
        derived_count=derived,
        primitive_count=primitive,
        success_rate=success_rate,
        false_rate=false_rate,
        true_rate=true_rate,
        derived_rate=derived_rate,
        confidence=confidence,
        recommended_task_kind=_recommended_task_kind(key.route, success_rate, false_rate, true_rate, support),
        warnings=[
            "Route policy cards are advisory scheduling evidence, not proof.",
            "Do not promote without verified proof or finite countermodel.",
        ],
        evidence={
            "pair_ids": [outcome.pair_id for outcome in outcomes[:10]],
            "origins": dict(Counter(outcome.origin for outcome in outcomes)),
            "trust_levels": dict(Counter(outcome.trust_level for outcome in outcomes)),
        },
    )


def _recommended_task_kind(
    route: str, success_rate: float, false_rate: float, true_rate: float, support: int
) -> str:
    if "countermodel" in route or false_rate > true_rate:
        return "finite_countermodel_search"
    if route in {
        "variable_identification",
        "direct_substitution_instance",
        "skeleton_preserving_relabel",
        "broad_split_to_skeleton_preserving_relabel",
    }:
        return "proof_template"
    if success_rate < 0.25 and support >= 1:
        return "obstruction_analysis"
    return "route_probe"


def _is_success(outcome: PairOutcome) -> bool:
    return (
        outcome.terminal_form in {"VERIFIED_PROOF", "FINITE_COUNTERMODEL"}
        or outcome.verification_status in SUCCESS_STATUSES
        or outcome.trust_level in SUCCESS_TRUST
    )


def _is_unknown(outcome: PairOutcome) -> bool:
    return outcome.trust_level in {"advisory_only", "unknown"} or outcome.verification_status == "UNKNOWN"


def _coerce_outcome(outcome: PairOutcome | dict[str, Any]) -> PairOutcome:
    return outcome if isinstance(outcome, PairOutcome) else PairOutcome.from_dict(outcome)


def _var_bucket(value: Any) -> str:
    count = int(value or 0)
    if count <= 0:
        return "v0"
    if count == 1:
        return "v1"
    if count == 2:
        return "v2"
    if count == 3:
        return "v3"
    return "v4plus"


def _op_delta_bucket(value: Any) -> str:
    delta = int(value or 0)
    if delta < 0:
        return "op_down"
    if delta == 0:
        return "op_same"
    if delta == 1:
        return "op_up_1"
    return "op_up_2plus"


def _len_delta_bucket(value: Any) -> str:
    delta = int(value or 0)
    if delta < 0:
        return "len_down"
    if delta == 0:
        return "len_same"
    if delta <= 10:
        return "len_up_small"
    return "len_up_large"


def _new_vars_bucket(value: Any) -> str:
    count = len(value or [])
    if count == 0:
        return "no_new_target_vars"
    if count == 1:
        return "one_new_target_var"
    return "many_new_target_vars"


def _skeleton_bucket(features: dict[str, Any]) -> str:
    if features.get("same_text"):
        return "same_text"
    if features.get("same_skeleton_rough"):
        return "same_skeleton"
    return "different_skeleton"


def _repeat_bucket(features: dict[str, Any]) -> str:
    if not features.get("target_has_repeated_vars"):
        return "target_no_repeat"
    if features.get("source_has_repeated_vars"):
        return "target_repeat_source_repeat"
    return "target_repeat_source_no_repeat"


def _recommendation_warnings() -> list[str]:
    return [
        "Route recommendation is advisory only.",
        "Do not promote without verified proof or finite countermodel.",
    ]


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

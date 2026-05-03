"""Deterministic H-Tilt v1 scheduler for certificate work queues."""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.kernel_oracle import KernelOracle, OracleAnswer
from mathgraph.outcome_dataset import PairOutcome, extract_pair_features
from mathgraph.route_learner import (
    ROUTE_FAMILIES,
    RouteLearner,
    RoutePolicyCard,
    RouteRecommendation,
    make_basin_key,
)


@dataclass(frozen=True)
class SchedulerInputPair:
    source: str
    target: str
    source_idx: int | None = None
    target_idx: int | None = None
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

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
    def from_dict(cls, data: dict[str, Any]) -> "SchedulerInputPair":
        return cls(
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            label=data.get("label"),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class HTiltScoreBreakdown:
    route_prior: float
    novelty_score: float
    gap_score: float
    uncertainty_score: float
    obstruction_pressure: float
    derived_amplification_potential: float
    corpus_value: float
    final_score: float
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_prior": self.route_prior,
            "novelty_score": self.novelty_score,
            "gap_score": self.gap_score,
            "uncertainty_score": self.uncertainty_score,
            "obstruction_pressure": self.obstruction_pressure,
            "derived_amplification_potential": self.derived_amplification_potential,
            "corpus_value": self.corpus_value,
            "final_score": self.final_score,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class ScheduledTask:
    task_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    label: str | None
    recommended_route: str | None
    recommended_task_kind: str
    priority: float
    htilt_score: float
    score_breakdown: dict[str, Any]
    route_recommendation: dict[str, Any] | None
    oracle_status: str
    terminal_form: str | None
    verification_status: str | None
    warnings: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "label": self.label,
            "recommended_route": self.recommended_route,
            "recommended_task_kind": self.recommended_task_kind,
            "priority": self.priority,
            "htilt_score": self.htilt_score,
            "score_breakdown": dict(self.score_breakdown),
            "route_recommendation": self.route_recommendation,
            "oracle_status": self.oracle_status,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class HTiltSchedulerStats:
    input_count: int
    scheduled_count: int
    skipped_known_count: int
    unknown_count: int
    by_task_kind: dict[str, int]
    by_recommended_route: dict[str, int]
    max_priority: float
    mean_priority: float
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_count": self.input_count,
            "scheduled_count": self.scheduled_count,
            "skipped_known_count": self.skipped_known_count,
            "unknown_count": self.unknown_count,
            "by_task_kind": dict(self.by_task_kind),
            "by_recommended_route": dict(self.by_recommended_route),
            "max_priority": self.max_priority,
            "mean_priority": self.mean_priority,
            "warnings": list(self.warnings),
        }


class HTiltScheduler:
    def __init__(
        self,
        oracle: KernelOracle | None = None,
        route_learner: RouteLearner | None = None,
        policy_cards: list[RoutePolicyCard] | list[dict[str, Any]] | None = None,
        outcomes: list[PairOutcome] | list[dict[str, Any]] | None = None,
        beta: float = 1.0,
    ) -> None:
        self.oracle = oracle
        self.beta = float(beta)
        if route_learner is not None:
            self.route_learner = route_learner
        elif outcomes is not None:
            self.route_learner = RouteLearner(outcomes)
            self.route_learner.build_policy_cards()
        else:
            self.route_learner = None
        self.policy_cards = [_coerce_policy_card(card) for card in (policy_cards or [])]
        self._last_input_count = 0
        self._last_skipped_known_count = 0

    def schedule(
        self,
        pairs: list[SchedulerInputPair] | list[dict[str, Any]],
        top_k: int | None = None,
        skip_known: bool = True,
    ) -> list[ScheduledTask]:
        input_pairs = [_coerce_pair(pair) for pair in pairs]
        self._last_input_count = len(input_pairs)
        self._last_skipped_known_count = 0
        tasks: list[ScheduledTask] = []
        for pair in input_pairs:
            answer = self._oracle_query(pair)
            if skip_known and _is_known(answer):
                self._last_skipped_known_count += 1
                continue
            tasks.append(self.score_pair(pair))
        tasks.sort(key=lambda task: (-task.htilt_score, task.source, task.target))
        if top_k is not None:
            tasks = tasks[: int(top_k)]
        max_score = max((task.htilt_score for task in tasks), default=0.0)
        if max_score > 0:
            tasks = [_replace_priority(task, task.htilt_score / max_score) for task in tasks]
        return tasks

    def score_pair(self, pair: SchedulerInputPair) -> ScheduledTask:
        pair = _coerce_pair(pair)
        features = extract_pair_features(pair.source, pair.target)
        oracle_answer = self._oracle_query(pair)
        recommendation = self._recommend(pair.source, pair.target)
        route_prior = recommendation.confidence if recommendation is not None else 0.25
        route_prior = min(max(route_prior, 0.0), 1.0)
        novelty = self._novelty_score(pair, features)
        gap = _gap_score(features)
        uncertainty = max(1.0 - route_prior, 0.15)
        task_kind = (
            "known_certificate_review"
            if _is_known(oracle_answer)
            else (recommendation.recommended_task_kind if recommendation else "route_probe")
        )
        obstruction = _obstruction_pressure(task_kind, gap, route_prior)
        amplification = _derived_amplification(pair, recommendation, route_prior)
        corpus_value = (
            0.30 * route_prior
            + 0.20 * uncertainty
            + 0.20 * gap
            + 0.20 * amplification
            + 0.10 * novelty
        )
        final_score = math.exp(self.beta * corpus_value)
        reasons = _reason_codes(route_prior, novelty, gap, uncertainty, obstruction, amplification)
        if _is_known(oracle_answer):
            reasons.append("exact_oracle_hit")
            corpus_value = 0.0
            final_score = 0.0
        breakdown = HTiltScoreBreakdown(
            route_prior=route_prior,
            novelty_score=novelty,
            gap_score=gap,
            uncertainty_score=uncertainty,
            obstruction_pressure=obstruction,
            derived_amplification_potential=amplification,
            corpus_value=corpus_value,
            final_score=final_score,
            reason_codes=reasons,
        )
        rec_dict = recommendation.to_dict() if recommendation is not None else None
        return ScheduledTask(
            task_id=content_id(
                "htilt_task",
                {
                    "source": pair.source,
                    "target": pair.target,
                    "route": recommendation.recommended_route if recommendation else None,
                    "task_kind": task_kind,
                },
            ),
            source=pair.source,
            target=pair.target,
            source_idx=pair.source_idx,
            target_idx=pair.target_idx,
            label=pair.label,
            recommended_route=recommendation.recommended_route if recommendation else None,
            recommended_task_kind=task_kind,
            priority=0.0,
            htilt_score=final_score,
            score_breakdown=breakdown.to_dict(),
            route_recommendation=rec_dict,
            oracle_status=oracle_answer.status if oracle_answer else "UNKNOWN",
            terminal_form=oracle_answer.terminal_form if oracle_answer else None,
            verification_status=oracle_answer.verification_status if oracle_answer else None,
            warnings=[
                "H-Tilt priority is scheduling pressure, not truth.",
                "Do not promote without verified proof or finite countermodel.",
            ],
            metadata={**pair.metadata, "features": features},
        )

    def stats(self, tasks: list[ScheduledTask]) -> HTiltSchedulerStats:
        priorities = [task.priority for task in tasks]
        warnings = []
        if not tasks:
            warnings.append("No tasks scheduled.")
        return HTiltSchedulerStats(
            input_count=self._last_input_count or len(tasks),
            scheduled_count=len(tasks),
            skipped_known_count=self._last_skipped_known_count,
            unknown_count=sum(1 for task in tasks if task.oracle_status == "UNKNOWN"),
            by_task_kind=dict(Counter(task.recommended_task_kind for task in tasks)),
            by_recommended_route=dict(Counter(task.recommended_route for task in tasks if task.recommended_route)),
            max_priority=max(priorities, default=0.0),
            mean_priority=(sum(priorities) / len(priorities)) if priorities else 0.0,
            warnings=warnings,
        )

    def save_tasks_json(self, path: str | Path, tasks: list[ScheduledTask]) -> None:
        _write_json([task.to_dict() for task in tasks], path)

    def save_tasks_jsonl(self, path: str | Path, tasks: list[ScheduledTask]) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for task in tasks:
                handle.write(json.dumps(task.to_dict(), sort_keys=True) + "\n")

    def save_stats_json(self, path: str | Path, stats: HTiltSchedulerStats) -> None:
        _write_json(stats.to_dict(), path)

    def _oracle_query(self, pair: SchedulerInputPair) -> OracleAnswer | None:
        if self.oracle is None:
            return None
        return self.oracle.query(pair.source, pair.target)

    def _recommend(self, source: str, target: str) -> RouteRecommendation | None:
        if self.route_learner is not None:
            return self.route_learner.recommend(source, target)
        if self.policy_cards:
            return _recommend_from_cards(self.policy_cards, source, target)
        return None

    def _novelty_score(self, pair: SchedulerInputPair, features: dict[str, Any]) -> float:
        score = 0.5
        if pair.source_idx is None:
            score += 0.2
        if pair.target_idx is None:
            score += 0.2
        if not self._shape_seen(features):
            score += 0.1
        return min(score, 1.0)

    def _shape_seen(self, features: dict[str, Any]) -> bool:
        cards = self.policy_cards
        if self.route_learner is not None:
            cards = self.route_learner.build_policy_cards()
        for route in ROUTE_FAMILIES:
            basin = make_basin_key(route, features).to_dict()
            if any(card.basin_key == basin for card in cards):
                return True
        return False


def _recommend_from_cards(
    cards: list[RoutePolicyCard], source: str, target: str
) -> RouteRecommendation:
    features = extract_pair_features(source, target)
    exact: list[RoutePolicyCard] = []
    for route in ROUTE_FAMILIES:
        basin = make_basin_key(route, features).to_dict()
        exact.extend(card for card in cards if card.basin_key == basin)
    candidates = exact or _aggregate_cards(cards)
    candidates.sort(key=lambda card: (-card.confidence, -card.support_count, card.route))
    if not candidates:
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
    best = candidates[0]
    return RouteRecommendation(
        source=source,
        target=target,
        features=features,
        candidate_cards=[card.to_dict() for card in candidates[:5]],
        recommended_route=best.route,
        recommended_task_kind=best.recommended_task_kind,
        confidence=best.confidence,
        reason_codes=["exact_basin_match"] if exact else ["route_level_fallback"],
        warnings=_recommendation_warnings(),
    )


def _aggregate_cards(cards: list[RoutePolicyCard]) -> list[RoutePolicyCard]:
    best: dict[str, RoutePolicyCard] = {}
    for card in cards:
        current = best.get(card.route)
        if current is None or card.confidence > current.confidence:
            best[card.route] = card
    return list(best.values())


def _gap_score(features: dict[str, Any]) -> float:
    score = 0.0
    if features.get("new_target_vars"):
        score += 0.25
    if int(features.get("op_delta", 0)) > 0:
        score += 0.25
    if int(features.get("len_delta", 0)) > 0:
        score += 0.15
    if not features.get("same_skeleton_rough") and not features.get("same_text"):
        score += 0.15
    return min(score, 1.0)


def _obstruction_pressure(task_kind: str, gap_score: float, route_prior: float) -> float:
    score = 0.0
    if task_kind == "obstruction_analysis":
        score += 0.55
    if gap_score >= 0.5 and route_prior <= 0.35:
        score += 0.35
    return min(score, 1.0)


def _derived_amplification(
    pair: SchedulerInputPair, recommendation: RouteRecommendation | None, route_prior: float
) -> float:
    score = 0.0
    if pair.source_idx is not None:
        score += 0.25
    if pair.target_idx is not None:
        score += 0.25
    if recommendation and recommendation.recommended_route == "finite_countermodel":
        score += 0.25
    if route_prior >= 0.5:
        score += 0.25
    return min(score, 1.0)


def _reason_codes(
    route_prior: float,
    novelty: float,
    gap: float,
    uncertainty: float,
    obstruction: float,
    amplification: float,
) -> list[str]:
    reasons = []
    if route_prior >= 0.5:
        reasons.append("high_route_prior")
    if gap >= 0.5:
        reasons.append("high_gap_score")
    if uncertainty >= 0.6:
        reasons.append("high_uncertainty")
    if amplification >= 0.5:
        reasons.append("high_derived_amplification")
    if novelty >= 0.8:
        reasons.append("novel_shape")
    if obstruction >= 0.5:
        reasons.append("obstruction_pressure")
    return reasons


def _replace_priority(task: ScheduledTask, priority: float) -> ScheduledTask:
    return ScheduledTask(**{**task.to_dict(), "priority": priority})


def _is_known(answer: OracleAnswer | None) -> bool:
    return answer is not None and answer.status in {"VERIFIED", "REFUTED"}


def _coerce_pair(pair: SchedulerInputPair | dict[str, Any]) -> SchedulerInputPair:
    return pair if isinstance(pair, SchedulerInputPair) else SchedulerInputPair.from_dict(pair)


def _coerce_policy_card(card: RoutePolicyCard | dict[str, Any]) -> RoutePolicyCard:
    if isinstance(card, RoutePolicyCard):
        return card
    return RoutePolicyCard(
        basin_key=dict(card["basin_key"]),
        support_count=int(card["support_count"]),
        route=str(card["route"]),
        success_count=int(card["success_count"]),
        failure_count=int(card.get("failure_count", 0)),
        unknown_count=int(card.get("unknown_count", 0)),
        verified_true_count=int(card.get("verified_true_count", 0)),
        verified_false_count=int(card.get("verified_false_count", 0)),
        derived_count=int(card.get("derived_count", 0)),
        primitive_count=int(card.get("primitive_count", 0)),
        success_rate=float(card.get("success_rate", 0.0)),
        false_rate=float(card.get("false_rate", 0.0)),
        true_rate=float(card.get("true_rate", 0.0)),
        derived_rate=float(card.get("derived_rate", 0.0)),
        confidence=float(card.get("confidence", 0.0)),
        recommended_task_kind=str(card.get("recommended_task_kind", "route_probe")),
        warnings=list(card.get("warnings", [])),
        evidence=dict(card.get("evidence", {})),
    )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _recommendation_warnings() -> list[str]:
    return [
        "Route recommendation is advisory only.",
        "Do not promote without verified proof or finite countermodel.",
    ]


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

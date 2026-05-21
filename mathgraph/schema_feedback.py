"""Feedback scoring for advisory Reason Atlas entries."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Sequence


@dataclass(frozen=True)
class FeedbackScoringConfig:
    support_weight: float = 0.15
    transfer_success_weight: float = 1.0
    verifier_success_weight: float = 0.8
    residual_compression_weight: float = 0.30
    deletion_hurt_weight: float = 0.75
    breadth_weight: float = 0.20
    failure_penalty: float = 0.65
    obstruction_penalty: float = 0.35
    deletion_safe_penalty: float = 0.40
    decay_per_day: float = 0.01
    deprecate_failure_rate: float = 0.75
    min_events_for_deprecation: int = 4


def compute_transfer_rate(entry: Any) -> float:
    successes = int(getattr(entry, "transfer_successes", 0) or 0)
    failures = int(getattr(entry, "transfer_failures", 0) or 0)
    total = successes + failures
    return successes / total if total else 0.0


def compute_verifier_rate(entry: Any) -> float:
    successes = int(getattr(entry, "verifier_successes", 0) or 0)
    failures = int(getattr(entry, "verifier_failures", 0) or 0)
    total = successes + failures
    return successes / total if total else 0.0


def compute_obstruction_penalty(entry: Any) -> float:
    return float(getattr(entry, "obstruction_count", 0) or 0)


def compute_deletion_value(entry: Any) -> float:
    return float(getattr(entry, "deletion_hurt_count", 0) or 0) - float(getattr(entry, "deletion_safe_count", 0) or 0)


def compute_decay_multiplier(entry: Any, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    updated = _parse_ts(getattr(entry, "updated_at", "")) or now
    age_days = max(0.0, (now - updated).total_seconds() / 86400.0)
    stored_decay = float(getattr(entry, "decay", 1.0) or 1.0)
    return max(0.1, stored_decay * (1.0 / (1.0 + age_days * FeedbackScoringConfig().decay_per_day)))


def compute_priority_score(entry: Any, config: FeedbackScoringConfig | None = None) -> float:
    cfg = config or FeedbackScoringConfig()
    breadth = int(getattr(entry, "family_count", 0) or 0) + int(getattr(entry, "root_count", 0) or 0)
    positive = (
        cfg.support_weight * int(getattr(entry, "support", 0) or 0)
        + cfg.transfer_success_weight * int(getattr(entry, "transfer_successes", 0) or 0)
        + cfg.verifier_success_weight * int(getattr(entry, "verifier_successes", 0) or 0)
        + cfg.residual_compression_weight * float(getattr(entry, "residual_compression_total", 0.0) or 0.0)
        + cfg.deletion_hurt_weight * int(getattr(entry, "deletion_hurt_count", 0) or 0)
        + cfg.breadth_weight * breadth
    )
    negative = (
        cfg.failure_penalty
        * (int(getattr(entry, "transfer_failures", 0) or 0) + int(getattr(entry, "verifier_failures", 0) or 0))
        + cfg.obstruction_penalty * int(getattr(entry, "obstruction_count", 0) or 0)
        + cfg.deletion_safe_penalty * int(getattr(entry, "deletion_safe_count", 0) or 0)
    )
    return max(0.0, (positive - negative) * compute_decay_multiplier(entry))


def compute_promotion_score(entry: Any, config: FeedbackScoringConfig | None = None) -> float:
    priority = compute_priority_score(entry, config)
    transfer = compute_transfer_rate(entry)
    verifier = compute_verifier_rate(entry)
    return max(0.0, priority * (0.5 + 0.3 * transfer + 0.2 * verifier))


def summarize_feedback_events(events: Sequence[Any]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for event in events:
        outcome = str(getattr(event, "outcome", ""))
        if hasattr(getattr(event, "outcome", None), "value"):
            outcome = event.outcome.value
        summary[outcome] = summary.get(outcome, 0) + 1
    return summary


def apply_feedback_to_entry(entry: Any, feedback_event: Any, config: FeedbackScoringConfig | None = None) -> Any:
    outcome = getattr(feedback_event, "outcome", "")
    outcome_value = outcome.value if hasattr(outcome, "value") else str(outcome)
    residual_delta = float(getattr(feedback_event, "residual_delta", 0.0) or 0.0)
    updates = {
        "support": int(getattr(entry, "support", 0) or 0),
        "transfer_successes": int(getattr(entry, "transfer_successes", 0) or 0),
        "transfer_failures": int(getattr(entry, "transfer_failures", 0) or 0),
        "verifier_successes": int(getattr(entry, "verifier_successes", 0) or 0),
        "verifier_failures": int(getattr(entry, "verifier_failures", 0) or 0),
        "obstruction_count": int(getattr(entry, "obstruction_count", 0) or 0),
        "residual_compression_total": float(getattr(entry, "residual_compression_total", 0.0) or 0.0),
        "deletion_hurt_count": int(getattr(entry, "deletion_hurt_count", 0) or 0),
        "deletion_safe_count": int(getattr(entry, "deletion_safe_count", 0) or 0),
    }
    if outcome_value == "TRANSFER_SUCCESS":
        updates["transfer_successes"] += 1
        updates["support"] += 1
    elif outcome_value == "TRANSFER_FAILURE":
        updates["transfer_failures"] += 1
    elif outcome_value == "VERIFIER_SUCCESS":
        updates["verifier_successes"] += 1
    elif outcome_value == "VERIFIER_FAILURE":
        updates["verifier_failures"] += 1
    elif outcome_value == "OBSTRUCTION_FOUND":
        updates["obstruction_count"] += 1
    elif outcome_value == "RESIDUAL_COMPRESSED":
        updates["residual_compression_total"] += max(0.0, residual_delta)
    elif outcome_value == "RESIDUAL_EXPANDED":
        updates["residual_compression_total"] -= abs(residual_delta)
    elif outcome_value == "DELETION_HURT":
        updates["deletion_hurt_count"] += 1
    elif outcome_value == "DELETION_SAFE":
        updates["deletion_safe_count"] += 1
    scored = replace(entry, **updates)
    return replace(
        scored,
        priority_score=compute_priority_score(scored, config),
        promotion_score=compute_promotion_score(scored, config),
        updated_at=_utc_now(),
        advisory_only=True,
        verifier_promoted=False,
    )


def should_deprecate_entry(entry: Any, config: FeedbackScoringConfig | None = None) -> bool:
    cfg = config or FeedbackScoringConfig()
    failures = int(getattr(entry, "transfer_failures", 0) or 0) + int(getattr(entry, "verifier_failures", 0) or 0)
    successes = int(getattr(entry, "transfer_successes", 0) or 0) + int(getattr(entry, "verifier_successes", 0) or 0)
    total = failures + successes
    return total >= cfg.min_events_for_deprecation and failures / total >= cfg.deprecate_failure_rate


def should_promote_advisory_entry(entry: Any, config: FeedbackScoringConfig | None = None) -> bool:
    return bool(getattr(entry, "advisory_only", True)) and compute_promotion_score(entry, config) > 1.0


def residual_compression_delta(before: int | float, after: int | float) -> float:
    return float(before) - float(after)


def oracle_fraction_captured(base_rate: float, candidate_rate: float, oracle_rate: float) -> float:
    gap = max(0.0, float(oracle_rate) - float(base_rate))
    if gap <= 0:
        return 0.0
    return max(0.0, float(candidate_rate) - float(base_rate)) / gap


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None

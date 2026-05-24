"""Standard metrics for the Compounding Lawbook Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from typing import Any


@dataclass(frozen=True)
class CompoundingMetrics:
    baseline_yield: float
    lawbook_yield: float
    htilt_yield: float
    attempts: float
    residual_before: float
    residual_after: float
    lawbook_hits: float
    lawbook_queries: float
    action_changes: float
    decode_successes: float
    decode_total: float
    advisory_boundary_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        attempts = max(float(self.attempts), 1.0)
        baseline = float(self.baseline_yield)
        lawbook = float(self.lawbook_yield)
        htilt = float(self.htilt_yield)
        residual_reduction = float(self.residual_before) - float(self.residual_after)
        return {
            "baseline_yield": baseline,
            "lawbook_yield": lawbook,
            "htilt_yield": htilt,
            "certificates_per_attempt": htilt / attempts,
            "residual_reduction": residual_reduction,
            "attempt_efficiency_gain": (lawbook + htilt - baseline) / attempts,
            "lawbook_hit_rate": self.lawbook_hits / self.lawbook_queries if self.lawbook_queries else 0.0,
            "lawbook_action_change_rate": self.action_changes / self.lawbook_queries if self.lawbook_queries else 0.0,
            "decode_success_rate": self.decode_successes / self.decode_total if self.decode_total else 0.0,
            "projection_gain": max(0.0, htilt - baseline),
            "cost_per_certificate": attempts / htilt if htilt else attempts,
            "episode_to_episode_gain": htilt - baseline,
            "advisory_boundary_preserved": self.advisory_boundary_preserved,
            "compounding_signal_detected": (htilt > baseline or residual_reduction > 0) and self.advisory_boundary_preserved,
            "metadata": dict(self.metadata),
        }


def compute_compounding_metrics(**kwargs: Any) -> dict[str, Any]:
    return CompoundingMetrics(**kwargs).to_dict()


def yield_rate(recovered: int, total: int) -> float:
    return float(recovered) / float(total) if total else 0.0


def residual_count(recovered: int, total: int) -> int:
    return max(0, int(total) - int(recovered))


def true_contamination_count(rows: Any) -> int:
    data = _records(rows)
    return sum(int(row.get("true_contamination_count", 0) or 0) for row in data)


def obstruction_entropy(rows: Any, key: str = "basin") -> float:
    data = _records(rows)
    counts: dict[str, int] = {}
    for row in data:
        value = str(row.get(key, "unknown") or "unknown")
        counts[value] = counts.get(value, 0) + 1
    total = sum(counts.values())
    if not total:
        return 0.0
    return -sum((count / total) * log2(count / total) for count in counts.values())


def named_obstruction_count(rows: Any) -> int:
    return len({str(row.get("obstruction_name") or row.get("obstruction_id")) for row in _records(rows) if row.get("obstruction_name") or row.get("obstruction_id")})


def constructor_family_compression(used_families: Any, total_families: Any) -> float:
    used = {str(x) for x in _iter_values(used_families) if str(x)}
    total = {str(x) for x in _iter_values(total_families) if str(x)}
    return 1.0 - (len(used) / len(total)) if total else 0.0


def marginal_gain_curve(values: Any) -> list[dict[str, float]]:
    nums = [float(v) for v in _iter_values(values)]
    out: list[dict[str, float]] = []
    previous = 0.0
    for i, value in enumerate(nums):
        out.append({"step": i, "value": value, "marginal_gain": value - previous})
        previous = value
    return out


def lawbook_reuse_rate(hits: int, queries: int) -> float:
    return int(hits) / int(queries) if queries else 0.0


def episode_lift_vs_baseline(episode_value: float, baseline_value: float) -> float:
    return float(episode_value) - float(baseline_value)


def episode_lift_vs_previous(episode_value: float, previous_value: float) -> float:
    return float(episode_value) - float(previous_value)


def summarize_episode_metrics(policy_rows: Any, obstruction_rows: Any, constructor_rows: Any) -> dict[str, Any]:
    policies = _records(policy_rows)
    best = max((float(row.get("yield_rate", 0.0) or 0.0) for row in policies), default=0.0)
    generic = max((float(row.get("yield_rate", 0.0) or 0.0) for row in policies if row.get("policy") in {"generic", "baseline"}), default=0.0)
    return {
        "best_yield_rate": best,
        "generic_yield_rate": generic,
        "episode_lift_vs_baseline": episode_lift_vs_baseline(best, generic),
        "true_contamination_count": true_contamination_count(policies),
        "obstruction_entropy": obstruction_entropy(obstruction_rows),
        "named_obstruction_count": named_obstruction_count(obstruction_rows),
        "constructor_family_count": len({str(row.get("family")) for row in _records(constructor_rows) if row.get("family")}),
    }


def _records(rows: Any) -> list[dict[str, Any]]:
    if rows is None:
        return []
    if hasattr(rows, "to_dict"):
        try:
            records = rows.to_dict("records")
            if isinstance(records, list):
                return [dict(row) for row in records]
        except TypeError:
            pass
    return [dict(row) for row in rows]


def _iter_values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]

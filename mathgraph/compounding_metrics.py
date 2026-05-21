"""Standard metrics for the Compounding Lawbook Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
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

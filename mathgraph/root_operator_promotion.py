"""Promotion metrics for advisory root operator schemas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from mathgraph.root_operator_schema import RootOperatorPromotionResult, RootOperatorSchema


@dataclass(frozen=True)
class RootOperatorPromotionConfig:
    min_support: int = 2
    min_solve_rate_gain: float = 0.01
    min_oracle_fraction_captured: float = 0.05
    min_residual_compression: int = 1
    min_promotion_score: float = 0.05


def score_schema_on_tasks(
    schema: RootOperatorSchema,
    tasks: Sequence[dict[str, Any]],
    evaluate_with_schema: Callable[[RootOperatorSchema, Sequence[dict[str, Any]]], dict[str, Any]],
    evaluate_base: Callable[[Sequence[dict[str, Any]]], dict[str, Any]],
    evaluate_oracle: Callable[[Sequence[dict[str, Any]]], dict[str, Any]],
) -> RootOperatorPromotionResult:
    base = evaluate_base(tasks)
    schema_metrics = evaluate_with_schema(schema, tasks)
    oracle = evaluate_oracle(tasks)
    base_rate = float(base.get("solve_rate", 0.0) or 0.0)
    schema_rate = float(schema_metrics.get("solve_rate", 0.0) or 0.0)
    oracle_rate = float(oracle.get("solve_rate", 0.0) or 0.0)
    gain = schema_rate - base_rate
    oracle_gap = max(0.0, oracle_rate - base_rate)
    oracle_fraction = gain / oracle_gap if oracle_gap > 0 else 0.0
    residual_base = int(base.get("residual_count", max(0, len(tasks) - int(base_rate * len(tasks)))) or 0)
    residual_schema = int(schema_metrics.get("residual_count", max(0, len(tasks) - int(schema_rate * len(tasks)))) or 0)
    residual_compression = max(0, residual_base - residual_schema)
    score = root_operator_law_score(gain, oracle_fraction, residual_compression, schema)
    promoted = score > 0
    scored_schema = schema.with_promotion(
        promotion_score=score,
        promoted=promoted,
        compression_gain_est=max(schema.compression_gain_est, float(residual_compression)),
    )
    return RootOperatorPromotionResult(
        schema=scored_schema,
        promoted=promoted,
        promotion_score=score,
        solve_rate_gain=gain,
        residual_compression=residual_compression,
        oracle_fraction_captured=oracle_fraction,
        reasons=tuple(_promotion_reasons(gain, oracle_fraction, residual_compression, schema, promoted)),
    )


def promote_root_operator_schemas(
    schemas: Sequence[RootOperatorSchema],
    tasks: Sequence[dict[str, Any]],
    evaluate_with_schema: Callable[[RootOperatorSchema, Sequence[dict[str, Any]]], dict[str, Any]],
    evaluate_base: Callable[[Sequence[dict[str, Any]]], dict[str, Any]],
    evaluate_oracle: Callable[[Sequence[dict[str, Any]]], dict[str, Any]],
    config: RootOperatorPromotionConfig | None = None,
) -> list[RootOperatorPromotionResult]:
    cfg = config or RootOperatorPromotionConfig()
    results = []
    for schema in schemas:
        result = score_schema_on_tasks(schema, tasks, evaluate_with_schema, evaluate_base, evaluate_oracle)
        passes = (
            schema.support >= cfg.min_support
            and result.solve_rate_gain >= cfg.min_solve_rate_gain
            and result.oracle_fraction_captured >= cfg.min_oracle_fraction_captured
            and result.residual_compression >= cfg.min_residual_compression
            and result.promotion_score >= cfg.min_promotion_score
        )
        results.append(
            RootOperatorPromotionResult(
                schema=result.schema.with_promotion(promotion_score=result.promotion_score, promoted=passes),
                promoted=passes,
                promotion_score=result.promotion_score,
                solve_rate_gain=result.solve_rate_gain,
                residual_compression=result.residual_compression,
                oracle_fraction_captured=result.oracle_fraction_captured,
                reasons=result.reasons if passes else tuple(list(result.reasons) + ["promotion_threshold_not_met"]),
            )
        )
    return sorted(results, key=lambda item: (-item.promotion_score, item.schema.compact_name))


def residual_compression_metrics(base_metrics: dict[str, Any], improved_metrics: dict[str, Any]) -> dict[str, Any]:
    base = int(base_metrics.get("residual_count", 0) or 0)
    improved = int(improved_metrics.get("residual_count", 0) or 0)
    compressed = max(0, base - improved)
    return {
        "base_residual_count": base,
        "improved_residual_count": improved,
        "residual_count_compressed": compressed,
        "compression_fraction": compressed / base if base else 0.0,
    }


def oracle_fraction_captured(base_solve_rate: float, improved_solve_rate: float, oracle_solve_rate: float) -> float:
    gap = max(0.0, oracle_solve_rate - base_solve_rate)
    if gap <= 0:
        return 0.0
    return max(0.0, improved_solve_rate - base_solve_rate) / gap


def root_operator_law_score(
    solve_rate_gain: float,
    oracle_fraction: float,
    residual_compression: int,
    schema: RootOperatorSchema,
) -> float:
    complexity_penalty = 0.02 * max(0, len(schema.atoms) - 2) + 0.01 * len(schema.parameters)
    support_bonus = min(schema.support, 10) * 0.01
    return max(0.0, solve_rate_gain + 0.5 * oracle_fraction + 0.02 * residual_compression + support_bonus - complexity_penalty)


def _promotion_reasons(
    gain: float,
    oracle_fraction: float,
    residual_compression: int,
    schema: RootOperatorSchema,
    promoted: bool,
) -> list[str]:
    reasons = []
    if gain > 0:
        reasons.append("solve_rate_improved")
    if oracle_fraction > 0:
        reasons.append("oracle_gap_partially_captured")
    if residual_compression > 0:
        reasons.append("residuals_compressed")
    if schema.support > 1:
        reasons.append("multi_trace_support")
    if not promoted:
        reasons.append("score_nonpositive")
    return reasons

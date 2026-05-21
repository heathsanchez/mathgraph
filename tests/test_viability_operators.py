import math

from mathgraph.viability_operators import (
    compute_composite_v,
    compute_constructor_deadend_v,
    compute_failure_density_v,
    compute_rejection_pressure_v,
    compute_residual_persistence_v,
    score_viability_operator,
)


def _rows():
    return [
        {"constructor": "a", "status": "rejected", "rejected": True, "promotion_gate_rejected": 1, "residual": True},
        {"constructor": "a", "status": "rejected", "rejected": True, "promotion_gate_rejected": 1, "residual": True},
        {"constructor": "b", "status": "accepted", "accepted": True, "promotion_gate_accepted": 1},
        {"constructor": "b", "status": "rejected", "rejected": True, "promotion_gate_rejected": 1},
    ]


def test_null_v_returns_constant_finite_scores():
    scores = score_viability_operator(_rows(), "null_v")
    assert {s.normalized_score for s in scores} == {0.5}
    assert all(math.isfinite(s.raw_score) for s in scores)


def test_random_v_is_deterministic_under_seed():
    a = [s.to_dict() for s in score_viability_operator(_rows(), "random_v")]
    b = [s.to_dict() for s in score_viability_operator(_rows(), "random_v")]
    assert a == b


def test_failure_and_rejection_pressure_increase_with_failures():
    failure = {s.item_id: s.normalized_score for s in compute_failure_density_v(_rows())}
    rejection = {s.item_id: s.normalized_score for s in compute_rejection_pressure_v(_rows())}
    assert failure["a"] > failure["b"]
    assert rejection["a"] > rejection["b"]


def test_residual_and_deadend_penalize_failed_constructors():
    residual = {s.item_id: s.normalized_score for s in compute_residual_persistence_v(_rows())}
    deadend = {s.item_id: s.normalized_score for s in compute_constructor_deadend_v(_rows())}
    assert residual["a"] > residual["b"]
    assert deadend["a"] > deadend["b"]


def test_composite_v_is_advisory_and_non_terminal():
    scores = compute_composite_v(_rows())
    assert scores
    assert all(s.advisory_only for s in scores)
    assert all(not s.emits_terminal_truth for s in scores)
    assert all(math.isfinite(s.normalized_score) for s in scores)

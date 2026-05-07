from mathgraph.metabolic_diagnostics import (
    compute_derived_amplification_factor,
    compute_residual_compression_gain,
    evaluate_better_shaped_unknown,
)


def test_residual_compression_gain():
    assert compute_residual_compression_gain(10, 4) == 0.6
    assert compute_residual_compression_gain(0, 4) == 0.0
    assert compute_residual_compression_gain(5, 8) == 0.0


def test_derived_amplification_factor():
    assert compute_derived_amplification_factor(4, 2) == 0.5
    assert compute_derived_amplification_factor(0, 3) == 3.0
    assert compute_derived_amplification_factor(0, 0) == 0.0


def test_better_shaped_unknown_decisions():
    assert evaluate_better_shaped_unknown({"unresolved_before": 5, "unresolved_after": 3})[0]
    assert evaluate_better_shaped_unknown(
        {"obstructions_added": 2, "residuals_grouped_by_signature": True}
    )[0]
    assert not evaluate_better_shaped_unknown(
        {"unresolved_before": 5, "unresolved_after": 5, "obstructions_added": 0}
    )[0]


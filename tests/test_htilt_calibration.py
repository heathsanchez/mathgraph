from mathgraph.htilt_calibration import (
    calibrate_htilt_operator,
    compare_htilt_operators,
    compute_effective_dimension,
    compute_survivor_entropy,
    compute_tv_distance_to_uniform,
    select_best_v_operator,
)


def _rows():
    return [
        {"constructor": "a", "status": "rejected", "rejected": True, "promotion_gate_rejected": 1, "residual": True},
        {"constructor": "a", "status": "rejected", "rejected": True, "promotion_gate_rejected": 1, "residual": True},
        {"constructor": "b", "status": "accepted", "accepted": True, "promotion_gate_accepted": 1},
        {"constructor": "c", "status": "accepted", "accepted": True, "promotion_gate_accepted": 1},
    ]


def test_calibration_produces_survivor_metrics():
    result = calibrate_htilt_operator(_rows(), "failure_density_v")
    assert result.advisory_boundary_ok is True
    assert result.effective_dimension > 0
    assert result.normalized_entropy >= 0
    assert result.tv_distance_to_uniform >= 0


def test_entropy_dimension_and_tv_are_finite():
    dist = {"a": 0.7, "b": 0.3}
    assert compute_survivor_entropy(dist) <= 1
    assert compute_effective_dimension(dist) > 1
    assert compute_tv_distance_to_uniform(dist) > 0


def test_strong_v_is_more_concentrated_than_null_v():
    null = calibrate_htilt_operator(_rows(), "null_v")
    strong = calibrate_htilt_operator(_rows(), "failure_density_v")
    assert strong.max_mass >= null.max_mass


def test_compare_and_select_prefers_higher_law_score():
    report = compare_htilt_operators(_rows(), ["null_v", "failure_density_v"], law_scores={"null_v": 1.0, "failure_density_v": 2.0})
    assert report.selected_best_operator == "failure_density_v"
    selected = select_best_v_operator(report.results)
    assert selected.operator_kind == "failure_density_v"

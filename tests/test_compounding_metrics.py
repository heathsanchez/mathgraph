from mathgraph.compounding_metrics import (
    constructor_family_compression,
    lawbook_reuse_rate,
    marginal_gain_curve,
    named_obstruction_count,
    obstruction_entropy,
    residual_count,
    yield_rate,
)


def test_basic_compounding_metrics_are_json_like():
    assert yield_rate(3, 4) == 0.75
    assert residual_count(3, 4) == 1
    assert lawbook_reuse_rate(2, 4) == 0.5
    assert constructor_family_compression(["a"], ["a", "b"]) == 0.5


def test_obstruction_metrics_count_and_entropy():
    rows = [
        {"obstruction_name": "a", "basin": "x"},
        {"obstruction_name": "b", "basin": "x"},
        {"obstruction_name": "c", "basin": "y"},
    ]

    assert named_obstruction_count(rows) == 3
    assert obstruction_entropy(rows) > 0


def test_marginal_gain_curve():
    curve = marginal_gain_curve([1, 3, 6])

    assert [row["marginal_gain"] for row in curve] == [1.0, 2.0, 3.0]

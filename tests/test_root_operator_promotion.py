from mathgraph.root_operator_induction import anti_unify_trace_group
from mathgraph.root_operator_promotion import (
    oracle_fraction_captured,
    promote_root_operator_schemas,
    residual_compression_metrics,
)


def _schema():
    return anti_unify_trace_group(
        [
            {"trace_id": "t1", "atoms": [{"name": "move", "kind": "spatial", "params": {"axis": "x"}}]},
            {"trace_id": "t2", "atoms": [{"name": "move", "kind": "spatial", "params": {"axis": "y"}}]},
        ]
    )


def test_promotion_score_positive_when_solve_rate_improves():
    schema = _schema()
    tasks = [{"task_id": "a"}, {"task_id": "b"}]
    results = promote_root_operator_schemas(
        [schema],
        tasks,
        lambda _schema, _tasks: {"solve_rate": 1.0, "residual_count": 0},
        lambda _tasks: {"solve_rate": 0.0, "residual_count": 2},
        lambda _tasks: {"solve_rate": 1.0, "residual_count": 0},
    )
    assert results[0].promotion_score > 0
    assert results[0].promoted is True


def test_oracle_fraction_captured_computed_correctly():
    assert abs(oracle_fraction_captured(0.2, 0.6, 1.0) - 0.5) < 1e-9


def test_residual_compression_computed_correctly():
    metrics = residual_compression_metrics({"residual_count": 10}, {"residual_count": 4})
    assert metrics["residual_count_compressed"] == 6


def test_promoted_schemas_remain_advisory_only():
    result = promote_root_operator_schemas(
        [_schema()],
        [{"task_id": "a"}],
        lambda _schema, _tasks: {"solve_rate": 1.0, "residual_count": 0},
        lambda _tasks: {"solve_rate": 0.0, "residual_count": 1},
        lambda _tasks: {"solve_rate": 1.0, "residual_count": 0},
    )[0]
    assert result.schema.advisory_only is True
    assert result.schema.verifier_promoted is False


def test_no_truth_terminal_status_is_emitted():
    result = promote_root_operator_schemas(
        [_schema()],
        [{"task_id": "a"}],
        lambda _schema, _tasks: {"solve_rate": 1.0, "residual_count": 0},
        lambda _tasks: {"solve_rate": 0.0, "residual_count": 1},
        lambda _tasks: {"solve_rate": 1.0, "residual_count": 0},
    )[0]
    assert result.to_dict()["terminal_form"] is None

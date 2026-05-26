import pandas as pd

from mathgraph.source_law_repair import (
    compute_repair_cell_pressure,
    find_source_violations,
    propose_repair_moves,
    repair_conditioned_constructors,
    run_source_law_repair,
    target_violation_preserved,
    touched_cells_for_assignment,
)


BAD_RIGHT_PROJECTION = [[0, 1], [0, 1]]
LEFT_PROJECTION = [[0, 0], [1, 1]]


def test_find_source_violations_returns_violations_on_bad_table():
    violations = find_source_violations(BAD_RIGHT_PROJECTION, "(x * y) = x")
    assert violations
    assert violations[0].touched_cells


def test_find_source_violations_empty_on_source_satisfying_table():
    assert find_source_violations(LEFT_PROJECTION, "(x * y) = x") == []


def test_touched_cells_for_assignment_is_deterministic():
    first = touched_cells_for_assignment(BAD_RIGHT_PROJECTION, "(x * y) = x", {"x": 0, "y": 1})
    second = touched_cells_for_assignment(BAD_RIGHT_PROJECTION, "(x * y) = x", {"x": 0, "y": 1})
    assert first == second == [(0, 1)]


def test_target_violation_preserved_detects_preserved_and_destroyed():
    assert target_violation_preserved(BAD_RIGHT_PROJECTION, "x = y", {"x": 0, "y": 1})
    assert not target_violation_preserved(BAD_RIGHT_PROJECTION, "x = y", {"x": 0, "y": 0})


def test_compute_repair_cell_pressure_marks_target_cells_frozen():
    violations = find_source_violations(BAD_RIGHT_PROJECTION, "(x * y) = x")
    pressures = compute_repair_cell_pressure(BAD_RIGHT_PROJECTION, violations, "(x * y) = x", {"x": 0, "y": 1})
    touched = [p for p in pressures if p.cell == (0, 1)]
    assert touched and touched[0].target_witness_touched and touched[0].frozen


def test_pressure_descent_reduces_source_violations_and_recovers():
    result = run_source_law_repair(
        BAD_RIGHT_PROJECTION,
        "(x * y) = x",
        "x = y",
        {"x": 0, "y": 1},
        pair_id="toy",
        constructor_id="bad-right",
        family="projection_completion_right",
        strategy="pressure_descent",
    )
    assert result.finite_checked is True
    assert result.recovered is True
    assert result.trace["final_source_violations"] < result.trace["started_source_violations"]


def test_target_frozen_pressure_descent_keeps_target_witness_cell():
    result = run_source_law_repair(
        BAD_RIGHT_PROJECTION,
        "(x * y) = x",
        "(x * y) = x",
        {"x": 0, "y": 1},
        pair_id="toy",
        constructor_id="bad-right",
        family="projection_completion_right",
        strategy="target_frozen_pressure_descent",
    )
    assert result.repaired_table[0][1] == BAD_RIGHT_PROJECTION[0][1]


def test_diagonal_first_prioritizes_diagonal_cells():
    pressures = compute_repair_cell_pressure(
        [[1, 0], [1, 0]],
        find_source_violations([[1, 0], [1, 0]], "(x * x) = x"),
        "x = y",
        {"x": 0, "y": 1},
    )
    moves = propose_repair_moves([[1, 0], [1, 0]], pressures, "diagonal_first_repair")
    assert moves
    assert moves[0].cell[0] == moves[0].cell[1]


def test_quotient_merge_repair_is_deterministic():
    violations = find_source_violations(BAD_RIGHT_PROJECTION, "(x * y) = x")
    pressures = compute_repair_cell_pressure(BAD_RIGHT_PROJECTION, violations, "x = y", {"x": 0, "y": 1})
    first = propose_repair_moves(BAD_RIGHT_PROJECTION, pressures, "quotient_merge_repair", seed=7)
    second = propose_repair_moves(BAD_RIGHT_PROJECTION, pressures, "quotient_merge_repair", seed=7)
    assert first == second


def test_failed_repair_does_not_promote_truth():
    result = run_source_law_repair(
        BAD_RIGHT_PROJECTION,
        "(x * y) = x",
        "(x * y) = x",
        {"x": 0, "y": 1},
        pair_id="toy",
        constructor_id="bad-right",
        family="projection_completion_right",
        strategy="target_frozen_pressure_descent",
    )
    assert result.terminal_form != "VERIFIED_PROOF"
    assert result.can_promote_truth is False


def test_repair_conditioned_constructors_returns_checked_results():
    constructors = pd.DataFrame(
        [
            {
                "pair_id": "toy",
                "constructor_id": "bad-right",
                "family": "projection_completion_right",
                "table": BAD_RIGHT_PROJECTION,
                "source_equation": "(x * y) = x",
                "target_equation": "x = y",
            }
        ]
    )
    results, traces = repair_conditioned_constructors(constructors, strategies=["pressure_descent"])
    assert not results.empty
    assert results["finite_checked"].map(bool).all()
    assert traces["recovered"].map(bool).any()

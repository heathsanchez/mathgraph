from mathgraph.synthetic_cycle_data import build_synthetic_metabolic_frontier


def test_synthetic_frontier_has_stable_mixed_rows():
    rows = build_synthetic_metabolic_frontier()
    assert rows
    assert rows[0]["task_id"] == "synthetic_cycle_0001_structural_exact"
    required = {"task_id", "source", "target", "route", "terminal_goal"}
    assert all(required <= set(row) for row in rows)
    goals = {row["terminal_goal"] for row in rows}
    kinds = {row["task_kind"] for row in rows}
    assert "VERIFIED_PROOF" in goals
    assert "FINITE_COUNTERMODEL" in goals
    assert "UNKNOWN_OR_OBSTRUCTION" in goals
    assert "structural_true" in kinds
    assert "finite_countermodel_search" in kinds
    assert "residual_probe" in kinds


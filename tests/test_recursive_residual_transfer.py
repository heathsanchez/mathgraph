import json
import sqlite3

from mathgraph.recursive_residual_transfer import (
    GATE_NAMES,
    SOURCE_BREAKTHROUGH_METRICS,
    ResidualMinedConstructor,
    build_recursive_transfer_summary,
    compute_transfer_gates,
    evaluate_route_transfer,
    source_breakthrough_route_evaluations,
    write_recursive_transfer_artifacts,
)


def test_source_breakthrough_gates_preserve_names_and_metrics() -> None:
    gates, _best = compute_transfer_gates(source_breakthrough_route_evaluations())
    values = {gate.gate: gate.value for gate in gates}

    assert [gate.gate for gate in gates] == list(GATE_NAMES)
    assert all(gate.passed for gate in gates)
    assert round(float(values["compact_transfer_gain_vs_generic_positive"]), 6) == 234.166667
    assert round(float(values["compact_beats_random_same_size"]), 6) == 205.0
    assert round(float(values["compact_beats_shuffled_atlas_same_size"]), 6) == 86.958333
    assert round(float(values["compact_retains_recursive_gain"]), 6) == 0.989575
    assert round(float(values["compact_prunes_recursive_memory"]), 6) == 0.53
    assert round(float(values["oracle_gap_captured"]), 5) == 0.68992
    assert values["zero_true_contamination"] == 0
    assert values["advisory_boundary_preserved"] is True


def test_evaluate_route_transfer_counts_recoveries_without_truth_promotion() -> None:
    result = evaluate_route_transfer(
        seed=1729,
        split="heldout_a",
        route="compact_top_2",
        route_kind="compact_atlas",
        route_size=6,
        false_hits=[True, False, True, True],
        generic_false_hits=[True, False, False, False],
        true_hits=[False, False],
    )

    assert result.recoveries == 3
    assert result.residuals == 1
    assert result.new_recoveries_vs_generic == 2
    assert result.true_contamination_count == 0
    assert result.advisory_only is True
    assert result.can_promote_truth is False


def test_summary_and_artifacts_preserve_advisory_boundary(tmp_path) -> None:
    routes = source_breakthrough_route_evaluations()
    summary = build_recursive_transfer_summary(
        routes,
        equations=SOURCE_BREAKTHROUGH_METRICS["equations"],
        matrix_shape=SOURCE_BREAKTHROUGH_METRICS["matrix_shape"],
        true_count=SOURCE_BREAKTHROUGH_METRICS["true_count"],
        false_count=SOURCE_BREAKTHROUGH_METRICS["false_count"],
        source_run_metrics=SOURCE_BREAKTHROUGH_METRICS,
    )
    paths = write_recursive_transfer_artifacts(
        tmp_path,
        summary=summary,
        route_evaluations=routes,
        constructors=[ResidualMinedConstructor("c1", generation=1, source="gen1_projection_perturb")],
        write_report=True,
    )

    payload = json.loads((tmp_path / "recursive_transfer_summary.json").read_text(encoding="utf-8"))
    assert payload["equations"] == 4694
    assert payload["matrix_shape"] == [4694, 4694]
    assert payload["true_count"] == 8178279
    assert payload["false_count"] == 13855357
    assert payload["true_contamination_max"] == 0
    assert payload["advisory_boundary_ok"] is True
    assert payload["gates_passed"] == 9
    assert (tmp_path / "compact_atlas_eval.csv").exists()
    assert "Route scores are not truth" in (tmp_path / "recursive_transfer_report.md").read_text(encoding="utf-8")
    with sqlite3.connect(paths["recursive_transfer_sqlite"]) as con:
        tables = {row[0] for row in con.execute("select name from sqlite_master where type='table'")}
    assert {"route_eval_by_seed_split", "gate_results", "compact_atlas_eval"} <= tables

from mathgraph.polarized_quotient_ir import build_equation_features, build_pair_features, classify_basin, classify_deep_ir, recommend_constructor_families


def test_build_equation_features():
    row = build_equation_features("(x * y) = (y * x)")

    assert row["parse_ok"] is True
    assert row["lhs_size"] == 3
    assert row["rhs_size"] == 3


def test_pair_features_required_fields_and_advisory_boundary():
    row = build_pair_features("(x * y) = (y * x)", "(x * y) = x")

    for key in (
        "source_size",
        "target_size",
        "quotient_pressure",
        "target_separation_pressure",
        "fresh_variable_escape_count",
        "projection_boundary_score",
        "ir_continuation_gradient",
        "basin",
        "deep_ir_candidate",
        "recommended_families",
    ):
        assert key in row
    assert row["advisory_only"] is True
    assert row["can_promote_truth"] is False


def test_basin_and_recommendations_are_deterministic():
    row = build_pair_features("x = x", "x = y")

    assert classify_basin(row) in {"fresh_variable_escape", "projection_pressure"}
    assert classify_deep_ir(row)
    assert recommend_constructor_families(row)


def test_malformed_pair_returns_parse_error():
    row = build_pair_features("bad", "x = x")

    assert row["parse_ok"] is False
    assert row["can_promote_truth"] is False

from mathgraph.constructor_families import all_constructor_families, default_priority_for_basin, normalize_family_name, parse_constructor_id


def test_constructor_family_catalog_contains_required_names():
    names = {row.family for row in all_constructor_families()}

    assert "constant" in names
    assert "quotient_fresh_gate" in names
    assert "tail_coupled_projection" in names
    assert all(row.advisory_only and not row.can_promote_truth for row in all_constructor_families())


def test_normalize_family_name_and_parse_constructor_id():
    assert normalize_family_name("affine") == "linear_combo_mod"
    parsed = parse_constructor_id("quotient_fresh_gate:demo:n4:abcd")

    assert parsed["family"] == "quotient_fresh_gate"
    assert parsed["name"] == "demo"
    assert parsed["carrier"] == "n4"
    assert parsed["hash"] == "abcd"


def test_default_priority_by_basin():
    projection = default_priority_for_basin("projection_pressure")
    fresh = default_priority_for_basin("fresh_variable_escape")

    assert "left_projection" in projection
    assert "quotient_fresh_gate" in fresh

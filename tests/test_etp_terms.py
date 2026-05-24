from mathgraph.etp_terms import equation_features, parse_equation, skeleton_signature, term_position_paths, variable_first_canonicalize_equation


def test_operator_normalization_and_canonicalization():
    eq = parse_equation("a ◇ b = b · a")

    assert eq.normalized == "a * b = b * a"
    assert eq.canonical() == "(v0 * v1) = (v1 * v0)"


def test_term_features_and_positions():
    eq = parse_equation("((x * y) * x) = y")

    assert eq.lhs.size() == 5
    assert eq.lhs.depth() == 2
    assert eq.lhs.variable_counts()["x"] == 2
    assert () in term_position_paths(eq.lhs)
    assert skeleton_signature(eq.lhs) == "((v*v)*v)"


def test_equation_features_parse_error_is_advisory():
    row = equation_features("not an equation")

    assert row["parse_ok"] is False
    assert row["parse_error"]


def test_variable_first_canonicalization_is_stable():
    assert variable_first_canonicalize_equation("z * x = x") == "(v0 * v1) = v1"

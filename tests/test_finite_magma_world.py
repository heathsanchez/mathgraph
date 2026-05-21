from mathgraph.finite_magma_world import (
    add_mod_n,
    check_finite_countermodel,
    constant_table,
    eval_term,
    left_projection,
    parse_equation,
    parse_term,
    right_projection,
    table_satisfies_equation,
    table_violates_equation,
    xor_mod_2,
)


def test_term_parsing_and_evaluation():
    term = parse_term("((x * y) * z)")
    assert term.to_string() == "((x * y) * z)"
    assert eval_term(term, left_projection(2), {"x": 1, "y": 0, "z": 0}) == 1


def test_equation_parsing():
    eq = parse_equation("(x * x) = x")
    assert eq.to_string() == "(x * x) = x"
    assert eq.variables() == ("x",)


def test_global_satisfaction_and_violation():
    assert table_satisfies_equation(left_projection(2), "(x * x) = x")
    assert table_violates_equation(left_projection(2), "(x * y) = (y * x)")


def test_basic_tables():
    assert left_projection(2)[1][0] == 1
    assert right_projection(2)[1][0] == 0
    assert constant_table(2, 0)[1][1] == 0
    assert xor_mod_2()[1][1] == 0
    assert add_mod_n(3)[2][2] == 1


def test_valid_finite_countermodel_accepts():
    result = check_finite_countermodel("(x * x) = x", "(x * y) = (y * x)", left_projection(2))
    assert result.satisfies_source is True
    assert result.violates_target is True
    assert result.terminal_candidate_ok is True
    assert result.witness_env


def test_invalid_table_does_not_pass():
    result = check_finite_countermodel("(x * x) = x", "(x * y) = (y * x)", xor_mod_2())
    assert result.terminal_candidate_ok is False
    assert result.satisfies_source is False

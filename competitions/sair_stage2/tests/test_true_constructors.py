from competitions.sair_stage2.src.equation_core import parse_equation
from competitions.sair_stage2.src.true_constructors import (
    prove_alpha_or_swap,
    prove_contextual_fixed_point,
    prove_direct_substitution,
    prove_normal_form,
    prove_true,
)


def test_alpha_and_substitution_true_constructors():
    assert prove_alpha_or_swap(parse_equation("x * y = x"), parse_equation("a * b = a"))
    proof = prove_direct_substitution(parse_equation("x = x"), parse_equation("a * b = a * b"))
    assert proof["terminal_form"] == "ADVISORY_TRUE_CANDIDATE"


def test_normal_form_and_contextual_fixed_point():
    assert prove_normal_form(parse_equation("x = x * x"), parse_equation("(x * x) * x = x"))
    assert prove_contextual_fixed_point(parse_equation("x = x * x"), parse_equation("x = (x * x) * (x * x)"))
    assert prove_true(parse_equation("x = x"), parse_equation("y = y"))


def test_dual_alpha_is_not_automatic_true():
    source = parse_equation("x * y = x")
    target = parse_equation("y * x = x")
    proof = prove_alpha_or_swap(source, target)
    assert proof is None or proof["method"] != "dual_alpha"


def test_known_unsound_dual_alpha_regressions_not_true():
    bad_pairs = [
        ("x * x = ((y * z) * x) * y", "x * x = y * (x * (z * y))"),
        ("x = y * (((x * y) * x) * y)", "x = (y * (x * (y * x))) * y"),
        ("x = x * ((y * x) * x)", "x = (x * (x * y)) * x"),
    ]
    for source, target in bad_pairs:
        proof = prove_true(parse_equation(source), parse_equation(target))
        assert proof is None or proof["method"] in {"alpha", "side_swap_alpha", "direct_substitution", "bounded_rewrite"}

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
    assert proof["terminal_form"] == "VERIFIED_PROOF"


def test_normal_form_and_contextual_fixed_point():
    assert prove_normal_form(parse_equation("x = x * x"), parse_equation("(x * x) * x = x"))
    assert prove_contextual_fixed_point(parse_equation("x = x * x"), parse_equation("x = (x * x) * (x * x)"))
    assert prove_true(parse_equation("x = x"), parse_equation("y = y"))


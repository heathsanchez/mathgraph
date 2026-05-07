from competitions.sair_stage2.src.equation_core import (
    alpha_canonical_equation,
    bounded_rewrite_derives,
    canonical_equation,
    dual_equation,
    match_pattern,
    parse_equation,
    parse_term,
)


def test_parse_and_canonicalize_common_equations():
    assert canonical_equation(parse_equation("x = x ◇ y")) == "x=(x*y)"
    assert canonical_equation(parse_equation("x * (y * z) = (x * y) * z")) == "(x*(y*z))=((x*y)*z)"


def test_alpha_equivalence_and_dual():
    a = parse_equation("x * y = x")
    b = parse_equation("a * b = a")
    assert alpha_canonical_equation(a) == alpha_canonical_equation(b)
    assert canonical_equation(dual_equation(a)) == "(y*x)=x"


def test_substitution_match():
    subst = match_pattern(parse_term("x * y"), parse_term("(a * b) * c"))
    assert subst["x"] == parse_term("a * b")
    assert subst["y"] == parse_term("c")


def test_bounded_rewrite():
    source = parse_equation("x = x * x")
    target = parse_equation("x = x * x")
    assert bounded_rewrite_derives(source, target)


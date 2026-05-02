from mathgraph.terms import Term, parse_term


def test_parse_product_term_variables_and_string() -> None:
    term = parse_term("x * (y * z)")
    assert term == Term("*", (Term("x"), Term("*", (Term("y"), Term("z")))))
    assert term.variables() == {"x", "y", "z"}
    assert str(term) == "(x * (y * z))"


def test_evaluate_term() -> None:
    term = parse_term("x * y")
    assert term.evaluate({"x": 1, "y": 0}, lambda a, b: a ^ b) == 1

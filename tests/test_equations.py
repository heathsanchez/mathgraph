from mathgraph.equations import equations_alpha_equivalent, equations_swapped, parse_equation


def test_parse_equation() -> None:
    equation = parse_equation("(x * y) * z = x * (y * z)")
    assert equation.variables() == {"x", "y", "z"}
    assert str(equation) == "((x * y) * z) = (x * (y * z))"


def test_equation_holds_for_all() -> None:
    equation = parse_equation("x * y = y * x")
    assert equation.holds_for_all(range(2), lambda a, b: a ^ b)


def test_alpha_equivalent_equations() -> None:
    assert equations_alpha_equivalent(parse_equation("x * x = x"), parse_equation("y * y = y"))
    assert not equations_alpha_equivalent(parse_equation("x * y = x"), parse_equation("a * a = a"))


def test_swapped_equations() -> None:
    assert equations_swapped(parse_equation("x * y = y * x"), parse_equation("y * x = x * y"))

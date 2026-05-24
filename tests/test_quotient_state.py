from mathgraph.etp_terms import parse_equation
from mathgraph.quotient_state import BoundedTermUniverse, CongruenceClosure, UnionFind, closure_from_equation


def test_union_find_basic_merge():
    uf = UnionFind(["x", "y"])
    assert uf.union("x", "y", "source")
    assert uf.find("x") == uf.find("y")


def test_bounded_term_universe_contains_binary_terms():
    universe = BoundedTermUniverse.build(["x", "y"], max_depth=1)

    assert "x" in universe.terms
    assert "(x * y)" in universe.terms


def test_congruence_closure_add_equation_and_explain():
    eq = parse_equation("x = y")
    closure = CongruenceClosure(BoundedTermUniverse.build(["x", "y"], max_depth=1))
    closure.add_equation(eq.lhs, eq.rhs, "test")

    assert closure.are_equal("x", "y")
    assert closure.are_equal("(x * x)", "(y * y)")
    explanation = closure.explain("(x * x)", "(y * y)")
    assert explanation["equal"] is True
    assert explanation["advisory_only"] is True


def test_closure_from_equation_helper():
    closure = closure_from_equation("x = y", max_depth=1)

    assert closure.are_equal("x", "y")

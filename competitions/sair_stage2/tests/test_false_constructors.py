from competitions.sair_stage2.src.equation_core import parse_equation
from competitions.sair_stage2.src.false_constructors import generated_tables, prove_false
from competitions.sair_stage2.src.finite_magma_core import verify_countermodel_certificate


def test_generated_tables_and_false_constructor():
    assert any(name.startswith("left_projection") for name, _ in generated_tables(2))
    eq1 = parse_equation("x = x")
    eq2 = parse_equation("x * x = x")
    result = prove_false(eq1, eq2)
    assert result["terminal_form"] == "FINITE_COUNTERMODEL"
    assert verify_countermodel_certificate(eq1, eq2, result["certificate"])


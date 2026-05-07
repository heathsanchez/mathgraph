from competitions.sair_stage2.src.equation_core import parse_equation
from competitions.sair_stage2.src.finite_magma_core import (
    countermodel_certificate,
    satisfies_equation,
    verify_countermodel_certificate,
)


def test_projection_tables_satisfy_expected_equations():
    left = ((0, 0), (1, 1))
    right = ((0, 1), (0, 1))
    assert satisfies_equation(parse_equation("x * y = x"), left)
    assert satisfies_equation(parse_equation("x * y = y"), right)


def test_countermodel_certificate_verification():
    eq1 = parse_equation("x = x")
    eq2 = parse_equation("x * x = x")
    xor = ((0, 1), (1, 0))
    cert = countermodel_certificate(eq1, eq2, xor)
    assert cert
    assert verify_countermodel_certificate(eq1, eq2, cert)
    cert["table"][0][0] = 9
    assert not verify_countermodel_certificate(eq1, eq2, cert)


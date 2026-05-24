from mathgraph.finite_magma import FiniteMagma, equation_holds, equation_violated_with_witness, implication_false_certificate


def test_finite_countermodel_requires_source_global_and_target_witness():
    magma = FiniteMagma(((0, 0), (0, 0)), "constant", "constant_n2_0")

    cert = implication_false_certificate("(x * y) = (y * x)", "(x * y) = x", magma)

    assert cert.eq1_holds is True
    assert cert.eq2_violated is True
    assert cert.witness_env
    assert cert.certificate_status == "finite_countermodel_found"
    assert cert.can_promote_truth is True


def test_failed_finite_search_is_not_terminal_truth():
    magma = FiniteMagma(((0, 1), (0, 1)), "right_projection", "right_projection_n2")

    cert = implication_false_certificate("(x * y) = x", "(x * y) = y", magma)

    assert cert.certificate_status == "not_a_countermodel"
    assert cert.advisory_only is True
    assert cert.can_promote_truth is False


def test_equation_evaluator_finds_violation_witness():
    magma = FiniteMagma(((0, 1), (0, 1)), "right_projection", "right_projection_n2")

    assert equation_holds("(x * y) = y", magma)
    witness = equation_violated_with_witness("(x * y) = x", magma)
    assert witness is not None

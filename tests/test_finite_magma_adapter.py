from adapters.finite_magma_adapter import FiniteMagma
from mathgraph.equations import parse_equation


def test_finite_magma_validates_table_entries() -> None:
    magma = FiniteMagma.from_table([[0, 1], [1, 0]])
    assert magma.size == 2
    assert magma.op(1, 0) == 1


def test_finite_magma_finds_counterexample_to_equation() -> None:
    magma = FiniteMagma.from_table([[0, 1], [1, 0]], name="xor")
    witness = magma.counterexample_to_equation(parse_equation("x * x = x"))
    assert witness == {"assignment": {"x": 1}, "lhs": 0, "rhs": 1}


def test_finite_magma_finds_implication_countermodel() -> None:
    magma = FiniteMagma.from_table([[0, 1], [1, 0]], name="xor")
    witness = magma.counterexample_to_implication([], parse_equation("x * x = x"))
    assert witness is not None
    assert witness["size"] == 2
    assert witness["carrier_order"] == 2
    assert witness["assignment"] == {"x": 1}
    assert witness["premises_satisfied"] is True
    assert witness["conclusion_violated"] is True
    assert witness["table_invariants"]["commutative"] is True


def test_countermodel_certificate_payload_includes_invariants() -> None:
    magma = FiniteMagma.from_table([[0, 1], [1, 0]], name="xor")
    payload = magma.countermodel_certificate_payload(
        parse_equation("x = x"),
        parse_equation("x * x = x"),
    )
    assert payload is not None
    assert payload["table"] == [[0, 1], [1, 0]]
    assert payload["carrier_order"] == 2
    assert payload["source_equation"] == "x = x"
    assert payload["target_equation"] == "(x * x) = x"
    assert payload["source_satisfied"] is True
    assert payload["target_violated"] is True
    assert payload["assignment"] == {"x": 1}
    assert payload["table_invariants"]["commutative"] is True
    assert payload["table_invariants"]["idempotent"] is False

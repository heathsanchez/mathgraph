import pytest

from mathgraph.certificates import Certificate, TerminalForm, finite_countermodel, verified_proof
from mathgraph.verification import verify_certificate


def test_certificate_terminal_forms_validate() -> None:
    cert = verified_proof("x = x", "demo-proof")
    assert verify_certificate(cert).terminal_form == TerminalForm.VERIFIED_PROOF


def test_finite_countermodel_certificate() -> None:
    cert = finite_countermodel("claim", {"size": 2})
    assert cert.payload["model"]["size"] == 2


def test_malformed_certificate_is_rejected() -> None:
    with pytest.raises(ValueError):
        verify_certificate(Certificate(TerminalForm.VERIFIED_PROOF, "claim"))

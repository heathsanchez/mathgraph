import pytest

from mathgraph.terminal_contract import (
    ProvenanceType,
    Status,
    TerminalContractResult,
    TerminalForm,
    TrustLevel,
    VerifierBoundary,
)


def test_terminal_contract_accepts_valid_finite_refutation():
    result = TerminalContractResult(
        status=Status.REFUTED,
        terminal_form=TerminalForm.REFUTATION_CERTIFICATE,
        trust_level=TrustLevel.FINITE_VERIFIED,
        provenance_type=ProvenanceType.PRIMITIVE,
        verifier_boundary=VerifierBoundary.IMPORTER_REVALIDATED,
        certificate_id="cert_1",
        certificate_chain=["cert_1"],
        warnings=[],
        evidence={"table_hash": "abc"},
    )
    assert result.to_dict()["terminal_form"] == TerminalForm.REFUTATION_CERTIFICATE


def test_terminal_contract_rejects_verified_advisory():
    with pytest.raises(ValueError):
        TerminalContractResult(
            status=Status.VERIFIED,
            terminal_form=TerminalForm.VERIFIED_PROOF,
            trust_level=TrustLevel.ADVISORY_ROUTE,
            provenance_type=ProvenanceType.ADVISORY,
            verifier_boundary=VerifierBoundary.ADVISORY_ONLY,
            certificate_id="proof",
            certificate_chain=["proof"],
            warnings=[],
            evidence={},
        )


def test_terminal_contract_rejects_refutation_without_certificate_id():
    with pytest.raises(ValueError):
        TerminalContractResult(
            status=Status.REFUTED,
            terminal_form=TerminalForm.REFUTATION_CERTIFICATE,
            trust_level=TrustLevel.FINITE_VERIFIED,
            provenance_type=ProvenanceType.PRIMITIVE,
            verifier_boundary=VerifierBoundary.IMPORTER_REVALIDATED,
            certificate_id=None,
            certificate_chain=[],
            warnings=[],
            evidence={},
        )


def test_terminal_contract_rejects_finite_verified_true():
    with pytest.raises(ValueError):
        TerminalContractResult(
            status=Status.VERIFIED_TRUE,
            terminal_form=TerminalForm.VERIFIED_PROOF,
            trust_level=TrustLevel.FINITE_VERIFIED,
            provenance_type=ProvenanceType.PRIMITIVE,
            verifier_boundary=VerifierBoundary.FINITE_CHECKED,
            certificate_id="bad",
            certificate_chain=["bad"],
            warnings=[],
            evidence={},
        )


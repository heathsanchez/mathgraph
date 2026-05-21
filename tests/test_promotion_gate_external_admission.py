from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import sha256_hex
from mathgraph.promotion_gate import PromotionGate, PromotionGateDecisionKind
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


def test_valid_finite_countermodel_external_certificate_is_accepted():
    cert = _finite_countermodel_cert()

    decision = PromotionGate().evaluate(cert)

    assert decision.accepted is True
    assert decision.decision_kind == PromotionGateDecisionKind.ACCEPT_FOR_LAWBOOK
    assert decision.lawbook_candidate is not None
    assert decision.terminal_form == "REFUTATION_CERTIFICATE"
    assert decision.certificate_id == cert.cert_id


def test_valid_lean_proof_external_certificate_is_accepted():
    cert_id = "lean-cert"
    evidence = ExternalBoundaryEvidence(
        evidence_id="lean-ev",
        boundary_kind=VerifierBoundaryKind.LEAN_TYPECHECKED,
        certificate_id=cert_id,
        terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
        raw_output_hash=sha256_hex("lean accepted"),
        verifier_kind=ExternalVerifierKind.LEAN4,
        advisory=False,
    )
    cert = ExternalCertificate(
        cert_id=cert_id,
        verifier=ExternalVerifierKind.LEAN4,
        status=ExternalCertificateStatus.ACCEPTED,
        claim="theorem t : True",
        claim_hash=sha256_hex("claim"),
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
        boundary_evidence=evidence,
        boundary_valid=True,
        accepted=True,
        advisory_only=False,
        advisory=False,
    )

    decision = PromotionGate().evaluate(cert)

    assert decision.accepted is True
    assert decision.decision_kind == PromotionGateDecisionKind.ACCEPT_FOR_LAWBOOK
    assert decision.lawbook_candidate["terminal_form"] == "VERIFIED_PROOF"
    assert decision.certificate_id == cert_id


def test_advisory_only_certificate_is_rejected():
    cert = ExternalCertificate(
        cert_id="advisory",
        verifier=ExternalVerifierKind.UNKNOWN,
        status=ExternalCertificateStatus.PENDING,
        claim="candidate",
        claim_hash=sha256_hex("candidate"),
        certificate_kind=ExternalCertificateKind.ADVISORY_ONLY,
    )

    decision = PromotionGate().evaluate(cert)

    assert decision.accepted is False
    assert decision.decision_kind == PromotionGateDecisionKind.REJECT_ADVISORY_ONLY


def test_raw_success_text_without_boundary_is_rejected():
    cert = ExternalCertificate(
        cert_id="raw",
        verifier=ExternalVerifierKind.LEAN4,
        status=ExternalCertificateStatus.ACCEPTED,
        claim="raw success",
        claim_hash=sha256_hex("raw success"),
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
        metadata={"raw_success_text": True},
    )

    decision = PromotionGate().evaluate(cert)

    assert decision.accepted is False
    assert decision.decision_kind == PromotionGateDecisionKind.REJECT_INVALID_BOUNDARY


def test_finite_search_miss_cannot_become_proof():
    cert = ExternalCertificate(
        cert_id="miss",
        verifier=ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
        status=ExternalCertificateStatus.REJECTED,
        claim="bounded search missed",
        claim_hash=sha256_hex("miss"),
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
        metadata={"finite_search_miss": True},
    )

    decision = PromotionGate().evaluate(cert)

    assert decision.accepted is False
    assert decision.decision_kind == PromotionGateDecisionKind.REJECT_FINITE_SEARCH_MISS


def _finite_countermodel_cert() -> ExternalCertificate:
    cert_id = "finite-cert"
    evidence = ExternalBoundaryEvidence(
        evidence_id="finite-ev",
        boundary_kind=VerifierBoundaryKind.FINITE_CHECKED,
        certificate_id=cert_id,
        terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
        artifact_hash=sha256_hex("finite artifact"),
        verifier_kind=ExternalVerifierKind.PYTHON_FINITE_CHECKER,
        advisory=False,
    )
    return ExternalCertificate(
        cert_id=cert_id,
        verifier=ExternalVerifierKind.PYTHON_FINITE_CHECKER,
        status=ExternalCertificateStatus.COUNTERMODEL_FOUND,
        claim="eq1 does not imply eq2",
        claim_hash=sha256_hex("claim"),
        certificate_kind=ExternalCertificateKind.FINITE_COUNTERMODEL,
        proposed_terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
        boundary_evidence=evidence,
        boundary_valid=True,
        accepted=True,
        advisory_only=False,
        advisory=False,
    )

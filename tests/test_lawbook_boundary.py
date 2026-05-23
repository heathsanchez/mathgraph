from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import content_id, sha256_hex
from mathgraph.lawbook_boundary import evaluate_lawbook_admission, reject_failed_search_as_truth
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


def _cert(*, proof: bool = False) -> ExternalCertificate:
    form = CanonicalTerminalForm.VERIFIED_PROOF if proof else CanonicalTerminalForm.REFUTATION_CERTIFICATE
    kind = ExternalCertificateKind.VERIFIED_PROOF if proof else ExternalCertificateKind.FINITE_COUNTERMODEL
    verifier = ExternalVerifierKind.LEAN4 if proof else ExternalVerifierKind.PYTHON_FINITE_CHECKER
    boundary_kind = VerifierBoundaryKind.LEAN_TYPECHECKED if proof else VerifierBoundaryKind.FINITE_CHECKED
    payload = {"proof": proof, "claim": "x=x"}
    cert_id = content_id("lawbook-boundary-test", payload)
    boundary = ExternalBoundaryEvidence(
        evidence_id=content_id("lawbook-boundary-evidence", payload),
        boundary_kind=boundary_kind,
        certificate_id=cert_id,
        terminal_form=form,
        source_artifact_id="claim:test",
        artifact_hash=sha256_hex(payload),
        verifier_kind=verifier,
        advisory=False,
    )
    return ExternalCertificate(
        cert_id=cert_id,
        verifier=verifier,
        status=ExternalCertificateStatus.ACCEPTED,
        claim="x=x",
        claim_hash=sha256_hex("x=x"),
        certificate_kind=kind,
        proposed_terminal_form=form,
        boundary_evidence=boundary,
        boundary_valid=True,
        accepted=True,
    )


def test_valid_finite_countermodel_certificate_can_be_admitted():
    decision = evaluate_lawbook_admission(_cert())

    assert decision.accepted is True
    assert decision.can_promote_truth is True
    assert decision.advisory_only is False
    assert decision.terminal_form.value in {"REFUTATION_CERTIFICATE", "FINITE_COUNTERMODEL"}
    assert decision.boundary_evidence_type.value == "finite_checked"


def test_valid_lean_proof_certificate_can_be_admitted():
    decision = evaluate_lawbook_admission(_cert(proof=True))

    assert decision.accepted is True
    assert decision.terminal_form.value == "VERIFIED_PROOF"
    assert decision.boundary_evidence_type.value == "lean_typechecked"


def test_advisory_route_reason_atlas_and_htilt_are_rejected():
    for candidate in (
        {"kind": "advisory_route", "terminal_form": "VERIFIED_PROOF"},
        {"kind": "reason_atlas_entry", "support_count": 999, "terminal_form": "VERIFIED_PROOF"},
        {"kind": "htilt_score", "new_priority_score": 12.0, "terminal_form": "FINITE_COUNTERMODEL"},
    ):
        decision = evaluate_lawbook_admission(candidate)
        assert decision.accepted is False
        assert decision.can_promote_truth is False


def test_raw_success_text_is_rejected():
    decision = evaluate_lawbook_admission("success: theorem checked")

    assert decision.accepted is False
    assert decision.reason == "raw_success_text_is_not_boundary_evidence"


def test_failed_finite_search_never_promotes_true():
    decision = reject_failed_search_as_truth()

    assert decision.accepted is False
    assert decision.reason == "failed_finite_search_cannot_be_true"
    assert evaluate_lawbook_admission({"failed_finite_search": True, "terminal_form": "TRUE"}).accepted is False

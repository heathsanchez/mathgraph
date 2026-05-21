from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
    plan_external_certificate_import,
)
from mathgraph.hashing import sha256_hex
from mathgraph.terminal_schema import CanonicalTerminalForm, RefutationKind, VerifierBoundaryKind


def test_lean4_accepted_maps_to_advisory_verified_proof_candidate():
    cert = ExternalCertificate("c1", ExternalVerifierKind.LEAN4, ExternalCertificateStatus.ACCEPTED, "claim", "h")
    assert cert.candidate_terminal_form() == CanonicalTerminalForm.VERIFIED_PROOF
    payload = cert.to_candidate_payload()
    assert payload["advisory"] is True
    assert payload["can_cross_verifier_boundary"] is False


def test_z3_sat_with_countermodel_maps_to_refutation_candidate():
    cert = ExternalCertificate(
        "c2",
        ExternalVerifierKind.Z3,
        ExternalCertificateStatus.SAT,
        "claim",
        "h",
        countermodel={"x": 1},
    )
    assert cert.candidate_terminal_form() == CanonicalTerminalForm.REFUTATION_CERTIFICATE
    assert cert.candidate_refutation_kind() == RefutationKind.SMT_COUNTERMODEL


def test_z3_unsat_without_metadata_does_not_self_promote_as_proof():
    cert = ExternalCertificate("c3", ExternalVerifierKind.Z3, ExternalCertificateStatus.UNSAT, "claim", "h")
    assert cert.candidate_terminal_form() == CanonicalTerminalForm.NAMED_OBSTRUCTION


def test_timeout_maps_to_named_obstruction_candidate():
    cert = ExternalCertificate("c4", ExternalVerifierKind.COQ, ExternalCertificateStatus.TIMEOUT, "claim", "h")
    assert cert.candidate_terminal_form() == CanonicalTerminalForm.NAMED_OBSTRUCTION


def test_external_certificate_is_always_advisory():
    cert = ExternalCertificate("c5", ExternalVerifierKind.COQ, ExternalCertificateStatus.ACCEPTED, "claim", "h", advisory=False)
    assert cert.advisory is True
    assert cert.to_dict()["advisory"] is True


def test_import_decision_requires_replay_boundary():
    cert = ExternalCertificate("c6", ExternalVerifierKind.LEAN4, ExternalCertificateStatus.ACCEPTED, "claim", "h")
    decision = plan_external_certificate_import(cert)
    assert decision.accepted_for_replay is True
    assert decision.advisory is True


def test_external_certificate_json_roundtrip_and_stable_id():
    cert = ExternalCertificate.from_dict(
        {
            "verifier": "LEAN",
            "status": "ACCEPTED",
            "claim": "claim",
            "claim_hash": "h",
            "certificate_kind": "VERIFIED_PROOF",
        }
    )
    assert ExternalCertificate.from_json(cert.to_json()).cert_id == cert.cert_id


def test_valid_boundary_evidence_allows_boundary_valid_candidate():
    evidence = ExternalBoundaryEvidence(
        "ev1",
        VerifierBoundaryKind.LEAN_TYPECHECKED,
        "cert1",
        CanonicalTerminalForm.VERIFIED_PROOF,
        artifact_hash=sha256_hex("artifact"),
        verifier_kind=ExternalVerifierKind.LEAN,
    )
    cert = ExternalCertificate(
        "cert1",
        ExternalVerifierKind.LEAN,
        ExternalCertificateStatus.ACCEPTED,
        "claim",
        "h",
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
        boundary_evidence=evidence,
        boundary_valid=True,
    )
    assert cert.boundary_valid is True
    assert cert.advisory_only is True


def test_raw_success_text_alone_is_not_boundary_evidence():
    cert = ExternalCertificate(
        "cert_raw",
        ExternalVerifierKind.LEAN,
        ExternalCertificateStatus.ACCEPTED,
        "claim",
        "h",
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        metadata={"raw_success_text": True},
    )
    assert cert.boundary_valid is False
    assert cert.advisory_only is True


def test_finite_search_miss_cannot_imply_proof():
    cert = ExternalCertificate(
        "cert_miss",
        ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
        ExternalCertificateStatus.REJECTED,
        "claim",
        "h",
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        metadata={"finite_search_miss": True},
    )
    assert cert.boundary_valid is False

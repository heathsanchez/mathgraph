from mathgraph.external_certificates import (
    ExternalCertificate,
    ExternalCertificateStatus,
    ExternalVerifierKind,
    plan_external_certificate_import,
)
from mathgraph.terminal_schema import CanonicalTerminalForm, RefutationKind


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

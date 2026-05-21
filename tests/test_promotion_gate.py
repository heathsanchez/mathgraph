from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import sha256_hex
from mathgraph.promotion_gate import PromotionGate, PromotionGateDecisionKind
from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind, ReasonAtlasFeedbackEvent, ReasonAtlasFeedbackOutcome
from mathgraph.root_operator_schema import RootOperatorSchema
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


def _valid_cert():
    evidence = ExternalBoundaryEvidence(
        "ev",
        VerifierBoundaryKind.LEAN_TYPECHECKED,
        "cert",
        CanonicalTerminalForm.VERIFIED_PROOF,
        artifact_hash=sha256_hex("artifact"),
        verifier_kind=ExternalVerifierKind.LEAN,
    )
    return ExternalCertificate(
        "cert",
        ExternalVerifierKind.LEAN,
        ExternalCertificateStatus.ACCEPTED,
        "claim",
        "h",
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
        boundary_evidence=evidence,
        boundary_valid=True,
    )


def test_valid_external_certificate_with_boundary_is_accepted():
    decision = PromotionGate().evaluate(_valid_cert())
    assert decision.decision_kind == PromotionGateDecisionKind.ACCEPT_FOR_LAWBOOK
    assert decision.lawbook_candidate["terminal_form"] == "VERIFIED_PROOF"


def test_invalid_boundary_is_rejected():
    cert = ExternalCertificate("c", ExternalVerifierKind.LEAN, ExternalCertificateStatus.ACCEPTED, "claim", "h", certificate_kind=ExternalCertificateKind.VERIFIED_PROOF)
    assert PromotionGate().evaluate(cert).decision_kind == PromotionGateDecisionKind.REJECT_INVALID_BOUNDARY


def test_reason_atlas_entry_root_schema_route_law_and_feedback_are_rejected():
    gate = PromotionGate()
    entry = ReasonAtlasEntry("e", ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA, "schema")
    schema = RootOperatorSchema.create([{"name": "move", "params": {}}], support=2)
    route_law = {"law_kind": "PROMOTED_ROUTE_LAW", "law_id": "l"}
    feedback = ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.VERIFIER_SUCCESS)
    assert gate.evaluate(entry).accepted is False
    assert gate.evaluate(schema).accepted is False
    assert gate.evaluate(route_law).accepted is False
    assert gate.evaluate(feedback).accepted is False


def test_advisory_only_cannot_become_terminal_truth():
    cert = ExternalCertificate("c", ExternalVerifierKind.UNKNOWN, ExternalCertificateStatus.PENDING, "claim", "h", certificate_kind=ExternalCertificateKind.ADVISORY_ONLY)
    assert PromotionGate().evaluate(cert).decision_kind == PromotionGateDecisionKind.REJECT_ADVISORY_ONLY


def test_finite_search_miss_cannot_promote_true_or_verified_proof():
    cert = ExternalCertificate(
        "c",
        ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER,
        ExternalCertificateStatus.REJECTED,
        "claim",
        "h",
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        metadata={"finite_search_miss": True},
    )
    assert PromotionGate().evaluate(cert).decision_kind == PromotionGateDecisionKind.REJECT_FINITE_SEARCH_MISS

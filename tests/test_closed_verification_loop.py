from mathgraph.closed_verification_loop import ClosedVerificationLoop
from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import sha256_hex
from mathgraph.reason_atlas_feedback_loop import ReasonAtlasFeedbackLoop
from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


def _setup(tmp_path):
    loop = ReasonAtlasFeedbackLoop(tmp_path / "atlas.sqlite")
    loop.ingest_entries(
        [
            ReasonAtlasEntry("entry_valid", ReasonAtlasEntryKind.CONSTRUCTOR_HINT, "valid", atoms=["valid"]),
            ReasonAtlasEntry("entry_raw", ReasonAtlasEntryKind.CONSTRUCTOR_HINT, "raw", atoms=["raw"]),
        ]
    )
    return loop


def _fake(row):
    if row["entry_id"] == "entry_valid":
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
    return ExternalCertificate(
        "raw",
        ExternalVerifierKind.LEAN,
        ExternalCertificateStatus.ACCEPTED,
        "raw",
        "h",
        certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
        metadata={"raw_success_text": True},
    )


def test_loop_consumes_queue_gates_feedback_and_exports(tmp_path):
    reason_loop = _setup(tmp_path)
    queue = reason_loop.next_advisory_tasks(limit=10)
    result = ClosedVerificationLoop(reason_loop).run(queue, _fake)
    assert result.summary["accepted_terminal_count"] == 1
    assert result.summary["rejected_advisory_count"] == 1
    assert reason_loop.store.stats().feedback_count >= 2
    assert all(row["advisory_only"] is True for row in result.next_queue_rows)
    out = tmp_path / "exports"
    paths = ClosedVerificationLoop(reason_loop).export_result(result, out)
    assert paths["summary"]
    assert "VERIFIED_PROOF" not in str(result.next_queue_rows)

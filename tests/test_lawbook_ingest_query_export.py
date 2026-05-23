import json

from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import content_id, sha256_hex
from mathgraph.lawbook_export import export_lawbook_jsonl, export_lawbook_manifest, export_lawbook_summary
from mathgraph.lawbook_ingest import ingest_external_certificate, reject_advisory_artifact
from mathgraph.lawbook_query import query_by_claim_id, query_by_terminal_form, query_reusable_artifacts
from mathgraph.lawbook_reuse import classify_reuse_kind, compute_action_change_rate, compute_lawbook_hit_rate
from mathgraph.lawbook_store import LawbookStore
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


def _finite_cert() -> ExternalCertificate:
    payload = {"table": [[0, 0], [0, 0]], "witness": {"x": 1, "y": 0}}
    cert_id = content_id("ingest-finite-cert", payload)
    boundary = ExternalBoundaryEvidence(
        evidence_id=content_id("ingest-boundary", payload),
        boundary_kind=VerifierBoundaryKind.FINITE_CHECKED,
        certificate_id=cert_id,
        terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
        source_artifact_id="claim:finite",
        artifact_hash=sha256_hex(payload),
        verifier_kind=ExternalVerifierKind.PYTHON_FINITE_CHECKER,
        advisory=False,
    )
    return ExternalCertificate(
        cert_id=cert_id,
        verifier=ExternalVerifierKind.PYTHON_FINITE_CHECKER,
        status=ExternalCertificateStatus.COUNTERMODEL_FOUND,
        claim="comm => leftzero",
        claim_hash=sha256_hex("comm => leftzero"),
        source_artifact_id="claim:finite",
        certificate_kind=ExternalCertificateKind.FINITE_COUNTERMODEL,
        proposed_terminal_form=CanonicalTerminalForm.REFUTATION_CERTIFICATE,
        boundary_evidence=boundary,
        boundary_valid=True,
        accepted=True,
    )


def test_ingest_query_and_export_valid_finite_certificate(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    result = ingest_external_certificate(store, _finite_cert(), domain="demo", claim_id="claim:finite")

    assert result["decision"]["accepted"] is True
    assert len(query_by_claim_id(store, "claim:finite")) == 1
    assert len(query_by_terminal_form(store, "REFUTATION_CERTIFICATE")) >= 1
    assert len(query_reusable_artifacts(store, {"domain": "demo", "source_id": "", "target_id": ""})) >= 1

    jsonl = tmp_path / "lawbook.jsonl"
    assert export_lawbook_jsonl(store, jsonl) == 1
    assert jsonl.read_text(encoding="utf-8").strip()
    manifest = export_lawbook_manifest(store, tmp_path / "manifest.json")
    assert manifest["artifacts"] == 1
    summary = export_lawbook_summary(store)
    assert summary["artifact_count"] == 1


def test_advisory_artifact_rejection_and_reuse_metrics():
    rejected = reject_advisory_artifact({"kind": "route_law"})
    assert rejected["accepted"] is False
    rows = [{"hit": True, "changed_action": True}, {"hit": False, "changed_action": False}]
    assert compute_lawbook_hit_rate(rows) == 0.5
    assert compute_action_change_rate(rows) == 0.5
    assert classify_reuse_kind({"terminal_form": "ADVISORY", "trust_level": 10}) == "advisory_reuse"

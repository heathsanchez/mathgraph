#!/usr/bin/env python
"""Smoke test the Reason Atlas -> verifier callback -> PromotionGate loop."""

from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.closed_verification_loop import ClosedVerificationLoop, ClosedVerificationLoopConfig  # noqa: E402
from mathgraph.external_certificates import (  # noqa: E402
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import content_id, sha256_hex  # noqa: E402
from mathgraph.reason_atlas_feedback_loop import ReasonAtlasFeedbackLoop  # noqa: E402
from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind  # noqa: E402
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind  # noqa: E402


OUT_DIR = Path("/tmp/mathgraph_closed_verification_loop_smoke")


def _seed_loop(db_path: Path) -> ReasonAtlasFeedbackLoop:
    if db_path.exists():
        db_path.unlink()
    loop = ReasonAtlasFeedbackLoop(db_path)
    loop.ingest_entries(
        [
            ReasonAtlasEntry("entry_valid", ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA, "valid hint", atoms=["move"], pattern="move"),
            ReasonAtlasEntry("entry_fail", ReasonAtlasEntryKind.REPAIRABLE_OBSTRUCTION, "repair hint", atoms=["repair"], pattern="repair"),
            ReasonAtlasEntry("entry_raw", ReasonAtlasEntryKind.CONSTRUCTOR_HINT, "raw hint", atoms=["raw"], pattern="raw"),
        ]
    )
    loop.rescore()
    return loop


def _fake_verifier(row: dict) -> ExternalCertificate:
    entry_id = row.get("entry_id")
    if entry_id == "entry_valid":
        cert_id = "cert_valid_boundary"
        evidence = ExternalBoundaryEvidence(
            evidence_id="evidence_valid_boundary",
            boundary_kind=VerifierBoundaryKind.LEAN_TYPECHECKED,
            certificate_id=cert_id,
            terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
            source_artifact_id=row.get("task_id"),
            artifact_hash=sha256_hex("valid-artifact"),
            verifier_kind=ExternalVerifierKind.LEAN,
            checker_name="fake-lean",
            checker_version="0",
        )
        return ExternalCertificate(
            cert_id=cert_id,
            verifier=ExternalVerifierKind.LEAN,
            status=ExternalCertificateStatus.ACCEPTED,
            claim="fake theorem accepted",
            claim_hash=sha256_hex("fake theorem accepted"),
            source_artifact_id=row.get("task_id"),
            certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
            proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
            boundary_evidence=evidence,
            artifact_hash=evidence.artifact_hash,
            boundary_valid=True,
        )
    if entry_id == "entry_raw":
        return ExternalCertificate(
            cert_id="cert_raw_success",
            verifier=ExternalVerifierKind.LEAN,
            status=ExternalCertificateStatus.ACCEPTED,
            claim="raw success text only",
            claim_hash=sha256_hex("raw success text only"),
            certificate_kind=ExternalCertificateKind.VERIFIED_PROOF,
            proposed_terminal_form=CanonicalTerminalForm.VERIFIED_PROOF,
            metadata={"raw_success_text": True},
        )
    return ExternalCertificate(
        cert_id=content_id("cert_fail", entry_id),
        verifier=ExternalVerifierKind.UNKNOWN,
        status=ExternalCertificateStatus.ERROR,
        claim="advisory failure",
        claim_hash=sha256_hex("advisory failure"),
        certificate_kind=ExternalCertificateKind.ADVISORY_ONLY,
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reason_loop = _seed_loop(OUT_DIR / "reason_atlas_store.sqlite")
    queue = reason_loop.next_advisory_tasks(limit=10)
    loop = ClosedVerificationLoop(reason_loop, config=ClosedVerificationLoopConfig(out_dir=OUT_DIR, max_tasks=10))
    result = loop.run(queue, _fake_verifier)
    summary_path = OUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(result.summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    reason_loop.close()
    return 0 if result.summary["overall"] in {"PASS", "PROMISING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

import json
import subprocess
import sys
from pathlib import Path

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.proof_verification import (
    ProofArtifact,
    ProofArtifactKind,
    ProofVerificationResult,
    ProofVerificationStatus,
    ProofVerificationTrace,
    ProofVerifierKind,
    chain_audit_proof,
    import_verified_proof,
    make_lean_skeleton,
    proof_verification_trace_to_agent_experiences,
    proof_verification_trace_to_alchemical_trace,
    run_proof_verification_pipeline,
    run_proof_verifier,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment


ROOT = Path(__file__).resolve().parents[1]


def test_proof_artifact_serializes_deserializes():
    artifact = ProofArtifact(
        artifact_id="pa-1",
        claim_id="claim-1",
        source="A",
        target="B",
        kind=ProofArtifactKind.LEMMA_CANDIDATE,
        content="candidate lemma",
        theorem_name="mg_candidate",
        imports=("Mathlib",),
    )

    restored = ProofArtifact.from_json(artifact.to_json())

    assert restored.to_dict() == artifact.to_dict()


def test_proof_verification_result_serializes_deserializes():
    result = ProofVerificationResult(
        result_id="pvr-1",
        artifact_id="pa-1",
        status=ProofVerificationStatus.VERIFIER_NOT_RUN,
        verifier_kind=ProofVerifierKind.LEAN,
        command=("lean", "file.lean"),
        failure_reason="not run",
    )

    restored = ProofVerificationResult.from_json(result.to_json())

    assert restored.to_dict() == result.to_dict()


def test_lean_skeleton_is_advisory_and_non_terminal():
    artifact = make_lean_skeleton(claim_id="claim-1", source="x=x", target="x=x", theorem_name="mg_smoke")

    assert artifact.kind == ProofArtifactKind.LEAN_SKELETON
    assert artifact.advisory
    assert "advisory" in artifact.content
    assert "theorem mg_smoke" in artifact.content


def test_verifier_not_run_is_non_terminal():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    result = run_proof_verifier(artifact)

    assert result.status == ProofVerificationStatus.VERIFIER_NOT_RUN
    assert not result.is_terminal()


def test_verifier_failed_is_non_terminal():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    result = run_proof_verifier(
        artifact,
        verifier_kind=ProofVerifierKind.LEAN,
        command=(sys.executable, "-c", "import sys; sys.exit(1)"),
    )

    assert result.status == ProofVerificationStatus.VERIFIER_FAILED
    assert not result.is_terminal()


def test_imported_verified_proof_requires_verified_provenance_or_external_certificate():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)

    rejected = import_verified_proof(artifact=artifact, provenance={"verified": False})
    imported = import_verified_proof(artifact=artifact, provenance={"verified": True})

    assert rejected.status == ProofVerificationStatus.REJECTED
    assert not rejected.is_terminal()
    assert imported.status == ProofVerificationStatus.IMPORTED_VERIFIED
    assert imported.is_terminal()


def test_chain_audit_requires_parent_ids_and_chain_safe_metadata():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)

    residual = chain_audit_proof(artifact=artifact, parent_certificate_ids=(), audit_rule="transitivity")
    audited = chain_audit_proof(
        artifact=artifact,
        parent_certificate_ids=("cert-a", "cert-b"),
        audit_rule="transitivity",
        audit_metadata={"chain_safe": True},
    )

    assert residual.status == ProofVerificationStatus.RESIDUAL
    assert not residual.is_terminal()
    assert audited.status == ProofVerificationStatus.CHAIN_AUDITED
    assert audited.is_terminal()


def test_mock_verifier_is_test_only_and_alignment_catches_unsafe_production_use():
    unsafe = ProofVerificationTrace(
        trace_id="pvt-bad",
        episode_id="episode-1",
        agent_id="agent-1",
        results=[
            ProofVerificationResult(
                result_id="mock-bad",
                artifact_id="artifact-1",
                status=ProofVerificationStatus.VERIFIER_PASSED,
                verifier_kind=ProofVerifierKind.MOCK_VERIFIER,
                terminal_form=TerminalForm.VERIFIED_PROOF,
                certificate_id="cert-mock",
                verifier_boundary_crossed=True,
                metadata={"test_only": False},
            )
        ],
    )

    report = check_roadmap_alignment(proof_verification_traces=[unsafe])

    assert not report.is_aligned()
    assert "MOCK_VERIFIER_PRODUCTION_TRUTH" in {finding.code for finding in report.findings}


def test_run_proof_verification_pipeline_handles_empty_inputs():
    trace = run_proof_verification_pipeline()

    assert trace.artifacts == []
    assert trace.results == []
    assert trace.summary["artifacts_total"] == 0


def test_proof_trace_to_alchemical_trace_phases_and_fixation_only_for_verified():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    advisory_trace = run_proof_verification_pipeline(artifacts=[artifact])
    advisory_alchemy = proof_verification_trace_to_alchemical_trace(advisory_trace)
    verified_result = import_verified_proof(artifact=artifact, provenance={"verified": True})
    verified_trace = ProofVerificationTrace(
        trace_id="pvt-good",
        episode_id="episode-1",
        agent_id="agent-1",
        artifacts=[artifact],
        results=[verified_result],
    )
    verified_alchemy = proof_verification_trace_to_alchemical_trace(verified_trace)

    assert advisory_alchemy.has_phase(AlchemicalPhase.DESCENSION)
    assert advisory_alchemy.has_phase(AlchemicalPhase.DISTILLATION)
    assert not advisory_alchemy.has_phase(AlchemicalPhase.FIXATION)
    assert verified_alchemy.has_phase(AlchemicalPhase.FIXATION)


def test_proof_trace_to_agent_experiences_does_not_promote_failed_verifier_runs():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    result = run_proof_verifier(
        artifact,
        verifier_kind=ProofVerifierKind.LEAN,
        command=(sys.executable, "-c", "import sys; sys.exit(1)"),
    )
    trace = ProofVerificationTrace(
        trace_id="pvt-fail",
        episode_id="episode-1",
        agent_id="agent-1",
        artifacts=[artifact],
        results=[result],
    )

    experiences = proof_verification_trace_to_agent_experiences(trace)

    assert experiences
    assert experiences[0].terminal_form is None
    assert not experiences[0].verifier_boundary_crossed


def test_roadmap_alignment_catches_skeleton_as_truth():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    bad = ProofVerificationTrace(
        trace_id="pvt-skeleton-bad",
        episode_id="episode-1",
        agent_id="agent-1",
        artifacts=[artifact],
        results=[
            ProofVerificationResult(
                result_id="skeleton-bad",
                artifact_id=artifact.artifact_id,
                status=ProofVerificationStatus.SKELETON_GENERATED,
                terminal_form=TerminalForm.VERIFIED_PROOF,
                certificate_id="cert-nope",
                verifier_boundary_crossed=False,
            )
        ],
    )

    report = check_roadmap_alignment(proof_verification_traces=[bad])

    assert not report.is_aligned()
    assert {
        "PROOF_VERIFIED_WITHOUT_BOUNDARY",
        "UNVERIFIED_PROOF_STATUS_CLAIMS_TERMINAL",
    }.issubset({finding.code for finding in report.findings})


def test_proof_verification_cli_runs_empty_inputs_and_produces_aligned_report(tmp_path):
    out_json = tmp_path / "proof.json"
    report_json = tmp_path / "alignment.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_proof_verification.py"),
            "--out-json",
            str(out_json),
            "--alignment-report-json",
            str(report_json),
            "--fail-on-critical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    trace = json.loads(out_json.read_text(encoding="utf-8"))
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert trace["artifacts"] == []
    assert trace["results"] == []
    assert report["is_aligned"] is True


def test_proof_verification_cli_can_make_lean_skeleton_without_lean(tmp_path):
    out_json = tmp_path / "proof.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_proof_verification.py"),
            "--make-lean-skeleton",
            "--claim-id",
            "claim-1",
            "--source",
            "x=x",
            "--target",
            "x=x",
            "--theorem-name",
            "mg_cli_smoke",
            "--out-json",
            str(out_json),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    trace = json.loads(out_json.read_text(encoding="utf-8"))
    assert trace["artifacts"][0]["kind"] == "LEAN_SKELETON"
    assert trace["results"][0]["status"] == "VERIFIER_NOT_RUN"

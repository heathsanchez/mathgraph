import json
import subprocess
import sys

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.proof_digestion import (
    DigestionStatus,
    ExpositionNote,
    KeyIdeaCandidate,
    ProofDependencyMap,
    ProofDigestionTrace,
    ProofStepDigest,
    ReusableSchemaCandidate,
    classify_proof_steps,
    digest_proof_artifact,
    extract_dependencies_from_proof_artifact,
    make_assimilation_candidate_id,
    make_exposition_note_id,
    make_key_idea_id,
    make_lawbook_assimilation_candidate,
    make_schema_id,
    make_step_digest_id,
    proof_artifact_from_content,
    proof_digestion_trace_to_agent_experiences,
    proof_digestion_trace_to_alchemical_trace,
    proof_digestion_trace_to_continuation_outputs,
    proof_digestion_trace_to_projection_candidates,
)
from mathgraph.proof_verification import ProofArtifact, ProofArtifactKind, make_lean_skeleton, make_proof_artifact_id
from mathgraph.roadmap_alignment import check_roadmap_alignment


def _artifact() -> ProofArtifact:
    content = """import Mathlib
-- key idea: reduce to a routine closing step
theorem foo : True := by
  have h : True := by trivial
  trivial
  apply h
"""
    return ProofArtifact(
        artifact_id=make_proof_artifact_id({"content": content, "name": "foo"}),
        claim_id="claim-1",
        source="A",
        target="B",
        kind=ProofArtifactKind.LEAN_SKELETON,
        language="lean",
        content=content,
        theorem_name="foo",
        imports=("Init",),
        dependencies=("dep_a", "dep_b"),
        advisory=True,
        metadata={"verified_dependencies": ["dep_a"], "key_idea": "Reduce proof to True introduction."},
    )


def test_dependency_map_serializes_roundtrip():
    dep = extract_dependencies_from_proof_artifact(_artifact())

    assert ProofDependencyMap.from_json(dep.to_json()).to_dict() == dep.to_dict()


def test_step_digest_serializes_roundtrip():
    step = classify_proof_steps(_artifact())[0]

    assert ProofStepDigest.from_dict(step.to_dict()).to_dict() == step.to_dict()


def test_key_idea_candidate_serializes_roundtrip():
    idea = KeyIdeaCandidate(
        key_idea_id=make_key_idea_id("idea"),
        statement="A reusable idea.",
        metadata={"advisory_only": True},
    )

    assert KeyIdeaCandidate.from_json(idea.to_json()).to_dict() == idea.to_dict()


def test_reusable_schema_candidate_serializes_roundtrip():
    schema = ReusableSchemaCandidate(
        schema_id=make_schema_id("schema"),
        name="schema:foo",
        pattern="A -> B",
        conditions=("review required",),
        metadata={"advisory_only": True},
    )

    assert ReusableSchemaCandidate.from_json(schema.to_json()).to_dict() == schema.to_dict()


def test_exposition_note_serializes_roundtrip():
    note = ExpositionNote(
        note_id=make_exposition_note_id("note"),
        title="Digest",
        summary="A note.",
        limitations=("advisory",),
    )

    assert ExpositionNote.from_json(note.to_json()).to_dict() == note.to_dict()


def test_proof_digestion_trace_serializes_roundtrip():
    trace = digest_proof_artifact(_artifact())

    assert ProofDigestionTrace.from_json(trace.to_json()).to_dict() == trace.to_dict()


def test_extract_dependencies_from_proof_artifact_uses_imports_and_dependencies():
    dep = extract_dependencies_from_proof_artifact(_artifact())

    assert "Init" in dep.imports
    assert "Mathlib" in dep.imports
    assert "dep_a" in dep.verified_dependencies
    assert "dep_b" in dep.unverified_dependencies
    assert "foo" in dep.theorem_names


def test_classify_proof_steps_marks_routine_and_load_bearing():
    steps = classify_proof_steps(_artifact())
    classes = {step.classification for step in steps}

    assert "routine" in classes
    assert "load_bearing" in classes


def test_digest_unverified_skeleton_is_advisory_non_terminal():
    trace = digest_proof_artifact(make_lean_skeleton(claim_id="c", source="A", target="B", theorem_name="bar"))

    assert not trace.is_truth_terminal()
    assert trace.advisory is True
    assert trace.terminal_form is None
    assert trace.status in {DigestionStatus.EXPOSITION_READY, DigestionStatus.KEY_IDEA_EXTRACTED, DigestionStatus.REUSABLE_SCHEMA_EXTRACTED}


def test_digest_verified_certificate_inherits_boundary_without_inventing_it():
    trace = digest_proof_artifact(
        _artifact(),
        certificate_id="cert-proof-1",
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=True,
    )
    unsafe = digest_proof_artifact(_artifact(), certificate_id="cert-proof-2", terminal_form=TerminalForm.VERIFIED_PROOF)

    assert trace.is_truth_terminal()
    assert trace.certificate_id == "cert-proof-1"
    assert not unsafe.is_truth_terminal()
    assert unsafe.certificate_id is None


def test_lawbook_assimilation_candidate_ready_only_with_verified_certificate():
    verified = digest_proof_artifact(
        _artifact(),
        certificate_id="cert-proof",
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=True,
    )
    unverified = digest_proof_artifact(_artifact())

    ready = make_lawbook_assimilation_candidate(verified)
    not_ready = make_lawbook_assimilation_candidate(unverified)

    assert ready.ready is True
    assert ready.certificate_id == "cert-proof"
    assert not_ready.ready is False


def test_bridges_preserve_boundary():
    trace = digest_proof_artifact(_artifact())
    alchemy = proof_digestion_trace_to_alchemical_trace(trace)
    experiences = proof_digestion_trace_to_agent_experiences(trace)
    outputs = proof_digestion_trace_to_continuation_outputs(trace)

    assert alchemy.has_phase(AlchemicalPhase.DISTILLATION)
    assert not alchemy.is_promoted()
    assert experiences and all(not exp.verifier_boundary_crossed for exp in experiences)
    assert outputs and all(not output.is_terminal() for output in outputs)


def test_projection_hints_are_advisory():
    trace = digest_proof_artifact(_artifact())
    projections = proof_digestion_trace_to_projection_candidates(trace)

    assert projections
    assert all(candidate.advisory for candidate in projections)


def test_alignment_catches_digest_certificate_without_boundary():
    trace = digest_proof_artifact(_artifact())
    unsafe = ProofDigestionTrace.from_dict(
        {
            **trace.to_dict(),
            "terminal_form": TerminalForm.VERIFIED_PROOF.value,
            "certificate_id": "invented",
            "verifier_boundary_crossed": False,
        }
    )

    report = check_roadmap_alignment(proof_digestion_traces=[unsafe])

    assert report.critical_count() >= 1
    assert any(finding.code == "DIGESTION_TERMINAL_WITHOUT_BOUNDARY" for finding in report.findings)


def test_alignment_catches_key_idea_claiming_proof():
    trace = digest_proof_artifact(_artifact())
    trace.key_ideas[0].statement = "This is VERIFIED_PROOF now."

    report = check_roadmap_alignment(proof_digestion_traces=[trace])

    assert report.critical_count() >= 1
    assert any(finding.code == "KEY_IDEA_CANDIDATE_CLAIMS_PROOF" for finding in report.findings)


def test_cli_runs_with_empty_input(tmp_path):
    out_path = tmp_path / "digestion.json"
    report_path = tmp_path / "alignment.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_proof_digestion.py",
            "--out-json",
            str(out_path),
            "--alignment-report-json",
            str(report_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(out_path.read_text(encoding="utf-8"))["summary"]["traces_total"] == 0


def test_cli_digests_content_input(tmp_path):
    out_path = tmp_path / "digestion.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_proof_digestion.py",
            "--content",
            "theorem foo : True := by trivial",
            "--out-json",
            str(out_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["traces_total"] == 1
    assert payload["traces"][0]["verifier_boundary_crossed"] is False


def test_cli_verified_certificate_inherits_boundary_safely(tmp_path):
    out_path = tmp_path / "digestion.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_proof_digestion.py",
            "--content",
            "theorem foo : True := by trivial",
            "--verified",
            "--certificate-id",
            "cert-cli",
            "--out-json",
            str(out_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["traces"][0]["certificate_id"] == "cert-cli"
    assert payload["traces"][0]["verifier_boundary_crossed"] is True


def test_assimilation_candidate_serializes_roundtrip():
    trace = digest_proof_artifact(_artifact())
    candidate = make_lawbook_assimilation_candidate(trace)
    candidate.assimilation_id = make_assimilation_candidate_id("roundtrip")

    assert type(candidate).from_json(candidate.to_json()).to_dict() == candidate.to_dict()

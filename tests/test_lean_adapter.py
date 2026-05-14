from pathlib import Path

from adapters import lean_adapter
from mathgraph import TerminalForm
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase
from mathgraph.lean_adapter import (
    LeanAdapterTrace,
    LeanArtifactStatus,
    LeanCheckResult,
    LeanEnvironment,
    LeanFileArtifact,
    check_lean_file,
    detect_lean_environment,
    extract_lean_imports,
    extract_lean_theorem_names,
    import_checked_lean_artifact,
    lean_adapter_trace_to_agent_experiences,
    lean_adapter_trace_to_alchemical_trace,
    lean_adapter_trace_to_proof_verification_trace,
    lean_file_from_proof_artifact,
    make_lean_file_id,
    run_lean_adapter_pipeline,
)
from mathgraph.proof_verification import ProofArtifactKind, make_lean_skeleton
from mathgraph.roadmap_alignment import check_roadmap_alignment


EXPECTED_DETECT_KEYS = {
    "lean_path",
    "lake_path",
    "lean_available",
    "lake_available",
    "lean_version",
    "lake_version",
}


def test_detect_lean_returns_expected_keys() -> None:
    result = lean_adapter.detect_lean()

    assert set(result) == EXPECTED_DETECT_KEYS
    assert isinstance(result["lean_available"], bool)
    assert isinstance(result["lake_available"], bool)


def test_verify_lean_file_missing_returns_status(tmp_path: Path) -> None:
    result = lean_adapter.verify_lean_file(tmp_path / "missing.lean")

    assert result["status"] in {"lean_file_missing", "lean_unavailable"}
    assert result["exit_code"] is None


def test_verify_lean_code_handles_unavailable_gracefully(monkeypatch) -> None:
    monkeypatch.setattr(
        lean_adapter,
        "detect_lean",
        lambda: {
            "lean_path": None,
            "lake_path": None,
            "lean_available": False,
            "lake_available": False,
            "lean_version": None,
            "lake_version": None,
        },
    )

    result = lean_adapter.verify_lean_code("theorem t : True := True.intro")

    assert result["status"] == "lean_unavailable"
    assert result["exit_code"] is None


def test_verify_lean_code_success_when_available() -> None:
    if not lean_adapter.detect_lean()["lean_available"]:
        return

    result = lean_adapter.verify_lean_code("theorem t : True := True.intro")

    assert result["status"] == "lean_verified"
    assert result["exit_code"] == 0


def test_verify_lean_code_failure_when_available_is_not_proof() -> None:
    if not lean_adapter.detect_lean()["lean_available"]:
        return

    result = lean_adapter.verify_lean_code("theorem bad : False := by trivial")

    assert result["status"] == "lean_failed"
    assert result["status"] != TerminalForm.VERIFIED_PROOF.value


def test_lean_environment_serializes_roundtrip() -> None:
    env = LeanEnvironment(lean_command=("missing-lean",), lean_available=False, version=None)

    assert LeanEnvironment.from_json(env.to_json()).to_dict() == env.to_dict()


def test_lean_file_artifact_serializes_roundtrip() -> None:
    lean_file = _lean_file()

    assert LeanFileArtifact.from_json(lean_file.to_json()).to_dict() == lean_file.to_dict()


def test_lean_check_result_serializes_roundtrip() -> None:
    result = LeanCheckResult(
        result_id="lean-check-1",
        lean_file_id="lean-file-1",
        status=LeanArtifactStatus.CHECK_NOT_RUN,
    )

    assert LeanCheckResult.from_json(result.to_json()).to_dict() == result.to_dict()


def test_extract_lean_imports_finds_imports() -> None:
    assert extract_lean_imports("import Mathlib\nimport Foo.Bar\n\ntheorem t : True := by trivial") == (
        "Mathlib",
        "Foo.Bar",
    )


def test_extract_lean_theorem_names_finds_theorem_and_lemma() -> None:
    names = extract_lean_theorem_names("theorem t1 : True := by trivial\nlemma l1 : True := by trivial\nexample : True := by trivial")

    assert names == ("t1", "l1")


def test_lean_file_from_proof_artifact_preserves_advisory_boundary() -> None:
    artifact = make_lean_skeleton(claim_id="claim", source="x=x", target="x=x", theorem_name="foo")

    lean_file = lean_file_from_proof_artifact(artifact)

    assert lean_file.proof_artifact_id == artifact.artifact_id
    assert lean_file.status == LeanArtifactStatus.SKELETON
    assert lean_file.advisory is True
    assert "foo" in lean_file.theorem_names


def test_detect_lean_environment_handles_missing_command_gracefully() -> None:
    env = detect_lean_environment(lean_command=("definitely-missing-lean-binary",), lake_command=("definitely-missing-lake-binary",))

    assert env.lean_available is False
    assert env.lake_available is False


def test_check_lean_file_returns_not_available_when_command_missing() -> None:
    env = LeanEnvironment(lean_command=("definitely-missing-lean-binary",), lean_available=False)

    result = check_lean_file(_lean_file(), environment=env)

    assert result.status == LeanArtifactStatus.LEAN_NOT_AVAILABLE
    assert not result.is_verified()


def test_import_checked_lean_artifact_requires_provenance_or_certificate() -> None:
    result = import_checked_lean_artifact(_lean_file())

    assert result.status == LeanArtifactStatus.RESIDUAL
    assert not result.is_verified()


def test_verified_import_creates_terminal_proof_verification_result() -> None:
    result = import_checked_lean_artifact(_lean_file(), provenance={"verified": True})

    assert result.status == LeanArtifactStatus.IMPORTED_VERIFIED
    assert result.is_verified()
    assert result.proof_verification_result is not None
    assert result.proof_verification_result.terminal_form == TerminalForm.VERIFIED_PROOF


def test_check_failed_is_non_terminal() -> None:
    result = LeanCheckResult(
        result_id="lean-check-failed",
        lean_file_id="lean-file",
        status=LeanArtifactStatus.CHECK_FAILED,
        stderr_excerpt="error",
    )

    assert not result.is_verified()
    assert result.certificate_id is None


def test_lean_adapter_trace_summarizes_counts() -> None:
    trace = run_lean_adapter_pipeline(
        lean_files=[_lean_file()],
        environment=LeanEnvironment(lean_available=False),
        check=True,
    )

    assert trace.summary["files_total"] == 1
    assert trace.not_available_count() == 1


def test_bridges_create_proof_alchemy_and_agent_traces_safely() -> None:
    trace = run_lean_adapter_pipeline(lean_files=[_lean_file()])

    proof_trace = lean_adapter_trace_to_proof_verification_trace(trace)
    alchemical = lean_adapter_trace_to_alchemical_trace(trace)
    experiences = lean_adapter_trace_to_agent_experiences(trace)

    assert proof_trace.artifacts[0].kind == ProofArtifactKind.LEAN_FILE
    assert alchemical.has_phase(AlchemicalPhase.DESCENSION)
    assert experiences[0].outcome == AgentExperienceOutcome.ADVISORY_ONLY
    assert not experiences[0].verifier_boundary_crossed


def test_roadmap_alignment_catches_lean_text_as_truth() -> None:
    trace = run_lean_adapter_pipeline(lean_files=[_lean_file()])
    trace.files[0].metadata["terminal_form"] = TerminalForm.VERIFIED_PROOF.value

    report = check_roadmap_alignment(lean_adapter_traces=[trace])

    assert report.critical_count() >= 1
    assert any(finding.code == "LEAN_FILE_ARTIFACT_CLAIMS_TERMINAL" for finding in report.findings)


def test_lean_adapter_cli_runs_empty_input(tmp_path: Path) -> None:
    out = tmp_path / "trace.json"
    report = tmp_path / "alignment.json"
    result = _run_cli("--out-json", str(out), "--alignment-report-json", str(report), "--fail-on-critical")

    assert result.returncode == 0, result.stderr
    assert out.exists()


def test_lean_adapter_cli_content_without_lean_produces_aligned_report(tmp_path: Path) -> None:
    out = tmp_path / "trace.json"
    report = tmp_path / "alignment.json"
    result = _run_cli(
        "--content",
        "theorem t : True := by trivial",
        "--lean-command",
        "definitely-missing-lean-binary",
        "--check",
        "--out-json",
        str(out),
        "--alignment-report-json",
        str(report),
        "--fail-on-critical",
    )

    assert result.returncode == 0, result.stderr
    assert out.exists()


def _lean_file() -> LeanFileArtifact:
    content = "import Mathlib\n\ntheorem foo : True := by trivial\n"
    return LeanFileArtifact(
        lean_file_id=make_lean_file_id(content=content),
        proof_artifact_id=None,
        path=None,
        content=content,
        theorem_names=extract_lean_theorem_names(content),
        imports=extract_lean_imports(content),
        status=LeanArtifactStatus.SKELETON,
        metadata={"advisory_only": True},
    )


def _run_cli(*args: str):
    import subprocess
    import sys

    return subprocess.run(
        [sys.executable, "scripts/run_lean_adapter.py", *args],
        check=False,
        text=True,
        capture_output=True,
    )

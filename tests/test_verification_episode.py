import json
import subprocess
import sys
from pathlib import Path

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.proof_verification import (
    ProofVerificationResult,
    ProofVerificationStatus,
    ProofVerificationTrace,
    ProofVerifierKind,
    import_verified_proof,
    make_lean_skeleton,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.root_constructors import ConstructorAttempt, RootConstructorStatus, RootConstructorTrace
from mathgraph.verification_episode import (
    VerificationEpisodeInput,
    VerificationEpisodeRouteDecision,
    VerificationEpisodeStatus,
    VerificationEpisodeTrace,
    VerificationRouteKind,
    combine_episode_alchemical_trace,
    choose_episode_routes,
    run_verification_episode,
)


ROOT = Path(__file__).resolve().parents[1]


def test_verification_episode_input_serializes_deserializes():
    episode_input = VerificationEpisodeInput(
        claim_id="claim-1",
        source="A",
        target="B",
        source_idx=1,
        target_idx=2,
        route_hint=VerificationRouteKind.BOTH_SIDES,
        agent_id="agent-1",
        episode_id="episode-1",
    )

    restored = VerificationEpisodeInput.from_json(episode_input.to_json())

    assert restored.to_dict() == episode_input.to_dict()


def test_verification_episode_trace_serializes_deserializes():
    trace = run_verification_episode(episode_input=VerificationEpisodeInput(episode_id="episode-1"), run_alignment=False)

    restored = VerificationEpisodeTrace.from_json(trace.to_json())

    assert restored.to_dict() == trace.to_dict()


def test_empty_episode_is_advisory_non_terminal():
    trace = run_verification_episode(episode_input=VerificationEpisodeInput(episode_id="episode-1"))

    assert trace.status in {VerificationEpisodeStatus.EMPTY, VerificationEpisodeStatus.ADVISORY_ONLY}
    assert trace.is_advisory()
    assert not trace.is_terminal()


def test_route_decisions_are_advisory_and_cannot_claim_truth():
    decisions = choose_episode_routes(
        VerificationEpisodeInput(source="A", target="B"),
        route_hint=VerificationRouteKind.BOTH_SIDES,
    )

    assert decisions
    assert all(decision.advisory for decision in decisions)
    assert all("terminal_form" not in decision.to_dict() for decision in decisions)


def test_episode_with_only_lean_skeleton_is_non_terminal():
    trace = run_verification_episode(
        episode_input=VerificationEpisodeInput(claim_id="claim-1", source="x=x", target="x=x", episode_id="episode-1")
    )

    assert trace.proof_verification_trace is not None
    assert trace.proof_verification_trace.artifacts
    assert trace.terminal_form is None
    assert not trace.is_terminal()


def test_episode_with_mock_verifier_unsafe_use_is_caught_by_alignment():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    proof_trace = ProofVerificationTrace(
        trace_id="proof-bad",
        episode_id="episode-1",
        agent_id="agent-1",
        artifacts=[artifact],
        results=[
            ProofVerificationResult(
                result_id="mock-bad",
                artifact_id=artifact.artifact_id,
                status=ProofVerificationStatus.VERIFIER_PASSED,
                verifier_kind=ProofVerifierKind.MOCK_VERIFIER,
                terminal_form=TerminalForm.VERIFIED_PROOF,
                certificate_id="cert-mock",
                verifier_boundary_crossed=True,
                metadata={"test_only": False},
            )
        ],
    )
    episode = VerificationEpisodeTrace(
        episode_id="episode-1",
        input=VerificationEpisodeInput(episode_id="episode-1"),
        status=VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF,
        proof_verification_trace=proof_trace,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id="cert-mock",
        verifier_boundary_crossed=True,
    )

    report = check_roadmap_alignment(proof_verification_traces=[proof_trace], verification_episode_traces=[episode])

    assert not report.is_aligned()
    assert "MOCK_VERIFIER_PRODUCTION_TRUTH" in {finding.code for finding in report.findings}


def test_episode_with_trusted_imported_proof_is_terminal_verified_proof():
    artifact = make_lean_skeleton(claim_id="claim-1", source=None, target=None)
    result = import_verified_proof(artifact=artifact, external_certificate_id="proof-cert", provenance={"verified": True})
    proof_trace = ProofVerificationTrace(
        trace_id="proof-good",
        episode_id="episode-1",
        agent_id="agent-1",
        artifacts=[artifact],
        results=[result],
    )
    episode = VerificationEpisodeTrace(
        episode_id="episode-1",
        input=VerificationEpisodeInput(episode_id="episode-1"),
        status=VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF,
        proof_verification_trace=proof_trace,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id="proof-cert",
        verifier_boundary_crossed=True,
    )

    assert episode.is_terminal()
    assert episode.status == VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF


def test_episode_with_importer_verified_countermodel_subtrace_is_terminal():
    attempt = ConstructorAttempt(
        attempt_id="attempt-good",
        plan_id="plan-1",
        status=RootConstructorStatus.IMPORTER_VERIFIED,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="false-cert",
        verifier_boundary_crossed=True,
    )
    root_trace = RootConstructorTrace(
        trace_id="root-good",
        episode_id="episode-1",
        agent_id="agent-1",
        attempts=[attempt],
    )
    episode = VerificationEpisodeTrace(
        episode_id="episode-1",
        input=VerificationEpisodeInput(episode_id="episode-1"),
        status=VerificationEpisodeStatus.TERMINAL_FINITE_COUNTERMODEL,
        root_constructor_trace=root_trace,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="false-cert",
        verifier_boundary_crossed=True,
    )

    assert episode.is_terminal()
    assert episode.status == VerificationEpisodeStatus.TERMINAL_FINITE_COUNTERMODEL


def test_candidate_table_subtrace_does_not_make_episode_terminal():
    attempt = ConstructorAttempt(
        attempt_id="attempt-candidate",
        plan_id="plan-1",
        status=RootConstructorStatus.CANDIDATE_TABLE_FOUND,
        candidate_artifact_id="candidate-table",
    )
    root_trace = RootConstructorTrace(trace_id="root-candidate", episode_id="episode-1", agent_id=None, attempts=[attempt])
    episode = VerificationEpisodeTrace(
        episode_id="episode-1",
        input=VerificationEpisodeInput(episode_id="episode-1"),
        status=VerificationEpisodeStatus.CONSTRUCTOR_ATTEMPTED,
        root_constructor_trace=root_trace,
    )

    assert not episode.is_terminal()


def test_search_miss_does_not_make_episode_true():
    attempt = ConstructorAttempt(
        attempt_id="attempt-miss",
        plan_id="plan-1",
        status=RootConstructorStatus.SEARCH_MISS,
        failure_reason="bounded miss",
    )
    root_trace = RootConstructorTrace(trace_id="root-miss", episode_id="episode-1", agent_id=None, attempts=[attempt])
    episode = VerificationEpisodeTrace(
        episode_id="episode-1",
        input=VerificationEpisodeInput(episode_id="episode-1"),
        status=VerificationEpisodeStatus.RESIDUAL,
        root_constructor_trace=root_trace,
    )

    assert not episode.is_terminal()
    assert episode.terminal_form is None


def test_combine_episode_alchemical_trace_includes_relevant_phases():
    episode = run_verification_episode(
        episode_input=VerificationEpisodeInput(claim_id="claim-1", source="x=x", target="x=x", episode_id="episode-1"),
        constructor_dry_run=True,
        run_alignment=False,
    )

    alchemy = combine_episode_alchemical_trace(
        episode_id=episode.episode_id,
        agent_id=None,
        projection_trace=episode.projection_trace,
        root_constructor_trace=episode.root_constructor_trace,
        proof_verification_trace=episode.proof_verification_trace,
    )

    assert alchemy.has_phase(AlchemicalPhase.RAW_MATTER)
    assert alchemy.has_phase(AlchemicalPhase.DESCENSION)
    assert alchemy.has_phase(AlchemicalPhase.DISTILLATION)


def test_agent_experiences_from_subtraces_are_included():
    trace = run_verification_episode(
        episode_input=VerificationEpisodeInput(source="x=x", target="x=x", episode_id="episode-1"),
        constructor_dry_run=True,
    )

    assert trace.agent_experiences


def test_roadmap_alignment_catches_unsafe_terminal_episode():
    episode = VerificationEpisodeTrace(
        episode_id="episode-bad",
        input=VerificationEpisodeInput(episode_id="episode-bad"),
        status=VerificationEpisodeStatus.TERMINAL_VERIFIED_PROOF,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=False,
    )

    report = check_roadmap_alignment(verification_episode_traces=[episode])

    assert not report.is_aligned()
    assert {
        "EPISODE_TERMINAL_WITHOUT_BOUNDARY",
        "EPISODE_VERIFIED_PROOF_WITHOUT_PROOF_TRACE",
    }.issubset({finding.code for finding in report.findings})


def test_verification_episode_cli_runs_empty_inputs_and_produces_aligned_advisory_episode(tmp_path):
    out_json = tmp_path / "episode.json"
    report_json = tmp_path / "alignment.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_verification_episode.py"),
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

    data = json.loads(out_json.read_text(encoding="utf-8"))
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert data["terminal_form"] is None
    assert report["is_aligned"] is True


def test_verification_episode_cli_source_target_creates_advisory_skeleton_without_lean(tmp_path):
    out_json = tmp_path / "episode.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_verification_episode.py"),
            "--claim-id",
            "claim-1",
            "--source",
            "x=x",
            "--target",
            "x=x",
            "--out-json",
            str(out_json),
            "--fail-on-critical",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["proof_verification_trace"]["artifacts"][0]["kind"] == "LEAN_SKELETON"
    assert data["terminal_form"] is None

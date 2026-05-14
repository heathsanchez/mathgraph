import json
import subprocess
import sys

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import (
    ContinuationAction,
    ContinuationActionInput,
    ContinuationActionKind,
    ContinuationActionOutput,
    ContinuationActionStatus,
    ContinuationActionTrace,
    ContinuationOutputKind,
    apply_continuation_action,
    continuation_outputs_to_episode_inputs,
    continuation_outputs_to_projection_candidates,
    continuation_outputs_to_proof_artifacts,
    continuation_trace_to_agent_experiences,
    continuation_trace_to_alchemical_trace,
    default_continuation_action_registry,
    form_equivalence_claim,
    form_implication_claim,
    make_continuation_action_id,
    make_continuation_input_id,
    make_continuation_output_id,
    make_continuation_trace_id,
    run_continuation_actions,
)
from mathgraph.domain_claims import FormalWorldKind, parse_domain_claim
from mathgraph.proof_verification import ProofArtifactKind
from mathgraph.roadmap_alignment import check_roadmap_alignment


def _action(kind: ContinuationActionKind) -> ContinuationAction:
    return default_continuation_action_registry().by_kind(kind)[0]


def _magma_claim():
    return parse_domain_claim("x*x=x => x*y=x").domain_claim


def _lean_claim():
    return parse_domain_claim("theorem foo : True := by trivial").domain_claim


def test_continuation_action_serializes_roundtrip():
    action = _action(ContinuationActionKind.DUALIZE)

    assert ContinuationAction.from_json(action.to_json()).to_dict() == action.to_dict()


def test_continuation_action_input_serializes_roundtrip():
    action_input = ContinuationActionInput(
        input_id=make_continuation_input_id("input"),
        domain_claims=[_magma_claim()],
        raw_texts=["a=b"],
        metadata={"advisory_only": True},
    )

    assert ContinuationActionInput.from_json(action_input.to_json()).to_dict() == action_input.to_dict()


def test_continuation_action_output_serializes_roundtrip():
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("output"),
        action_id=make_continuation_action_id(ContinuationActionKind.EMIT_OBSTRUCTION_TASK, "emit_obstruction_task"),
        kind=ContinuationOutputKind.OBSTRUCTION_CANDIDATE,
        status=ContinuationActionStatus.PRODUCED_CANDIDATE,
        obstruction_name="candidate_obstruction",
        metadata={"advisory_only": True},
    )

    assert ContinuationActionOutput.from_json(output.to_json()).to_dict() == output.to_dict()
    assert ContinuationActionOutput.from_jsonl_line(output.to_jsonl_line()).output_id == output.output_id


def test_continuation_action_trace_serializes_roundtrip():
    action_input = ContinuationActionInput(input_id=make_continuation_input_id("input"))
    action = _action(ContinuationActionKind.EMIT_PROOF_TASK)
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("note"),
        action_id=action.action_id,
        kind=ContinuationOutputKind.NOTE,
        status=ContinuationActionStatus.ADVISORY_ONLY,
        note="advisory",
        metadata={"advisory_only": True},
    )
    trace = ContinuationActionTrace(
        trace_id=make_continuation_trace_id(action_input.to_dict(), action.to_dict(), output.to_dict()),
        input=action_input,
        actions=[action],
        outputs=[output],
    )

    assert ContinuationActionTrace.from_json(trace.to_json()).to_dict() == trace.to_dict()


def test_default_registry_includes_core_actions():
    registry = default_continuation_action_registry()

    assert registry.by_kind(ContinuationActionKind.SPECIALIZE)
    assert registry.by_kind(ContinuationActionKind.EMIT_PROOF_TASK)
    assert registry.by_kind(ContinuationActionKind.PROJECT_LAWBOOK_ENTRY)


def test_form_implication_claim_creates_advisory_domain_claim():
    claim = form_implication_claim("x*x=x", "x*y=x")

    assert claim.world == FormalWorldKind.MAGMA_EQUATIONAL
    assert claim.advisory is True
    assert claim.source == "x*x=x"
    assert claim.target == "x*y=x"


def test_form_equivalence_claim_creates_two_advisory_implications():
    claims = form_equivalence_claim("x*x=x", "x=y")

    assert len(claims) == 2
    assert {claim.source for claim in claims} == {"x*x=x", "x=y"}
    assert all(claim.advisory for claim in claims)


def test_lean_claim_emit_proof_task_produces_advisory_proof_artifact():
    action_input = ContinuationActionInput(input_id=make_continuation_input_id("lean"), domain_claims=[_lean_claim()])

    outputs = apply_continuation_action(_action(ContinuationActionKind.EMIT_PROOF_TASK), action_input)

    assert outputs[0].kind == ContinuationOutputKind.PROOF_ARTIFACT
    assert outputs[0].proof_artifact.kind == ProofArtifactKind.LEAN_SKELETON
    assert outputs[0].proof_artifact.advisory is True
    assert not outputs[0].is_terminal()


def test_magma_claim_emit_countermodel_task_produces_advisory_episode_input():
    action_input = ContinuationActionInput(input_id=make_continuation_input_id("magma"), domain_claims=[_magma_claim()])

    outputs = apply_continuation_action(_action(ContinuationActionKind.EMIT_COUNTERMODEL_TASK), action_input)

    assert outputs[0].kind == ContinuationOutputKind.EPISODE_INPUT
    assert outputs[0].episode_input.source == "x*x=x"
    assert outputs[0].task_payload["task_kind"] == "countermodel_search"
    assert not outputs[0].is_terminal()


def test_projection_task_action_produces_advisory_projection_candidate():
    action_input = ContinuationActionInput(input_id=make_continuation_input_id("magma"), domain_claims=[_magma_claim()])

    outputs = apply_continuation_action(_action(ContinuationActionKind.EMIT_PROJECTION_TASK), action_input)

    assert outputs[0].kind == ContinuationOutputKind.PROJECTION_CANDIDATE
    assert outputs[0].projection_candidate.advisory is True
    assert not outputs[0].is_terminal()


def test_action_output_is_not_terminal_without_verifier_boundary():
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("unsafe"),
        action_id="action",
        kind=ContinuationOutputKind.PROOF_ARTIFACT,
        status=ContinuationActionStatus.PRODUCED_TASK,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        metadata={"advisory_only": True},
    )

    assert not output.is_terminal()


def test_run_continuation_actions_works_on_empty_input():
    trace = run_continuation_actions(action_input=ContinuationActionInput(input_id=make_continuation_input_id("empty")))

    assert trace.output_count() >= 1
    assert trace.terminal_count() == 0
    assert trace.summary["terminal_outputs"] == 0


def test_run_continuation_actions_produces_outputs_for_magma_implication():
    trace = run_continuation_actions(
        action_input=ContinuationActionInput(input_id=make_continuation_input_id("magma"), domain_claims=[_magma_claim()]),
        action_kinds=[ContinuationActionKind.EMIT_COUNTERMODEL_TASK, ContinuationActionKind.EMIT_PROJECTION_TASK],
    )

    assert trace.summary["episode_input_outputs"] == 1
    assert trace.summary["projection_candidate_outputs"] == 1
    assert trace.terminal_count() == 0


def test_bridges_preserve_advisory_boundary():
    trace = run_continuation_actions(
        action_input=ContinuationActionInput(input_id=make_continuation_input_id("magma"), domain_claims=[_magma_claim()]),
        action_kinds=[ContinuationActionKind.EMIT_COUNTERMODEL_TASK, ContinuationActionKind.EMIT_PROOF_TASK, ContinuationActionKind.EMIT_PROJECTION_TASK],
    )

    alchemical = continuation_trace_to_alchemical_trace(trace)
    experiences = continuation_trace_to_agent_experiences(trace)

    assert alchemical.has_phase(AlchemicalPhase.RAW_MATTER)
    assert alchemical.has_phase(AlchemicalPhase.DESCENSION)
    assert not alchemical.is_promoted()
    assert experiences
    assert all(not exp.verifier_boundary_crossed for exp in experiences)
    assert continuation_outputs_to_episode_inputs(trace)
    assert continuation_outputs_to_projection_candidates(trace)
    assert continuation_outputs_to_proof_artifacts(trace)


def test_roadmap_alignment_catches_generated_proof_treated_as_truth():
    action_input = ContinuationActionInput(input_id=make_continuation_input_id("unsafe"))
    action = _action(ContinuationActionKind.EMIT_PROOF_TASK)
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("unsafe"),
        action_id=action.action_id,
        kind=ContinuationOutputKind.PROOF_ARTIFACT,
        status=ContinuationActionStatus.PRODUCED_TASK,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        metadata={"advisory_only": True},
    )
    trace = ContinuationActionTrace(
        trace_id=make_continuation_trace_id(action_input.to_dict(), output.to_dict()),
        input=action_input,
        actions=[action],
        outputs=[output],
    )

    report = check_roadmap_alignment(continuation_action_traces=[trace])

    assert report.critical_count() >= 1
    assert any(finding.code == "CONTINUATION_OUTPUT_TERMINAL_WITHOUT_BOUNDARY" for finding in report.findings)


def test_cli_runs_with_empty_input(tmp_path):
    out_path = tmp_path / "continuation.json"
    report_path = tmp_path / "alignment.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_continuation_actions.py",
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
    assert json.loads(out_path.read_text(encoding="utf-8"))["summary"]["terminal_outputs"] == 0


def test_cli_parses_claim_and_emits_advisory_outputs(tmp_path):
    out_path = tmp_path / "continuation.json"
    episode_path = tmp_path / "episodes.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_continuation_actions.py",
            "--claim",
            "x*x=x => x*y=x",
            "--action-kind",
            "EMIT_COUNTERMODEL_TASK",
            "--out-json",
            str(out_path),
            "--out-episode-inputs-jsonl",
            str(episode_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["episode_input_outputs"] == 1
    rows = [json.loads(line) for line in episode_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["source"] == "x*x=x"

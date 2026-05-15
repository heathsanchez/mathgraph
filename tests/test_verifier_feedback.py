import json
import importlib
import subprocess
import sys

from mathgraph.alchemy import AlchemicalPhase
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import ContinuationOutputKind
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_feedback import (
    FlawSeverity,
    RepairActionKind,
    RepairLoopTrace,
    VerifierFeedback,
    classify_flaw_from_message,
    feedback_from_text,
    make_repair_loop_trace_id,
    plan_repair_from_feedback,
    repair_loop_trace_to_agent_experiences,
    repair_loop_trace_to_alchemical_trace,
    repair_loop_trace_to_continuation_outputs,
    run_repair_loop,
)


def test_verifier_feedback_serializes_roundtrip():
    feedback = feedback_from_text(raw_message="unknown identifier foo", artifact_id="a1")

    assert VerifierFeedback.from_json(feedback.to_json()).to_dict() == feedback.to_dict()
    assert VerifierFeedback.from_jsonl_line(feedback.to_jsonl_line()).feedback_id == feedback.feedback_id


def test_repair_plan_serializes_roundtrip():
    feedback = feedback_from_text(raw_message="unknown identifier foo")
    plan = plan_repair_from_feedback(feedback)[0]

    assert type(plan).from_json(plan.to_json()).to_dict() == plan.to_dict()


def test_repair_loop_trace_serializes_roundtrip():
    trace = run_repair_loop([feedback_from_text(raw_message="type mismatch")])

    assert RepairLoopTrace.from_json(trace.to_json()).to_dict() == trace.to_dict()


def test_classify_minor_repairable_syntax_import_errors():
    assert classify_flaw_from_message("syntax error near theorem") == FlawSeverity.MINOR_REPAIRABLE
    assert classify_flaw_from_message("missing import Mathlib") == FlawSeverity.MINOR_REPAIRABLE


def test_classify_structural_gaps():
    assert classify_flaw_from_message("unsolved goals remain") == FlawSeverity.STRUCTURAL_GAP
    assert classify_flaw_from_message("failed to synthesize instance") == FlawSeverity.STRUCTURAL_GAP


def test_classify_critical_invalidation_language():
    assert classify_flaw_from_message("counterexample found") == FlawSeverity.CRITICAL_INVALIDATION
    assert classify_flaw_from_message("invalid certificate payload") == FlawSeverity.CRITICAL_INVALIDATION


def test_classify_passed_success_as_none():
    assert classify_flaw_from_message("verified successfully") == FlawSeverity.NONE


def test_roadmap_alignment_module_compiles_and_imports():
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", "mathgraph/roadmap_alignment.py"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert importlib.import_module("mathgraph.roadmap_alignment") is not None


def test_negative_verification_phrases_are_not_none():
    assert classify_flaw_from_message("not verified") != FlawSeverity.NONE
    assert classify_flaw_from_message("verification failed") != FlawSeverity.NONE


def test_verified_false_theorem_is_not_success():
    assert classify_flaw_from_message("verified false theorem") == FlawSeverity.CRITICAL_INVALIDATION


def test_counterexample_found_but_verified_is_critical():
    assert classify_flaw_from_message("counterexample found but verified") == FlawSeverity.CRITICAL_INVALIDATION


def test_feedback_from_text_creates_advisory_feedback():
    feedback = feedback_from_text(raw_message="type mismatch", claim_id="c1", verifier_kind="LEAN")

    assert feedback.advisory is True
    assert feedback.claim_id == "c1"
    assert feedback.flaw_severity == FlawSeverity.STRUCTURAL_GAP


def test_raw_text_verified_successfully_does_not_create_terminal_truth():
    feedback = feedback_from_text(raw_message="verified successfully")
    trace = run_repair_loop([feedback])

    assert feedback.status.value == "PASSED"
    assert feedback.metadata["text_feedback_not_verifier_boundary"] is True
    assert not trace.is_terminal()


def test_plan_minor_repairable_to_local_revise():
    feedback = feedback_from_text(raw_message="unknown identifier foo")
    plans = plan_repair_from_feedback(feedback)

    assert plans[0].action_kind == RepairActionKind.LOCAL_REVISE
    assert plans[0].continuation_output is not None


def test_plan_structural_gap_to_reroute_and_proof_task():
    feedback = feedback_from_text(raw_message="unsolved goals")
    kinds = {plan.action_kind for plan in plan_repair_from_feedback(feedback)}

    assert RepairActionKind.REROUTE in kinds
    assert RepairActionKind.EMIT_PROOF_TASK in kinds


def test_plan_critical_invalidation_to_obstruction_or_residual():
    feedback = feedback_from_text(raw_message="counterexample found")
    kinds = {plan.action_kind for plan in plan_repair_from_feedback(feedback)}

    assert RepairActionKind.EMIT_OBSTRUCTION_TASK in kinds
    assert RepairActionKind.MARK_RESIDUAL in kinds


def test_run_repair_loop_works_on_empty_feedback():
    trace = run_repair_loop([])

    assert trace.feedback_count() == 0
    assert trace.repair_plan_count() == 0
    assert trace.summary["feedback_total"] == 0


def test_run_repair_loop_emits_advisory_continuation_outputs():
    trace = run_repair_loop([feedback_from_text(raw_message="unknown identifier foo")])

    assert trace.continuation_outputs
    assert all(not output.is_terminal() for output in trace.continuation_outputs)


def test_repair_loop_output_not_terminal_without_boundary():
    trace = run_repair_loop([feedback_from_text(raw_message="unknown identifier foo")])

    assert not trace.is_terminal()


def test_bridges_preserve_boundary():
    trace = run_repair_loop([feedback_from_text(raw_message="counterexample found")])
    alchemy = repair_loop_trace_to_alchemical_trace(trace)
    experiences = repair_loop_trace_to_agent_experiences(trace)
    outputs = repair_loop_trace_to_continuation_outputs(trace)

    assert alchemy.has_phase(AlchemicalPhase.DISTILLATION)
    assert not alchemy.is_promoted()
    assert experiences and all(not exp.verifier_boundary_crossed for exp in experiences)
    assert outputs and all(output.kind in {ContinuationOutputKind.TASK, ContinuationOutputKind.OBSTRUCTION_CANDIDATE} for output in outputs)


def test_agent_experience_bridge_does_not_emit_verified_proof_for_raw_feedback():
    trace = run_repair_loop([feedback_from_text(raw_message="verified successfully")])

    experiences = repair_loop_trace_to_agent_experiences(trace)

    assert experiences[0].outcome == AgentExperienceOutcome.ADVISORY_ONLY
    assert experiences[0].terminal_form is None
    assert experiences[0].verifier_boundary_crossed is False


def test_alignment_catches_repair_trace_certificate_without_boundary():
    trace = run_repair_loop([feedback_from_text(raw_message="unknown identifier foo")])
    unsafe = RepairLoopTrace.from_dict(
        {
            **trace.to_dict(),
            "terminal_form": TerminalForm.VERIFIED_PROOF.value,
            "certificate_id": "invented",
            "verifier_boundary_crossed": False,
        }
    )

    report = check_roadmap_alignment(repair_loop_traces=[unsafe])

    assert report.critical_count() >= 1
    assert any(finding.code == "REPAIR_TRACE_TERMINAL_WITHOUT_BOUNDARY" for finding in report.findings)


def test_alignment_catches_natural_language_repair_marked_as_truth():
    feedback = feedback_from_text(raw_message="natural_language critique says VERIFIED_PROOF", artifact_id="a1")
    feedback.metadata["verifier_boundary"] = True

    report = check_roadmap_alignment(verifier_feedback_items=[feedback])

    assert report.critical_count() >= 1
    assert any(finding.code == "NATURAL_LANGUAGE_REPAIR_AS_VERIFICATION" for finding in report.findings)


def test_alignment_catches_raw_text_feedback_claiming_boundary():
    feedback = feedback_from_text(raw_message="verified successfully", artifact_id="a1")
    feedback.metadata["verifier_boundary"] = True

    report = check_roadmap_alignment(verifier_feedback_items=[feedback])

    assert report.critical_count() >= 1
    assert any(finding.code == "RAW_TEXT_FEEDBACK_AS_VERIFIER_BOUNDARY" for finding in report.findings)


def test_cli_runs_with_empty_input(tmp_path):
    out_path = tmp_path / "repair.json"
    report_path = tmp_path / "alignment.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_verifier_feedback.py",
            "--out-repair-trace-json",
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
    assert json.loads(out_path.read_text(encoding="utf-8"))["summary"]["feedback_total"] == 0


def test_cli_runs_with_message_input_and_emits_repair_trace(tmp_path):
    out_path = tmp_path / "repair.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_verifier_feedback.py",
            "--message",
            "unknown identifier foo",
            "--out-repair-trace-json",
            str(out_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["minor_repairable_count"] == 1
    assert payload["repair_plans"]


def test_cli_writes_continuation_outputs_jsonl(tmp_path):
    out_path = tmp_path / "outputs.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_verifier_feedback.py",
            "--message",
            "unsolved goals",
            "--out-continuation-outputs-jsonl",
            str(out_path),
            "--fail-on-critical",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert rows


def test_make_repair_loop_trace_id_is_deterministic():
    assert make_repair_loop_trace_id("x") == make_repair_loop_trace_id("x")

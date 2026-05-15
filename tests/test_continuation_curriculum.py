import json
import subprocess
import sys

from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import (
    ContinuationActionOutput,
    ContinuationActionStatus,
    ContinuationOutputKind,
    make_continuation_output_id,
)
from mathgraph.continuation_curriculum import (
    ContinuationCurriculum,
    CurriculumStage,
    CurriculumStageKind,
    CurriculumTraceStatus,
    build_continuation_curriculum,
    build_curriculum_from_actions,
    build_curriculum_from_proof_digestion,
    build_curriculum_from_projection_candidates,
    build_curriculum_from_repair_loop,
    build_curriculum_from_verifier_feedback,
    build_empty_curriculum,
    build_magma_equational_curriculum,
    curriculum_to_agent_experiences,
    curriculum_to_alchemical_trace,
    curriculum_to_continuation_outputs,
    curriculum_to_episode_inputs,
    curriculum_to_route_telemetry_events,
    make_curriculum_stage_id,
)
from mathgraph.proof_digestion import digest_proof_artifact, proof_artifact_from_content
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind, make_projection_candidate_id
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_feedback import feedback_from_text, run_repair_loop


def test_curriculum_stage_serializes_roundtrip():
    stage = CurriculumStage(stage_id=make_curriculum_stage_id("s"), kind=CurriculumStageKind.PROOF_TASK, title="proof")
    assert CurriculumStage.from_json(stage.to_json()).to_dict() == stage.to_dict()


def test_continuation_curriculum_serializes_roundtrip():
    curriculum = build_magma_equational_curriculum(source="x*x=x", target="x*y=x", claim_id="c")
    assert ContinuationCurriculum.from_json(curriculum.to_json()).to_dict() == curriculum.to_dict()


def test_empty_curriculum_is_advisory_and_non_terminal():
    curriculum = build_empty_curriculum()
    assert curriculum.status == CurriculumTraceStatus.EMPTY
    assert curriculum.advisory is True
    assert not curriculum.is_terminal()


def test_magma_curriculum_emits_core_stages():
    kinds = {stage.kind for stage in build_magma_equational_curriculum(source="x*x=x", target="x*y=x").stages}
    assert {CurriculumStageKind.TARGET, CurriculumStageKind.WARMUP_CLAIM, CurriculumStageKind.FINITE_EXAMPLE, CurriculumStageKind.PROOF_TASK, CurriculumStageKind.COUNTERMODEL_TASK} <= kinds


def test_curriculum_from_actions_converts_tasks():
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("counter"),
        action_id="a",
        kind=ContinuationOutputKind.TASK,
        status=ContinuationActionStatus.PRODUCED_TASK,
        task_payload={"task_kind": "countermodel_search"},
    )
    curriculum = build_curriculum_from_actions([output])
    assert curriculum.stages[0].kind == CurriculumStageKind.COUNTERMODEL_TASK


def test_feedback_minor_maps_to_repair_task():
    curriculum = build_curriculum_from_verifier_feedback([feedback_from_text(raw_message="syntax error")])
    assert any(stage.kind == CurriculumStageKind.REPAIR_TASK for stage in curriculum.stages)


def test_feedback_structural_maps_to_proof_or_prerequisite():
    curriculum = build_curriculum_from_verifier_feedback([feedback_from_text(raw_message="unsolved goals")])
    assert any(stage.kind in {CurriculumStageKind.PROOF_TASK, CurriculumStageKind.PREREQUISITE_LEMMA} for stage in curriculum.stages)


def test_feedback_critical_maps_to_countermodel_or_residual():
    curriculum = build_curriculum_from_verifier_feedback([feedback_from_text(raw_message="counterexample found")])
    assert any(stage.kind in {CurriculumStageKind.COUNTERMODEL_TASK, CurriculumStageKind.RESIDUAL_REVIEW} for stage in curriculum.stages)


def test_curriculum_from_repair_loop_preserves_plan_ids():
    trace = run_repair_loop([feedback_from_text(raw_message="syntax error")])
    curriculum = build_curriculum_from_repair_loop(trace)
    assert any(stage.repair_plan_id == trace.repair_plans[0].repair_plan_id for stage in curriculum.stages)


def test_curriculum_from_proof_digestion_emits_tasks():
    digest = digest_proof_artifact(proof_artifact_from_content("theorem foo : True := by\n  have h : True := trivial\n  exact h"))
    curriculum = build_curriculum_from_proof_digestion(digest)
    assert any(stage.kind in {CurriculumStageKind.PROOF_TASK, CurriculumStageKind.DIGESTION_TASK, CurriculumStageKind.PROJECTION_TASK} for stage in curriculum.stages)


def test_curriculum_from_projection_candidates_emits_projection_stages():
    candidate = ProjectionCandidate(candidate_id=make_projection_candidate_id("p"), source_claim_id="a", target_claim_id="b", rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY)
    curriculum = build_curriculum_from_projection_candidates([candidate])
    assert curriculum.stages[0].kind == CurriculumStageKind.PROJECTION_TASK


def test_build_continuation_curriculum_deduplicates_stages():
    curriculum = build_continuation_curriculum(source="x*x=x", target="x*y=x", projection_candidates=[])
    assert len(curriculum.stages) == len({stage.stage_id for stage in curriculum.stages})


def test_build_continuation_curriculum_respects_max_stages():
    curriculum = build_continuation_curriculum(source="x*x=x", target="x*y=x", max_stages=3)
    assert len(curriculum.stages) == 3


def test_curriculum_to_continuation_outputs_are_advisory():
    outputs = curriculum_to_continuation_outputs(build_magma_equational_curriculum(source="x*x=x", target="x*y=x"))
    assert outputs
    assert all(not output.is_terminal() for output in outputs)


def test_curriculum_to_episode_inputs_emits_dict_payloads():
    rows = curriculum_to_episode_inputs(build_magma_equational_curriculum(source="x*x=x", target="x*y=x", claim_id="c"))
    assert rows
    assert all("source" in row and "target" in row for row in rows)


def test_curriculum_to_alchemical_trace_has_no_fixation():
    trace = curriculum_to_alchemical_trace(build_magma_equational_curriculum(source="x*x=x", target="x*y=x"))
    assert trace.has_phase(AlchemicalPhase.RAW_MATTER)
    assert not trace.has_phase(AlchemicalPhase.FIXATION)


def test_curriculum_to_agent_experiences_never_emit_verified_proof():
    experiences = curriculum_to_agent_experiences(build_magma_equational_curriculum(source="x*x=x", target="x*y=x"))
    assert experiences
    assert all(exp.outcome != AgentExperienceOutcome.VERIFIED_PROOF for exp in experiences)


def test_curriculum_to_route_telemetry_events_are_dicts():
    events = curriculum_to_route_telemetry_events(build_magma_equational_curriculum(source="x*x=x", target="x*y=x"))
    assert events and isinstance(events[0], dict)
    assert events[0]["advisory"] is True


def test_alignment_catches_curriculum_terminal_truth_without_boundary():
    curriculum = build_empty_curriculum()
    curriculum.terminal_form = TerminalForm.VERIFIED_PROOF
    curriculum.certificate_id = "cert"
    report = check_roadmap_alignment(continuation_curricula=[curriculum])
    assert any(f.code == "CURRICULUM_TERMINAL_WITHOUT_BOUNDARY" for f in report.findings)


def test_alignment_catches_stage_claiming_terminal_truth():
    curriculum = build_empty_curriculum()
    curriculum.stages = [CurriculumStage(stage_id="s", kind=CurriculumStageKind.PROOF_TASK, metadata={"terminal_form": "VERIFIED_PROOF"})]
    report = check_roadmap_alignment(continuation_curricula=[curriculum])
    assert any(f.code == "CURRICULUM_STAGE_CLAIMS_TERMINAL_TRUTH" for f in report.findings)


def test_alignment_warns_on_target_without_stages():
    curriculum = build_empty_curriculum(target_claim_id="c")
    report = check_roadmap_alignment(continuation_curricula=[curriculum])
    assert any(f.code == "CURRICULUM_TARGET_WITHOUT_STAGES" for f in report.findings)


def test_cli_runs_empty_input(tmp_path):
    out = tmp_path / "curriculum.json"
    result = subprocess.run([sys.executable, "scripts/run_continuation_curriculum.py", "--out-curriculum-json", str(out)], capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(out.read_text())["status"] == "EMPTY"


def test_cli_runs_source_target_input(tmp_path):
    out = tmp_path / "curriculum.json"
    result = subprocess.run([sys.executable, "scripts/run_continuation_curriculum.py", "--source", "x*x=x", "--target", "x*y=x", "--out-curriculum-json", str(out)], capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(out.read_text())["summary"]["stage_total"] > 0


def test_cli_writes_episode_inputs_jsonl(tmp_path):
    out = tmp_path / "episodes.jsonl"
    result = subprocess.run([sys.executable, "scripts/run_continuation_curriculum.py", "--source", "x*x=x", "--target", "x*y=x", "--out-episode-inputs-jsonl", str(out)], capture_output=True, text=True)
    assert result.returncode == 0
    assert out.read_text().strip()


def test_cli_writes_alignment_report(tmp_path):
    out = tmp_path / "alignment.json"
    result = subprocess.run([sys.executable, "scripts/run_continuation_curriculum.py", "--source", "x*x=x", "--target", "x*y=x", "--alignment-report-json", str(out)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "critical_count" in json.loads(out.read_text())


def test_no_curriculum_object_is_terminal_by_default():
    assert not build_magma_equational_curriculum(source="x*x=x", target="x*y=x").is_terminal()

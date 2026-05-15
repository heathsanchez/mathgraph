import json
import subprocess
import sys

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace
from mathgraph.certificates import TerminalForm
from mathgraph.continuation_actions import ContinuationActionOutput, ContinuationActionStatus, ContinuationOutputKind, make_continuation_output_id
from mathgraph.continuation_curriculum import CurriculumStage, CurriculumStageKind, build_magma_equational_curriculum, make_curriculum_stage_id
from mathgraph.discovery_value import (
    DiscoveryValueDecision,
    DiscoveryValueObjectKind,
    DiscoveryValueReport,
    DiscoveryValueScore,
    DiscoveryValueSignal,
    DiscoveryValueSignalKind,
    build_discovery_value_report,
    discovery_value_report_to_agent_experiences,
    discovery_value_report_to_alchemical_trace,
    discovery_value_report_to_continuation_outputs,
    discovery_value_report_to_curriculum,
    make_discovery_value_score_id,
    make_discovery_value_signal_id,
    score_agent_experience,
    score_alchemical_trace,
    score_continuation_output,
    score_curriculum,
    score_curriculum_stage,
    score_lawbook_assimilation_candidate,
    score_projection_candidate,
    score_proof_digestion_trace,
    score_repair_plan,
    score_repair_loop,
    score_route_telemetry_event,
    score_verifier_feedback,
)
from mathgraph.proof_digestion import digest_proof_artifact, make_lawbook_assimilation_candidate, proof_artifact_from_content
from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind, make_projection_candidate_id
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_feedback import feedback_from_text, run_repair_loop


def _signal():
    return DiscoveryValueSignal(
        signal_id=make_discovery_value_signal_id("s"),
        kind=DiscoveryValueSignalKind.PROOF_POTENTIAL,
        value=2.0,
    )


def test_signal_roundtrip():
    signal = _signal()
    assert DiscoveryValueSignal.from_json(signal.to_json()).to_dict() == signal.to_dict()


def test_score_roundtrip():
    score = DiscoveryValueScore(score_id=make_discovery_value_score_id("s"), object_id="o", object_kind=DiscoveryValueObjectKind.RAW_TASK, signals=[_signal()])
    score.recompute()
    assert DiscoveryValueScore.from_json(score.to_json()).to_dict() == score.to_dict()


def test_report_roundtrip():
    report = build_discovery_value_report(raw_tasks=[{"task": "x"}])
    assert DiscoveryValueReport.from_json(report.to_json()).to_dict() == report.to_dict()


def test_empty_report_is_advisory_and_nonterminal():
    report = build_discovery_value_report()
    assert report.advisory is True
    assert report.summary["terminal_count"] == 0
    assert report.score_count() == 0


def test_score_curriculum_detects_core_stages():
    score = score_curriculum(build_magma_equational_curriculum(source="x*x=x", target="x*y=x"))
    kinds = {signal.kind for signal in score.signals}
    assert {DiscoveryValueSignalKind.CURRICULUM_VALUE, DiscoveryValueSignalKind.PROOF_POTENTIAL, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL, DiscoveryValueSignalKind.CERTIFICATE_POTENTIAL} <= kinds


def test_score_curriculum_is_not_terminal():
    assert not score_curriculum(build_magma_equational_curriculum(source="x*x=x", target="x*y=x")).is_terminal()


def test_score_curriculum_stage_handles_task_kinds():
    for kind in [CurriculumStageKind.PROOF_TASK, CurriculumStageKind.COUNTERMODEL_TASK, CurriculumStageKind.PROJECTION_TASK, CurriculumStageKind.REPAIR_TASK]:
        score = score_curriculum_stage(CurriculumStage(stage_id=make_curriculum_stage_id(kind.value), kind=kind))
        assert score.signals


def test_score_proof_digestion_rewards_digest_artifacts():
    trace = digest_proof_artifact(proof_artifact_from_content("theorem foo : True := by\n  -- key idea\n  exact trivial"))
    score = score_proof_digestion_trace(trace)
    assert any(signal.kind == DiscoveryValueSignalKind.DIGESTION_VALUE for signal in score.signals)


def test_score_feedback_minor_is_repair_value():
    score = score_verifier_feedback(feedback_from_text(raw_message="syntax error"))
    assert any(signal.kind == DiscoveryValueSignalKind.REPAIR_VALUE for signal in score.signals)


def test_score_feedback_structural_has_obstruction_or_proof():
    score = score_verifier_feedback(feedback_from_text(raw_message="unsolved goals"))
    assert any(signal.kind in {DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, DiscoveryValueSignalKind.PROOF_POTENTIAL} for signal in score.signals)


def test_score_feedback_critical_has_obstruction_and_countermodel():
    score = score_verifier_feedback(feedback_from_text(raw_message="counterexample found"))
    kinds = {signal.kind for signal in score.signals}
    assert {DiscoveryValueSignalKind.OBSTRUCTION_POTENTIAL, DiscoveryValueSignalKind.COUNTERMODEL_POTENTIAL} <= kinds


def test_score_repair_loop_rewards_plans_not_truth():
    score = score_repair_loop(run_repair_loop([feedback_from_text(raw_message="syntax error")]))
    assert score.raw_score > 0
    assert not score.is_terminal()


def test_score_repair_plan_and_assimilation_candidate_are_first_class():
    repair = run_repair_loop([feedback_from_text(raw_message="syntax error")]).repair_plans[0]
    digest = digest_proof_artifact(proof_artifact_from_content("theorem foo : True := by trivial"))
    assimilation = make_lawbook_assimilation_candidate(digest)
    assert score_repair_plan(repair).object_kind == DiscoveryValueObjectKind.REPAIR_PLAN
    assert score_lawbook_assimilation_candidate(assimilation).object_kind == DiscoveryValueObjectKind.LAWBOOK_ASSIMILATION_CANDIDATE


def test_score_projection_candidate_rewards_confidence():
    candidate = ProjectionCandidate(candidate_id=make_projection_candidate_id("p"), source_claim_id="a", target_claim_id="b", rule_kind=ProjectionRuleKind.TRANSITIVITY, confidence=0.9)
    assert score_projection_candidate(candidate).raw_score > 0


def test_score_continuation_output_handles_task():
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("proof"),
        action_id="a",
        kind=ContinuationOutputKind.PROOF_ARTIFACT,
        status=ContinuationActionStatus.PRODUCED_TASK,
        task_payload={"task_kind": "proof_task"},
    )
    assert score_continuation_output(output).raw_score > 0


def test_score_alchemical_trace_rewards_projection_compression():
    trace = AlchemicalTrace(trace_id="a")
    trace.add_step(phase=AlchemicalPhase.PROJECTION, status=AlchemicalStatus.ADVISORY_ONLY, compression_gain=1.0)
    assert score_alchemical_trace(trace).raw_score > 0


def test_score_agent_experience_uses_gains_and_costs():
    exp = AgentExperience(experience_id="e", agent_id="a", episode_id=None, claim_id=None, route=None, phase=None, outcome=AgentExperienceOutcome.ADVISORY_ONLY, compression_gain=1.0, cost_units=5)
    score = score_agent_experience(exp)
    assert any(signal.kind == DiscoveryValueSignalKind.COST_PENALTY for signal in score.signals)


def test_score_route_event_kill_penalty():
    score = score_route_telemetry_event({"event_id": "r", "killed": True, "route_kind": "PROOF_VERIFICATION"})
    assert any(signal.kind == DiscoveryValueSignalKind.ROUTE_SURVIVAL_VALUE and signal.value < 0 for signal in score.signals)


def test_report_ranks_descending_and_normalizes():
    report = build_discovery_value_report(curricula=[build_magma_equational_curriculum(source="x*x=x", target="x*y=x")], raw_tasks=[{"task": "low"}])
    assert report.scores == sorted(report.scores, key=lambda score: (-score.normalized_score, -score.expected_gain, -score.raw_score, score.object_id))
    assert all(0.0 <= score.normalized_score <= 1.0 for score in report.scores)


def test_report_creates_varied_decisions():
    curriculum = build_magma_equational_curriculum(source="x*x=x", target="x*y=x")
    projection = ProjectionCandidate(candidate_id=make_projection_candidate_id("p2"), source_claim_id="a", target_claim_id="b", confidence=1.0)
    feedback = feedback_from_text(raw_message="syntax error")
    report = build_discovery_value_report(curricula=[curriculum], projection_candidates=[projection], verifier_feedback_items=[feedback], raw_tasks=[{"task": "unknown"}])
    decisions = {score.decision for score in report.scores}
    assert DiscoveryValueDecision.NEEDS_REPAIR in decisions
    assert DiscoveryValueDecision.PROJECT in decisions
    assert decisions & {DiscoveryValueDecision.RUN_NOW, DiscoveryValueDecision.QUEUE_SOON, DiscoveryValueDecision.HOLD_IN_CHORA}


def test_high_risk_object_is_not_run_now():
    output = ContinuationActionOutput(
        output_id=make_continuation_output_id("unsafe"),
        action_id="a",
        kind=ContinuationOutputKind.PROOF_ARTIFACT,
        status=ContinuationActionStatus.PRODUCED_TASK,
        terminal_form=TerminalForm.VERIFIED_PROOF,
    )
    report = build_discovery_value_report(continuation_outputs=[output])
    assert report.scores[0].decision != DiscoveryValueDecision.RUN_NOW


def test_report_bridges_are_advisory():
    report = build_discovery_value_report(curricula=[build_magma_equational_curriculum(source="x*x=x", target="x*y=x")])
    outputs = discovery_value_report_to_continuation_outputs(report)
    curriculum = discovery_value_report_to_curriculum(report)
    alchemy = discovery_value_report_to_alchemical_trace(report)
    experiences = discovery_value_report_to_agent_experiences(report)
    assert all(not output.is_terminal() for output in outputs)
    assert not curriculum.is_terminal()
    assert not alchemy.has_phase(AlchemicalPhase.FIXATION)
    assert all(exp.outcome not in {AgentExperienceOutcome.VERIFIED_PROOF, AgentExperienceOutcome.FINITE_COUNTERMODEL} for exp in experiences)


def test_alignment_catches_score_terminal_without_boundary():
    score = DiscoveryValueScore(score_id="s", object_id="o", object_kind=DiscoveryValueObjectKind.RAW_TASK, terminal_form=TerminalForm.VERIFIED_PROOF, certificate_id="cert")
    report = check_roadmap_alignment(discovery_value_scores=[score])
    assert any(f.code == "DISCOVERY_VALUE_TERMINAL_WITHOUT_BOUNDARY" for f in report.findings)


def test_alignment_catches_value_as_proof():
    score = DiscoveryValueScore(score_id="s", object_id="o", object_kind=DiscoveryValueObjectKind.RAW_TASK, signals=[_signal()], metadata={"value_as_truth": True, "terminal_form": "VERIFIED_PROOF"})
    report = check_roadmap_alignment(discovery_value_scores=[score])
    assert any(f.code == "DISCOVERY_VALUE_AS_TRUTH" for f in report.findings)


def test_cli_runs_empty(tmp_path):
    out = tmp_path / "report.json"
    result = subprocess.run([sys.executable, "scripts/run_discovery_value.py", "--out-report-json", str(out)], capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(out.read_text())["status"] == "EMPTY"


def test_cli_scores_curriculum_and_writes_outputs(tmp_path):
    curriculum = build_magma_equational_curriculum(source="x*x=x", target="x*y=x")
    source = tmp_path / "curriculum.json"
    curriculum.write_json(source)
    report = tmp_path / "report.json"
    outputs = tmp_path / "outputs.jsonl"
    emitted_curriculum = tmp_path / "emitted_curriculum.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_discovery_value.py",
            "--curriculum-json",
            str(source),
            "--out-report-json",
            str(report),
            "--out-continuation-outputs-jsonl",
            str(outputs),
            "--out-curriculum-json",
            str(emitted_curriculum),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(report.read_text())["summary"]["score_total"] == 1
    assert emitted_curriculum.exists()
    assert outputs.exists()

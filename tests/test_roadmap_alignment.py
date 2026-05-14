import importlib.metadata

from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalTrace
from mathgraph.certificates import TerminalForm
from mathgraph.roadmap_alignment import check_roadmap_alignment


def test_roadmap_alignment_catches_advisory_output_falsely_claiming_terminal_truth():
    exp = AgentExperience(
        experience_id="exp-bad",
        agent_id="agent-1",
        episode_id="episode-1",
        claim_id="claim-a",
        route="h_tilt_pick",
        phase="FIXATION",
        outcome=AgentExperienceOutcome.VERIFIED_PROOF,
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verifier_boundary_crossed=False,
    )

    report = check_roadmap_alignment(agent_experiences=[exp])

    assert not report.is_aligned()
    assert report.critical_count() >= 1
    assert {
        "EXPERIENCE_TERMINAL_WITHOUT_BOUNDARY",
        "ADVISORY_OUTCOME_FALSELY_TERMINAL",
    }.issubset({finding.code for finding in report.findings})


def test_roadmap_alignment_passes_clean_minimal_episode():
    trace = AlchemicalTrace(
        trace_id="trace-clean",
        claim_id="claim-a",
        agent_id="agent-1",
        episode_id="episode-1",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        promoted_certificate_id="cert-1",
    )
    trace.add_step(phase=AlchemicalPhase.RAW_MATTER, status=AlchemicalStatus.ADVISORY_ONLY)
    trace.add_step(
        phase=AlchemicalPhase.CALCINATION,
        status=AlchemicalStatus.SUCCEEDED,
        compression_gain=0.25,
    )
    trace.add_step(
        phase=AlchemicalPhase.DESCENSION,
        status=AlchemicalStatus.SUCCEEDED,
        residual_delta=-1,
    )
    trace.add_step(
        phase=AlchemicalPhase.FIXATION,
        status=AlchemicalStatus.PROMOTED_BY_VERIFIER,
        verifier_boundary="FINITE_CHECKED",
    )
    trace.add_step(
        phase=AlchemicalPhase.PROJECTION,
        status=AlchemicalStatus.SUCCEEDED,
        compression_gain=0.5,
    )
    exp = AgentExperience(
        experience_id="exp-clean",
        agent_id="agent-1",
        episode_id="episode-1",
        claim_id="claim-a",
        route="finite_magma",
        phase="FIXATION",
        outcome=AgentExperienceOutcome.FINITE_COUNTERMODEL,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="cert-1",
        compression_gain=0.75,
        projection_gain=0.25,
        derived_amplification=1.2,
        residual_delta=-1,
        verifier_boundary_crossed=True,
        taste_delta={"route:finite_magma": 0.1},
    )
    summary = {
        "residual_compression_gain": 0.75,
        "derived_amplification": 1.2,
        "metadata": {"h_tilt_lite": "advisory-only not truth"},
    }

    report = check_roadmap_alignment(
        alchemical_traces=[trace],
        agent_experiences=[exp],
        summary=summary,
    )

    assert report.is_aligned()
    assert report.critical_count() == 0
    assert {finding.code for finding in report.findings} >= {
        "TERMINAL_CONTRACT_RESPECTED",
        "PROJECTION_RECORDED",
        "AGENT_TASTE_UPDATED",
        "RESIDUAL_GOT_SHARPER",
        "DERIVED_AMPLIFICATION_OBSERVED",
    }


def test_new_runtime_layer_requires_no_new_dependency():
    metadata = importlib.metadata.metadata("mathgraph")
    requires = metadata.get_all("Requires-Dist") or []
    runtime_requires = [req for req in requires if "extra ==" not in req]

    assert runtime_requires == []

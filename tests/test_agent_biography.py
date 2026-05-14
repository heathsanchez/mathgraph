from mathgraph.agent_biography import (
    AgentBiography,
    AgentExperience,
    AgentExperienceOutcome,
    AgentProfile,
    score_route_htilt_lite,
)
from mathgraph.certificates import TerminalForm


def test_agent_experience_serializes_deserializes():
    exp = AgentExperience(
        experience_id="exp-1",
        agent_id="agent-1",
        episode_id="episode-1",
        claim_id="claim-a",
        route="finite_magma",
        phase="DESCENSION",
        outcome=AgentExperienceOutcome.FINITE_COUNTERMODEL,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="cert-1",
        cost_units=2.0,
        compression_gain=0.5,
        projection_gain=0.25,
        derived_amplification=1.0,
        verifier_boundary_crossed=True,
    )

    restored = AgentExperience.from_json(exp.to_json())

    assert restored.to_dict() == exp.to_dict()


def test_agent_biography_updates_route_and_phase_taste_deterministically():
    bio = AgentBiography(AgentProfile(agent_id="agent-1", name="Route Shaper"))
    exp = AgentExperience(
        experience_id="exp-1",
        agent_id="agent-1",
        episode_id="episode-1",
        claim_id="claim-a",
        route="finite_magma",
        phase="DESCENSION",
        outcome=AgentExperienceOutcome.FINITE_COUNTERMODEL,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="cert-1",
        cost_units=2.0,
        compression_gain=0.5,
        projection_gain=0.25,
        derived_amplification=1.0,
        verifier_boundary_crossed=True,
    )

    updates = bio.update_taste_from_experience(exp, learning_rate=0.1)

    assert updates == {"route:finite_magma": 0.455, "phase:DESCENSION": 0.455}
    assert bio.profile.taste_weights["route:finite_magma"] == 0.455
    assert bio.profile.taste_weights["phase:DESCENSION"] == 0.455


def test_failed_search_increments_scars_and_does_not_create_terminal_truth():
    bio = AgentBiography(AgentProfile(agent_id="agent-1", name="Scar Keeper"))
    exp = AgentExperience(
        experience_id="exp-failed",
        agent_id="agent-1",
        episode_id="episode-1",
        claim_id="claim-a",
        route="root_probe",
        phase="CALCINATION",
        outcome=AgentExperienceOutcome.FAILED_SEARCH,
        cost_units=10.0,
        scar_tags=("timeout",),
        verifier_boundary_crossed=False,
    )

    bio.add_experience(exp)
    bio.update_taste_from_experience(exp)

    assert exp.terminal_form is None
    assert not exp.verifier_boundary_crossed
    assert bio.profile.scar_counts["timeout"] == 1
    assert bio.profile.scar_counts["FAILED_SEARCH"] == 1
    assert bio.profile.scar_counts["route:root_probe"] == 1


def test_htilt_lite_score_changes_with_taste_scar_cost_and_beta():
    profile = AgentProfile(
        agent_id="agent-1",
        name="Taste",
        taste_weights={"route:finite_magma": 1.0},
        scar_counts={"route:finite_magma": 2},
    )

    baseline = score_route_htilt_lite("finite_magma", base_score=0.0, beta=1.0)
    tasted = score_route_htilt_lite(
        "finite_magma",
        agent=profile,
        base_score=0.0,
        expected_cost=0.1,
        expected_projection_gain=0.2,
        expected_compression_gain=0.3,
        beta=1.0,
    )
    hotter = score_route_htilt_lite(
        "finite_magma",
        agent=profile,
        base_score=0.0,
        expected_cost=0.1,
        expected_projection_gain=0.2,
        expected_compression_gain=0.3,
        beta=2.0,
    )
    costly = score_route_htilt_lite(
        "finite_magma",
        agent=profile,
        base_score=0.0,
        expected_cost=3.0,
        beta=1.0,
    )

    assert tasted.taste_score == 1.0
    assert tasted.scar_penalty == 0.5
    assert tasted.cost_penalty == 0.1
    assert tasted.final_score > baseline.final_score
    assert hotter.final_score > tasted.final_score
    assert costly.final_score < tasted.final_score

from mathgraph.alchemy import (
    AlchemicalPhase,
    AlchemicalStatus,
    AlchemicalStep,
    AlchemicalTrace,
    make_alchemical_trace_id,
)
from mathgraph.certificates import TerminalForm


def test_alchemical_trace_serializes_deserializes():
    trace = AlchemicalTrace(
        trace_id=make_alchemical_trace_id("claim-a", "episode-1"),
        claim_id="claim-a",
        agent_id="agent-1",
        episode_id="episode-1",
    )
    trace.add_step(
        AlchemicalStep(
            phase=AlchemicalPhase.RAW_MATTER,
            status=AlchemicalStatus.ADVISORY_ONLY,
            output_artifact_ids=("residual-a",),
            route="seed",
            cost_units=1.5,
            residual_delta=-1,
            compression_gain=0.25,
            advisory_notes=("not truth",),
        )
    )

    restored = AlchemicalTrace.from_json(trace.to_json())

    assert restored.to_dict() == trace.to_dict()
    assert restored.phases_seen() == (AlchemicalPhase.RAW_MATTER,)
    assert restored.last_status() == AlchemicalStatus.ADVISORY_ONLY
    assert restored.total_cost() == 1.5
    assert restored.total_residual_delta() == -1
    assert restored.total_compression_gain() == 0.25


def test_advisory_fixation_without_verifier_promotion_is_not_promoted():
    trace = AlchemicalTrace(trace_id="trace-advisory", claim_id="claim-a")
    trace.add_step(phase=AlchemicalPhase.FIXATION, status=AlchemicalStatus.ADVISORY_ONLY)

    assert trace.is_fixed()
    assert not trace.is_promoted()


def test_verifier_promoted_trace_is_promoted():
    trace = AlchemicalTrace(
        trace_id="trace-promoted",
        claim_id="claim-a",
        terminal_form=TerminalForm.VERIFIED_PROOF,
        promoted_certificate_id="cert-1",
    )
    trace.add_step(
        phase=AlchemicalPhase.FIXATION,
        status=AlchemicalStatus.PROMOTED_BY_VERIFIER,
        verifier_boundary="LEAN_TYPECHECKED",
    )

    assert trace.is_promoted()

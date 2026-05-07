from mathgraph.backend_results import (
    ModelFinderResult,
    ModelFinderStatus,
    ProofFinderResult,
    ProofFinderStatus,
)


def test_backend_results_do_not_promote_misses():
    proof_miss = ProofFinderResult("p0", "c", "b", None, None, ProofFinderStatus.NO_PROOF_FOUND)
    assert not proof_miss.is_authoritative()
    assert "not refutation" in proof_miss.advisory_warning()

    proof_hit = ProofFinderResult(
        "p1", "c", "b", None, None, ProofFinderStatus.PROOF_FOUND,
        proof_artifact_id="artifact", trust_level="LEAN_VERIFIED", artifact_risk="LOW"
    )
    assert proof_hit.is_authoritative()

    model_miss = ModelFinderResult("m0", "c", "b", None, None, ModelFinderStatus.NO_MODEL_FOUND)
    assert not model_miss.is_authoritative()
    assert "not proof" in model_miss.advisory_warning()

    model_hit = ModelFinderResult("m1", "c", "b", None, None, ModelFinderStatus.MODEL_FOUND, model_payload={"n": 2})
    assert model_hit.is_refutation_candidate()
    assert not model_hit.is_authoritative()

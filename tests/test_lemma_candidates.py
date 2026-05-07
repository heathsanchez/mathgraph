from mathgraph.lemma_candidates import (
    LemmaCandidate,
    LemmaCandidateStatus,
    canonical_lemma_name,
    lemma_candidate_from_motif,
)
from mathgraph.proof_motifs import ProofMotif, ProofMotifKind


def test_lemma_candidate_truth_boundary_and_factory():
    assert canonical_lemma_name("Projection Left", "Collapse") == "mg_projection_left_collapse"
    candidate = LemmaCandidate("lc", "mg_candidate")
    assert not candidate.is_verified()
    assert not candidate.is_authoritative()
    assert "not theorems" in candidate.advisory_warning()

    verified = LemmaCandidate(
        "lc2",
        "mg_verified",
        status=LemmaCandidateStatus.LEAN_VERIFIED,
        trust_level="LEAN_VERIFIED",
        verification_status="LEAN_VERIFIED",
        verifier_id="lean",
    )
    assert verified.is_verified()
    assert verified.is_authoritative()

    motif = ProofMotif("pm", ProofMotifKind.PROJECTION_FORCED, support_count=3, unique_claims=3)
    generated = lemma_candidate_from_motif(motif)
    assert generated.expected_covered_claims == 3
    assert generated.proof_motif_id == "pm"

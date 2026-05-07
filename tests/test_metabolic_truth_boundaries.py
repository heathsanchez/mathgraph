from mathgraph.lean_artifacts import LeanArtifact, LeanVerificationStatus
from mathgraph.lemma_candidates import LemmaCandidate
from mathgraph.metabolic_cycle import build_route_yield_stats
from mathgraph.proof_motifs import ProofMotif


def test_advisory_objects_do_not_become_truth():
    motif = ProofMotif(proof_motif_id="pm1", motif_kind="UNKNOWN")
    lemma = LemmaCandidate(lemma_candidate_id="lc1", candidate_name="candidate")
    sketch = LeanArtifact(
        lean_artifact_id="la1",
        artifact_kind="PROOF_SKETCH",
        name="sketch",
        verification_status=LeanVerificationStatus.GENERATED,
    )
    assert not motif.is_authoritative()
    assert not lemma.is_authoritative()
    assert not sketch.is_authoritative()


def test_route_scores_and_no_countermodel_are_advisory():
    stats = build_route_yield_stats(
        [
            {"route": "finite_countermodel", "terminal_form": "NAMED_OBSTRUCTION"},
            {"route": "finite_countermodel", "terminal_form": "FINITE_COUNTERMODEL"},
        ]
    )
    assert stats["finite_countermodel"]["advisory_only"]
    assert stats["finite_countermodel"]["named_obstructions"] == 1
    assert stats["finite_countermodel"]["finite_countermodels"] == 1


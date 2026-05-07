from mathgraph.lean_artifacts import (
    LeanArtifact,
    LeanArtifactKind,
    LeanVerificationStatus,
    render_lean_skeleton,
)
from mathgraph.lemma_candidates import LemmaCandidate


def test_lean_artifact_skeleton_and_authority():
    artifact = LeanArtifact("la", LeanArtifactKind.PROOF_SKETCH, "candidate")
    assert not artifact.is_authoritative()
    assert artifact.summary()["truth_boundary"]

    verified = LeanArtifact(
        "la2",
        LeanArtifactKind.COMPLETE_PROOF,
        "verified",
        verification_status=LeanVerificationStatus.LEAN_VERIFIED,
        trust_level="LEAN_VERIFIED",
    )
    assert verified.is_verified()
    assert verified.is_authoritative()

    skeleton = render_lean_skeleton(LemmaCandidate("lc", "mg_candidate", lean_statement="True"))
    assert "theorem mg_candidate" in skeleton
    assert "not authoritative" in skeleton

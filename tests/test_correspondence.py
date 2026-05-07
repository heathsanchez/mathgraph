from mathgraph.correspondence import CorrespondenceClaim, CorrespondenceStatus


def test_correspondence_authority_requires_artifact_and_safe_trust():
    advisory = CorrespondenceClaim("c0", "k", None, "cond", "axiom", status=CorrespondenceStatus.ADVISORY)
    assert not advisory.is_authoritative()
    assert "advisory" in advisory.advisory_warning()

    no_artifact = CorrespondenceClaim(
        "c1", "k", None, "cond", "axiom", status=CorrespondenceStatus.VERIFIED, trust_level="LEAN_VERIFIED"
    )
    assert not no_artifact.is_authoritative()

    verified = CorrespondenceClaim(
        "c2",
        "k",
        None,
        "cond",
        "axiom",
        status=CorrespondenceStatus.VERIFIED,
        proof_artifact_id="p",
        trust_level="LEAN_VERIFIED",
    )
    assert verified.is_authoritative()

    refuted = CorrespondenceClaim(
        "c3",
        "k",
        None,
        "cond",
        "axiom",
        status=CorrespondenceStatus.REFUTED,
        countermodel_artifact_id="m",
        trust_level="FINITE_VERIFIED",
    )
    assert refuted.is_authoritative()

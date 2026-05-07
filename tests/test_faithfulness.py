from mathgraph.faithfulness import (
    FaithfulnessAssessment,
    FaithfulnessStatus,
    SoundnessStatus,
)


def test_faithfulness_support_requires_soundness_and_no_counterexamples():
    unknown = FaithfulnessAssessment("fa0", "aot", None, "emb", "AOT", "HOL")
    assert not unknown.is_promotion_supporting()
    assert "risk" in unknown.risk_note()

    good = FaithfulnessAssessment(
        "fa1",
        "aot",
        None,
        "emb",
        "AOT",
        "HOL",
        status=FaithfulnessStatus.MECHANIZED,
        soundness_status=SoundnessStatus.SOUND,
    )
    assert good.is_promotion_supporting()

    failed = FaithfulnessAssessment(
        "fa2",
        "aot",
        None,
        "emb",
        "AOT",
        "HOL",
        status=FaithfulnessStatus.FAILED,
        soundness_status=SoundnessStatus.SOUND,
    )
    assert not failed.is_promotion_supporting()

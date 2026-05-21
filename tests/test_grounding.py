from mathgraph.grounding import GroundingFunctionSpec, GroundingRecord, GroundingStatus, SensorSignature


def _record() -> GroundingRecord:
    return GroundingRecord(
        "g1",
        "HOT",
        SensorSignature("s1", "scalar", 1, 1.0, (0.0, 1.0)),
        GroundingFunctionSpec("mean", "mean threshold", threshold=0.5),
    )


def test_strong_signal_grounds():
    grounded = _record().attempt_grounding([0.8, 0.9])
    assert grounded.status == GroundingStatus.EMPIRICALLY_GROUNDED


def test_weak_signal_is_partial():
    grounded = _record().attempt_grounding([0.1, 0.2])
    assert grounded.status == GroundingStatus.PARTIALLY_GROUNDED


def test_empty_signal_fails():
    grounded = _record().attempt_grounding([])
    assert grounded.status == GroundingStatus.GROUNDING_FAILED


def test_custom_htilt_function_is_used():
    grounded = _record().attempt_grounding([0.1], htilt_fn=lambda signal: 0.95)
    assert grounded.status == GroundingStatus.EMPIRICALLY_GROUNDED
    assert grounded.confidence == 0.95


def test_payload_cannot_cross_verifier_boundary():
    payload = _record().attempt_grounding([0.8]).to_denotation_payload()
    assert payload["can_cross_verifier_boundary"] is False
    assert payload["advisory"] is True


def test_advisory_always_true():
    assert GroundingRecord.from_json(_record().to_json()).advisory is True

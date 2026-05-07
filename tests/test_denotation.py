import pytest

from mathgraph.denotation import DenotationRecord, DenotationStatus, can_promote_denotation, require_denotes


def test_denotation_promotion_guard():
    assert can_promote_denotation(DenotationStatus.DENOTES)
    for status in [
        DenotationStatus.UNKNOWN,
        DenotationStatus.NON_DENOTING,
        DenotationStatus.BLOCKED_BY_FREE_LOGIC,
    ]:
        assert not can_promote_denotation(status)
        with pytest.raises(ValueError):
            require_denotes(status)


def test_denotation_record_roundtrip():
    record = DenotationRecord(
        denotation_id="d1",
        object_id="o1",
        domain_kernel_id="aot",
        formal_world_id="w",
        denotation_status=DenotationStatus.DENOTES,
        reason="primitive object imported",
    )
    assert DenotationRecord.from_dict(record.to_dict()).denotation_status is DenotationStatus.DENOTES

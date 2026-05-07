from mathgraph.denotation import DenotationStatus
from mathgraph.reason_containment import ContainmentMode, ReasonContainmentRecord
from mathgraph.trust import TrustLevel


def test_reason_containment_is_advisory_without_certificate():
    record = ReasonContainmentRecord(
        containment_id="c",
        reason_node_id="r",
        domain_kernel_id="etp_magma",
        formal_world_id="w",
        source_id="s",
        target_id="t",
        containment_mode=ContainmentMode.SOURCE_CONTAINS_TARGET,
        denotation_status=DenotationStatus.DENOTES,
    )
    assert not record.is_authoritative()
    assert "advisory" in record.advisory_warning()


def test_reason_containment_authoritative_only_with_certificate():
    record = ReasonContainmentRecord(
        containment_id="c",
        reason_node_id="r",
        domain_kernel_id="etp_magma",
        formal_world_id="w",
        source_id="s",
        target_id="t",
        containment_mode=ContainmentMode.COUNTERMODEL_SEPARATES,
        separator_certificate_id="cert",
        trust_level=TrustLevel.FINITE_VERIFIED,
        denotation_status=DenotationStatus.DENOTES,
    )
    assert record.is_authoritative()

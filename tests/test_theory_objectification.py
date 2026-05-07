from mathgraph.denotation import DenotationStatus
from mathgraph.theory_objectification import (
    AnalyticTruth,
    TheoryDenotation,
    TheoryObjectKind,
    TheoryObjectificationMap,
    TheoryReading,
)
from mathgraph.trust import ProvenanceType, TrustLevel


def test_theory_objectification_records():
    mapping = TheoryObjectificationMap(
        map_id="m",
        domain_kernel_id="etp_magma",
        formal_world_id="w",
        theory_id="T",
        description="terms to objects",
    )
    assert mapping.to_dict()["trust_level"] == TrustLevel.ADVISORY_ROUTE.value
    denotation = TheoryDenotation(
        denotation_id="d",
        domain_kernel_id="etp_magma",
        formal_world_id="w",
        theory_id="T",
        source_symbol="◇",
        source_kind=TheoryObjectKind.OPERATION_SYMBOL,
        target_object_id="op_T",
        target_type_expr="<i,i>",
        denotation_status=DenotationStatus.DENOTES,
    )
    assert denotation.to_dict()["source_kind"] == "OPERATION_SYMBOL"


def test_reading_and_analytic_truth_authority_guard():
    reading = TheoryReading(
        reading_id="r",
        domain_kernel_id="aot",
        formal_world_id="w",
        theory_id="AOT",
        source_statement="theorem X",
        reading_statement="X_AOT",
        reading_type_expr="<>",
        denotation_status=DenotationStatus.UNKNOWN,
    )
    assert not reading.is_authoritative()
    assert not AnalyticTruth(
        analytic_truth_id="a",
        domain_kernel_id="aot",
        formal_world_id="w",
        theory_id="AOT",
        statement="X",
        reading_id="r",
        denotation_status=DenotationStatus.UNKNOWN,
    ).is_authoritative()
    assert AnalyticTruth(
        analytic_truth_id="b",
        domain_kernel_id="aot",
        formal_world_id="w",
        theory_id="AOT",
        statement="X",
        reading_id="r",
        trust_level=TrustLevel.LEAN_VERIFIED,
        provenance_type=ProvenanceType.IMPORTED,
        verifier_id="isabelle",
        denotation_status=DenotationStatus.DENOTES,
    ).is_authoritative()

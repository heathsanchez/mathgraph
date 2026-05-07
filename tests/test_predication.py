from mathgraph.denotation import DenotationStatus
from mathgraph.predication import PredicationMode, PredicateKind, encodes, exemplifies
from mathgraph.trust import ProvenanceType, TrustLevel


def test_encoding_is_not_exemplification_or_authority():
    fact = encodes(
        "root1",
        "projection_left",
        predicate_kind=PredicateKind.ADVISORY_FEATURE,
        denotation_status=DenotationStatus.DENOTES,
    )
    assert fact.mode is PredicationMode.ENCODES
    assert not fact.is_authoritative()


def test_safe_exemplification_can_be_authoritative():
    fact = exemplifies(
        "cert1",
        "FINITE_COUNTERMODEL",
        predicate_kind=PredicateKind.TERMINAL_FEATURE,
        trust_level=TrustLevel.FINITE_VERIFIED,
        provenance_type=ProvenanceType.PRIMITIVE,
        denotation_status=DenotationStatus.DENOTES,
    )
    assert fact.mode is PredicationMode.EXEMPLIFIES
    assert fact.is_authoritative()

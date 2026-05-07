from mathgraph import ProvenanceType, TrustLevel
from mathgraph.trust import TrustProvenance, provenance_type, trust_level


def test_trust_and_provenance_are_orthogonal():
    pair = TrustProvenance(
        trust_level=TrustLevel.FINITE_VERIFIED,
        provenance_type=ProvenanceType.DERIVED,
    )
    assert pair.to_dict() == {
        "trust_level": "FINITE_VERIFIED",
        "provenance_type": "DERIVED",
    }


def test_trust_provenance_roundtrip_and_safe_defaults():
    pair = TrustProvenance.from_dict({"trust_level": "LEAN_VERIFIED", "provenance_type": "PRIMITIVE"})
    assert pair.trust_level is TrustLevel.LEAN_VERIFIED
    assert pair.provenance_type is ProvenanceType.PRIMITIVE
    assert trust_level("unknown") is TrustLevel.ADVISORY_ROUTE
    assert provenance_type("unknown") is ProvenanceType.IMPORTED

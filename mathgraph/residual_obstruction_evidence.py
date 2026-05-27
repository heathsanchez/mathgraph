"""Loaders for residual obstruction atlas evidence packs."""

from __future__ import annotations

from mathgraph.evidence_packs import EvidencePack, EvidencePackError, load_evidence_pack


RESIDUAL_ZERO_PRINCIPLE = "RESIDUAL_ZERO_MEANS_INCOMPLETE_WITNESS_UNIVERSE"
RESIDUAL_OBSTRUCTION_V8_4_PACK = "residual_obstruction_atlas_v8_4"


def load_residual_obstruction_v8_4_evidence() -> EvidencePack:
    pack = load_evidence_pack(
        RESIDUAL_OBSTRUCTION_V8_4_PACK,
        required_fields=(
            "official_false_pairs",
            "finite_covered_false",
            "remaining_frontier",
            "top_constructor_pressure",
            "named_principle",
        ),
    )
    validate_residual_zero_principle(pack)
    return pack


def validate_residual_zero_principle(pack: EvidencePack) -> None:
    if pack.metrics.get("named_principle") != RESIDUAL_ZERO_PRINCIPLE:
        raise EvidencePackError(f"{pack.pack_id} does not preserve {RESIDUAL_ZERO_PRINCIPLE}")
    boundary = pack.trust_boundary
    if boundary.get("residual_zero_is_not_true") is not True:
        raise EvidencePackError(f"{pack.pack_id} must mark residual-zero as not TRUE")

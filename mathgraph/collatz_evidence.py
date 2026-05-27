"""Loaders for frozen Collatz evidence packs.

The Collatz v12.2 pack is fixation-stage evidence, not a proof.  The loader
keeps that boundary explicit so downstream code cannot treat the candidate law
as a verified theorem.
"""

from __future__ import annotations

from mathgraph.evidence_packs import EvidencePack, EvidencePackError, load_evidence_pack


COLLATZ_V12_2_PACK = "collatz_primitive_divisor_v12_2"


def load_collatz_v12_2_evidence() -> EvidencePack:
    pack = load_evidence_pack(
        COLLATZ_V12_2_PACK,
        required_fields=(
            "not_a_proof",
            "main_obstruction",
            "primitive_growth_pairs",
            "pairs_processed",
            "total_integer_candidate_count",
        ),
    )
    validate_collatz_v12_2_not_a_proof(pack)
    return pack


def validate_collatz_v12_2_not_a_proof(pack: EvidencePack) -> None:
    if pack.metrics.get("not_a_proof") is not True:
        raise EvidencePackError(f"{pack.pack_id} must be marked not_a_proof")
    if pack.metrics.get("main_obstruction") != "UNCANCELLED_PRIMITIVE_DIVISOR_GROWTH":
        raise EvidencePackError(f"{pack.pack_id} does not preserve the v12.2 obstruction name")
    if int(pack.metrics.get("total_integer_candidate_count", -1)) != 0:
        raise EvidencePackError(f"{pack.pack_id} unexpectedly reports integer candidates")

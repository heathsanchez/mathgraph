"""Loaders for root-node persistent-filtration evidence packs."""

from __future__ import annotations

from mathgraph.evidence_packs import EvidencePack, EvidencePackError, load_evidence_pack


ROOT_NODE_V16_3_PACK = "root_node_persistent_filtration_v16_3"
REQUIRED_ROOT_NODE_FIELDS: tuple[str, ...] = (
    "path_concentration_score",
    "load_bearing_score",
    "persistence_score",
    "constructor_yield",
    "obstruction_yield",
    "lawbook_compression_gain",
    "null_lift",
    "shadow_duplicate_discount",
    "effective_filtration_count",
)


def load_root_node_v16_3_evidence() -> EvidencePack:
    pack = load_evidence_pack(
        ROOT_NODE_V16_3_PACK,
        required_fields=(
            "promoted_root_nodes",
            "watchlist_root_nodes",
            "shadow_clusters",
            "required_root_node_fields",
            "doctrine",
        ),
    )
    validate_root_node_fields(pack)
    return pack


def validate_root_node_fields(pack: EvidencePack) -> None:
    fields = set(pack.metrics.get("required_root_node_fields", []) or [])
    missing = [field for field in REQUIRED_ROOT_NODE_FIELDS if field not in fields]
    if missing:
        raise EvidencePackError(f"{pack.pack_id} missing root-node evidence fields: {', '.join(missing)}")
    doctrine = str(pack.metrics.get("doctrine", ""))
    if "persistent_load_bearing_continuation_root" not in doctrine:
        raise EvidencePackError(f"{pack.pack_id} weakens the root-node doctrine")

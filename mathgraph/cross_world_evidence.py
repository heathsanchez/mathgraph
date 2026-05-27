"""Loader for the CrossWorld v2 semantic residual evidence pack."""

from __future__ import annotations

from mathgraph.evidence_packs import EvidencePack, EvidencePackError, load_evidence_pack


PACK_ID = "cross_world_semantic_residual_invariant"


def load_cross_world_semantic_residual_invariant(pack_id: str = PACK_ID) -> EvidencePack:
    """Load the artifact-backed CrossWorld semantic residual invariant pack."""

    return load_evidence_pack(
        pack_id,
        required_fields=(
            "semantic_root_all_world_auc_false",
            "residual_rank_all_world_auc_false",
            "leave_one_world_out_mean_auc_false",
            "etp_semantic_root_auc_false",
            "world_count",
            "proof_status_summary",
        ),
    )


def validate_cross_world_semantic_residual_invariant(pack: EvidencePack | None = None) -> EvidencePack:
    """Validate the empirical CrossWorld v2 evidence thresholds and trust boundary."""

    pack = pack or load_cross_world_semantic_residual_invariant()
    metrics = pack.metrics
    boundary = pack.trust_boundary
    proof_status = dict(metrics.get("proof_status_summary", {}) or {})

    checks = (
        (metrics.get("world_count") == 4, "world_count must be 4"),
        (
            float(metrics.get("semantic_root_all_world_auc_false", 0.0)) >= 0.99,
            "semantic_root_all_world_auc_false must be >= 0.99",
        ),
        (
            float(metrics.get("residual_rank_all_world_auc_false", 0.0)) >= 0.99,
            "residual_rank_all_world_auc_false must be >= 0.99",
        ),
        (
            float(metrics.get("leave_one_world_out_mean_auc_false", 0.0)) >= 0.98,
            "leave_one_world_out_mean_auc_false must be >= 0.98",
        ),
        (
            float(metrics.get("etp_semantic_root_auc_false", 0.0)) >= 0.97,
            "etp_semantic_root_auc_false must be >= 0.97",
        ),
        (proof_status.get("false_underexplained") == 73, "false_underexplained must be 73"),
        (bool(boundary.get("not_formal_theorem")) is True, "not_formal_theorem must be true"),
        (bool(boundary.get("advisory_only")) is True, "advisory_only must be true"),
    )
    for passed, message in checks:
        if not passed:
            raise EvidencePackError(f"{pack.pack_id} invalid CrossWorld evidence: {message}")
    return pack

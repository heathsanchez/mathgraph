from pathlib import Path

import pytest

from mathgraph.evidence_packs import EvidencePackError, assert_trust_boundary, list_evidence_packs, load_evidence_pack
from mathgraph.recursive_residual_transfer import GATE_NAMES, compare_to_frozen_recursive_transfer_evidence, load_frozen_recursive_transfer_evidence, source_breakthrough_route_evaluations, build_recursive_transfer_summary

REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_PACKS = (
    "recursive_residual_transfer_v1_20260523",
    "sair_stage2_breakthrough_20260526",
    "residual_obstruction_atlas_v8_4",
    "collatz_primitive_divisor_v12_2",
    "root_node_persistent_filtration_v16_3",
    "cross_world_semantic_residual_invariant",
)

EVIDENCE_DOCS = (
    "docs/recursive_residual_transfer.md",
    "docs/evidence/official_sair_stage2_breakthrough_20260526.md",
    "docs/evidence/residual_obstruction_atlas_v8_4.md",
    "docs/evidence/collatz_primitive_divisor_v12_2.md",
    "docs/evidence/root_node_persistent_filtration_v16_3.md",
    "docs/evidence/cross_world_semantic_residual_invariant.md",
)


def test_canonical_evidence_packs_load_and_have_trust_boundaries() -> None:
    available = set(list_evidence_packs())
    for pack_id in CANONICAL_PACKS:
        assert pack_id in available
        pack = load_evidence_pack(pack_id)
        assert pack.metrics["pack_id"] == pack_id
        assert pack.trust_boundary
        assert (pack.directory / "README.md").exists()
        assert (pack.directory / "manifest.json").exists()


def test_trust_boundary_blocks_forbidden_truth_promotions() -> None:
    with pytest.raises(EvidencePackError):
        assert_trust_boundary({"advisory_promoted_truth_count": 1}, "bad_advisory")
    with pytest.raises(EvidencePackError):
        assert_trust_boundary({"failed_search_promoted_true_count": 1}, "bad_failed_search")
    with pytest.raises(EvidencePackError):
        assert_trust_boundary({"trust_boundary": {"route_scores_can_promote_truth": True}}, "bad_route_score")
    with pytest.raises(EvidencePackError):
        assert_trust_boundary({"advisory_boundary_ok": False}, "bad_boundary")


def test_recursive_transfer_pack_preserves_gate_names_and_comparison_shape() -> None:
    frozen = load_frozen_recursive_transfer_evidence("recursive_residual_transfer_v1_20260523")
    assert frozen["gates_passed"] == 9
    assert frozen["gates_total"] == 9
    assert tuple(GATE_NAMES) == (
        "compact_transfer_gain_vs_generic_positive",
        "compact_beats_random_same_size",
        "compact_beats_shuffled_atlas_same_size",
        "compact_retains_recursive_gain",
        "compact_prunes_recursive_memory",
        "zero_true_contamination",
        "positive_gain_in_enough_seeds",
        "oracle_gap_captured",
        "advisory_boundary_preserved",
    )

    routes = source_breakthrough_route_evaluations()
    summary = build_recursive_transfer_summary(
        routes,
        equations=frozen["equations"],
        matrix_shape=frozen["matrix_shape"],
        true_count=frozen["true_count"],
        false_count=frozen["false_count"],
    )
    comparison = compare_to_frozen_recursive_transfer_evidence(summary, [], frozen)
    assert comparison["reproduced_breakthrough_shape"] is True
    assert "reproduced_original_magnitude" in comparison


def test_official_sair_evidence_preserves_finite_checked_false_certificates() -> None:
    pack = load_evidence_pack("sair_stage2_breakthrough_20260526")
    assert pack.metrics["accepted_false_certificates"] == 36
    assert pack.metrics["finite_checked_countermodels"] == 36
    assert pack.metrics["advisory_promoted_truth_count"] == 0
    assert pack.metrics["failed_search_promoted_true_count"] == 0
    assert pack.metrics["true_contamination_count"] == 0


def test_cross_world_pack_is_empirical_not_proof() -> None:
    pack = load_evidence_pack("cross_world_semantic_residual_invariant")
    assert pack.metrics["semantic_root_all_world_auc_false"] == 0.9933195438173603
    assert pack.metrics["etp_false_underexplained"] == 73
    assert pack.metrics["claim_status"] == "empirical_cross_world_invariant_candidate"
    assert pack.metrics["provenance"] == "artifact_backed_uploaded_files1_zip_crossworld_v2"
    assert pack.trust_boundary["not_a_proof"] is True
    assert pack.trust_boundary["not_formal_theorem"] is True
    assert pack.trust_boundary["advisory_only"] is True


def test_evidence_docs_front_load_claim_boundaries_and_readme_links() -> None:
    for rel_path in EVIDENCE_DOCS:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert "## What This Proves" in text
        assert "## What This Does Not Prove" in text

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for pack_id in CANONICAL_PACKS:
        assert pack_id in readme
    assert "docs/evidence/evidence_map.md" in readme

    evidence_map = (REPO_ROOT / "docs/evidence/evidence_map.md").read_text(encoding="utf-8")
    assert "empirical_cross_world_invariant_candidate" in evidence_map
    assert "failed finite search is never TRUE" in evidence_map
    assert "not verified theorem" in evidence_map

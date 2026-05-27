from pathlib import Path

import pytest

from mathgraph.cross_world_evidence import (
    load_cross_world_semantic_residual_invariant,
    validate_cross_world_semantic_residual_invariant,
)
from mathgraph.evidence_packs import EvidencePack, EvidencePackError
from scripts.run_repo_architecture_audit import run_audit


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cross_world_pack_loads_and_preserves_v2_metrics() -> None:
    pack = load_cross_world_semantic_residual_invariant()
    metrics = pack.metrics
    assert metrics["world_count"] == 4
    assert metrics["worlds"] == ["BOOLEAN", "ETP", "GRAPH", "REWRITE"]
    assert metrics["semantic_root_all_world_auc_false"] == pytest.approx(0.9933195438173603)
    assert metrics["residual_rank_all_world_auc_false"] == pytest.approx(0.9969114909460145)
    assert metrics["leave_one_world_out_mean_auc_false"] == pytest.approx(0.9837976420735745)
    assert metrics["etp_semantic_root_auc_false"] == pytest.approx(0.97914248)
    assert metrics["combined_claim_rows"] == 16156
    assert metrics["combined_false_rows"] == 11818
    assert metrics["combined_true_rows"] == 4338
    assert metrics["top_shared_feature"] == "near_force_score"
    assert metrics["top_shared_feature_importance"] == pytest.approx(1.4279646993093744)
    assert metrics["best_abstract_root_signature"] == "residual_escape|gap_extreme|rank_very_high|source_large|absorption_low"
    assert metrics["best_root_score"] == pytest.approx(49.32726794109356)
    assert metrics["best_root_world_count"] == 2
    assert metrics["producer_script_name"] == "MATHGRAPH CROSSWORLD v2 \u2014 SEMANTIC RESIDUAL INDEPENDENCE RANK TEST"
    assert metrics["producer_script_provenance"] == "conversation_provided_source_code_not_committed_as_repo_runner"


def test_cross_world_proof_status_and_raw_shape_fields_are_preserved() -> None:
    metrics = load_cross_world_semantic_residual_invariant().metrics
    assert metrics["proof_status_summary"] == {
        "explained_false": 11745,
        "explained_true": 4338,
        "false_underexplained": 73,
    }
    assert metrics["etp_false_explained"] == 2427
    assert metrics["etp_false_total"] == 2500
    assert metrics["etp_true_explained"] == 2500
    assert metrics["etp_true_total"] == 2500
    assert metrics["etp_false_underexplained"] == 73
    assert metrics["root_level_candidate"] is False
    assert metrics["breakthrough_shaped"] is False


def test_cross_world_validation_treats_auc_metrics_as_supported_invariant() -> None:
    pack = validate_cross_world_semantic_residual_invariant()
    assert pack.metrics["candidate_invariant"] == "semantic_residual_independence_after_source_closure"
    assert pack.metrics["claim_status"] == "empirical_cross_world_invariant_candidate"
    assert pack.trust_boundary["not_formal_theorem"] is True
    assert pack.trust_boundary["advisory_only"] is True


def test_cross_world_validation_rejects_missing_or_weak_boundary() -> None:
    pack = load_cross_world_semantic_residual_invariant()
    bad_metrics = dict(pack.metrics)
    bad_metrics["semantic_root_all_world_auc_false"] = 0.50
    bad = EvidencePack(pack_id=pack.pack_id, directory=pack.directory, metrics=bad_metrics, manifest=pack.manifest)
    with pytest.raises(EvidencePackError):
        validate_cross_world_semantic_residual_invariant(bad)

    bad_boundary = dict(pack.metrics)
    bad_boundary["trust_boundary"] = dict(pack.trust_boundary)
    bad_boundary["trust_boundary"]["not_formal_theorem"] = False
    bad_manifest = dict(pack.manifest)
    bad_manifest["trust_boundary"] = dict(pack.trust_boundary)
    bad_manifest["trust_boundary"]["not_formal_theorem"] = False
    bad = EvidencePack(pack_id=pack.pack_id, directory=pack.directory, metrics=bad_boundary, manifest=bad_manifest)
    with pytest.raises(EvidencePackError):
        validate_cross_world_semantic_residual_invariant(bad)


def test_cross_world_docs_and_audit_preserve_trust_boundary_wording() -> None:
    doc = (REPO_ROOT / "docs/evidence/cross_world_semantic_residual_invariant.md").read_text(encoding="utf-8").lower()
    readme = (
        REPO_ROOT / "examples/evidence_packs/cross_world_semantic_residual_invariant/README.md"
    ).read_text(encoding="utf-8").lower()
    combined = f"{doc}\n{readme}"
    assert "not a formal theorem" in combined
    assert "not a truth oracle" in combined
    assert "advisory only" in combined
    assert "failed finite search is not true" in combined
    assert "proof-route candidate only unless verified" in combined
    assert "not errors and not true" in combined
    assert "not committed as a new repo runner" in combined

    audit = run_audit(REPO_ROOT)
    assert audit["status"] == "PASS"
    assert audit["crossworld_trust_boundary_wording"]["all_present"] is True

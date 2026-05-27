import pytest

from mathgraph.collatz_evidence import load_collatz_v12_2_evidence, validate_collatz_v12_2_not_a_proof
from mathgraph.evidence_packs import EvidencePack, EvidencePackError, load_evidence_pack
from mathgraph.residual_obstruction_evidence import RESIDUAL_ZERO_PRINCIPLE, load_residual_obstruction_v8_4_evidence
from mathgraph.root_node_evidence import REQUIRED_ROOT_NODE_FIELDS, load_root_node_v16_3_evidence


def test_collatz_v12_2_is_marked_not_a_proof() -> None:
    pack = load_collatz_v12_2_evidence()
    assert pack.metrics["not_a_proof"] is True
    assert pack.metrics["main_obstruction"] == "UNCANCELLED_PRIMITIVE_DIVISOR_GROWTH"
    assert pack.metrics["primitive_growth_pairs"] == 4999
    assert pack.metrics["pairs_processed"] == 5000
    assert pack.metrics["total_integer_candidate_count"] == 0
    assert pack.metrics["residual_obstruction"] == "LOW_NOVELTY_RECURRENCE_RESIDUAL"


def test_collatz_validator_rejects_proof_claim() -> None:
    pack = EvidencePack(
        pack_id="bad_collatz",
        directory=load_collatz_v12_2_evidence().directory,
        metrics={"not_a_proof": False, "main_obstruction": "UNCANCELLED_PRIMITIVE_DIVISOR_GROWTH", "total_integer_candidate_count": 0},
    )
    with pytest.raises(EvidencePackError):
        validate_collatz_v12_2_not_a_proof(pack)


def test_residual_obstruction_pack_preserves_residual_zero_principle() -> None:
    pack = load_residual_obstruction_v8_4_evidence()
    assert pack.metrics["named_principle"] == RESIDUAL_ZERO_PRINCIPLE
    assert pack.metrics["remaining_frontier"] == 61151
    assert pack.metrics["top_constructor_pressure"] == "needs_new_semantic_universe_or_higher_carrier"
    assert pack.trust_boundary["residual_zero_is_not_true"] is True


def test_root_node_pack_requires_persistence_and_load_bearing_fields() -> None:
    pack = load_root_node_v16_3_evidence()
    fields = set(pack.metrics["required_root_node_fields"])
    assert set(REQUIRED_ROOT_NODE_FIELDS) <= fields
    assert pack.metrics["promoted_root_nodes"] == 164
    assert pack.trust_boundary["root_node_score_can_promote_truth"] is False


def test_manifest_small_policy_marks_bulky_artifacts_external() -> None:
    pack = load_evidence_pack("collatz_primitive_divisor_v12_2")
    external = [artifact for artifact in pack.artifacts if not artifact.copied_to_repo]
    assert any(artifact.filename.endswith(".sqlite") for artifact in external)
    assert all(artifact.reason_not_copied == "bulky_artifact_manifested_only" for artifact in external)

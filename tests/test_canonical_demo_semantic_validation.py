import json

from mathgraph.evidence_replay import replay_evidence_manifest
from scripts.run_canonical_finite_countermodel_demo import run_demo


def test_canonical_demo_writes_semantic_validation_metadata(tmp_path):
    summary = run_demo(tmp_path)
    assert summary["semantic_validation_status"] == "VALIDATED"
    manifest = json.loads((tmp_path / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert manifest["informal_claim_id"] == "informal_commutativity_not_left_zero"
    assert manifest["formal_claim_id"] == "canonical_commutativity_not_left_zero"
    assert manifest["semantic_validation_status"] == "VALIDATED"
    assert manifest["semantic_validation_evidence_refs"]
    assert replay_evidence_manifest(tmp_path / "evidence_manifest.json").ok

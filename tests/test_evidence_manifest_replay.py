import json

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.evidence_replay import replay_evidence_manifest
from mathgraph.finite_magma_world import check_finite_countermodel, left_projection
from mathgraph.hashing import sha256_hex


def _write_manifest(tmp_path, *, terminal_form=TerminalForm.FINITE_COUNTERMODEL, artifact=None, claim_data=None, witness=None):
    result = check_finite_countermodel("x = x", "x = y", left_projection(2))
    artifact = artifact or {"claim_id": "c", "countermodel": result.to_dict()}
    (tmp_path / "artifact.json").write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8")
    manifest = EvidenceManifest(
        claim_id="c",
        terminal_form=terminal_form,
        evidence_type="finite_magma_countermodel",
        verifier_boundary="finite_model_checker",
        artifact_hashes=(sha256_hex(artifact),),
        artifact_paths=("artifact.json",),
        claim_data=claim_data or {"source_equation": "x = x", "target_equation": "x = y", "table": [[0, 0], [1, 1]]},
        witness=witness or result.witness_env,
        provenance=("test",),
        replay_instructions=("python demo.py",),
    )
    path = tmp_path / "manifest.json"
    path.write_text(manifest.to_json(), encoding="utf-8")
    return path


def test_replay_valid_finite_countermodel_manifest_passes(tmp_path):
    path = _write_manifest(tmp_path)
    assert replay_evidence_manifest(path).ok


def test_replay_hash_mismatch_fails(tmp_path):
    path = _write_manifest(tmp_path)
    (tmp_path / "artifact.json").write_text(json.dumps({"changed": True}), encoding="utf-8")
    result = replay_evidence_manifest(path)
    assert not result.ok
    assert any("artifact_hash_mismatch" in item for item in result.failures)


def test_replay_terminal_form_mismatch_fails(tmp_path):
    path = _write_manifest(tmp_path)
    result = replay_evidence_manifest(path, expected_terminal_form=TerminalForm.VERIFIED_PROOF)
    assert not result.ok
    assert "terminal_form_mismatch" in result.failures


def test_replay_missing_witness_or_claim_data_fails(tmp_path):
    path = _write_manifest(tmp_path, claim_data={"source_equation": "x = x"})
    result = replay_evidence_manifest(path)
    assert not result.ok
    assert "finite_countermodel_claim_data_missing" in result.failures

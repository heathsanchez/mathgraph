import json

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.finite_magma_world import check_finite_countermodel, constant_table
from mathgraph.hashing import sha256_hex
from mathgraph.invariants import TrustBoundaryEvidence
from mathgraph.lawbook_acceptance import lawbook_entry_from_evidence_manifest, validate_lawbook_acceptance
from mathgraph.semantic_validation import SemanticValidationStatus


def _manifest(tmp_path, *, status=SemanticValidationStatus.MISSING, claims_solution=True):
    result = check_finite_countermodel("(x * y) = (y * x)", "(x * y) = x", constant_table(2, 0))
    artifact = {"claim_id": "formal", "countermodel": result.to_dict()}
    artifact_hash = sha256_hex(artifact)
    (tmp_path / "artifact.json").write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8")
    manifest = EvidenceManifest(
        claim_id="formal",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        evidence_type="finite",
        verifier_boundary="finite_model_checker",
        artifact_hashes=(artifact_hash,),
        artifact_paths=("artifact.json",),
        claim_data={"source_equation": "(x * y) = (y * x)", "target_equation": "(x * y) = x", "table": [[0, 0], [0, 0]]},
        witness=result.witness_env,
        provenance=("p",),
        replay_instructions=("run",),
        informal_claim_id="informal",
        formal_claim_id="formal",
        semantic_validation_status=status,
        semantic_validation_evidence_refs=("ev",) if status == SemanticValidationStatus.VALIDATED else (),
    )
    path = tmp_path / "manifest.json"
    path.write_text(manifest.to_json(), encoding="utf-8")
    evidence = TrustBoundaryEvidence(
        replayable=True,
        advisory=False,
        artifact_hashes=(artifact_hash,),
        witness_checked=True,
        source_satisfied=True,
        target_violated=True,
        provenance=("p",),
        trust_level=100,
    )
    entry = lawbook_entry_from_evidence_manifest(
        manifest,
        evidence=evidence,
        metadata={"informal_claim_id": "informal", "claims_informal_solution": claims_solution},
    )
    return entry, manifest, path, evidence


def test_informal_missing_validation_cannot_claim_solution(tmp_path):
    entry, manifest, path, evidence = _manifest(tmp_path, status=SemanticValidationStatus.MISSING)
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert not result.ok
    assert any(v.code == "informal_solution_without_validation" for v in result.violations)


def test_semantic_rejected_blocks_informal_solution_claim(tmp_path):
    entry, manifest, path, evidence = _manifest(tmp_path, status=SemanticValidationStatus.REJECTED)
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert not result.ok
    assert any(v.code == "semantic_validation_rejected" for v in result.violations)


def test_semantic_validated_and_verified_finite_countermodel_passes(tmp_path):
    entry, manifest, path, evidence = _manifest(tmp_path, status=SemanticValidationStatus.VALIDATED)
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert result.ok
    assert "semantic_validation_validated" in result.reason_codes


def test_formal_only_entry_with_missing_semantic_validation_passes(tmp_path):
    entry, manifest, path, evidence = _manifest(tmp_path, status=SemanticValidationStatus.MISSING, claims_solution=False)
    entry.metadata["informal_claim_id"] = ""
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert result.ok

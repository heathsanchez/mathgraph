import json

import pytest

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.finite_magma_world import check_finite_countermodel, left_projection
from mathgraph.hashing import sha256_hex
from mathgraph.invariants import TrustBoundaryEvidence
from mathgraph.lawbook import LawbookEntry, LawbookEntryKind, LawbookEntryStatus
from mathgraph.lawbook_acceptance import (
    accept_lawbook_entry,
    lawbook_entry_from_evidence_manifest,
    validate_lawbook_acceptance,
)


def _finite_manifest(tmp_path):
    result = check_finite_countermodel("x = x", "x = y", left_projection(2))
    artifact = {"claim_id": "c", "countermodel": result.to_dict()}
    artifact_hash = sha256_hex(artifact)
    (tmp_path / "artifact.json").write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8")
    manifest = EvidenceManifest(
        claim_id="c",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        evidence_type="finite_magma_countermodel",
        verifier_boundary="finite_model_checker",
        artifact_hashes=(artifact_hash,),
        artifact_paths=("artifact.json",),
        claim_data={"source_equation": "x = x", "target_equation": "x = y", "table": [[0, 0], [1, 1]]},
        witness=result.witness_env,
        provenance=("test",),
        replay_instructions=("python demo.py",),
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
        provenance=("test",),
        trust_level=100,
    )
    return manifest, path, evidence


def test_valid_finite_countermodel_manifest_enters_lawbook(tmp_path):
    manifest, manifest_path, evidence = _finite_manifest(tmp_path)
    entry = lawbook_entry_from_evidence_manifest(manifest, evidence=evidence)
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(manifest_path))
    assert result.ok
    accepted = accept_lawbook_entry(entry, manifest=manifest, evidence=evidence, manifest_path=str(manifest_path))
    assert accepted.status.value == "ACCEPTED"
    assert accepted.terminal_form == TerminalForm.FINITE_COUNTERMODEL


def test_advisory_route_cannot_enter_lawbook_as_truth(tmp_path):
    manifest, manifest_path, evidence = _finite_manifest(tmp_path)
    entry = lawbook_entry_from_evidence_manifest(manifest, evidence=evidence)
    entry.advisory = True
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(manifest_path))
    assert not result.ok
    assert any(v.code == "advisory_lawbook_truth" for v in result.violations)


def test_reason_atlas_route_policy_cannot_enter_lawbook_as_truth(tmp_path):
    manifest, manifest_path, evidence = _finite_manifest(tmp_path)
    entry = LawbookEntry(
        "route",
        LawbookEntryKind.ROUTE_RULE_ENTRY,
        LawbookEntryStatus.CANDIDATE,
        claim_id="c",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        metadata={"reason_type": "reason_atlas_route_policy"},
    )
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(manifest_path))
    assert not result.ok
    assert any(v.code == "reason_atlas_truth_promotion" for v in result.violations)


def test_lawbook_entry_without_manifest_fails(tmp_path):
    manifest, _manifest_path, evidence = _finite_manifest(tmp_path)
    entry = lawbook_entry_from_evidence_manifest(manifest, evidence=evidence)
    result = validate_lawbook_acceptance(entry, manifest=None, evidence=evidence, require_replay=False)
    assert not result.ok
    assert any(v.code == "missing_evidence_manifest" for v in result.violations)


def test_manifest_without_replay_instructions_fails(tmp_path):
    with pytest.raises(ValueError):
        EvidenceManifest(
            claim_id="c",
            terminal_form=TerminalForm.FINITE_COUNTERMODEL,
            evidence_type="finite",
            verifier_boundary="finite_model_checker",
            artifact_hashes=("h",),
            witness={"x": 0},
            provenance=("p",),
            replay_instructions=(),
        )

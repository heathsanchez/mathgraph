from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.hashing import sha256_hex
from mathgraph.invariants import TrustBoundaryEvidence
from mathgraph.lawbook import LawbookEntryKind
from mathgraph.lawbook_acceptance import lawbook_entry_from_evidence_manifest, validate_lawbook_acceptance


def _derived_entry(tmp_path, *, metadata, evidence_boundary=""):
    artifact = {"claim_id": "derived", "obstruction": "chain"}
    (tmp_path / "artifact.json").write_text("{}\n", encoding="utf-8")
    manifest = EvidenceManifest(
        claim_id="derived",
        terminal_form=TerminalForm.NAMED_OBSTRUCTION,
        evidence_type="derived_obstruction",
        verifier_boundary="derived_obstruction",
        artifact_hashes=(sha256_hex({}),),
        artifact_paths=("artifact.json",),
        obstruction_id="obs",
        provenance=("parent",),
        replay_instructions=("python replay.py",),
    )
    path = tmp_path / "manifest.json"
    path.write_text(manifest.to_json(), encoding="utf-8")
    evidence = TrustBoundaryEvidence(
        replayable=True,
        advisory=False,
        artifact_hashes=(sha256_hex({}),),
        obstruction_id="obs",
        structured_obstruction=True,
        provenance=("parent",),
        trust_level=metadata.get("trust_level", 50),
        verifier_boundary=evidence_boundary,
    )
    entry = lawbook_entry_from_evidence_manifest(manifest, evidence=evidence, metadata={**metadata, "derived": True})
    entry.kind = LawbookEntryKind.DERIVED_CERTIFICATE_ENTRY
    return entry, manifest, path, evidence


def test_derived_without_parent_provenance_or_refs_fails(tmp_path):
    entry, manifest, path, evidence = _derived_entry(tmp_path, metadata={"trust_level": 50, "parent_trust_level": 50})
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert not result.ok
    assert any(v.code == "derived_missing_parent_evidence_refs" for v in result.violations)


def test_derived_trust_upgrade_without_verifier_fails(tmp_path):
    entry, manifest, path, evidence = _derived_entry(
        tmp_path,
        metadata={"trust_level": 80, "parent_trust_level": 50, "parent_evidence_refs": ("p",), "parent_provenance": ("p",)},
    )
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert not result.ok
    assert any(v.code == "derived_trust_upgrade_without_boundary" for v in result.violations)


def test_derived_preserving_provenance_without_upgrade_passes(tmp_path):
    entry, manifest, path, evidence = _derived_entry(
        tmp_path,
        metadata={"trust_level": 50, "parent_trust_level": 50, "parent_evidence_refs": ("p",), "parent_provenance": ("p",)},
    )
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=str(path))
    assert result.ok

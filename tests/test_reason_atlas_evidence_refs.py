import json

from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.reason_atlas import (
    ReasonAtlasEvidenceRef,
    ReasonAtlasTrustLevel,
    ReasonAtlasEntry,
    build_reason_atlas_entry_from_outcomes,
    validate_reason_atlas_entry,
)
from scripts.run_canonical_finite_countermodel_demo import run_demo


def test_missing_or_malformed_evidence_refs_fail():
    entry = ReasonAtlasEntry(
        basin_id="b",
        signature="s",
        basin_name="b",
        constructor_family="c",
        route_priority=1.0,
        support_count=1,
        heldout_gain=0.0,
        new_losses=0,
        true_control_countermodels=0,
        trust_level=ReasonAtlasTrustLevel.VERIFIER_BACKED,
        evidence=(ReasonAtlasEvidenceRef("", verifier_backed=True, advisory_only=False),),
    )
    report = validate_reason_atlas_entry(entry)
    assert not report.ok
    codes = {v.code for v in report.violations}
    assert "missing_evidence_id" in codes
    assert "verifier_backed_ref_missing_manifest_or_lawbook" in codes


def test_canonical_manifest_can_be_referenced_and_preserves_semantic_status(tmp_path):
    summary = run_demo(tmp_path)
    manifest_path = summary["outputs"]["manifest"]
    manifest = EvidenceManifest.from_dict(json.loads((tmp_path / "evidence_manifest.json").read_text(encoding="utf-8")))
    entry = build_reason_atlas_entry_from_outcomes(
        basin_id="b",
        signature="s",
        basin_name="b",
        constructor_family="constant",
        outcomes=(
            ReasonAtlasEvidenceRef(
                "canonical",
                claim_id=manifest.claim_id,
                terminal_form=manifest.terminal_form.value,
                manifest_path=manifest_path,
                manifest_hash=manifest.stable_hash(),
                lawbook_entry_id=summary["lawbook_entry_id"],
                verifier_backed=True,
                advisory_only=False,
                replay_status="replayable",
                semantic_validation_status=manifest.semantic_validation_status.value,
            ),
        ),
    )
    report = validate_reason_atlas_entry(entry)
    assert report.ok
    assert entry.evidence[0].semantic_validation_status == "VALIDATED"

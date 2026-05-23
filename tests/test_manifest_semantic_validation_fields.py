from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.semantic_validation import SemanticValidationStatus


def test_manifest_semantic_validation_fields_roundtrip_and_hash_stable():
    manifest = EvidenceManifest(
        claim_id="formal",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        evidence_type="finite",
        verifier_boundary="finite_model_checker",
        artifact_hashes=("h",),
        witness={"x": 0},
        provenance=("p",),
        replay_instructions=("run",),
        informal_claim_id="informal",
        formal_claim_id="formal",
        semantic_validation_status=SemanticValidationStatus.VALIDATED,
        semantic_validation_evidence_refs=("ev",),
        translation_assumptions=({"assumption_id": "a", "description": "d"},),
        validation_report_hash="vh",
        created_at="t1",
    )
    loaded = EvidenceManifest.from_dict({**manifest.to_dict(), "created_at": "t2"})
    assert loaded.semantic_validation_status == SemanticValidationStatus.VALIDATED
    assert loaded.semantic_validation_evidence_refs == ("ev",)
    assert manifest.stable_hash() == loaded.stable_hash()

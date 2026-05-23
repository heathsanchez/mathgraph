from mathgraph.certificates import TerminalForm
from mathgraph.reason_atlas import (
    ReasonAtlasEvidenceRef,
    ReasonAtlasTrustLevel,
    build_reason_atlas_entry_from_outcomes,
    compute_reason_atlas_metrics,
    summarize_constructor_family_performance,
    validate_reason_atlas_entry,
)
from mathgraph.semantic_validation import SemanticValidationStatus


def test_verifier_backed_evidence_refs_pass_as_routing_knowledge():
    entry = build_reason_atlas_entry_from_outcomes(
        basin_id="b",
        signature="sig",
        basin_name="basin",
        constructor_family="constant",
        outcomes=(
            ReasonAtlasEvidenceRef(
                "ev",
                claim_id="c",
                terminal_form=TerminalForm.FINITE_COUNTERMODEL.value,
                manifest_hash="mh",
                lawbook_entry_id="le",
                verifier_backed=True,
                advisory_only=False,
                replay_status="replayable",
                semantic_validation_status=SemanticValidationStatus.VALIDATED.value,
            ),
        ),
    )
    report = validate_reason_atlas_entry(entry)
    assert report.ok
    assert entry.trust_level == ReasonAtlasTrustLevel.VERIFIER_BACKED
    assert entry.to_dict()["advisory_only"] is True


def test_advisory_only_evidence_passes_only_as_exploratory():
    entry = build_reason_atlas_entry_from_outcomes(
        basin_id="b",
        signature="sig",
        basin_name="basin",
        constructor_family="projection",
        outcomes=(ReasonAtlasEvidenceRef("obs", advisory_only=True, outcome="observation"),),
    )
    report = validate_reason_atlas_entry(entry)
    assert report.ok
    assert entry.trust_level == ReasonAtlasTrustLevel.ADVISORY
    assert entry.promotion_status == "EXPLORATORY"


def test_metrics_compute_deterministic_counts():
    metrics = compute_reason_atlas_metrics(
        [
            ReasonAtlasEvidenceRef("a", terminal_form="FINITE_COUNTERMODEL", verifier_backed=True, advisory_only=False, replay_status="replayable"),
            ReasonAtlasEvidenceRef("b", advisory_only=True, outcome="rejected"),
        ],
        heldout_gain=2.0,
        new_losses=1,
    )
    assert metrics.support_count == 2
    assert metrics.verifier_backed_count == 1
    assert metrics.advisory_only_count == 1
    assert metrics.success_count_by_terminal_form == {"FINITE_COUNTERMODEL": 1}
    assert metrics.failure_count == 1
    assert metrics.replayable_count == 1
    assert metrics.evidence_coverage_ratio == 1.0


def test_constructor_family_summary_accumulates():
    entry = build_reason_atlas_entry_from_outcomes(
        basin_id="b",
        signature="sig",
        basin_name="basin",
        constructor_family="constant",
        outcomes=(ReasonAtlasEvidenceRef("a", terminal_form="FINITE_COUNTERMODEL", verifier_backed=True, advisory_only=False, manifest_hash="h"),),
    )
    summary = summarize_constructor_family_performance([entry])
    assert summary["constant"]["support_count"] == 1
    assert summary["constant"]["verifier_backed_count"] == 1

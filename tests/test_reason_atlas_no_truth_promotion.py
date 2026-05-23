from mathgraph.reason_atlas import (
    ReasonAtlasEvidenceRef,
    build_reason_atlas_entry_from_outcomes,
    check_reason_atlas_no_truth_promotion,
    validate_reason_atlas_entry,
)


def test_reason_atlas_entry_cannot_create_verified_proof():
    report = check_reason_atlas_no_truth_promotion({"terminal_form": "VERIFIED_PROOF"})
    assert not report.ok
    assert report.violations[0].code == "reason_atlas_truth_promotion"


def test_route_priority_cannot_bypass_lawbook_acceptance():
    report = check_reason_atlas_no_truth_promotion({"route_priority": 999, "lawbook_acceptance": "ACCEPTED"})
    assert not report.ok
    assert report.violations[0].code == "reason_atlas_lawbook_bypass"


def test_high_support_without_verifier_evidence_stays_advisory():
    entry = build_reason_atlas_entry_from_outcomes(
        basin_id="b",
        signature="sig",
        basin_name="basin",
        constructor_family="constant",
        route_priority=999.0,
        outcomes=(ReasonAtlasEvidenceRef("obs", advisory_only=True),),
    )
    data = entry.to_dict()
    data["support_count"] = 10_000
    report = validate_reason_atlas_entry(data)
    assert report.ok
    assert data["advisory_only"] is True

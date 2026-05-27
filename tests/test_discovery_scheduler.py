import csv
import json

from mathgraph.discovery_scheduler import (
    ALLOWED_DESCENSION_TARGETS,
    DiscoveryCandidate,
    allocate_attention,
    fallback_demo_candidates,
    make_policy,
    run_discovery_scheduler,
    validate_candidate,
)


EXPECTED_FILES = {
    "discovery_candidates.csv",
    "ranked_attention.csv",
    "selected_attention.csv",
    "invalid_candidates.csv",
    "taste_policy.json",
    "trust_boundary_audit.json",
    "discovery_scheduler_summary.json",
    "discovery_scheduler_report.md",
}


def test_fallback_demo_emits_expected_files_and_audit(tmp_path) -> None:
    result = run_discovery_scheduler(tmp_path / "run", fallback_demo=True, mode="balanced", top_k=3)
    assert result.candidate_count == 6
    assert result.eligible_count == 4
    assert result.chosen_count == 3
    assert result.advisory_boundary_ok is False
    assert result.can_promote_truth_count == 1
    assert EXPECTED_FILES <= {path.name for path in (tmp_path / "run").iterdir()}

    summary = json.loads((tmp_path / "run" / "discovery_scheduler_summary.json").read_text(encoding="utf-8"))
    assert summary["invalid_descension_count"] == 1
    assert abs(summary["total_attention_probability"] - 1.0) < 1e-9
    audit = json.loads((tmp_path / "run" / "trust_boundary_audit.json").read_text(encoding="utf-8"))
    assert "cannot promote truth" in audit["statement"]
    report = (tmp_path / "run" / "discovery_scheduler_report.md").read_text(encoding="utf-8")
    assert "No descension target, no attention" in report or "no-descension" in report


def test_candidate_validation_requires_descension_and_boundary() -> None:
    no_descension = DiscoveryCandidate(candidate_id="x", candidate_type="demo", source="test")
    ok, violations = validate_candidate(no_descension)
    assert ok is False
    assert "invalid_or_missing_descension_target" in violations

    promotes_truth = DiscoveryCandidate(
        candidate_id="y",
        candidate_type="demo",
        source="test",
        descension_target="reason_atlas_route_test",
        can_promote_truth=True,
    )
    ok, violations = validate_candidate(promotes_truth)
    assert ok is False
    assert "can_promote_truth_true" in violations


def test_attention_probabilities_sum_over_eligible_candidates() -> None:
    policy = make_policy("balanced", beta=1.0)
    ranked, selected, invalid = allocate_attention(fallback_demo_candidates(), policy, top_k=2)
    assert invalid
    assert len(selected) == 2
    assert all(candidate.descension_target in ALLOWED_DESCENSION_TARGETS for candidate in ranked)
    assert abs(sum(candidate.attention_probability for candidate in ranked) - 1.0) < 1e-9
    assert all(candidate.advisory_only and not candidate.can_promote_truth for candidate in selected)


def test_modes_prefer_expected_candidate_shapes() -> None:
    candidates = [
        DiscoveryCandidate(
            candidate_id="harvest_candidate",
            candidate_type="certificate",
            source="test",
            descension_target="finite_countermodel_attempt",
            expected_certificate_value=1.0,
            expected_reuse=1.0,
            verification_cost=0.1,
        ),
        DiscoveryCandidate(
            candidate_id="frontier_candidate",
            candidate_type="frontier",
            source="test",
            descension_target="obstruction_naming_attempt",
            expected_obstruction_value=1.0,
            expected_residual_compression=1.0,
            novelty_score=1.0,
            verification_cost=0.4,
        ),
        DiscoveryCandidate(
            candidate_id="architectonic_candidate",
            candidate_type="projection",
            source="test",
            descension_target="projection_test",
            expected_projection_gain=1.0,
            expected_residual_compression=0.8,
            expected_reuse=1.0,
            novelty_score=0.8,
            verification_cost=0.4,
        ),
    ]
    harvest_ranked, _, _ = allocate_attention(candidates, make_policy("harvest", beta=2.0), top_k=1)
    frontier_ranked, _, _ = allocate_attention(candidates, make_policy("frontier", beta=2.0), top_k=1)
    architectonic_ranked, _, _ = allocate_attention(candidates, make_policy("architectonic", beta=2.0), top_k=1)
    assert harvest_ranked[0].candidate_id == "harvest_candidate"
    assert frontier_ranked[0].candidate_id == "frontier_candidate"
    assert architectonic_ranked[0].candidate_id == "architectonic_candidate"


def test_outputs_do_not_claim_verified_proof_or_route_score_truth(tmp_path) -> None:
    run_discovery_scheduler(tmp_path / "run", fallback_demo=True, mode="frontier", top_k=3)
    selected = list(csv.DictReader(open(tmp_path / "run" / "selected_attention.csv", encoding="utf-8")))
    assert selected
    assert {row["advisory_only"] for row in selected} == {"True"}
    assert {row["can_promote_truth"] for row in selected} == {"False"}
    ranked = list(csv.DictReader(open(tmp_path / "run" / "ranked_attention.csv", encoding="utf-8")))
    assert all(row.get("terminal_form_observed", "") != "VERIFIED_PROOF" for row in ranked)
    audit = json.loads((tmp_path / "run" / "trust_boundary_audit.json").read_text(encoding="utf-8"))
    assert any(row["reason"] == "can_promote_truth_true" for row in audit["violations"])

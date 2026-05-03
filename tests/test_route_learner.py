import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    PairOutcome,
    RouteLearner,
    extract_outcome_pair_features,
    make_basin_key,
)


ROOT = Path(__file__).resolve().parents[1]


def _outcome(
    route: str | None,
    terminal_form: str,
    verification_status: str,
    trust_level: str,
    origin: str = "primitive_trace",
    source: str = "x * y = x",
    target: str = "x * x = x",
) -> PairOutcome:
    return PairOutcome(
        pair_id=f"{origin}:{route}:{terminal_form}:{source}:{target}",
        source=source,
        target=target,
        source_idx=None,
        target_idx=None,
        claim_id=None,
        terminal_form=terminal_form,
        verification_status=verification_status,
        trust_level=trust_level,
        origin=origin,
        route=route,
        derivation_rule="true_transitivity" if origin == "derived_certificate" else None,
        parent_claims=[],
        features=extract_outcome_pair_features(source, target),
        labels={
            "is_verified_true": terminal_form == "VERIFIED_PROOF",
            "is_verified_false": terminal_form == "FINITE_COUNTERMODEL",
            "is_derived": origin == "derived_certificate",
            "is_unknown": verification_status == "UNKNOWN",
        },
        evidence={},
        warnings=[],
    )


def test_basin_key_deterministic_bucketing() -> None:
    features = extract_outcome_pair_features("x * y = x", "x * x = x")
    one = make_basin_key("variable_identification", features)
    two = make_basin_key("variable_identification", features)
    assert one == two
    assert one.source_var_bucket == "v2"
    assert one.new_target_vars_bucket == "no_new_target_vars"


def test_learner_accepts_pair_outcome_objects() -> None:
    learner = RouteLearner([_outcome("variable_identification", "VERIFIED_PROOF", "VERIFIED", "lean_verified")])
    assert learner.stats().usable_outcome_count == 1


def test_learner_accepts_dict_rows() -> None:
    row = _outcome("variable_identification", "VERIFIED_PROOF", "VERIFIED", "lean_verified").to_dict()
    learner = RouteLearner([row])
    assert learner.build_policy_cards()[0].route == "variable_identification"


def test_policy_cards_include_primitive_and_derived_successes() -> None:
    outcomes = [
        _outcome("variable_identification", "VERIFIED_PROOF", "VERIFIED", "lean_verified"),
        _outcome(
            "variable_identification",
            "VERIFIED_PROOF",
            "DERIVED_VERIFIED",
            "derived_from_verified_traces",
            origin="derived_certificate",
        ),
    ]
    card = RouteLearner(outcomes).build_policy_cards()[0]
    assert card.primitive_count == 1
    assert card.derived_count == 1
    assert card.success_count == 2


def test_unknown_and_advisory_rows_do_not_become_failures() -> None:
    outcomes = [
        _outcome("variable_identification", "NAMED_OBSTRUCTION", "UNKNOWN", "unknown", origin="oracle_unknown"),
        _outcome("variable_identification", "NAMED_OBSTRUCTION", "UNKNOWN", "advisory_only", origin="advisory_task"),
    ]
    card = RouteLearner(outcomes).build_policy_cards()[0]
    assert card.unknown_count == 2
    assert card.failure_count == 0
    assert card.success_count == 0


def test_confidence_bounded_and_support_sensitive() -> None:
    small = RouteLearner([
        _outcome("finite_countermodel", "FINITE_COUNTERMODEL", "REFUTED", "finite_verified")
    ]).build_policy_cards()[0]
    large = RouteLearner([
        _outcome("finite_countermodel", "FINITE_COUNTERMODEL", "REFUTED", "finite_verified", source=f"x{i} * y = x{i}")
        for i in range(10)
    ]).build_policy_cards()
    best_large = max(card.confidence for card in large)
    assert 0 <= small.confidence < 1
    assert best_large > small.confidence


def test_recommended_task_kind_for_proof_and_countermodel_routes() -> None:
    proof = RouteLearner([
        _outcome("variable_identification", "VERIFIED_PROOF", "VERIFIED", "lean_verified")
    ]).build_policy_cards()[0]
    counter = RouteLearner([
        _outcome("finite_countermodel", "FINITE_COUNTERMODEL", "REFUTED", "finite_verified")
    ]).build_policy_cards()[0]
    assert proof.recommended_task_kind == "proof_template"
    assert counter.recommended_task_kind == "finite_countermodel_search"


def test_recommend_returns_warning_and_uses_exact_basin() -> None:
    learner = RouteLearner([
        _outcome("variable_identification", "VERIFIED_PROOF", "VERIFIED", "lean_verified")
    ])
    learner.build_policy_cards()
    recommendation = learner.recommend("x * y = x", "x * x = x")
    assert recommendation.recommended_route == "variable_identification"
    assert "exact_basin_match" in recommendation.reason_codes
    assert "advisory only" in recommendation.warnings[0]


def test_recommend_falls_back_safely_without_exact_basin() -> None:
    learner = RouteLearner([
        _outcome("finite_countermodel", "FINITE_COUNTERMODEL", "REFUTED", "finite_verified")
    ])
    learner.build_policy_cards()
    recommendation = learner.recommend("x = x", "x * y * z = z")
    assert recommendation.candidate_cards
    assert "route_level_fallback" in recommendation.reason_codes
    assert recommendation.recommended_task_kind in {"finite_countermodel_search", "proof_template", "route_probe"}


def test_json_jsonl_save(tmp_path: Path) -> None:
    learner = RouteLearner([
        _outcome("finite_countermodel", "FINITE_COUNTERMODEL", "REFUTED", "finite_verified")
    ])
    learner.build_policy_cards()
    policy_json = tmp_path / "policy.json"
    policy_jsonl = tmp_path / "policy.jsonl"
    stats_json = tmp_path / "stats.json"
    learner.save_policy_cards_json(policy_json)
    learner.save_policy_cards_jsonl(policy_jsonl)
    learner.save_stats_json(stats_json)
    assert json.loads(policy_json.read_text(encoding="utf-8"))
    assert policy_jsonl.read_text(encoding="utf-8").splitlines()
    assert json.loads(stats_json.read_text(encoding="utf-8"))["policy_card_count"] == 1


def test_cli_works_with_temp_jsonl(tmp_path: Path) -> None:
    outcomes_path = tmp_path / "outcomes.jsonl"
    outcomes_path.write_text(
        json.dumps(_outcome("finite_countermodel", "FINITE_COUNTERMODEL", "REFUTED", "finite_verified").to_dict()) + "\n",
        encoding="utf-8",
    )
    policy_json = tmp_path / "policy.json"
    policy_jsonl = tmp_path / "policy.jsonl"
    stats_json = tmp_path / "stats.json"
    rec_json = tmp_path / "recommendation.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_route_policy.py"),
            "--outcomes-jsonl",
            str(outcomes_path),
            "--out-policy-json",
            str(policy_json),
            "--out-policy-jsonl",
            str(policy_jsonl),
            "--out-stats",
            str(stats_json),
            "--recommend-source",
            "x * y = x",
            "--recommend-target",
            "x * x = x",
            "--out-recommendation",
            str(rec_json),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["policy_card_count"] == 1
    assert policy_json.exists()
    assert policy_jsonl.exists()
    assert stats_json.exists()
    assert rec_json.exists()

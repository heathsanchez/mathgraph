import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    Certificate,
    CertificateLawbook,
    HTiltScheduler,
    KernelOracle,
    LawbookStore,
    PairOutcome,
    RoutePolicyCard,
    SchedulerInputPair,
    TerminalForm,
    Trace,
    VerificationStatus,
    extract_outcome_pair_features,
)


ROOT = Path(__file__).resolve().parents[1]


def _policy(
    route: str = "variable_identification",
    confidence: float = 0.7,
    source: str = "x * y = x",
    target: str = "x * x = x",
) -> RoutePolicyCard:
    from mathgraph import make_basin_key

    basin = make_basin_key(route, extract_outcome_pair_features(source, target)).to_dict()
    return RoutePolicyCard(
        basin_key=basin,
        support_count=10,
        route=route,
        success_count=9,
        failure_count=0,
        unknown_count=1,
        verified_true_count=9 if route != "finite_countermodel" else 0,
        verified_false_count=9 if route == "finite_countermodel" else 0,
        derived_count=2,
        primitive_count=7,
        success_rate=0.9,
        false_rate=0.9 if route == "finite_countermodel" else 0.0,
        true_rate=0.0 if route == "finite_countermodel" else 0.9,
        derived_rate=0.2,
        confidence=confidence,
        recommended_task_kind="finite_countermodel_search"
        if route == "finite_countermodel"
        else "proof_template",
        warnings=[],
        evidence={},
    )


def _outcome(route: str = "variable_identification") -> PairOutcome:
    terminal = "FINITE_COUNTERMODEL" if route == "finite_countermodel" else "VERIFIED_PROOF"
    status = "REFUTED" if route == "finite_countermodel" else "VERIFIED"
    trust = "finite_verified" if route == "finite_countermodel" else "lean_verified"
    return PairOutcome(
        pair_id=f"pair:{route}",
        source="x * y = x",
        target="x * x = x",
        source_idx=1,
        target_idx=2,
        claim_id=None,
        terminal_form=terminal,
        verification_status=status,
        trust_level=trust,
        origin="primitive_trace",
        route=route,
        derivation_rule=None,
        parent_claims=[],
        features=extract_outcome_pair_features("x * y = x", "x * x = x"),
        labels={},
        evidence={},
        warnings=[],
    )


def _store(path: Path) -> LawbookStore:
    trace = Trace(
        claim="A=>B",
        source="A",
        target="B",
        routes_tried=["variable_identification"],
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verification_status=VerificationStatus.VERIFIED,
        certificate=Certificate(TerminalForm.VERIFIED_PROOF, "A=>B", payload={}),
    )
    store = LawbookStore(path)
    store.import_lawbook(CertificateLawbook.from_traces([trace]), replace=True)
    return store


def test_scheduler_input_pair_json_safe_conversion() -> None:
    pair = SchedulerInputPair("A", "B", source_idx=1, target_idx=2, label="demo", metadata={"k": "v"})
    assert SchedulerInputPair.from_dict(pair.to_dict()) == pair


def test_score_is_deterministic() -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy()])
    pair = SchedulerInputPair("x * y = x", "x * x = x")
    assert scheduler.score_pair(pair).score_breakdown == scheduler.score_pair(pair).score_breakdown


def test_higher_route_prior_increases_route_prior_field() -> None:
    pair = SchedulerInputPair("x * y = x", "x * x = x")
    low = HTiltScheduler(policy_cards=[_policy(confidence=0.2)]).score_pair(pair)
    high = HTiltScheduler(policy_cards=[_policy(confidence=0.8)]).score_pair(pair)
    assert high.score_breakdown["route_prior"] > low.score_breakdown["route_prior"]


def test_gap_features_increase_gap_score() -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy()])
    simple = scheduler.score_pair(SchedulerInputPair("x = x", "x = x"))
    gap = scheduler.score_pair(SchedulerInputPair("x = x", "x * y * z = z"))
    assert gap.score_breakdown["gap_score"] > simple.score_breakdown["gap_score"]


def test_missing_idx_increases_novelty_score() -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy()])
    known_idx = scheduler.score_pair(SchedulerInputPair("x * y = x", "x * x = x", 1, 2))
    missing_idx = scheduler.score_pair(SchedulerInputPair("x * y = x", "x * x = x"))
    assert missing_idx.score_breakdown["novelty_score"] > known_idx.score_breakdown["novelty_score"]


def test_derived_amplification_potential_works() -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy(route="finite_countermodel")])
    task = scheduler.score_pair(SchedulerInputPair("x * y = x", "x * x = x", 1, 2))
    assert task.score_breakdown["derived_amplification_potential"] >= 0.75


def test_known_oracle_hit_skip_and_include_modes(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        scheduler = HTiltScheduler(oracle=KernelOracle(store), policy_cards=[_policy()])
        assert scheduler.schedule([{"source": "A", "target": "B"}], skip_known=True) == []
        included = scheduler.schedule([{"source": "A", "target": "B"}], skip_known=False)
        assert included[0].recommended_task_kind == "known_certificate_review"
        assert included[0].priority == 0
        assert included[0].oracle_status == "VERIFIED"
    finally:
        store.close()


def test_priorities_normalize_and_top_k_truncates() -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy(), _policy(route="finite_countermodel")])
    tasks = scheduler.schedule(
        [
            {"source": "x * y = x", "target": "x * x = x"},
            {"source": "x = x", "target": "x * y * z = z"},
        ],
        top_k=1,
    )
    assert len(tasks) == 1
    assert tasks[0].priority == 1.0


def test_stats_counts_by_route_and_task_kind() -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy(route="finite_countermodel")])
    tasks = scheduler.schedule([{"source": "x * y = x", "target": "x * x = x"}])
    stats = scheduler.stats(tasks)
    assert stats.scheduled_count == 1
    assert stats.by_task_kind["finite_countermodel_search"] == 1
    assert stats.by_recommended_route["finite_countermodel"] == 1


def test_json_jsonl_save_and_warnings(tmp_path: Path) -> None:
    scheduler = HTiltScheduler(policy_cards=[_policy()])
    tasks = scheduler.schedule([{"source": "x * y = x", "target": "x * x = x"}])
    stats = scheduler.stats(tasks)
    tasks_json = tmp_path / "tasks.json"
    tasks_jsonl = tmp_path / "tasks.jsonl"
    stats_json = tmp_path / "stats.json"
    scheduler.save_tasks_json(tasks_json, tasks)
    scheduler.save_tasks_jsonl(tasks_jsonl, tasks)
    scheduler.save_stats_json(stats_json, stats)
    assert "scheduling pressure" in tasks[0].warnings[0]
    assert json.loads(tasks_json.read_text(encoding="utf-8"))
    assert tasks_jsonl.read_text(encoding="utf-8").splitlines()
    assert json.loads(stats_json.read_text(encoding="utf-8"))["scheduled_count"] == 1


def test_scheduler_can_build_from_outcomes() -> None:
    scheduler = HTiltScheduler(outcomes=[_outcome("variable_identification")])
    task = scheduler.schedule([{"source": "x * y = x", "target": "x * x = x"}])[0]
    assert task.recommended_route == "variable_identification"


def test_cli_works_with_temp_candidate_pairs(tmp_path: Path) -> None:
    pairs = tmp_path / "pairs.jsonl"
    outcomes = tmp_path / "outcomes.jsonl"
    tasks_json = tmp_path / "tasks.json"
    tasks_jsonl = tmp_path / "tasks.jsonl"
    stats_json = tmp_path / "stats.json"
    pairs.write_text(json.dumps({"source": "x * y = x", "target": "x * x = x"}) + "\n", encoding="utf-8")
    outcomes.write_text(json.dumps(_outcome("variable_identification").to_dict()) + "\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "schedule_certificate_tasks.py"),
            "--pairs-jsonl",
            str(pairs),
            "--outcomes-jsonl",
            str(outcomes),
            "--out-tasks-json",
            str(tasks_json),
            "--out-tasks-jsonl",
            str(tasks_jsonl),
            "--out-stats",
            str(stats_json),
            "--top-k",
            "10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["task_count"] == 1
    assert tasks_json.exists()
    assert tasks_jsonl.exists()
    assert stats_json.exists()

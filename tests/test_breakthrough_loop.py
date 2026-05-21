from pathlib import Path

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks, builtin_constructor_families
from mathgraph.breakthrough_loop import BreakthroughLoop, BreakthroughLoopConfig
from mathgraph.external_certificates import ExternalCertificate
from mathgraph.finite_magma_world import check_finite_countermodel
from mathgraph.promotion_gate import PromotionGateDecisionKind


def _run_loop(tmp_path: Path) -> tuple[BreakthroughLoop, dict]:
    loop = BreakthroughLoop(
        builtin_breakthrough_tasks(),
        builtin_constructor_families(),
        BreakthroughLoopConfig(episodes=4, attempts_per_task=1, out_dir=tmp_path, reason_atlas_db=tmp_path / "ra.sqlite"),
    )
    return loop, loop.run()


def test_loop_creates_attempts_and_improves(tmp_path):
    loop, summary = _run_loop(tmp_path)
    assert loop.all_attempts
    assert summary["final_solved_or_refuted_count"] > summary["initial_solved_or_refuted_count"]
    assert summary["final_residual_count"] < summary["initial_residual_count"]


def test_successful_countermodel_creates_gate_accepted_certificate(tmp_path):
    loop, _summary = _run_loop(tmp_path)
    accepted = [attempt for attempt in loop.all_attempts if attempt.promotion_accepted]
    assert accepted
    cert = ExternalCertificate.from_dict(accepted[0].certificate)
    assert cert.boundary_evidence is not None
    assert cert.boundary_evidence.is_valid_boundary()
    assert accepted[0].promotion_decision["decision_kind"] == PromotionGateDecisionKind.ACCEPT_FOR_LAWBOOK.value


def test_failed_search_is_feedback_not_truth(tmp_path):
    loop, _summary = _run_loop(tmp_path)
    rejected = [attempt for attempt in loop.all_attempts if not attempt.promotion_accepted]
    assert rejected
    assert all(attempt.lawbook_candidate is None for attempt in rejected)
    assert loop.reason_loop.store.stats().feedback_count > 0


def test_lawbook_candidates_and_advisory_queue(tmp_path):
    loop, summary = _run_loop(tmp_path)
    assert loop.lawbook_candidates
    assert summary["advisory_boundary_ok"] is True
    rows = loop.reason_loop.next_advisory_tasks()
    assert rows
    assert all(row.get("advisory_only", True) for row in rows)


def test_accepted_certificates_are_checkable(tmp_path):
    loop, _summary = _run_loop(tmp_path)
    for cert_row in loop.accepted_certificates:
        cert = ExternalCertificate.from_dict(cert_row)
        cm = cert.countermodel
        result = check_finite_countermodel(cm["source_equation"], cm["target_equation"], cm["table"])
        assert result.terminal_candidate_ok

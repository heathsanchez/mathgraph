import json
from pathlib import Path

import pytest

from mathgraph.external_certificates import ExternalCertificate
from mathgraph.finite_magma_world import check_finite_countermodel
from mathgraph.sair_breakthrough_runner import SAIRBreakthroughRunConfig, run_sair_breakthrough_loop


def test_fallback_mode_runs_successfully(tmp_path):
    result = run_sair_breakthrough_loop(SAIRBreakthroughRunConfig(equations_path=tmp_path / "missing.txt", matrix_path=tmp_path / "missing.npy", out_dir=tmp_path / "out", max_tasks=10, episodes=3, attempt_budget=8))
    summary = result.summary
    assert summary["source_mode"] == "fallback_demo"
    assert summary["overall"] == "PASS"
    assert summary["promotion_gate_accepted"] > 0
    assert Path(result.output_paths["sair_report.md"]).exists()


def test_mini_sair_mode_runs_and_writes_outputs(tmp_path):
    np = pytest.importorskip("numpy")
    equations = tmp_path / "equations.txt"
    equations.write_text("x = x\nx = y\nx = x ◇ y\nx = y ◇ x\n", encoding="utf-8")
    matrix = tmp_path / "matrix.npy"
    np.save(matrix, np.array([[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]], dtype=bool))
    out_dir = tmp_path / "out"
    result = run_sair_breakthrough_loop(SAIRBreakthroughRunConfig(equations_path=equations, matrix_path=matrix, out_dir=out_dir, max_tasks=4, episodes=3, attempt_budget=8))
    summary = result.summary
    assert summary["source_mode"] == "real_sair"
    assert summary["equations_loaded"] == 4
    assert summary["matrix_pairs_sampled"] > 0
    assert summary["overall"] in {"PASS", "PROMISING"}
    for name in (
        "sair_breakthrough_summary.json",
        "sair_episode_metrics.csv",
        "sair_attempts.csv",
        "sair_accepted_certificates.jsonl",
        "sair_rejected_attempts.jsonl",
        "sair_residual_tasks.csv",
        "sair_reason_atlas_feedback.jsonl",
        "sair_lawbook_candidates.jsonl",
        "sair_constructor_priority_shift.csv",
        "sair_report.md",
    ):
        assert (out_dir / name).exists()


def test_accepted_certificates_are_finite_checkable(tmp_path):
    result = run_sair_breakthrough_loop(SAIRBreakthroughRunConfig(equations_path=tmp_path / "missing.txt", matrix_path=tmp_path / "missing.npy", out_dir=tmp_path / "out", max_tasks=10, episodes=3, attempt_budget=8))
    cert_path = Path(result.output_paths["sair_accepted_certificates.jsonl"])
    first = json.loads(cert_path.read_text(encoding="utf-8").splitlines()[0])
    cert = ExternalCertificate.from_dict(first)
    cm = cert.countermodel
    assert check_finite_countermodel(cm["source_equation"], cm["target_equation"], cm["table"]).terminal_candidate_ok


def test_failed_attempts_do_not_become_truth(tmp_path):
    result = run_sair_breakthrough_loop(SAIRBreakthroughRunConfig(equations_path=tmp_path / "missing.txt", matrix_path=tmp_path / "missing.npy", out_dir=tmp_path / "out", max_tasks=10, episodes=2, attempt_budget=2))
    rows = [json.loads(line) for line in Path(result.output_paths["sair_rejected_attempts.jsonl"]).read_text(encoding="utf-8").splitlines()]
    assert rows
    assert all(row["decision"]["accepted"] is False for row in rows)
    assert all(row["decision"]["lawbook_candidate"] is None for row in rows)
    assert result.summary["promotion_gate_rejected"] > 0

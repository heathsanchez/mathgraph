import json
import subprocess
import sys

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks, expected_demo_fields


def test_demo_corpus_deterministic():
    assert builtin_breakthrough_tasks() == builtin_breakthrough_tasks()
    assert len(builtin_breakthrough_tasks()) >= 12


def test_runner_summary_and_files(tmp_path):
    out_dir = tmp_path / "demo"
    subprocess.run(
        [sys.executable, "scripts/run_breakthrough_loop_demo.py", "--out-dir", str(out_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads((out_dir / "breakthrough_summary.json").read_text(encoding="utf-8"))
    for field in expected_demo_fields():
        assert field in summary
    assert summary["overall"] == "PASS"
    assert summary["final_solved_or_refuted_count"] > summary["initial_solved_or_refuted_count"]
    assert summary["final_residual_count"] < summary["initial_residual_count"]
    assert (out_dir / "episode_metrics.csv").exists()
    assert (out_dir / "attempts.csv").exists()
    assert (out_dir / "accepted_certificates.jsonl").exists()
    assert (out_dir / "rejected_attempts.jsonl").exists()
    assert (out_dir / "report.md").exists()


def test_report_contains_breakthrough_result(tmp_path):
    out_dir = tmp_path / "demo"
    subprocess.run(
        [sys.executable, "scripts/run_breakthrough_loop_demo.py", "--out-dir", str(out_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "BREAKTHROUGH LOOP RESULT" in report
    assert "PromotionGate accepted" in report
    assert "Overall: `PASS`" in report

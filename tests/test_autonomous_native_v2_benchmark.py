import json
import subprocess
import sys
from pathlib import Path


def test_native_v2_benchmark_tiny_demo_outputs_cross_seed_artifacts(tmp_path):
    out_dir = tmp_path / "benchmark"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_autonomous_native_v2_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--tiny-demo",
            "--seeds",
            "1729",
            "1730",
            "--episodes",
            "3",
            "--sample-pairs",
            "80",
            "--repair-budget",
            "10",
            "--max-n",
            "3",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["all_terminal_safety_passed"] is True
    assert summary["total_true_contamination_count"] == 0
    assert summary["total_terminal_claims_from_advisory_count"] == 0
    assert summary["total_failed_search_promoted_true_count"] == 0
    assert summary["mean_repair_final_yield"] >= summary["mean_generic_final_yield"]

    for name in [
        "benchmark_summary.json",
        "benchmark_report.md",
        "cross_seed_summary.csv",
        "cross_seed_gate_results.csv",
        "cross_seed_episode_metrics.csv",
        "cross_seed_artifact_manifest.csv",
    ]:
        assert (out_dir / name).exists(), name

    manifest = (out_dir / "cross_seed_artifact_manifest.csv").read_text(encoding="utf-8")
    assert "seed_output_dir" in manifest
    assert str(out_dir / "seed_1729") in manifest
    assert str(out_dir / "seed_1730") in manifest


def test_native_v2_benchmark_refuses_missing_real_files(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_autonomous_native_v2_benchmark.py",
            "--equations",
            str(tmp_path / "missing-equations.txt"),
            "--matrix",
            str(tmp_path / "missing-matrix.npy"),
            "--out-dir",
            str(tmp_path / "benchmark"),
            "--seeds",
            "1",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "requires existing equations and matrix" in result.stderr

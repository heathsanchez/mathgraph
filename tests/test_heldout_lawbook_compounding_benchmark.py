import csv
import json
import subprocess
import sys
from pathlib import Path


def test_heldout_lawbook_benchmark_tiny_demo(tmp_path):
    out_dir = tmp_path / "heldout"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_heldout_lawbook_compounding_benchmark.py",
            "--allow-fallback-demo",
            "--out-dir",
            str(out_dir),
            "--seeds",
            "1729,1730",
            "--train-pairs",
            "30",
            "--heldout-pairs",
            "30",
            "--true-pairs",
            "10",
            "--episodes",
            "2",
            "--repair-budget",
            "8",
            "--max-n",
            "3",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["total_true_contamination_count"] == 0
    assert summary["total_terminal_claims_from_advisory_count"] == 0
    assert summary["total_failed_search_promoted_true_count"] == 0
    assert summary["mean_lawbook_yield"] >= summary["mean_generic_yield"]

    required = [
        "heldout_lawbook_summary.json",
        "heldout_lawbook_report.md",
        "cross_seed_summary.csv",
        "per_seed_policy_eval.csv",
        "per_seed_gate_results.csv",
        "train_lawbook_manifest.csv",
        "heldout_pair_features.csv",
        "heldout_recovery_eval.csv",
        "heldout_obstruction_atlas.csv",
        "terminal_form_audit.csv",
        "artifact_manifest.json",
    ]
    for name in required:
        assert (out_dir / name).exists(), name

    policies = list(csv.DictReader((out_dir / "per_seed_policy_eval.csv").open(newline="", encoding="utf-8")))
    assert any(row["policy"] == "heldout_lawbook_guided" for row in policies)

    seed_rows = list(csv.DictReader((out_dir / "cross_seed_summary.csv").open(newline="", encoding="utf-8")))
    assert seed_rows
    assert all(int(row["train_heldout_overlap_count"]) == 0 for row in seed_rows)

    terminal_rows = list(csv.DictReader((out_dir / "terminal_form_audit.csv").open(newline="", encoding="utf-8")))
    assert terminal_rows
    assert not any(row["status"] == "RESIDUAL" and row["terminal_form"] == "VERIFIED_PROOF" for row in terminal_rows)


def test_heldout_lawbook_benchmark_requires_real_or_fallback(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_heldout_lawbook_compounding_benchmark.py",
            "--out-dir",
            str(tmp_path / "missing"),
            "--seeds",
            "1",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "provide real --equations/--matrix or pass --allow-fallback-demo" in result.stderr

import json
import subprocess
import sys

import pandas as pd


def test_active_residual_discovery_fallback_cli(tmp_path):
    out_dir = tmp_path / "active"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_active_residual_discovery_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--seed",
            "1729",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["residual_basin_count"] >= 3
    assert summary["proposal_count"] >= 6
    assert summary["total_recovered_pairs"] > 0
    assert summary["true_contamination_count"] == 0
    assert summary["terminal_claims_from_advisory_count"] == 0
    assert summary["failed_search_promoted_true_count"] == 0

    required = [
        "active_residual_basins.csv",
        "constructor_proposals.csv",
        "proposal_evaluations.csv",
        "active_discovery_summary.json",
        "active_discovery_report.md",
        "active_discovery.sqlite",
        "artifact_manifest.json",
    ]
    for name in required:
        assert (out_dir / name).exists(), name

    proposals = pd.read_csv(out_dir / "constructor_proposals.csv")
    assert not proposals.empty
    assert not proposals["can_promote_truth"].astype(str).str.lower().isin(["true", "1"]).any()

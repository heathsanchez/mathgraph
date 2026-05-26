import json
import subprocess
import sys

import pandas as pd


def test_standalone_synthesis_fallback_cli(tmp_path):
    out_dir = tmp_path / "synthesis"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_proposal_constructor_synthesis.py",
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
    assert summary["proposal_count"] >= 5
    assert summary["synthesized_constructor_count"] >= 20
    assert summary["synthesized_recovered_pairs"] > 0
    assert summary["true_contamination_count"] == 0
    assert summary["terminal_claims_from_advisory_count"] == 0

    for name in [
        "synthesized_constructors.csv",
        "synthesis_results.csv",
        "synthesized_recoveries.csv",
        "synthesis_summary.json",
        "synthesis_report.md",
        "synthesis.sqlite",
        "artifact_manifest.json",
    ]:
        assert (out_dir / name).exists(), name

    constructors = pd.read_csv(out_dir / "synthesized_constructors.csv")
    assert not constructors.empty
    assert not constructors["can_promote_truth"].astype(str).str.lower().isin(["true", "1"]).any()

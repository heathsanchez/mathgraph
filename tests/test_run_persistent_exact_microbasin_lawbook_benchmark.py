import json
import subprocess
import sys

import pandas as pd


def test_cli_fallback_persistent_exact_benchmark(tmp_path):
    out_dir = tmp_path / "persistent"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_persistent_exact_microbasin_lawbook_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--seeds",
            "1729,1730,1731",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["persistent_memory_nonempty"] is True
    assert summary["persistent_memory_reused"] is True
    assert summary["total_exact_recipe_reuse_count"] > 0
    assert summary["true_contamination_count"] == 0
    assert summary["terminal_claims_from_advisory_count"] == 0
    assert summary["failed_search_promoted_true_count"] == 0
    assert summary["compounding_classification"] in {"weak_compounding", "strong_compounding", "neutral_memory"}

    required = [
        "persistent_exact_microbasin_summary.json",
        "persistent_exact_microbasin_report.md",
        "persistent_exact_microbasin_lawbook.csv",
        "persistent_exact_microbasin_lawbook.sqlite",
        "persistent_replay_curve.csv",
        "persistent_replay_eval.csv",
        "persistent_recipe_reuse.csv",
        "terminal_form_audit.csv",
        "artifact_manifest.json",
    ]
    for name in required:
        assert (out_dir / name).exists(), name

    replay = pd.read_csv(out_dir / "persistent_replay_eval.csv")
    assert "persistent_recovered_proxy" in replay.columns
    assert not replay["can_promote_truth"].astype(str).str.lower().isin(["true", "1"]).any()

import json
import subprocess
import sys

import pandas as pd


def test_v2_fallback_demo_writes_artifacts_and_safety(tmp_path):
    out_dir = tmp_path / "v2"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_persistent_exact_microbasin_lawbook_v2_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--seeds",
            "1729,1730,1731,1732",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["selected_route_count"] > 0
    assert summary["rejected_route_count"] > 0
    assert summary["v2_minus_v1_gain"] >= 0
    assert summary["total_true_contamination_count"] == 0
    assert summary["total_terminal_claims_from_advisory_count"] == 0
    assert summary["total_failed_search_promoted_true_count"] == 0

    required = [
        "persistent_exact_microbasin_v2_summary.json",
        "persistent_exact_microbasin_v2_report.md",
        "causal_route_scores.csv",
        "selected_causal_routes.csv",
        "causal_replay_curve.csv",
        "causal_replay_eval.csv",
        "v1_vs_v2_policy_comparison.csv",
        "terminal_form_audit.csv",
        "artifact_manifest.json",
        "persistent_exact_microbasin_lawbook_v2.sqlite",
    ]
    for name in required:
        assert (out_dir / name).exists(), name

    selected = pd.read_csv(out_dir / "selected_causal_routes.csv")
    assert not selected.empty
    assert not selected["can_promote_truth"].astype(str).str.lower().isin(["true", "1"]).any()


def test_v2_no_current_episode_leakage(tmp_path):
    out_dir = tmp_path / "v2"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_persistent_exact_microbasin_lawbook_v2_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--seeds",
            "1,2,3,4",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads((out_dir / "persistent_exact_microbasin_v2_summary.json").read_text())
    assert summary["no_current_episode_leakage"] is True

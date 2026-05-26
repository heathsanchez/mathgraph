import json
import subprocess
import sys


def test_active_discovery_with_synthesis_writes_artifacts(tmp_path):
    out_dir = tmp_path / "active_synth"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_active_residual_discovery_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--synthesize-constructors",
            "--seed",
            "1729",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["synthesis_enabled"] is True
    assert summary["synthesized_constructor_count"] > 0
    assert summary["finite_checked_recoveries"] > 0
    assert summary["evaluation_mode"] == "finite_checked"
    assert summary["true_contamination_count"] == 0
    assert summary["terminal_claims_from_advisory_count"] == 0

    for name in [
        "synthesized_constructors.csv",
        "synthesis_results.csv",
        "synthesized_recoveries.csv",
        "synthesis_summary.json",
    ]:
        assert (out_dir / name).exists(), name

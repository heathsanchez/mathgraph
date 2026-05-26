import json
import subprocess
import sys


def test_active_discovery_residual_conditioned_integration(tmp_path):
    out_dir = tmp_path / "active_conditioned"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_active_residual_discovery_benchmark.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--synthesize-constructors",
            "--residual-conditioned-synthesis",
            "--seed",
            "1729",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["residual_conditioned_enabled"] is True
    assert summary["residual_conditioned_constructor_count"] > 0
    assert summary["residual_conditioned_recovered_pairs"] > 0
    assert summary["evaluation_mode"] == "finite_checked_conditioned"
    assert summary["true_contamination_count"] == 0
    assert summary["terminal_claims_from_advisory_count"] == 0

    for name in [
        "residual_conditioned_pair_specs.csv",
        "residual_conditioned_attempts.csv",
        "residual_conditioned_constructors.csv",
        "residual_conditioned_recoveries.csv",
        "residual_conditioned_summary.json",
    ]:
        assert (out_dir / name).exists(), name

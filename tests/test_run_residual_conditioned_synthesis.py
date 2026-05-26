import json
import subprocess
import sys


def test_residual_conditioned_fallback_cli(tmp_path):
    out_dir = tmp_path / "conditioned"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_residual_conditioned_synthesis.py",
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
    assert summary["residual_conditioned_pair_count"] >= 8
    assert summary["residual_conditioned_attempt_count"] >= 20
    assert summary["residual_conditioned_constructor_count"] >= 5
    assert summary["residual_conditioned_recovered_pairs"] >= 1
    assert summary["true_contamination_count"] == 0

    for name in [
        "residual_conditioned_pair_specs.csv",
        "residual_conditioned_attempts.csv",
        "residual_conditioned_constructors.csv",
        "residual_conditioned_recoveries.csv",
        "residual_conditioned_summary.json",
        "residual_conditioned_report.md",
        "residual_conditioned.sqlite",
        "artifact_manifest.json",
    ]:
        assert (out_dir / name).exists(), name

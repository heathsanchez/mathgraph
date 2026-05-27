import json
import subprocess
import sys


def test_cli_fallback_demo_is_safe_infrastructure_only(tmp_path) -> None:
    out = tmp_path / "fallback"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_recursive_residual_transfer.py",
            "--equations",
            str(tmp_path / "missing_equations.txt"),
            "--matrix",
            str(tmp_path / "missing_matrix.npy"),
            "--out-dir",
            str(out),
            "--seeds",
            "1729,42,137",
            "--profile",
            "transfer_fast",
            "--strict-advisory-boundary",
            "--write-report",
            "--fallback-demo",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads((out / "recursive_transfer_summary.json").read_text(encoding="utf-8"))
    assert "classification: safe_infrastructure_only" in result.stdout
    assert summary["classification"] == "safe_infrastructure_only"
    assert summary["advisory_boundary_ok"] is True
    assert summary["true_contamination_max"] == 0
    for name in [
        "seed_summary.csv",
        "route_eval_by_seed_split.csv",
        "constructor_manifest.csv",
        "constructor_attribution.csv",
        "compact_atlas_eval.csv",
        "best_compact_by_seed_split.csv",
        "gate_results.csv",
        "recursive_transfer_report.md",
        "recursive_transfer.sqlite",
    ]:
        assert (out / name).exists()


def test_cli_requires_real_inputs_without_fallback(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_recursive_residual_transfer.py",
            "--equations",
            str(tmp_path / "missing_equations.txt"),
            "--matrix",
            str(tmp_path / "missing_matrix.npy"),
            "--out-dir",
            str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Use --fallback-demo" in result.stderr

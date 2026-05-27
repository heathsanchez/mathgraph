from __future__ import annotations

import json
import subprocess
import sys


def test_cli_fallback_mode(tmp_path):
    out_dir = tmp_path / "demo"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_sair_stage2_end_to_end.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--episodes",
            "2",
            "--train-false",
            "100",
            "--heldout-false",
            "100",
            "--sample-true",
            "50",
            "--seeds",
            "1729",
            "--strict-admission",
            "--write-report",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["final_classification"] == "safe_infrastructure_only"
    assert (out_dir / "artifact_manifest.json").exists()
    assert (out_dir / "sair_stage2_evidence_summary.json").exists()
    assert "final_classification" in summary


def test_cli_refuses_real_mode_without_files(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_sair_stage2_end_to_end.py",
            "--out-dir",
            str(tmp_path / "real"),
            "--strict-admission",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "requires --equations and --matrix" in result.stderr

from __future__ import annotations

import json
import subprocess
import sys


def test_cli_fallback_breakthrough_search(tmp_path):
    out_dir = tmp_path / "search"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_sair_stage2_breakthrough_search.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
            "--seeds",
            "1729,1730",
            "--train-false",
            "100",
            "--heldout-false",
            "100",
            "--sample-true",
            "50",
            "--episodes",
            "2",
            "--policy-search-rounds",
            "2",
            "--strict-admission",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["fallback_demo"] is True
    assert (out_dir / "breakthrough_search_summary.json").exists()
    assert (out_dir / "canonical_policy.json").exists()


def test_cli_real_requires_files(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/run_sair_stage2_breakthrough_search.py", "--out-dir", str(tmp_path / "real")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "requires --equations and --matrix" in result.stderr

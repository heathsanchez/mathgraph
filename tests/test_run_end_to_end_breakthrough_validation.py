import json
import subprocess
import sys
from pathlib import Path


def test_breakthrough_validation_cli_fallback_exits_zero(tmp_path: Path):
    out = tmp_path / "breakthrough_cli"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_end_to_end_breakthrough_validation.py",
            "--out-dir",
            str(out),
            "--fallback-demo",
            "--seed",
            "1729",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["all_safety_gates_passed"] is True
    assert (out / "breakthrough_validation_summary.json").exists()
    assert (out / "breakthrough_validation.sqlite").exists()
    report = (out / "breakthrough_validation_report.md").read_text(encoding="utf-8")
    assert "Breakthrough Classification" in report

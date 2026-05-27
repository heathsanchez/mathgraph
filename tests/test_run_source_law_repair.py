import json
import subprocess
import sys
from pathlib import Path


def test_source_law_repair_fallback_cli_writes_artifacts(tmp_path: Path):
    out = tmp_path / "source_repair"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_source_law_repair.py",
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
    assert summary["source_law_repair_attempt_count"] >= 5
    assert summary["source_law_repair_recovered_pairs"] >= 1
    assert summary["true_contamination_count"] == 0
    assert (out / "source_law_repair_results.csv").exists()
    assert (out / "source_law_repair_traces.csv").exists()
    assert (out / "source_law_repair.sqlite").exists()

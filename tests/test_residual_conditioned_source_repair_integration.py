import json
import subprocess
import sys
from pathlib import Path


def test_residual_conditioned_cli_with_source_repair_writes_artifacts(tmp_path: Path):
    out = tmp_path / "conditioned_repair"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_residual_conditioned_synthesis.py",
            "--out-dir",
            str(out),
            "--fallback-demo",
            "--enable-source-law-repair",
            "--repair-max-steps",
            "1000",
            "--seed",
            "1729",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(result.stdout)
    assert summary["benchmark_passed"] is True
    assert summary["source_law_repair_enabled"] is True
    assert summary["true_contamination_count"] == 0
    assert (out / "source_law_repair_results.csv").exists()
    assert (out / "source_law_repair_traces.csv").exists()

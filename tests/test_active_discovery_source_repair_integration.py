import json
import subprocess
import sys
from pathlib import Path


def test_active_discovery_with_source_repair_writes_metrics(tmp_path: Path):
    out = tmp_path / "active_source_repair"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_active_residual_discovery_benchmark.py",
            "--out-dir",
            str(out),
            "--fallback-demo",
            "--synthesize-constructors",
            "--residual-conditioned-synthesis",
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
    assert "source_law_repair_recovered_pairs" in summary
    assert summary["true_contamination_count"] == 0
    assert (out / "source_law_repair_results.csv").exists()
    assert (out / "source_law_repair_summary.json").exists()

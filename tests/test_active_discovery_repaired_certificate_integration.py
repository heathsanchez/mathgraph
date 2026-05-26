import json
import subprocess
import sys
from pathlib import Path


def test_active_discovery_assimilates_repaired_certificates(tmp_path: Path):
    out = tmp_path / "active_certs"
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
            "--assimilate-repaired-certificates",
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
    assert summary["certificate_assimilation_enabled"] is True
    assert "repaired_certificate_count" in summary
    assert summary["true_contamination_count"] == 0
    assert (out / "repaired_countermodel_certificates" / "repaired_countermodel_lawbook.sqlite").exists()

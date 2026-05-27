import json
import subprocess
import sys
from pathlib import Path


def test_repaired_countermodel_certificate_assimilation_fallback(tmp_path: Path):
    out = tmp_path / "certs"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_repaired_countermodel_certificate_assimilation.py",
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
    assert summary["certificate_count"] >= 1
    assert summary["rejected_count"] >= 1
    assert summary["safety_advisory_promotion_count"] == 0
    assert (out / "repaired_countermodel_certificates.csv").exists()
    assert (out / "repaired_countermodel_lawbook.sqlite").exists()

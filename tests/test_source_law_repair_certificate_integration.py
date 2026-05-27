import json
import subprocess
import sys
from pathlib import Path


def test_source_law_repair_cli_assimilates_certificates(tmp_path: Path):
    out = tmp_path / "source_repair"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_source_law_repair.py",
            "--out-dir",
            str(out),
            "--fallback-demo",
            "--assimilate-certificates",
            "--seed",
            "1729",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(result.stdout)
    assert summary["certificate_assimilation_enabled"] is True
    assert summary["repaired_certificate_count"] >= 1
    assert (out / "repaired_countermodel_certificates" / "repaired_countermodel_manifest.json").exists()

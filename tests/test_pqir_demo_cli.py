import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_polarized_quotient_ir_demo.py"


def test_pqir_demo_cli_fallback_writes_outputs(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--out-dir", str(tmp_path), "--sample-pairs", "20", "--seed", "1729"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["overall"] == "PASS"
    assert summary["source_mode"] == "fallback_demo"
    for name in ("pair_features.csv", "obstruction_atlas.csv", "pqir_demo_summary.json", "pqir_demo_report.md"):
        assert (tmp_path / name).exists()


def test_pqir_demo_summary_fields(tmp_path):
    subprocess.run([sys.executable, str(SCRIPT), "--out-dir", str(tmp_path), "--sample-pairs", "10"], cwd=ROOT, check=True)
    data = json.loads((tmp_path / "pqir_demo_summary.json").read_text(encoding="utf-8"))

    assert data["advisory_boundary_preserved"] is True
    assert data["terminal_claims_from_advisory_count"] == 0
    assert data["failed_search_promoted_true_count"] == 0
    assert data["pairs_sampled"] == 10

import json
import subprocess
import sys


def test_run_metabolic_cycle_cli_strict_json(tmp_path):
    out_dir = tmp_path / "cycle"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_metabolic_cycle.py",
            "--store",
            str(tmp_path / "cycle.sqlite"),
            "--out-dir",
            str(out_dir),
            "--max-tasks",
            "20",
            "--synthetic-seed",
            "--strict",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert "better_shaped_unknown" in payload
    assert (out_dir / "metabolic_cycle_summary.json").exists()
    assert (out_dir / "metabolic_cycle_report.md").exists()


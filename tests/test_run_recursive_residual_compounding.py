import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_recursive_residual_compounding.py"


def test_script_help_works():
    proc = subprocess.run([sys.executable, str(SCRIPT), "--help"], cwd=ROOT, text=True, capture_output=True, check=False)

    assert proc.returncode == 0
    assert "--profile" in proc.stdout


def test_script_fallback_smoke_writes_required_outputs(tmp_path):
    out_dir = tmp_path / "smoke"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            "smoke",
            "--allow-fallback-demo",
            "--out-dir",
            str(out_dir),
            "--skip-sqlite",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["overall"] == "PASS"
    assert summary["fallback_mode"] is True
    assert (out_dir / "recursive_residual_summary.json").exists()
    assert (out_dir / "artifact_manifest.json").exists()


def test_script_refuses_missing_real_mode_without_fallback(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--equations",
            str(tmp_path / "missing_equations.txt"),
            "--matrix",
            str(tmp_path / "missing_matrix.npy"),
            "--out-dir",
            str(tmp_path / "real"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode != 0
    error = json.loads(proc.stderr)
    assert error["overall"] == "FAIL"
    assert "could not be loaded" in error["error"]


def test_json_summary_has_expected_fields(tmp_path):
    out_dir = tmp_path / "summary"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--profile", "smoke", "--allow-fallback-demo", "--out-dir", str(out_dir), "--skip-sqlite"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads((out_dir / "recursive_residual_summary.json").read_text(encoding="utf-8"))
    for key in (
        "source_mode",
        "generic_recoveries",
        "recursive_full_recoveries",
        "best_compact_recoveries",
        "true_contamination_count",
        "advisory_boundary_preserved",
    ):
        assert key in data

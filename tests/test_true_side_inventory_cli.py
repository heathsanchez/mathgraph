import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/run_true_side_inventory.py")


def test_true_side_inventory_tiny_demo_writes_outputs(tmp_path):
    out = tmp_path / "true_inventory"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out-dir", str(out), "--tiny-demo"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "source_mode: fallback_tiny_demo" in result.stdout
    required = [
        "true_inventory_summary.json",
        "true_inventory_report.md",
        "true_proof_template_inventory.csv",
        "congruence_explain_traces.csv",
        "false_control_promotion_audit.csv",
        "promotion_gate_report.csv",
        "lean_artifacts_manifest.csv",
        "lawbook.sqlite",
    ]
    for name in required:
        assert (out / name).exists(), name
    summary = json.loads((out / "true_inventory_summary.json").read_text())
    assert summary["false_controls_promoted_true"] == 0
    assert summary["advisory_boundary_preserved"] is True


def test_true_side_inventory_refuses_missing_real_inputs(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--out-dir",
            str(tmp_path / "real"),
            "--equations",
            str(tmp_path / "missing.txt"),
            "--matrix",
            str(tmp_path / "missing.npy"),
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "could not be loaded" in result.stderr or "could not be loaded" in result.stdout

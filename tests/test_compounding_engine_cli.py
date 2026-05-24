import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/run_mathgraph_compounding_engine.py")


def test_compounding_engine_cli_tiny_demo_writes_outputs(tmp_path):
    out = tmp_path / "demo"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out-dir", str(out), "--episodes", "2", "--tiny-demo"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "source_mode: fallback_tiny_demo" in result.stdout
    required = [
        "lawbook.sqlite",
        "compounding_summary.json",
        "compounding_report.md",
        "gate_results.csv",
        "cross_episode_policy_summary.csv",
        "cross_episode_policy_eval.csv",
        "cross_episode_obstruction_summary.csv",
        "constructor_bank_manifest.csv",
        "repair_gain_curve.csv",
        "repair_selected_constructors.csv",
        "quotient_repair_family_lawbook.csv",
        "obstruction_atlas.csv",
        "residual_queue.csv",
        "true_proof_template_summary.csv",
        "artifact_manifest.json",
    ]
    for name in required:
        assert (out / name).exists(), name
    summary = json.loads((out / "compounding_summary.json").read_text())
    assert summary["fallback_mode"] is True
    assert summary["advisory_boundary_preserved"] is True
    assert summary["true_contamination_count"] == 0


def test_compounding_engine_cli_refuses_missing_real_inputs(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out-dir", str(tmp_path / "real"), "--equations", str(tmp_path / "missing.txt"), "--matrix", str(tmp_path / "missing.npy")],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "could not be loaded" in result.stderr or "could not be loaded" in result.stdout

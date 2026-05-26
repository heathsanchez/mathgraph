import json
import subprocess
import sys
from pathlib import Path


def test_microbasin_distillation_cli_fallback_demo(tmp_path):
    out_dir = tmp_path / "demo"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_microbasin_distillation.py",
            "--out-dir",
            str(out_dir),
            "--fallback-demo",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    summary = json.loads(result.stdout)
    assert summary["safety"]["safety_passed"] is True
    assert summary["advisory_only"] is True
    assert summary["can_promote_truth"] is False
    for name in [
        "joined_recovery_features.csv",
        "microbasin_summary.csv",
        "microbasin_gain_attribution.csv",
        "minimal_constructor_recipes.csv",
        "residual_obstruction_targets.csv",
        "microbasin_distillation_summary.json",
        "microbasin_distillation_report.md",
        "artifact_manifest.json",
        "microbasin_distillation.sqlite",
    ]:
        assert (out_dir / name).exists(), name

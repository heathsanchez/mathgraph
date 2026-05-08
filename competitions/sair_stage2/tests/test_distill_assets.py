import json
import subprocess
import sys

import pytest


np = pytest.importorskip("numpy")


def test_distill_assets_emits_verified_false_assets(tmp_path):
    equations = tmp_path / "equations.txt"
    matrix = tmp_path / "matrix.npy"
    out_dir = tmp_path / "artifacts"
    equations.write_text("x = x\nx * x = x\n", encoding="utf-8")
    np.save(matrix, np.array([[True, False], [True, True]], dtype=bool))
    proc = subprocess.run(
        [
            sys.executable,
            "competitions/sair_stage2/scripts/distill_assets.py",
            "--equations-path",
            str(equations),
            "--matrix-path",
            str(matrix),
            "--sample-size",
            "1",
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(proc.stdout)
    assert summary["verified_false_certificates"] == 1
    assert (out_dir / "false_certificate_candidates.jsonl").exists()
    assets = (out_dir / "generated_solver_assets.py").read_text(encoding="utf-8")
    assert "EXACT_FALSE" in assets
    assert "0->1" in assets


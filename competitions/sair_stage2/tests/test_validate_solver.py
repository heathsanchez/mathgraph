import json
import subprocess
import sys

import pytest


np = pytest.importorskip("numpy")


def test_validate_solver_skips_missing_assets(tmp_path):
    solver = tmp_path / "solver.py"
    subprocess.run(
        [sys.executable, "competitions/sair_stage2/scripts/build_solver.py", "--out", str(solver)],
        check=True,
    )
    out_dir = tmp_path / "validation"
    result = subprocess.run(
        [
            sys.executable,
            "competitions/sair_stage2/scripts/validate_solver.py",
            "--solver",
            str(solver),
            "--equations-path",
            str(tmp_path / "missing_equations.txt"),
            "--matrix-path",
            str(tmp_path / "missing.npy"),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["status"] == "skipped"
    assert (out_dir / "validation_summary.json").exists()


def test_validate_solver_reports_method_summary_and_zero_wrong(tmp_path):
    solver = tmp_path / "solver.py"
    subprocess.run(
        [sys.executable, "competitions/sair_stage2/scripts/build_solver.py", "--out", str(solver)],
        check=True,
    )
    equations = tmp_path / "equations.txt"
    matrix = tmp_path / "matrix.npy"
    equations.write_text("x = x\nx * x = x\n", encoding="utf-8")
    np.save(matrix, np.array([[True, False], [True, True]], dtype=bool))
    out_dir = tmp_path / "validation"
    result = subprocess.run(
        [
            sys.executable,
            "competitions/sair_stage2/scripts/validate_solver.py",
            "--solver",
            str(solver),
            "--equations-path",
            str(equations),
            "--matrix-path",
            str(matrix),
            "--mode",
            "all",
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["wrong_true"] == 0
    assert summary["wrong_false"] == 0
    assert summary["method_summary"]
    assert summary["unsound_true_examples"] == []

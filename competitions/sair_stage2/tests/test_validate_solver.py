import json
import subprocess
import sys


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


import ast
import importlib.util
import subprocess
import sys


def test_build_solver_creates_standalone_under_budget(tmp_path):
    out = tmp_path / "solver.py"
    subprocess.run(
        [
            sys.executable,
            "competitions/sair_stage2/scripts/build_solver.py",
            "--out",
            str(out),
            "--max-bytes",
            "500000",
        ],
        check=True,
    )
    assert out.exists()
    assert out.stat().st_size < 500000
    subprocess.run(
        [
            sys.executable,
            "competitions/sair_stage2/scripts/check_solver_size.py",
            "--solver",
            str(out),
            "--max-bytes",
            "500000",
        ],
        check=True,
    )
    tree = ast.parse(out.read_text(encoding="utf-8"))
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports |= {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "mathgraph" not in imports
    assert "competitions" not in imports
    spec = importlib.util.spec_from_file_location("built_solver", out)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.solve("x * y = x", "a * b = a")["verdict"] == "TRUE"

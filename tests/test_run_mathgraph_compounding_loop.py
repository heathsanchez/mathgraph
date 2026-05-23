import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_mathgraph_compounding_loop.py"


def test_cli_runner_works_in_fallback_mode(tmp_path):
    out_dir = tmp_path / "fallback"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--allow-fallback-demo",
            "--out-dir",
            str(out_dir),
            "--episodes",
            "2",
            "--train-pairs",
            "2",
            "--eval-pairs",
            "4",
            "--attempt-budget",
            "4",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["overall"] == "PASS"
    assert summary["fallback_mode"] is True
    report = json.loads((out_dir / "compounding_report.json").read_text(encoding="utf-8"))
    assert report["fallback_mode"] is True
    assert "lawbook_hit_rate" in {row["metric"] for row in report["metrics"]}
    assert "decode_success_rate" in {row["metric"] for row in report["metrics"]}


def test_cli_refuses_missing_real_mode_without_fallback(tmp_path):
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
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode != 0
    error = json.loads(proc.stderr)
    assert error["overall"] == "FAIL"
    assert "real SAIR mode requested" in error["error"]

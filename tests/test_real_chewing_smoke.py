import argparse
import json
import subprocess
import sys
from pathlib import Path

from mathgraph.kernel import Kernel

from scripts.run_real_chewing_smoke import run_real_chewing_smoke


ROOT = Path(__file__).resolve().parents[1]


def _write_tiny_assets(tmp_path: Path) -> tuple[Path, Path]:
    traces = tmp_path / "traces.json"
    trace = Kernel().prove("x = x", "x = x")
    trace.metadata.update({"compiled_route": "variable_identification", "source_idx": 0, "target_idx": 0})
    traces.write_text(json.dumps([trace.to_dict()]), encoding="utf-8")
    equations = tmp_path / "equations.txt"
    equations.write_text("x = x\nx = y\nx * y = x\nx * y = y\n", encoding="utf-8")
    return traces, equations


def _args(tmp_path: Path, **overrides):
    traces, equations = _write_tiny_assets(tmp_path)
    data = {
        "out_dir": str(tmp_path / "real_smoke"),
        "traces_json": str(traces),
        "equations_path": str(equations),
        "matrix_path": None,
        "max_frontier_pairs": 12,
        "top_k_schedule": 8,
        "max_tasks": 8,
        "max_countermodel_order": 2,
        "random_tables_per_order": 0,
        "allow_synthetic_fallback": False,
        "copy_assets": False,
    }
    data.update(overrides)
    return argparse.Namespace(**data)


def test_missing_assets_report_ok_false_without_crash(tmp_path: Path) -> None:
    args = argparse.Namespace(
        out_dir=str(tmp_path / "missing"),
        traces_json=str(tmp_path / "missing_traces.json"),
        equations_path=str(tmp_path / "missing_equations.txt"),
        matrix_path=None,
        max_frontier_pairs=10,
        top_k_schedule=5,
        max_tasks=5,
        max_countermodel_order=2,
        random_tables_per_order=0,
        allow_synthetic_fallback=False,
        copy_assets=False,
    )
    report = run_real_chewing_smoke(args)
    assert not report["ok"]
    assert set(report["summary"]["missing_assets"]) == {"traces_json", "equations_path"}
    assert Path(report["paths"]["report_json"]).exists()


def test_real_chewing_tiny_assets_runs_store_frontier_schedule(tmp_path: Path) -> None:
    report = run_real_chewing_smoke(_args(tmp_path))
    assert report["summary"]["primitive_count_before"] >= 1
    assert report["summary"]["frontier_count"] > 0
    assert report["summary"]["scheduled_count"] > 0
    assert report["summary"]["task_count"] > 0
    assert Path(report["paths"]["report_json"]).exists()


def test_no_overclaiming_when_no_imported_countermodels(tmp_path: Path) -> None:
    traces, equations = _write_tiny_assets(tmp_path)
    equations.write_text("x = x\n", encoding="utf-8")
    report = run_real_chewing_smoke(
        _args(
            tmp_path,
            traces_json=str(traces),
            equations_path=str(equations),
            max_countermodel_order=1,
        )
    )
    if report["summary"]["imported_count"] == 0:
        assert "No new finite countermodels were imported." in report["summary"]["warnings"]
        assert report["summary"]["finite_executor_verified_count"] == 0


def test_real_chewing_with_synthetic_fallback_can_import(tmp_path: Path) -> None:
    report = run_real_chewing_smoke(
        _args(tmp_path, allow_synthetic_fallback=True, max_countermodel_order=2)
    )
    if report["summary"]["no_finite_tasks"]:
        assert report["summary"]["synthetic_fallback_used"]
    assert report["summary"]["frontier_count"] > 0


def test_cli_help_works() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_real_chewing_smoke.py"),
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "--out-dir" in completed.stdout


def test_cli_missing_assets_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "cli_missing"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_real_chewing_smoke.py"),
            "--out-dir",
            str(out),
            "--traces-json",
            str(tmp_path / "missing_traces.json"),
            "--equations-path",
            str(tmp_path / "missing_equations.txt"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert not payload["ok"]
    assert (out / "real_chewing_smoke_report.json").exists()

import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    ChewingSmokeConfig,
    ChewingSmokeResult,
    ChewingSmokeStageResult,
    run_chewing_smoke,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_equations(path: Path, rows: list[str] | None = None) -> None:
    path.write_text(
        "\n".join(rows or ["x = x", "x = y", "x * y = x", "x * y = y"]) + "\n",
        encoding="utf-8",
    )


def test_dataclass_roundtrip() -> None:
    config = ChewingSmokeConfig(equations_path="eq.txt", out_dir="out")
    assert ChewingSmokeConfig.from_dict(config.to_dict()) == config
    stage = ChewingSmokeStageResult(
        name="stage",
        ok=True,
        path="out/file",
        summary={"count": 1},
        warnings=[],
        elapsed_sec=0.1,
    )
    assert ChewingSmokeStageResult.from_dict(stage.to_dict()) == stage
    result = ChewingSmokeResult(
        ok=True,
        stages=[stage],
        summary={"ok": True},
        paths={"report": "out/report.json"},
        warnings=[],
        created_ts="now",
    )
    assert ChewingSmokeResult.from_dict(result.to_dict()) == result


def test_smoke_runs_empty_store_and_imports_easy_countermodel(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    _write_equations(equations)
    result = run_chewing_smoke(
        ChewingSmokeConfig(
            equations_path=str(equations),
            out_dir=str(tmp_path / "smoke"),
            max_frontier_pairs=20,
            top_k_schedule=12,
            max_tasks=12,
            max_countermodel_order=2,
        )
    )
    assert result.ok
    assert result.summary["imported_count"] >= 1
    assert result.summary["oracle_probe_success_count"] >= 1
    assert result.summary["lawbook_primitive_count_after_import"] >= result.summary["imported_count"]


def test_smoke_writes_expected_files(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    _write_equations(equations)
    result = run_chewing_smoke(
        ChewingSmokeConfig(
            equations_path=str(equations),
            out_dir=str(tmp_path / "smoke"),
            max_frontier_pairs=10,
            top_k_schedule=8,
            max_tasks=8,
            max_countermodel_order=2,
        )
    )
    expected = [
        "lawbook.sqlite",
        "frontier.jsonl",
        "frontier_summary.json",
        "schedule.jsonl",
        "schedule_summary.json",
        "task_queue.jsonl",
        "task_queue_summary.json",
        "finite_countermodel_results.jsonl",
        "finite_countermodel_summary.json",
        "countermodel_import_summary.json",
        "oracle_probe_results.json",
        "derived_after_import.jsonl",
        "outcome_after_import.jsonl",
        "chewing_smoke_report.json",
        "chewing_smoke_report.md",
    ]
    for name in expected:
        assert (tmp_path / "smoke" / name).exists(), name
    report = json.loads((tmp_path / "smoke" / "chewing_smoke_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["ok"] is result.ok
    assert set(stage["name"] for stage in report["stages"]) >= {"frontier", "scheduler", "oracle_probe"}


def test_zero_import_required_is_failure(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    _write_equations(equations, ["x = x"])
    result = run_chewing_smoke(
        ChewingSmokeConfig(
            equations_path=str(equations),
            out_dir=str(tmp_path / "smoke_fail"),
            max_frontier_pairs=5,
            top_k_schedule=5,
            max_tasks=5,
            max_countermodel_order=1,
            require_imported_countermodel=True,
        )
    )
    assert not result.ok
    assert result.summary["imported_count"] == 0
    assert any("No finite countermodels imported" in warning for warning in result.warnings)


def test_zero_import_allowed_is_warning_only(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    _write_equations(equations, ["x = x"])
    result = run_chewing_smoke(
        ChewingSmokeConfig(
            equations_path=str(equations),
            out_dir=str(tmp_path / "smoke_warn"),
            max_frontier_pairs=5,
            top_k_schedule=5,
            max_tasks=5,
            max_countermodel_order=1,
            require_imported_countermodel=False,
        )
    )
    assert result.ok
    assert result.summary["imported_count"] == 0
    assert any("No finite countermodels imported" in warning for warning in result.warnings)


def test_cli_smoke_writes_report(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    _write_equations(equations)
    out_dir = tmp_path / "cli_smoke"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_chewing_smoke.py"),
            "--equations-path",
            str(equations),
            "--out-dir",
            str(out_dir),
            "--max-frontier-pairs",
            "16",
            "--top-k-schedule",
            "12",
            "--max-tasks",
            "12",
            "--max-countermodel-order",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["summary"]["imported_count"] >= 1
    assert (out_dir / "chewing_smoke_report.json").exists()


def test_summary_counts_are_internally_consistent(tmp_path: Path) -> None:
    equations = tmp_path / "equations.txt"
    _write_equations(equations)
    result = run_chewing_smoke(
        ChewingSmokeConfig(
            equations_path=str(equations),
            out_dir=str(tmp_path / "smoke_counts"),
            max_frontier_pairs=12,
            top_k_schedule=10,
            max_tasks=10,
            max_countermodel_order=2,
        )
    )
    summary = result.summary
    assert summary["scheduled_count"] <= summary["frontier_count"]
    assert summary["task_count"] <= summary["scheduled_count"]
    assert summary["imported_count"] <= summary["finite_executor_verified_count"]
    assert summary["oracle_probe_success_count"] <= summary["oracle_probe_count"]
    assert summary["outcome_row_count_after_import"] >= summary["lawbook_primitive_count_after_import"]

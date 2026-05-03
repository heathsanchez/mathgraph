import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    FiniteCountermodelConfig,
    FiniteCountermodelResult,
    FiniteCountermodelRunResult,
    run_finite_countermodel_tasks,
)


ROOT = Path(__file__).resolve().parents[1]


def _task(
    task_id: str = "task1",
    source: str = "x = x",
    target: str = "x = y",
    task_kind: str = "finite_countermodel_search",
) -> dict:
    return {
        "task_id": task_id,
        "source": source,
        "target": target,
        "source_idx": 1,
        "target_idx": 2,
        "route": "finite_countermodel",
        "task_kind": task_kind,
        "priority": 1.0,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_dataclass_roundtrip() -> None:
    config = FiniteCountermodelConfig("queue.jsonl", "out.jsonl")
    assert FiniteCountermodelConfig.from_dict(config.to_dict()) == config
    result = FiniteCountermodelResult(
        task_id="t",
        source="x = x",
        target="x = y",
        source_idx=1,
        target_idx=2,
        route="finite_countermodel",
        status="no_countermodel_found",
        terminal_form=None,
        verification_status="NOT_VERIFIED",
        certificate_id=None,
        countermodel=None,
        witness=None,
        tables_tried=1,
        elapsed_sec=0.0,
        failure_reason="none",
        warnings=["warn"],
        evidence={},
    )
    assert FiniteCountermodelResult.from_dict(result.to_dict()) == result
    run = FiniteCountermodelRunResult([result.to_dict()], {"result_count": 1}, {"jsonl": "out"})
    assert FiniteCountermodelRunResult.from_dict(run.to_dict()) == run


def test_skips_proof_template_tasks(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task(task_kind="proof_template")])
    result = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out)))
    row = result.results[0]
    assert row["status"] == "skipped_non_countermodel_task"
    assert row["terminal_form"] is None
    assert row["verification_status"] == "NOT_VERIFIED"


def test_finds_countermodel_for_x_equals_x_implies_x_equals_y(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task(source="x = x", target="x = y")])
    result = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out), max_order=2))
    row = result.results[0]
    assert row["status"] == "finite_countermodel_found"
    assert row["terminal_form"] == "FINITE_COUNTERMODEL"
    assert row["verification_status"] == "FINITE_VERIFIED"
    assert row["countermodel"]["order"] == 2
    assert row["witness"]["target_left_value"] != row["witness"]["target_right_value"]


def test_finds_countermodel_for_projection_source(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task(source="x ◇ y = x", target="x ◇ y = y")])
    result = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out), max_order=2))
    row = result.results[0]
    assert row["status"] == "finite_countermodel_found"
    assert row["countermodel"]["family"] == "left_projection"


def test_same_text_returns_no_countermodel_found(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task(source="x = x", target="x = x")])
    result = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out), max_order=2))
    row = result.results[0]
    assert row["status"] == "no_countermodel_found"
    assert row["terminal_form"] is None
    assert row["verification_status"] == "NOT_VERIFIED"
    assert row["failure_reason"]


def test_writes_jsonl_and_summary(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task()])
    run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out), max_order=2))
    assert out.exists()
    assert out.with_name("finite_countermodel_summary.json").exists()
    summary = json.loads(out.with_name("finite_countermodel_summary.json").read_text(encoding="utf-8"))
    assert summary["result_count"] == 1
    assert summary["found_count"] == 1


def test_certificate_id_deterministic(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out1 = tmp_path / "results1.jsonl"
    out2 = tmp_path / "results2.jsonl"
    _write_jsonl(queue, [_task()])
    first = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out1), max_order=2))
    second = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out2), max_order=2))
    assert first.results[0]["certificate_id"] == second.results[0]["certificate_id"]


def test_warnings_and_no_lawbook_promotion(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task()])
    row = run_finite_countermodel_tasks(FiniteCountermodelConfig(str(queue), str(out), max_order=2)).results[0]
    assert "Finite countermodel results are exact" in row["warnings"][0]
    assert "lawbook" in row["warnings"][1]
    assert "LawbookStore" not in row["evidence"]


def test_cli_smoke(tmp_path: Path) -> None:
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "results.jsonl"
    _write_jsonl(queue, [_task()])
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_finite_countermodel_tasks.py"),
            "--task-queue-jsonl",
            str(queue),
            "--out",
            str(out),
            "--max-tasks",
            "10",
            "--max-order",
            "2",
            "--exhaustive-order-limit",
            "2",
            "--random-tables-per-order",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["found_count"] == 1
    assert out.exists()

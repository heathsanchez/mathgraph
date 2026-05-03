import json
import subprocess
import sys
from pathlib import Path

from mathgraph import TaskQueueConfig, TaskQueueItem, TaskQueueResult, build_task_queue


ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _row(**kwargs) -> dict:
    base = {
        "source": "x * y = x",
        "target": "x * x = x",
        "source_idx": 1,
        "target_idx": 2,
        "recommended_route": "variable_identification",
        "priority": 0.8,
        "label": "structural_unknown",
        "metadata": {"candidate_origin": "structural_frontier"},
        "score_breakdown": {"route_prior": 0.5},
    }
    base.update(kwargs)
    return base


def test_dataclass_roundtrip() -> None:
    item = TaskQueueItem(
        task_id="task",
        source="A",
        target="B",
        source_idx=1,
        target_idx=2,
        route="finite_countermodel",
        task_kind="finite_countermodel_search",
        terminal_goal="FINITE_COUNTERMODEL",
        priority=0.5,
        schedule_rank=1,
        candidate_origin="matrix",
        label="matrix_false_unverified",
        required_inputs=["source"],
        steps=["step"],
        success_criteria=["success"],
        failure_modes=["failure"],
        evidence={"x": 1},
        warnings=["warn"],
    )
    assert TaskQueueItem.from_dict(item.to_dict()) == item
    config = TaskQueueConfig("schedule.jsonl", "queue.jsonl")
    assert TaskQueueConfig.from_dict(config.to_dict()) == config
    result = TaskQueueResult([item.to_dict()], {"task_count": 1}, {"jsonl": "queue"})
    assert TaskQueueResult.from_dict(result.to_dict()) == result


def test_finite_countermodel_route_maps_correctly(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row(recommended_route="finite_countermodel")])
    task = build_task_queue(TaskQueueConfig(str(schedule), str(out))).tasks[0]
    assert task["task_kind"] == "finite_countermodel_search"
    assert task["terminal_goal"] == "FINITE_COUNTERMODEL"
    assert "Search only tables satisfying source." in task["steps"]


def test_proof_route_maps_correctly(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row(selected_route="skeleton_preserving_relabel", recommended_route=None)])
    task = build_task_queue(TaskQueueConfig(str(schedule), str(out))).tasks[0]
    assert task["task_kind"] == "proof_template"
    assert task["terminal_goal"] == "VERIFIED_PROOF"


def test_unknown_route_maps_to_obstruction(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row(top_route="mystery_route", recommended_route=None)])
    task = build_task_queue(TaskQueueConfig(str(schedule), str(out))).tasks[0]
    assert task["task_kind"] == "obstruction_analysis"
    assert task["terminal_goal"] == "NAMED_OBSTRUCTION"


def test_reads_priority_and_route_from_multiple_names(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    rows = [
        _row(route="direct_substitution_instance", recommended_route=None, normalized_priority=0.4, priority=None),
        _row(top_route="finite_countermodel", recommended_route=None, htilt_priority=0.5, priority=None),
        _row(selected_route="proof_template", recommended_route=None, frontier_score=0.6, priority=None),
    ]
    _write_jsonl(schedule, rows)
    tasks = build_task_queue(TaskQueueConfig(str(schedule), str(out))).tasks
    assert [task["route"] for task in tasks] == [
        "proof_template",
        "finite_countermodel",
        "direct_substitution_instance",
    ]
    assert [task["priority"] for task in tasks] == [0.6, 0.5, 0.4]


def test_output_and_summary_exist(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row()])
    result = build_task_queue(TaskQueueConfig(str(schedule), str(out)))
    assert out.exists()
    assert out.with_name("task_queue_summary.json").exists()
    assert result.summary["task_count"] == 1
    assert result.summary["by_task_kind"]["proof_template"] == 1


def test_max_tasks_and_min_priority_respected(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row(priority=0.1), _row(priority=0.9), _row(priority=0.8)])
    result = build_task_queue(
        TaskQueueConfig(str(schedule), str(out), max_tasks=1, min_priority=0.5)
    )
    assert result.summary["task_count"] == 1
    assert result.summary["skipped_count"] == 1
    assert result.tasks[0]["priority"] == 0.9


def test_warnings_and_no_terminal_promotion(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row()])
    task = build_task_queue(TaskQueueConfig(str(schedule), str(out))).tasks[0]
    assert "This task is not a proof" in task["warnings"][0]
    assert "verification_status" not in task
    assert "terminal_form" not in task


def test_known_rows_skipped_by_default(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row(oracle_status="VERIFIED", recommended_task_kind="known_certificate_review")])
    result = build_task_queue(TaskQueueConfig(str(schedule), str(out)))
    assert result.summary["task_count"] == 0
    included = build_task_queue(TaskQueueConfig(str(schedule), str(out), include_known=True))
    assert included.summary["task_count"] == 1


def test_cli_smoke(tmp_path: Path) -> None:
    schedule = tmp_path / "schedule.jsonl"
    out = tmp_path / "queue.jsonl"
    _write_jsonl(schedule, [_row(recommended_route="finite_countermodel", priority=0.7)])
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_task_queue.py"),
            "--schedule-jsonl",
            str(schedule),
            "--out",
            str(out),
            "--max-tasks",
            "10",
            "--min-priority",
            "0.2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["task_count"] == 1
    assert out.exists()

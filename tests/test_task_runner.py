import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CertificateTask,
    TaskOutcome,
    TaskRunSummary,
    execute_certificate_task,
    execute_many_certificate_tasks,
    read_outcomes_json,
    read_outcomes_jsonl,
    residual_outcomes,
    summarize_task_outcomes,
    write_outcomes_json,
    write_outcomes_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]


def _task(kind: str, **overrides) -> CertificateTask:
    base = {
        "task_id": f"task_{kind}",
        "source": "x = x",
        "target": "x * x = x",
        "task_kind": kind,
        "terminal_goal": "NAMED_OBSTRUCTION",
        "route": None,
        "priority": 0.5,
        "status": "planned",
        "required_inputs": [],
        "steps": [],
        "success_criteria": [],
        "failure_modes": [],
        "warnings": ["Do not promote without verification."],
        "evidence": {},
        "advice": {"status": "advisory_only"},
    }
    base.update(overrides)
    return CertificateTask.from_dict(base)


def _known_task() -> CertificateTask:
    return _task(
        "known_certificate",
        terminal_goal="FINITE_COUNTERMODEL",
        route="finite_countermodel",
        status="not_needed",
        advice={
            "status": "known_certificate",
            "verification_status": "REFUTED",
            "known_claim": "x = x => (x * x) = x",
        },
        evidence={"known_claim": "x = x => (x * x) = x", "exact_match": True},
    )


def _tasks() -> list[CertificateTask]:
    return [
        _known_task(),
        _task("proof_template", terminal_goal="VERIFIED_PROOF", route="variable_identification"),
        _task("finite_countermodel_search", terminal_goal="FINITE_COUNTERMODEL", route="finite_countermodel"),
        _task("obstruction_analysis", terminal_goal="NAMED_OBSTRUCTION", route=None),
    ]


def test_task_outcome_roundtrip() -> None:
    outcome = execute_certificate_task(_known_task())

    assert TaskOutcome.from_dict(outcome.to_dict()) == outcome


def test_known_certificate_preserves_terminal_form() -> None:
    outcome = execute_certificate_task(_known_task())

    assert outcome.status == "known_certificate"
    assert outcome.terminal_form == "FINITE_COUNTERMODEL"
    assert outcome.verification_status == "REFUTED"


def test_proof_template_does_not_become_verified_proof() -> None:
    outcome = execute_certificate_task(
        _task("proof_template", terminal_goal="VERIFIED_PROOF", route="variable_identification")
    )

    assert outcome.status == "mock_proof_template_generated"
    assert outcome.terminal_form == "NAMED_OBSTRUCTION"
    assert outcome.verification_status == "UNKNOWN"


def test_countermodel_search_does_not_become_finite_countermodel() -> None:
    outcome = execute_certificate_task(
        _task("finite_countermodel_search", terminal_goal="FINITE_COUNTERMODEL", route="finite_countermodel")
    )

    assert outcome.status == "mock_countermodel_search_queued"
    assert outcome.terminal_form == "NAMED_OBSTRUCTION"
    assert outcome.verification_status == "UNKNOWN"


def test_obstruction_task_becomes_named_obstruction() -> None:
    outcome = execute_certificate_task(_task("obstruction_analysis"))

    assert outcome.status == "mock_obstruction_recorded"
    assert outcome.terminal_form == "NAMED_OBSTRUCTION"
    assert outcome.verification_status == "OBSTRUCTED"


def test_malformed_task_handled_safely() -> None:
    outcome = execute_certificate_task({"not": "a certificate task"})

    assert outcome.status == "malformed_task"
    assert outcome.terminal_form == "NAMED_OBSTRUCTION"
    assert outcome.errors


def test_batch_execution_respects_limit() -> None:
    outcomes = execute_many_certificate_tasks(_tasks(), limit=2)

    assert len(outcomes) == 2


def test_summary_counts_are_correct() -> None:
    outcomes = execute_many_certificate_tasks(_tasks())
    summary = summarize_task_outcomes(outcomes)

    assert isinstance(TaskRunSummary.from_dict(summary.to_dict()), TaskRunSummary)
    assert summary.outcome_count == 4
    assert summary.known_certificate_count == 1
    assert summary.mock_proof_template_count == 1
    assert summary.mock_countermodel_queue_count == 1
    assert summary.obstruction_count == 1
    assert summary.residual_count == 3


def test_residuals_exclude_known_certificates() -> None:
    residuals = residual_outcomes(execute_many_certificate_tasks(_tasks()))

    assert len(residuals) == 3
    assert all(outcome.status != "known_certificate" for outcome in residuals)


def test_outcome_jsonl_and_json_roundtrip(tmp_path: Path) -> None:
    outcomes = execute_many_certificate_tasks(_tasks())
    json_path = tmp_path / "outcomes.json"
    jsonl_path = tmp_path / "outcomes.jsonl"

    write_outcomes_json(outcomes, json_path)
    write_outcomes_jsonl(outcomes, jsonl_path)

    assert read_outcomes_json(json_path) == outcomes
    assert read_outcomes_jsonl(jsonl_path) == outcomes


def test_cli_directory_mode(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    out_dir = tmp_path / "run"
    tasks_path.write_text(json.dumps([task.to_dict() for task in _tasks()]), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_certificate_tasks.py"),
            "--tasks-json",
            str(tasks_path),
            "--out",
            str(out_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "outcomes.json").exists()
    assert (out_dir / "outcomes.jsonl").exists()
    assert (out_dir / "residual.json").exists()


def test_cli_summary_only(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps([task.to_dict() for task in _tasks()]), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_certificate_tasks.py"),
            "--tasks-json",
            str(tasks_path),
            "--summary-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert '"outcome_count": 4' in result.stdout


def test_cli_explicit_paths(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    summary_path = tmp_path / "summary.json"
    outcomes_path = tmp_path / "outcomes.json"
    outcomes_jsonl = tmp_path / "outcomes.jsonl"
    residual_path = tmp_path / "residual.json"
    tasks_path.write_text("\n".join(json.dumps(task.to_dict()) for task in _tasks()) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_certificate_tasks.py"),
            "--tasks-jsonl",
            str(tasks_path),
            "--summary-json",
            str(summary_path),
            "--outcomes-json",
            str(outcomes_path),
            "--outcomes-jsonl",
            str(outcomes_jsonl),
            "--residual-json",
            str(residual_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert summary_path.exists()
    assert outcomes_path.exists()
    assert outcomes_jsonl.exists()
    assert residual_path.exists()


def test_cli_unsupported_mode_fails(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps([_known_task().to_dict()]), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_certificate_tasks.py"),
            "--tasks-json",
            str(tasks_path),
            "--mode",
            "real",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "only mock task execution mode" in result.stderr

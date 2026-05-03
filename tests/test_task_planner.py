import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CertificateLawbook,
    CertificateTask,
    Kernel,
    plan_certificate_task,
    plan_many_certificate_tasks,
)


ROOT = Path(__file__).resolve().parents[1]


def _lawbook() -> CertificateLawbook:
    known = Kernel().prove("x = x", "x * x = x")
    known.metadata["compiled_route"] = "finite_countermodel"
    proof = Kernel().prove("a * b = a", "a * a = a")
    proof.metadata["compiled_route"] = "variable_identification"
    return CertificateLawbook.from_traces([known, proof])


def test_known_pair_plan_is_not_needed() -> None:
    task = plan_certificate_task(_lawbook(), "x = x", "x * x = x")

    assert task.task_kind == "known_certificate"
    assert task.status == "not_needed"
    assert task.terminal_goal == "FINITE_COUNTERMODEL"
    assert task.success_criteria == ["Existing verified lawbook trace found."]


def test_unknown_finite_countermodel_advisory_plan() -> None:
    task = plan_certificate_task(_lawbook(), "x = x", "(x * z) * y = z")

    assert task.task_kind == "finite_countermodel_search"
    assert task.terminal_goal == "FINITE_COUNTERMODEL"
    assert task.status == "planned"
    assert "Search small finite magmas for a model satisfying source." in task.steps
    assert "Finite-search failure is residual only, not proof." in task.failure_modes


def test_unknown_proof_route_advisory_plan() -> None:
    task = plan_certificate_task(_lawbook(), "x * y = x", "x * x = x")

    assert task.task_kind == "proof_template"
    assert task.terminal_goal == "VERIFIED_PROOF"
    assert task.route == "variable_identification"
    assert "Run Lean verification." in task.steps
    assert "Lean failure." in task.failure_modes


def test_ambiguous_plan_becomes_obstruction_analysis() -> None:
    task = plan_certificate_task(_lawbook(), "", "x = x")

    assert task.task_kind == "obstruction_analysis"
    assert task.terminal_goal == "NAMED_OBSTRUCTION"
    assert task.status == "blocked"


def test_task_ids_are_deterministic() -> None:
    task1 = plan_certificate_task(_lawbook(), "x * y = x", "x * x = x")
    task2 = plan_certificate_task(_lawbook(), "x * y = x", "x * x = x")

    assert task1.task_id == task2.task_id


def test_task_roundtrip() -> None:
    task = plan_certificate_task(_lawbook(), "x * y = x", "x * x = x")

    assert CertificateTask.from_dict(task.to_dict()) == task


def test_batch_planning() -> None:
    tasks = plan_many_certificate_tasks(
        _lawbook(),
        [
            ("x = x", "x * x = x"),
            {"source": "x * y = x", "target": "x * x = x"},
        ],
    )

    assert [task.task_kind for task in tasks] == ["known_certificate", "proof_template"]


def test_warnings_prevent_overclaiming() -> None:
    task = plan_certificate_task(_lawbook(), "x * y = x", "x * x = x")

    assert any("Do not promote" in warning for warning in task.warnings)
    assert task.advice["status"] == "advisory_only"


def test_cli_single_pair(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    out = tmp_path / "task.json"
    traces.write_text(
        json.dumps([trace.to_dict() for trace in _lawbook().traces]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "plan_certificate_task.py"),
            "--traces-json",
            str(traces),
            "--source",
            "x * y = x",
            "--target",
            "x * x = x",
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["task_kind"] == "proof_template"
    assert '"task_id"' in result.stdout


def test_cli_batch(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    pairs = tmp_path / "pairs.json"
    out = tmp_path / "tasks.json"
    traces.write_text(
        json.dumps([trace.to_dict() for trace in _lawbook().traces]),
        encoding="utf-8",
    )
    pairs.write_text(
        json.dumps([["x = x", "x * x = x"], {"source": "x = x", "target": "(x * z) * y = z"}]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "plan_certificate_task.py"),
            "--traces-json",
            str(traces),
            "--pairs-json",
            str(pairs),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert [task["task_kind"] for task in payload] == [
        "known_certificate",
        "finite_countermodel_search",
    ]

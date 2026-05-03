import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CountermodelImportConfig,
    FiniteCountermodelConfig,
    KernelOracle,
    LawbookStore,
    import_finite_countermodel_results,
    run_finite_countermodel_tasks,
)


ROOT = Path(__file__).resolve().parents[1]
VISION_SMOKE = ROOT / "scripts" / "run_vision_smoke.py"


def _load_vision_smoke():
    spec = importlib.util.spec_from_file_location("run_vision_smoke", VISION_SMOKE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_synthetic_fallback_finite_queue_shape() -> None:
    module = _load_vision_smoke()
    tasks = module.fallback_finite_countermodel_tasks()
    assert tasks
    assert all(task["task_kind"] == "finite_countermodel_search" for task in tasks)
    assert all(task["terminal_goal"] == "FINITE_COUNTERMODEL" for task in tasks)
    assert all("Do not promote" in " ".join(task["warnings"]) for task in tasks)


def test_executor_finds_countermodel_on_fallback_examples(tmp_path: Path) -> None:
    module = _load_vision_smoke()
    queue = tmp_path / "queue.jsonl"
    out = tmp_path / "finite_results.jsonl"
    _write_jsonl(queue, module.fallback_finite_countermodel_tasks())
    run = run_finite_countermodel_tasks(
        FiniteCountermodelConfig(str(queue), str(out), max_order=2, max_tasks=10)
    )
    assert run.summary["found_count"] >= 1
    assert any(row["verification_status"] == "FINITE_VERIFIED" for row in run.results)


def test_importer_imports_verified_finite_results_and_oracle_refutes(tmp_path: Path) -> None:
    module = _load_vision_smoke()
    queue = tmp_path / "queue.jsonl"
    finite_results = tmp_path / "finite_results.jsonl"
    store_path = tmp_path / "lawbook.sqlite"
    _write_jsonl(queue, module.fallback_finite_countermodel_tasks()[:1])
    run_finite_countermodel_tasks(
        FiniteCountermodelConfig(str(queue), str(finite_results), max_order=2, max_tasks=10)
    )
    imported = import_finite_countermodel_results(
        CountermodelImportConfig(str(finite_results), str(store_path), revalidate=True)
    )
    assert imported.summary["imported_count"] == 1
    row = imported.results[0]
    store = LawbookStore(store_path)
    try:
        answer = KernelOracle(store).query(row.source, row.target)
        assert answer.status == "REFUTED"
        assert answer.terminal_form == "FINITE_COUNTERMODEL"
    finally:
        store.close()


def test_vision_smoke_uses_fallback_when_scheduler_queue_is_obstruction(tmp_path: Path) -> None:
    module = _load_vision_smoke()
    report = module.run_vision_smoke(tmp_path / "vision", max_order=2, max_tasks=10)
    assert report["ok"]
    assert report["summary"]["schedule_count"] > 0
    assert report["summary"]["task_queue_count"] > 0
    assert report["summary"]["fallback_used"] is True
    assert report["summary"]["initial_task_distribution"]["by_task_kind"].get("obstruction_analysis", 0) > 0
    assert report["summary"]["finite_executor_verified_count"] >= 1
    assert report["summary"]["imported_count"] >= 1
    assert report["summary"]["oracle_probe_success_count"] >= 1


def test_no_scheduler_or_obstruction_rows_are_promoted(tmp_path: Path) -> None:
    module = _load_vision_smoke()
    report = module.run_vision_smoke(tmp_path / "vision", max_order=2, max_tasks=10)
    import_payload = json.loads(
        Path(report["paths"]["import_summary"]).read_text(encoding="utf-8")
    )
    for row in import_payload["results"]:
        if row["imported"]:
            assert row["status"] == "imported"
            assert row["terminal_form"] == "FINITE_COUNTERMODEL"
            assert row["verification_status"] == "REFUTED"
        else:
            assert row["status"] != "imported"


def test_cli_writes_report(tmp_path: Path) -> None:
    out_dir = tmp_path / "vision_cli"
    completed = subprocess.run(
        [
            sys.executable,
            str(VISION_SMOKE),
            "--out-dir",
            str(out_dir),
            "--max-order",
            "2",
            "--max-tasks",
            "10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"]
    assert payload["summary"]["imported_count"] >= 1
    assert (out_dir / "vision_smoke_report.json").exists()
    assert (out_dir / "vision_smoke_report.md").exists()
    assert (out_dir / "oracle_probe.json").exists()

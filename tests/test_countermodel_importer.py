import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    CountermodelImportConfig,
    CountermodelImportResult,
    CountermodelImportRunResult,
    KernelOracle,
    LawbookStore,
    import_finite_countermodel_results,
)


ROOT = Path(__file__).resolve().parents[1]


def _valid_row(**updates) -> dict:
    row = {
        "task_id": "task1",
        "source": "x = x",
        "target": "x = y",
        "source_idx": 1,
        "target_idx": 2,
        "route": "finite_countermodel",
        "status": "finite_countermodel_found",
        "terminal_form": "FINITE_COUNTERMODEL",
        "verification_status": "FINITE_VERIFIED",
        "certificate_id": "cert1",
        "countermodel": {
            "order": 2,
            "table": [[0, 0], [1, 1]],
            "table_hash": "hash",
            "family": "left_projection",
        },
        "witness": {
            "assignment": {"x": 0, "y": 1},
            "target_left_value": 0,
            "target_right_value": 1,
        },
    }
    row.update(updates)
    return row


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_dataclass_roundtrip() -> None:
    config = CountermodelImportConfig("results.jsonl", "store.sqlite")
    assert CountermodelImportConfig.from_dict(config.to_dict()) == config
    item = CountermodelImportResult(
        source="A",
        target="B",
        source_idx=1,
        target_idx=2,
        task_id="task",
        certificate_id="cert",
        imported=True,
        status="imported",
        reason=None,
        lawbook_claim_id="claim",
        terminal_form="FINITE_COUNTERMODEL",
        verification_status="REFUTED",
        warnings=["warn"],
    )
    assert CountermodelImportResult.from_dict(item.to_dict()) == item
    run = CountermodelImportRunResult([item], {"row_count": 1}, config.to_dict(), "now")
    assert CountermodelImportRunResult.from_dict(run.to_dict()) == run


def test_skips_non_verified_rows(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    _write_jsonl(results, [_valid_row(status="no_countermodel_found", terminal_form=None, verification_status="NOT_VERIFIED")])
    run = import_finite_countermodel_results(CountermodelImportConfig(str(results), str(tmp_path / "store.sqlite")))
    assert run.results[0].status == "skipped_non_verified"
    assert run.summary["imported_count"] == 0


def test_skips_missing_countermodel_or_witness(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    _write_jsonl(results, [_valid_row(countermodel=None), _valid_row(witness=None)])
    run = import_finite_countermodel_results(CountermodelImportConfig(str(results), str(tmp_path / "store.sqlite")))
    assert [item.status for item in run.results] == ["skipped_missing_evidence", "skipped_missing_evidence"]


def test_imports_valid_countermodel_and_oracle_answers(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    store_path = tmp_path / "store.sqlite"
    _write_jsonl(results, [_valid_row()])
    run = import_finite_countermodel_results(CountermodelImportConfig(str(results), str(store_path)))
    assert run.summary["imported_count"] == 1
    store = LawbookStore(store_path)
    try:
        answer = KernelOracle(store).query("x = x", "x = y")
        assert answer.status == "REFUTED"
        assert answer.terminal_form == "FINITE_COUNTERMODEL"
        assert answer.trust_level == "verified_trace"
    finally:
        store.close()


def test_duplicate_import_skipped_by_default_and_allowed_when_configured(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    store_path = tmp_path / "store.sqlite"
    _write_jsonl(results, [_valid_row()])
    import_finite_countermodel_results(CountermodelImportConfig(str(results), str(store_path)))
    second = import_finite_countermodel_results(CountermodelImportConfig(str(results), str(store_path)))
    assert second.results[0].status == "skipped_duplicate"
    allowed = import_finite_countermodel_results(
        CountermodelImportConfig(str(results), str(store_path), allow_duplicate_certificates=True)
    )
    assert allowed.results[0].status == "imported"


def test_revalidation_failure_skipped(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    bad = _valid_row(witness={"assignment": {"x": 0, "y": 0}, "target_left_value": 0, "target_right_value": 0})
    _write_jsonl(results, [bad])
    run = import_finite_countermodel_results(CountermodelImportConfig(str(results), str(tmp_path / "store.sqlite")))
    assert run.results[0].status == "skipped_revalidation_failed"
    assert run.summary["revalidation_failed_count"] == 1


def test_summary_counts_and_out_json(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    out = tmp_path / "summary.json"
    _write_jsonl(results, [_valid_row(), _valid_row(status="parse_failed", terminal_form=None, verification_status="NOT_VERIFIED")])
    run = import_finite_countermodel_results(
        CountermodelImportConfig(str(results), str(tmp_path / "store.sqlite"), out_json=str(out))
    )
    assert run.summary["row_count"] == 2
    assert run.summary["imported_count"] == 1
    assert run.summary["skipped_count"] == 1
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["summary"]["row_count"] == 2


def test_cli_writes_summary_json(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    out = tmp_path / "summary.json"
    _write_jsonl(results, [_valid_row()])
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "import_finite_countermodels.py"),
            "--results-jsonl",
            str(results),
            "--store-path",
            str(tmp_path / "store.sqlite"),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["imported_count"] == 1
    assert out.exists()

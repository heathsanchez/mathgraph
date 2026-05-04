import json
import subprocess
import sys
from pathlib import Path

from mathgraph import Certificate, TerminalForm, Trace, VerificationStatus
from mathgraph.certificate_assimilation import (
    CertificateAssimilationConfig,
    CertificateAssimilationResult,
    CertificateAssimilationSummary,
    _episode_diagnostics,
    _task_outcome_ledger,
    _write_diagnostics_markdown,
    run_certificate_assimilation,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_fixture_assets(tmp_path: Path) -> tuple[Path, Path]:
    traces = tmp_path / "traces.json"
    seed = Trace(
        claim="x = x => x = y",
        source="x = x",
        target="x = y",
        routes_tried=["finite_countermodel"],
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        verification_status=VerificationStatus.REFUTED,
        certificate=Certificate(TerminalForm.FINITE_COUNTERMODEL, "x = x => x = y", payload={"model": {}}),
        metadata={"compiled_route": "finite_countermodel", "source_idx": 0, "target_idx": 1},
    )
    traces.write_text(json.dumps([seed.to_dict()], indent=2, sort_keys=True), encoding="utf-8")
    equations = tmp_path / "equations.txt"
    equations.write_text("x = x\nx = y\nx = z\n", encoding="utf-8")
    return traces, equations


def _config(tmp_path: Path, **overrides) -> CertificateAssimilationConfig:
    traces, equations = _write_fixture_assets(tmp_path)
    data = {
        "traces_json": str(traces),
        "equations_path": str(equations),
        "matrix_path": None,
        "out_dir": str(tmp_path / "episode"),
        "frontier_scan_limit": 20,
        "max_frontier_pairs": 8,
        "top_k_schedule": 8,
        "max_tasks": 8,
        "max_countermodel_order": 2,
        "progress": False,
        "heartbeat_sec": 0.1,
    }
    data.update(overrides)
    return CertificateAssimilationConfig(**data)


def test_dataclass_roundtrip(tmp_path: Path) -> None:
    config = _config(tmp_path)
    assert CertificateAssimilationConfig.from_dict(config.to_dict()) == config
    summary = CertificateAssimilationSummary(
        ok=True,
        real_asset_mode=True,
        synthetic_fallback_used=False,
        primitive_count_before=1,
        primitive_count_after=2,
        new_primitive_count=1,
        derived_count_before=0,
        derived_count_after=0,
        new_derived_count=0,
        outcome_row_count_before=1,
        outcome_row_count_after=2,
        new_outcome_row_count=1,
        frontier_count=1,
        scheduled_count=1,
        task_count=1,
        finite_task_count=1,
        finite_executor_verified_count=1,
        imported_count=1,
        duplicate_count=0,
        revalidation_failed_count=0,
        oracle_probe_count=1,
        oracle_probe_success_count=1,
        residual_count=0,
        elapsed_sec=0.1,
        paths={"x": "y"},
    )
    result = CertificateAssimilationResult(config, summary, [], [], "report.json", "report.md")
    assert CertificateAssimilationResult.from_dict(result.to_dict()).summary.new_primitive_count == 1


def test_fixture_run_succeeds_and_writes_outputs(tmp_path: Path) -> None:
    result = run_certificate_assimilation(_config(tmp_path))
    summary = result.summary
    assert summary.ok
    assert summary.primitive_count_before == 1
    assert summary.imported_count >= 1
    assert summary.new_primitive_count == summary.primitive_count_after - summary.primitive_count_before
    assert summary.new_derived_count == summary.derived_count_after - summary.derived_count_before
    assert summary.new_outcome_row_count == summary.outcome_row_count_after - summary.outcome_row_count_before
    assert Path(summary.paths["summary_json"]).exists()
    assert Path(summary.paths["report_md"]).exists()
    assert Path(summary.paths["new_certificates"]).exists()
    assert Path(summary.paths["residual_queue"]).exists()


def test_new_certificates_only_contains_imported_revalidated_rows(tmp_path: Path) -> None:
    result = run_certificate_assimilation(_config(tmp_path))
    rows = [
        json.loads(line)
        for line in Path(result.summary.paths["new_certificates"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    assert all(row["imported"] for row in rows)
    assert all(row["terminal_form"] == "FINITE_COUNTERMODEL" for row in rows)
    assert result.summary.new_primitive_count == result.summary.imported_count


def test_task_outcome_ledger_counts_match_summary(tmp_path: Path) -> None:
    result = run_certificate_assimilation(_config(tmp_path))
    ledger = [
        json.loads(line)
        for line in Path(result.summary.paths["task_outcome_ledger"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert ledger
    assert result.summary.task_count == len(ledger)
    assert result.summary.verified_count == sum(1 for row in ledger if row["verification_status"] == "FINITE_VERIFIED")
    assert result.summary.imported_count == sum(1 for row in ledger if row["import_status"] == "imported")
    assert result.summary.not_found_count == sum(1 for row in ledger if row["execution_status"] == "no_countermodel_found")
    assert all("terminal_form" in row for row in ledger)
    assert all("countermodel_order" in row for row in ledger)


def test_duplicate_verified_countermodel_recorded_as_duplicate(tmp_path: Path) -> None:
    paths = {
        "task_queue": tmp_path / "task_queue.jsonl",
        "finite_results": tmp_path / "finite_results.jsonl",
        "import_summary": tmp_path / "countermodel_import_summary.json",
    }
    task = {
        "task_id": "task_1",
        "source": "x = x",
        "target": "x = y",
        "source_idx": 0,
        "target_idx": 1,
        "route": "finite_countermodel",
        "task_kind": "finite_countermodel_search",
        "terminal_goal": "FINITE_COUNTERMODEL",
        "priority": 1.0,
    }
    finite = {
        **task,
        "status": "finite_countermodel_found",
        "verification_status": "FINITE_VERIFIED",
        "certificate_id": "cert_1",
        "countermodel": {"order": 2, "table": [[0, 0], [1, 1]], "table_hash": "h", "family": "left_projection"},
        "witness": {"assignment": {"x": 0, "y": 1}},
        "elapsed_sec": 0.01,
    }
    imported = {
        **task,
        "status": "skipped_duplicate",
        "imported": False,
        "certificate_id": "cert_1",
        "reason": "exact primitive pair already exists",
    }
    ledger = _task_outcome_ledger([task], [finite], [imported], paths)
    assert ledger[0]["verification_status"] == "FINITE_VERIFIED"
    assert ledger[0]["duplicate_status"] == "duplicate"
    assert ledger[0]["import_status"] == "skipped_duplicate"
    diagnostics = _episode_diagnostics(ledger)
    assert diagnostics["summary"]["verified_count"] == 1
    assert diagnostics["summary"]["duplicate_count"] == 1
    assert diagnostics["summary"]["imported_count"] == 0
    assert diagnostics["summary"]["residual_count"] == 0
    assert diagnostics["consistency_checks"]["imported_plus_duplicate_plus_residual_equals_task_count"]


def test_residual_queue_preserves_unpromoted_work(tmp_path: Path) -> None:
    traces, equations = _write_fixture_assets(tmp_path)
    equations.write_text("x = x\n", encoding="utf-8")
    result = run_certificate_assimilation(
        CertificateAssimilationConfig(
            traces_json=str(traces),
            equations_path=str(equations),
            matrix_path=None,
            out_dir=str(tmp_path / "residual_episode"),
            max_frontier_pairs=1,
            top_k_schedule=1,
            max_tasks=1,
            max_countermodel_order=1,
            progress=False,
        )
    )
    residual_path = Path(result.summary.paths["residual_queue"])
    assert residual_path.exists()
    assert result.summary.imported_count == 0
    assert "No new primitive certificates were promoted." in result.summary.warnings
    residual_rows = [
        json.loads(line)
        for line in Path(result.summary.paths["residual_queue"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert residual_rows or result.summary.task_count == 0
    obstruction_rows = [
        json.loads(line)
        for line in Path(result.summary.paths["residual_obstruction_candidates"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(obstruction_rows) == result.summary.residual_count


def test_progress_jsonl_contains_stage_events(tmp_path: Path) -> None:
    result = run_certificate_assimilation(_config(tmp_path, progress=False))
    events = [
        json.loads(line)
        for line in Path(result.summary.paths["progress"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(event["event"] == "stage_start" for event in events)
    assert any(event["event"] == "stage_end" for event in events)


def test_diagnostics_report_contains_imported_duplicate_residual_sections(tmp_path: Path) -> None:
    diagnostics = {
        "summary": {
            "imported_count": 1,
            "duplicate_count": 1,
            "residual_count": 1,
            "not_found_count": 1,
            "verification_failed_count": 0,
            "best_yield_route": "finite_countermodel",
        },
        "try_next": [{"task_id": "t", "route": "finite_countermodel", "priority": 0.5, "reason": "no_countermodel_found"}],
    }
    report = tmp_path / "diagnostics.md"
    _write_diagnostics_markdown(diagnostics, report)
    text = report.read_text(encoding="utf-8")
    assert "Episode Summary" in text
    assert "Outcome Ledger" in text
    assert "Imported Certificates" in text
    assert "Duplicate Certificates" in text
    assert "Residual / Obstruction Candidates" in text
    assert "Consistency Checks" in text
    assert "Safety Notes" in text


def test_missing_assets_fail_clearly_unless_synthetic_fallback(tmp_path: Path) -> None:
    missing = CertificateAssimilationConfig(
        traces_json=str(tmp_path / "missing_traces.json"),
        equations_path=str(tmp_path / "missing_equations.txt"),
        matrix_path=None,
        out_dir=str(tmp_path / "missing_episode"),
        progress=False,
    )
    result = run_certificate_assimilation(missing)
    assert not result.summary.ok
    assert result.summary.errors

    fallback = run_certificate_assimilation(
        CertificateAssimilationConfig.from_dict({**missing.to_dict(), "out_dir": str(tmp_path / "fallback"), "allow_synthetic_fallback": True})
    )
    assert fallback.summary.synthetic_fallback_used
    assert fallback.summary.ok


def test_cli_runs_and_writes_summary(tmp_path: Path) -> None:
    traces, equations = _write_fixture_assets(tmp_path)
    out_dir = tmp_path / "cli_episode"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_certificate_assimilation.py"),
            "--traces-json",
            str(traces),
            "--equations-path",
            str(equations),
            "--out-dir",
            str(out_dir),
            "--max-frontier-pairs",
            "8",
            "--top-k-schedule",
            "8",
            "--max-tasks",
            "8",
            "--frontier-scan-limit",
            "20",
            "--max-countermodel-order",
            "2",
            "--quiet",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["ok"]
    assert (out_dir / "certificate_assimilation_summary.json").exists()
    required = [
        "task_outcome_ledger.jsonl",
        "duplicate_certificates.jsonl",
        "residual_obstruction_candidates.jsonl",
        "assimilation_episode_diagnostics.json",
        "assimilation_episode_diagnostics.md",
    ]
    for filename in required:
        assert (out_dir / filename).exists()
    ledger = _read_jsonl(out_dir / "task_outcome_ledger.jsonl")
    duplicates = _read_jsonl(out_dir / "duplicate_certificates.jsonl")
    residuals = _read_jsonl(out_dir / "residual_obstruction_candidates.jsonl")
    new_certs = _read_jsonl(out_dir / "new_certificates.jsonl")
    assert len(ledger) == summary["task_count"]
    assert len(duplicates) == summary["duplicate_count"]
    assert len(residuals) == summary["residual_count"]
    assert len(new_certs) == summary["new_primitive_count"]
    assert summary["imported_count"] + summary["duplicate_count"] + summary["residual_count"] == summary["task_count"]
    assert all(row["duplicate_status"] == "duplicate" and row["import_status"] != "imported" for row in duplicates)
    assert all(row["import_status"] != "imported" for row in residuals)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

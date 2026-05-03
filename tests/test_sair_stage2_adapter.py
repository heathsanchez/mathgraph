import csv
import subprocess
import sys
from pathlib import Path

from adapters.sair_stage2_adapter import (
    import_results,
    import_traces,
    load_result_table,
    load_results_table,
    record_to_trace,
    row_to_trace,
    summarize_results,
    validate_imported_traces,
)
from mathgraph import TerminalForm, VerificationStatus


ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_load_results_table_csv(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    _write_csv(path, [{"source": "x=x", "target": "x=x", "verified_true": "true"}])

    records = load_results_table(path)

    assert records == [{"source": "x=x", "target": "x=x", "verified_true": "true"}]
    assert load_result_table(path) == records


def test_summarize_results_counts_records() -> None:
    records = [
        {"verified_true": "true", "compiled_route": "lean", "promotion_status": "promoted"},
        {"verified_false": "true", "compiled_route": "finite", "promotion_status": "promoted"},
        {"lean_status": "lean_failed", "error_class": "timeout"},
    ]

    summary = summarize_results(records)

    assert summary["row_count"] == 3
    assert summary["verified_total"] == 2
    assert summary["verified_true"] == 1
    assert summary["verified_false"] == 1
    assert summary["failed_total"] == 1
    assert summary["compiled_route_counts"] == {"lean": 1, "finite": 1}
    assert summary["promotion_status_counts"] == {"promoted": 2}
    assert summary["error_class_counts"] == {"timeout": 1}


def test_v19_1_columns_override_legacy_pending_statuses() -> None:
    pd = __import__("pytest").importorskip("pandas")
    frame = pd.DataFrame(
        [
            {
                "source": "x=x",
                "target": "x=x",
                "lean_status": "lean_artifact_generated_pending_run",
                "promotion_status": "python_structural_true_pending_lean",
                "lean_status_v19_1": "lean_verified_true",
                "promotion_status_v19_1": "lean_verified_true_promoted",
                "lean_verified_true_v19_1": True,
                "compiled_route": "legacy_route",
                "compiled_route_v19_1": "routelean_v19_1",
            },
            {
                "source": "x=x",
                "target": "x*x=x",
                "lean_status": "lean_artifact_generated_pending_run",
                "promotion_status": "python_validated_false_pending_lean",
                "lean_status_v19_1": "lean_verified_false",
                "promotion_status_v19_1": "lean_verified_false_promoted",
                "lean_verified_false_v19_1": True,
                "compiled_route": "legacy_route",
                "compiled_route_v19_1": "routelean_v19_1",
            },
        ]
    )

    summary = summarize_results(frame)
    traces = [row_to_trace(row) for row in frame.to_dict(orient="records")]

    assert summary["verified_total"] == 2
    assert summary["verified_true"] == 1
    assert summary["verified_false"] == 1
    assert summary["lean_status_counts"] == {
        "lean_verified_true": 1,
        "lean_verified_false": 1,
    }
    assert summary["promotion_status_counts"] == {
        "lean_verified_true_promoted": 1,
        "lean_verified_false_promoted": 1,
    }
    assert summary["compiled_route_counts"] == {"routelean_v19_1": 2}
    assert [trace.terminal_form for trace in traces] == [
        TerminalForm.VERIFIED_PROOF,
        TerminalForm.FINITE_COUNTERMODEL,
    ]


def test_verified_false_row_becomes_finite_countermodel() -> None:
    trace = row_to_trace(
        {
            "source_equation": "x = x",
            "target_equation": "x * x = x",
            "verified_false": "true",
            "compiled_route": "finite_magma",
            "countermodel": "table=[[0,1],[1,0]]",
        }
    )

    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    assert trace.certificate is not None
    assert trace.certificate.payload["model"]["countermodel"] == "table=[[0,1],[1,0]]"


def test_verified_true_row_becomes_verified_proof() -> None:
    trace = row_to_trace(
        {
            "source": "x * y = y * x",
            "target": "a * b = b * a",
            "lean_verified_true": "true",
            "route_name": "routelean",
            "claim_hash": "abc123",
        }
    )

    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.verification_status == VerificationStatus.VERIFIED
    assert trace.certificate is not None
    assert trace.certificate.payload["proof_id"] == "abc123"


def test_missing_verification_becomes_named_obstruction() -> None:
    trace = row_to_trace({"source": "x=x", "target": "y=y", "lean_status": "candidate"})

    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert trace.verification_status == VerificationStatus.OBSTRUCTED
    assert trace.certificate is None
    assert trace.obstruction is not None


def test_finite_search_failure_never_becomes_proof() -> None:
    trace = row_to_trace(
        {
            "source": "x=x",
            "target": "x*x=x",
            "verification_status": "finite_search_failed",
        }
    )

    assert trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION
    assert not trace.is_verified_proof()


def test_import_and_validate_traces(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    _write_csv(
        path,
        [
            {"source": "x=x", "target": "x=x", "verified_true": "true"},
            {"source": "x=x", "target": "x*x=x", "verified_false": "true"},
        ],
    )

    traces = import_traces(path)
    imported = import_results(path)
    summary = validate_imported_traces(traces)

    assert len(traces) == 2
    assert len(imported["traces"]) == 2
    assert imported["summary"]["row_count"] == 2
    assert summary["total"] == 2
    assert summary["promotable_count"] == 2
    assert summary["malformed_count"] == 0


def test_cli_summary_works_on_tiny_csv(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    _write_csv(path, [{"source": "x=x", "target": "x=x", "verified_true": "true"}])

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "import_sair_stage2_results.py"),
            "--input",
            str(path),
            "--summary-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert '"row_count": 1' in result.stdout

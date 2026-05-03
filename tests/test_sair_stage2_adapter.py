import csv
import json
import sqlite3
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


def test_v19_1_verified_false_promotable_preserves_metadata() -> None:
    trace = row_to_trace(
        {
            "source_idx": "12",
            "target_idx": "34",
            "source_equation": "x = x",
            "target_equation": "x * x = x",
            "claim_hash": "claimabc",
            "compiled_route": "routelean_v19_1",
            "terminal_form": "legacy_pending",
            "lean_status_v19_1": "lean_verified_false",
            "lean_verified_v19_1": "true",
            "lean_verified_false_v19_1": "true",
            "lean_error_class": "",
            "promotion_status_v19_1": "lean_verified_false_promotable",
            "countermodel": "small model",
            "artifact_path": "/external/artifact.lean",
            "certificate_hash": "cert123",
        }
    )

    assert trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert trace.verification_status == VerificationStatus.REFUTED
    model = trace.certificate.payload["model"]
    assert model["source_idx"] == "12"
    assert model["target_idx"] == "34"
    assert model["source_equation"] == "x = x"
    assert model["target_equation"] == "x * x = x"
    assert model["claim_hash"] == "claimabc"
    assert model["compiled_route"] == "routelean_v19_1"
    assert model["original_terminal_form"] == "legacy_pending"
    assert model["lean_status"] == "lean_verified_false"
    assert model["promotion_status"] == "lean_verified_false_promotable"
    assert model["countermodel"] == "small model"
    assert model["record"]["artifact_path"] == "/external/artifact.lean"
    assert model["record"]["certificate_hash"] == "cert123"


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


def test_v19_1_verified_true_promotable_preserves_certificate_metadata() -> None:
    trace = row_to_trace(
        {
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x * y = y * x",
            "target_equation": "a * b = b * a",
            "claim_hash": "claimtrue",
            "compiled_route": "routelean_v19_1",
            "terminal_form": "legacy_pending",
            "lean_status_v19_1": "lean_verified_true",
            "lean_verified_v19_1": "true",
            "lean_verified_true_v19_1": "true",
            "promotion_status_v19_1": "lean_verified_true_promotable",
        }
    )

    assert trace.terminal_form == TerminalForm.VERIFIED_PROOF
    assert trace.verification_status == VerificationStatus.VERIFIED
    payload = trace.certificate.payload
    assert payload["proof_id"] == "claimtrue"
    assert payload["source_idx"] == "1"
    assert payload["target_idx"] == "2"
    assert payload["compiled_route"] == "routelean_v19_1"
    assert payload["original_terminal_form"] == "legacy_pending"
    assert payload["lean_status"] == "lean_verified_true"
    assert payload["promotion_status"] == "lean_verified_true_promotable"


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


def test_terminal_form_without_verification_does_not_promote() -> None:
    trace = row_to_trace(
        {
            "source": "x=x",
            "target": "x=x",
            "terminal_form": "VERIFIED_PROOF",
            "promotion_status": "python_structural_true_pending_lean",
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


def test_cli_exports_requested_temp_artifacts(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    summary_path = tmp_path / "summary.json"
    traces_path = tmp_path / "traces.json"
    ledger_path = tmp_path / "ledger.jsonl"
    certs_path = tmp_path / "certificates.json"
    sqlite_path = tmp_path / "index.sqlite"
    _write_csv(
        path,
        [
            {
                "source": "x=x",
                "target": "x=x",
                "lean_verified_true_v19_1": "true",
                "promotion_status_v19_1": "lean_verified_true_promotable",
            }
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "import_sair_stage2_results.py"),
            "--input",
            str(path),
            "--summary-json",
            str(summary_path),
            "--export-traces-json",
            str(traces_path),
            "--export-ledger-jsonl",
            str(ledger_path),
            "--export-certificates-json",
            str(certs_path),
            "--sqlite-index",
            str(sqlite_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert '"trace_count": 1' in result.stdout
    assert summary_path.exists()
    assert traces_path.exists()
    assert ledger_path.exists()
    assert certs_path.exists()
    assert sqlite_path.exists()

    with sqlite3.connect(sqlite_path) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(traces)").fetchall()]
        count = conn.execute("SELECT count(*) FROM traces").fetchone()[0]

    assert count == 1
    assert columns == [
        "trace_hash",
        "terminal_form",
        "verification_status",
        "source_idx",
        "target_idx",
        "source_equation",
        "target_equation",
        "compiled_route",
        "claim_hash",
        "payload_json",
    ]


def test_cli_out_directory_mode_writes_default_exports(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    out_dir = tmp_path / "exports"
    _write_csv(
        path,
        [
            {
                "source_idx": "1",
                "target_idx": "2",
                "source_equation": "x=x",
                "target_equation": "x=x",
                "claim_hash": "claimtrue",
                "compiled_route": "routelean_v19_1",
                "lean_verified_true_v19_1": "true",
                "promotion_status_v19_1": "lean_verified_true_promotable",
            },
            {
                "source_idx": "3",
                "target_idx": "4",
                "source_equation": "x=x",
                "target_equation": "x*x=x",
                "claim_hash": "claimfalse",
                "compiled_route": "finite_magma",
                "lean_verified_false_v19_1": "true",
                "promotion_status_v19_1": "lean_verified_false_promotable",
            },
            {
                "source_idx": "5",
                "target_idx": "6",
                "source_equation": "x=x",
                "target_equation": "y=y",
                "promotion_status_v19_1": "pending",
            },
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "import_sair_stage2_results.py"),
            "--input",
            str(path),
            "--out",
            str(out_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "traces.json").exists()
    assert (out_dir / "traces.jsonl").exists()
    assert (out_dir / "certificates.json").exists()
    assert (out_dir / "index.sqlite").exists()

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    traces = json.loads((out_dir / "traces.json").read_text(encoding="utf-8"))

    assert summary["row_count"] == 3
    assert summary["verified_true"] == 1
    assert summary["verified_false"] == 1
    assert [trace["terminal_form"] for trace in traces] == [
        "VERIFIED_PROOF",
        "FINITE_COUNTERMODEL",
        "NAMED_OBSTRUCTION",
    ]

    with sqlite3.connect(out_dir / "index.sqlite") as conn:
        rows = conn.execute(
            """
            SELECT terminal_form, verification_status, source_idx, target_idx,
                   source_equation, target_equation, compiled_route, claim_hash
            FROM traces
            ORDER BY source_idx
            """
        ).fetchall()

    assert rows == [
        (
            "VERIFIED_PROOF",
            "VERIFIED",
            "1",
            "2",
            "x=x",
            "x=x",
            "routelean_v19_1",
            "claimtrue",
        ),
        (
            "FINITE_COUNTERMODEL",
            "REFUTED",
            "3",
            "4",
            "x=x",
            "x*x=x",
            "finite_magma",
            "claimfalse",
        ),
        (
            "NAMED_OBSTRUCTION",
            "OBSTRUCTED",
            "5",
            "6",
            "x=x",
            "y=y",
            None,
            None,
        ),
    ]


def test_cli_out_jsonl_preserves_legacy_ledger_mode(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    ledger_path = tmp_path / "legacy.jsonl"
    _write_csv(path, [{"source": "x=x", "target": "x=x", "verified_true": "true"}])

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "import_sair_stage2_results.py"),
            "--input",
            str(path),
            "--out",
            str(ledger_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert ledger_path.exists()
    assert (tmp_path / "summary.json").exists()
    assert not (tmp_path / "traces.json").exists()
    assert not (tmp_path / "certificates.json").exists()
    assert not (tmp_path / "index.sqlite").exists()
    assert len(ledger_path.read_text(encoding="utf-8").strip().splitlines()) == 1

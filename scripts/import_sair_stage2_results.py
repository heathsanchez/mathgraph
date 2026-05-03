#!/usr/bin/env python
"""Import or summarize external SAIR Stage 2 result tables."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.sair_stage2_adapter import (
    import_results,
    load_result_table,
    summarize_results,
)
from mathgraph.artifact_audit import audit_trace_artifacts
from mathgraph.hashing import hash_trace
from mathgraph.ledger import JsonlLedger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--export-traces-json", default=None)
    parser.add_argument("--export-ledger-jsonl", default=None)
    parser.add_argument("--export-certificates-json", default=None)
    parser.add_argument("--sqlite-index", default=None)
    parser.add_argument("--load-artifacts", action="store_true")
    parser.add_argument("--artifact-base", default=None)
    parser.add_argument("--strict-artifact-hashes", action="store_true")
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Output directory for default exports, or a .jsonl path for the "
            "legacy ledger-only behavior."
        ),
    )
    args = parser.parse_args(argv)

    output_paths = _resolve_output_paths(args)

    records = load_result_table(args.input)
    if args.limit is not None:
        records = records[: args.limit]
    summary = summarize_results(records)

    imported = None
    traces = []
    artifact_summary = _empty_artifact_summary(len(records))
    if args.load_artifacts or not args.summary_only:
        imported = import_results(
            args.input,
            limit=args.limit,
            load_artifacts=args.load_artifacts,
            artifact_base=args.artifact_base,
        )
        traces = imported["traces"]
        artifact_summary = audit_trace_artifacts(traces)

    summary_payload = dict(summary)
    summary_payload["artifact_summary"] = artifact_summary
    if output_paths["summary_json"]:
        _write_json(output_paths["summary_json"], summary_payload)

    if args.strict_artifact_hashes and artifact_summary["hash_mismatches"]:
        print(json.dumps(summary_payload, indent=2, sort_keys=True))
        return 1

    if args.summary_only:
        print(json.dumps(summary_payload, indent=2, sort_keys=True))
        return 0

    if imported is None:
        imported = import_results(args.input, limit=args.limit)
        traces = imported["traces"]

    if output_paths["export_traces_json"]:
        _write_json(output_paths["export_traces_json"], [trace.to_dict() for trace in traces])

    ledger_path = output_paths["export_ledger_jsonl"]
    if ledger_path:
        ledger = JsonlLedger(ledger_path)
        for trace in traces:
            ledger.append_trace(trace)

    if output_paths["export_certificates_json"]:
        certificates = [
            trace.certificate.to_dict()
            for trace in traces
            if trace.certificate is not None
        ]
        _write_json(output_paths["export_certificates_json"], certificates)

    if output_paths["sqlite_index"]:
        _write_sqlite_index(output_paths["sqlite_index"], traces)

    payload = {
        "summary": summary,
        "trace_count": len(traces),
        "validation": imported["validation"],
        "artifact_summary": artifact_summary,
        "summary_json": output_paths["summary_json"],
        "export_traces_json": output_paths["export_traces_json"],
        "export_ledger_jsonl": ledger_path,
        "export_certificates_json": output_paths["export_certificates_json"],
        "sqlite_index": output_paths["sqlite_index"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.strict_artifact_hashes and artifact_summary["hash_mismatches"]:
        return 1
    return 0


def _resolve_output_paths(args: argparse.Namespace) -> dict[str, str | None]:
    paths = {
        "summary_json": args.summary_json,
        "export_traces_json": args.export_traces_json,
        "export_ledger_jsonl": args.export_ledger_jsonl,
        "export_certificates_json": args.export_certificates_json,
        "sqlite_index": args.sqlite_index,
    }

    if not args.out:
        return paths

    out = Path(args.out)
    if out.suffix == ".jsonl":
        paths["export_ledger_jsonl"] = paths["export_ledger_jsonl"] or str(out)
        if not args.summary_only:
            paths["summary_json"] = paths["summary_json"] or str(out.with_name("summary.json"))
        return paths

    output_dir = out
    output_dir.mkdir(parents=True, exist_ok=True)
    paths["summary_json"] = paths["summary_json"] or str(output_dir / "summary.json")
    if not args.summary_only:
        paths["export_traces_json"] = paths["export_traces_json"] or str(output_dir / "traces.json")
        paths["export_ledger_jsonl"] = paths["export_ledger_jsonl"] or str(output_dir / "traces.jsonl")
        paths["export_certificates_json"] = paths["export_certificates_json"] or str(
            output_dir / "certificates.json"
        )
        paths["sqlite_index"] = paths["sqlite_index"] or str(output_dir / "index.sqlite")
    return paths


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _empty_artifact_summary(trace_count: int) -> dict[str, Any]:
    return {
        "trace_count": trace_count,
        "traces_with_artifacts": 0,
        "json_artifacts_total": 0,
        "json_artifacts_found": 0,
        "json_artifacts_missing": 0,
        "json_artifacts_hash_applicable": 0,
        "json_artifacts_hash_checked": 0,
        "json_artifacts_hash_match": 0,
        "json_artifacts_hash_mismatch": 0,
        "json_artifacts_hash_not_applicable": 0,
        "lean_artifacts_total": 0,
        "lean_artifacts_found": 0,
        "lean_artifacts_missing": 0,
        "lean_artifacts_hash_applicable": 0,
        "lean_artifacts_hash_checked": 0,
        "lean_artifacts_hash_match": 0,
        "lean_artifacts_hash_mismatch": 0,
        "lean_artifacts_hash_not_applicable": 0,
        "artifact_roles_counts": {},
        "artifact_source_column_counts": {},
        "canonical_json_found": 0,
        "canonical_json_hash_mismatch": 0,
        "canonical_lean_found": 0,
        "canonical_lean_hash_mismatch": 0,
        "executed_lean_found": 0,
        "executed_lean_hash_mismatch": 0,
        "prior_or_input_artifacts_found": 0,
        "prior_or_input_hash_not_applicable": 0,
        "hash_matches": 0,
        "hash_mismatches": 0,
        "countermodels_extracted": 0,
        "countermodels_missing": 0,
        "artifact_errors": [],
    }


def _write_sqlite_index(path: str, traces: list[object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_hash TEXT PRIMARY KEY,
                terminal_form TEXT,
                verification_status TEXT,
                source_idx TEXT,
                target_idx TEXT,
                source_equation TEXT,
                target_equation TEXT,
                compiled_route TEXT,
                claim_hash TEXT,
                payload_json TEXT
            )
            """
        )
        rows = []
        for trace in traces:
            payload = trace.to_dict()
            rows.append(
                (
                    hash_trace(trace),
                    trace.terminal_form.value,
                    trace.verification_status.value,
                    _trace_metadata_value(trace, "source_idx"),
                    _trace_metadata_value(trace, "target_idx"),
                    _trace_metadata_value(trace, "source_equation") or trace.source,
                    _trace_metadata_value(trace, "target_equation") or trace.target,
                    _trace_metadata_value(trace, "compiled_route"),
                    _trace_metadata_value(trace, "claim_hash"),
                    json.dumps(payload, sort_keys=True),
                )
            )
        conn.executemany(
            """
            INSERT OR REPLACE INTO traces (
                trace_hash,
                terminal_form,
                verification_status,
                source_idx,
                target_idx,
                source_equation,
                target_equation,
                compiled_route,
                claim_hash,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def _trace_metadata_value(trace: object, key: str) -> Any:
    metadata = getattr(trace, "metadata", {}) or {}
    if key in metadata:
        return metadata[key]

    certificate = getattr(trace, "certificate", None)
    payload = getattr(certificate, "payload", {}) if certificate is not None else {}
    if key in payload:
        return payload[key]

    model = payload.get("model") if isinstance(payload, dict) else None
    if isinstance(model, dict) and key in model:
        return model[key]

    record = payload.get("record") if isinstance(payload, dict) else None
    if isinstance(record, dict) and key in record:
        return record[key]

    return None


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit helpers for artifact-backed MathGraph traces."""

from __future__ import annotations

from typing import Any, Iterable

from mathgraph.certificates import TerminalForm
from mathgraph.trace import Trace


def audit_trace_artifacts(traces: Iterable[Trace]) -> dict[str, Any]:
    trace_list = list(traces)
    artifact_records: list[dict[str, Any]] = []
    traces_with_artifacts = 0
    countermodels_extracted = 0
    countermodels_missing = 0

    for trace in trace_list:
        artifacts = _trace_artifacts(trace)
        if artifacts:
            traces_with_artifacts += 1
            artifact_records.extend(artifacts)

        if trace.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
            model = trace.certificate.payload.get("model", {}) if trace.certificate else {}
            if model.get("countermodel") is not None:
                countermodels_extracted += 1
            else:
                countermodels_missing += 1

    json_records = [record for record in artifact_records if record.get("kind") == "json"]
    lean_records = [record for record in artifact_records if record.get("kind") == "lean"]
    errors = [record.get("error") for record in artifact_records if record.get("error")]

    return {
        "trace_count": len(trace_list),
        "traces_with_artifacts": traces_with_artifacts,
        "json_artifacts_total": len(json_records),
        "json_artifacts_found": _count_found(json_records),
        "json_artifacts_missing": _count_missing(json_records),
        "json_artifacts_hash_checked": _count_hash_checked(json_records),
        "json_artifacts_hash_mismatch": _count_hash_mismatch(json_records),
        "lean_artifacts_total": len(lean_records),
        "lean_artifacts_found": _count_found(lean_records),
        "lean_artifacts_missing": _count_missing(lean_records),
        "lean_artifacts_hash_checked": _count_hash_checked(lean_records),
        "lean_artifacts_hash_mismatch": _count_hash_mismatch(lean_records),
        "hash_matches": sum(1 for record in artifact_records if record.get("sha256_matches") is True),
        "hash_mismatches": sum(
            1 for record in artifact_records if record.get("sha256_matches") is False
        ),
        "countermodels_extracted": countermodels_extracted,
        "countermodels_missing": countermodels_missing,
        "artifact_errors": errors,
    }


def _trace_artifacts(trace: Trace) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    if trace.certificate is not None:
        payloads.append(trace.certificate.payload)
    if trace.obstruction is not None:
        payloads.append(trace.obstruction.payload)
    payloads.append(trace.metadata)

    records: list[dict[str, Any]] = []
    for payload in payloads:
        artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
        if isinstance(artifacts, dict):
            for value in artifacts.values():
                if isinstance(value, list):
                    records.extend(record for record in value if isinstance(record, dict))
                elif isinstance(value, dict):
                    records.append(value)
    return records


def _count_found(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("exists") is True)


def _count_missing(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("exists") is False)


def _count_hash_checked(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("sha256_matches") is not None)


def _count_hash_mismatch(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("sha256_matches") is False)

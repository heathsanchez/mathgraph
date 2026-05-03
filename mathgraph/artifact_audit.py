"""Audit helpers for artifact-backed MathGraph traces."""

from __future__ import annotations

from collections import Counter
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
    role_counts = Counter(str(record.get("role", "unknown")) for record in artifact_records)
    source_counts = Counter(
        str(record.get("source_column", "unknown")) for record in artifact_records
    )
    canonical_json = [record for record in json_records if record.get("role") == "canonical_json"]
    canonical_lean = [record for record in lean_records if record.get("role") == "canonical_lean"]
    executed_lean = [record for record in lean_records if record.get("role") == "executed_lean"]
    prior_or_input = [
        record
        for record in artifact_records
        if record.get("is_legacy_or_prior") or str(record.get("role", "")).startswith("v19_1_input")
    ]

    return {
        "trace_count": len(trace_list),
        "traces_with_artifacts": traces_with_artifacts,
        "json_artifacts_total": len(json_records),
        "json_artifacts_found": _count_found(json_records),
        "json_artifacts_missing": _count_missing(json_records),
        "json_artifacts_hash_applicable": _count_hash_applicable(json_records),
        "json_artifacts_hash_checked": _count_hash_checked(json_records),
        "json_artifacts_hash_match": _count_hash_match(json_records),
        "json_artifacts_hash_mismatch": _count_hash_mismatch(json_records),
        "json_artifacts_hash_not_applicable": _count_hash_not_applicable(json_records),
        "lean_artifacts_total": len(lean_records),
        "lean_artifacts_found": _count_found(lean_records),
        "lean_artifacts_missing": _count_missing(lean_records),
        "lean_artifacts_hash_applicable": _count_hash_applicable(lean_records),
        "lean_artifacts_hash_checked": _count_hash_checked(lean_records),
        "lean_artifacts_hash_match": _count_hash_match(lean_records),
        "lean_artifacts_hash_mismatch": _count_hash_mismatch(lean_records),
        "lean_artifacts_hash_not_applicable": _count_hash_not_applicable(lean_records),
        "artifact_roles_counts": dict(role_counts),
        "artifact_source_column_counts": dict(source_counts),
        "canonical_json_found": _count_found(canonical_json),
        "canonical_json_hash_mismatch": _count_hash_mismatch(canonical_json),
        "canonical_lean_found": _count_found(canonical_lean),
        "canonical_lean_hash_mismatch": _count_hash_mismatch(canonical_lean),
        "executed_lean_found": _count_found(executed_lean),
        "executed_lean_hash_mismatch": _count_hash_mismatch(executed_lean),
        "prior_or_input_artifacts_found": _count_found(prior_or_input),
        "prior_or_input_hash_not_applicable": _count_hash_not_applicable(prior_or_input),
        "hash_matches": _count_hash_match(artifact_records),
        "hash_mismatches": _count_hash_mismatch(artifact_records),
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
    seen: set[tuple[str, str, str, str | None]] = set()
    for payload in payloads:
        artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
        if isinstance(artifacts, dict):
            for value in artifacts.values():
                if isinstance(value, list):
                    for record in value:
                        if isinstance(record, dict) and _record_key(record) not in seen:
                            seen.add(_record_key(record))
                            records.append(record)
                elif isinstance(value, dict):
                    if _record_key(value) not in seen:
                        seen.add(_record_key(value))
                        records.append(value)
    return records


def _record_key(record: dict[str, Any]) -> tuple[str, str, str, str | None]:
    return (
        str(record.get("kind")),
        str(record.get("role")),
        str(record.get("source_column")),
        record.get("path"),
    )


def _count_found(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("exists") is True)


def _count_missing(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("exists") is False)


def _count_hash_checked(records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for record in records
        if record.get("hash_applicable") is True and record.get("sha256_matches") is not None
    )


def _count_hash_mismatch(records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for record in records
        if record.get("hash_applicable") is True and record.get("sha256_matches") is False
    )


def _count_hash_applicable(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("hash_applicable") is True)


def _count_hash_match(records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for record in records
        if record.get("hash_applicable") is True and record.get("sha256_matches") is True
    )


def _count_hash_not_applicable(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("hash_applicable") is False)

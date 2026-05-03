"""Import verified finite countermodel executor results into LawbookStore."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.certificates import Certificate, TerminalForm, VerificationStatus
from mathgraph.equations import parse_equation
from mathgraph.hashing import sha256_hex
from mathgraph.lawbook import CertificateLawbook
from mathgraph.lawbook_store import LawbookStore
from mathgraph.trace import Trace


IMPORT_WARNINGS = [
    "Only verified finite countermodel results are imported.",
    "Finite search failures are not imported as truth.",
    "Imported countermodels were revalidated by the importer unless disabled.",
]


@dataclass(frozen=True)
class CountermodelImportConfig:
    results_jsonl: str
    store_path: str
    out_json: str | None = None
    max_rows: int | None = None
    revalidate: bool = True
    allow_duplicate_certificates: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "results_jsonl": self.results_jsonl,
            "store_path": self.store_path,
            "out_json": self.out_json,
            "max_rows": self.max_rows,
            "revalidate": self.revalidate,
            "allow_duplicate_certificates": self.allow_duplicate_certificates,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CountermodelImportConfig":
        return cls(
            results_jsonl=str(data["results_jsonl"]),
            store_path=str(data["store_path"]),
            out_json=data.get("out_json"),
            max_rows=_optional_int(data.get("max_rows")),
            revalidate=bool(data.get("revalidate", True)),
            allow_duplicate_certificates=bool(data.get("allow_duplicate_certificates", False)),
        )


@dataclass(frozen=True)
class CountermodelImportResult:
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    task_id: str | None
    certificate_id: str | None
    imported: bool
    status: str
    reason: str | None
    lawbook_claim_id: str | None
    terminal_form: str | None
    verification_status: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "task_id": self.task_id,
            "certificate_id": self.certificate_id,
            "imported": self.imported,
            "status": self.status,
            "reason": self.reason,
            "lawbook_claim_id": self.lawbook_claim_id,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CountermodelImportResult":
        return cls(
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            task_id=data.get("task_id"),
            certificate_id=data.get("certificate_id"),
            imported=bool(data.get("imported", False)),
            status=str(data["status"]),
            reason=data.get("reason"),
            lawbook_claim_id=data.get("lawbook_claim_id"),
            terminal_form=data.get("terminal_form"),
            verification_status=data.get("verification_status"),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


@dataclass(frozen=True)
class CountermodelImportRunResult:
    results: list[CountermodelImportResult]
    summary: dict[str, Any]
    config: dict[str, Any]
    created_ts: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [result.to_dict() for result in self.results],
            "summary": dict(self.summary),
            "config": dict(self.config),
            "created_ts": self.created_ts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CountermodelImportRunResult":
        return cls(
            results=[CountermodelImportResult.from_dict(item) for item in data.get("results", [])],
            summary=dict(data.get("summary", {})),
            config=dict(data.get("config", {})),
            created_ts=str(data.get("created_ts", "")),
        )


def import_finite_countermodel_results(
    config: CountermodelImportConfig | dict[str, Any],
) -> CountermodelImportRunResult:
    config = config if isinstance(config, CountermodelImportConfig) else CountermodelImportConfig.from_dict(config)
    started = time.perf_counter()
    rows = _read_jsonl(config.results_jsonl)
    if config.max_rows is not None:
        rows = rows[: config.max_rows]
    store = LawbookStore(config.store_path)
    results: list[CountermodelImportResult] = []
    try:
        store.init_schema()
        for row in rows:
            results.append(_import_row(row, store, config))
        summary = _summary(results, time.perf_counter() - started, config)
        run = CountermodelImportRunResult(
            results=results,
            summary=summary,
            config=config.to_dict(),
            created_ts=datetime.now(timezone.utc).isoformat(),
        )
        if config.out_json:
            _write_json(run.to_dict(), config.out_json)
        return run
    finally:
        store.close()


def _import_row(
    row: dict[str, Any], store: LawbookStore, config: CountermodelImportConfig
) -> CountermodelImportResult:
    source = str(row.get("source", ""))
    target = str(row.get("target", ""))
    if not _is_verified_countermodel_row(row):
        return _result(row, imported=False, status="skipped_non_verified", reason="row is not FINITE_COUNTERMODEL / FINITE_VERIFIED")
    if not row.get("countermodel") or not row["countermodel"].get("table"):
        return _result(row, imported=False, status="skipped_missing_evidence", reason="missing countermodel table")
    if not row.get("witness") or not row["witness"].get("assignment"):
        return _result(row, imported=False, status="skipped_missing_evidence", reason="missing witness assignment")
    if not config.allow_duplicate_certificates and store.get_by_pair(source, target) is not None:
        return _result(row, imported=False, status="skipped_duplicate", reason="exact primitive pair already exists")
    if config.revalidate:
        ok, reason = _revalidate(row)
        if not ok:
            return _result(row, imported=False, status="skipped_revalidation_failed", reason=reason)
    try:
        trace = _trace_from_row(row, revalidated=config.revalidate)
        store.import_lawbook(CertificateLawbook.from_traces([trace]), replace=False)
        return _result(
            row,
            imported=True,
            status="imported",
            reason=None,
            lawbook_claim_id=trace.claim,
            terminal_form=TerminalForm.FINITE_COUNTERMODEL.value,
            verification_status=VerificationStatus.REFUTED.value,
        )
    except Exception as exc:
        return _result(row, imported=False, status="error", reason=str(exc))


def _is_verified_countermodel_row(row: dict[str, Any]) -> bool:
    return (
        row.get("terminal_form") == "FINITE_COUNTERMODEL"
        and row.get("verification_status") == "FINITE_VERIFIED"
    )


def _revalidate(row: dict[str, Any]) -> tuple[bool, str | None]:
    try:
        source_eq = parse_equation(_normalize_equation(str(row["source"])))
        target_eq = parse_equation(_normalize_equation(str(row["target"])))
        table = row["countermodel"]["table"]
        from adapters.finite_magma_adapter import FiniteMagma

        magma = FiniteMagma.from_table(table, name="import_revalidation")
        if not magma.satisfies(source_eq):
            return False, "source equation does not hold for all assignments"
        witness = row["witness"]
        assignment = {str(key): int(value) for key, value in witness["assignment"].items()}
        lhs = target_eq.lhs.evaluate(assignment, magma.op)
        rhs = target_eq.rhs.evaluate(assignment, magma.op)
        if lhs == rhs:
            return False, "provided witness does not violate target"
        if magma.counterexample_to_equation(target_eq) is None:
            return False, "target has no violating assignment"
        return True, None
    except Exception as exc:
        return False, str(exc)


def _trace_from_row(row: dict[str, Any], revalidated: bool) -> Trace:
    source = str(row["source"])
    target = str(row["target"])
    claim = f"{source} => {target}"
    payload = {
        "model": {
            "countermodel": row["countermodel"],
            "witness": row["witness"],
            "source_idx": row.get("source_idx"),
            "target_idx": row.get("target_idx"),
            "source_equation": source,
            "target_equation": target,
            "compiled_route": row.get("route") or "finite_countermodel",
            "task_id": row.get("task_id"),
            "executor_certificate_id": row.get("certificate_id"),
            "importer_revalidated": revalidated,
            "provenance": "finite_countermodel_executor_v1",
        },
        "countermodel": row["countermodel"],
        "witness": row["witness"],
        "task_id": row.get("task_id"),
        "executor_certificate_id": row.get("certificate_id"),
        "certificate_id": row.get("certificate_id") or _claim_hash(row),
    }
    certificate = Certificate(
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        claim=claim,
        payload=payload,
        verifier="mathgraph.countermodel_importer",
    )
    return Trace(
        claim=claim,
        source=source,
        target=target,
        routes_tried=[row.get("route") or "finite_countermodel"],
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        verification_status=VerificationStatus.REFUTED,
        certificate=certificate,
        metadata={
            "source_idx": row.get("source_idx"),
            "target_idx": row.get("target_idx"),
            "compiled_route": row.get("route") or "finite_countermodel",
            "claim_hash": _claim_hash(row),
            "executor_certificate_id": row.get("certificate_id"),
            "importer_revalidated": revalidated,
            "provenance": "finite_countermodel_executor_v1",
        },
    )


def _result(
    row: dict[str, Any],
    *,
    imported: bool,
    status: str,
    reason: str | None,
    lawbook_claim_id: str | None = None,
    terminal_form: str | None = None,
    verification_status: str | None = None,
) -> CountermodelImportResult:
    return CountermodelImportResult(
        source=str(row.get("source", "")),
        target=str(row.get("target", "")),
        source_idx=_optional_int(row.get("source_idx")),
        target_idx=_optional_int(row.get("target_idx")),
        task_id=row.get("task_id"),
        certificate_id=row.get("certificate_id"),
        imported=imported,
        status=status,
        reason=reason,
        lawbook_claim_id=lawbook_claim_id,
        terminal_form=terminal_form,
        verification_status=verification_status,
        warnings=list(IMPORT_WARNINGS),
    )


def _summary(
    results: list[CountermodelImportResult],
    elapsed: float,
    config: CountermodelImportConfig,
) -> dict[str, Any]:
    return {
        "row_count": len(results),
        "imported_count": sum(1 for result in results if result.imported),
        "skipped_count": sum(1 for result in results if result.status.startswith("skipped")),
        "error_count": sum(1 for result in results if result.status == "error"),
        "duplicate_count": sum(1 for result in results if result.status == "skipped_duplicate"),
        "revalidation_failed_count": sum(1 for result in results if result.status == "skipped_revalidation_failed"),
        "by_status": dict(Counter(result.status for result in results)),
        "elapsed_sec": elapsed,
        "store_path": config.store_path,
        "results_jsonl": config.results_jsonl,
    }


def _claim_hash(row: dict[str, Any]) -> str:
    return sha256_hex(
        {
            "source": row.get("source"),
            "target": row.get("target"),
            "countermodel": row.get("countermodel"),
            "witness": row.get("witness"),
            "executor_certificate_id": row.get("certificate_id"),
        }
    )


def _normalize_equation(source: str) -> str:
    return source.replace("◇", "*").replace("·", "*")


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(payload: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

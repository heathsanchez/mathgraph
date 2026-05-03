"""Finite countermodel executor for queued MathGraph tasks."""

from __future__ import annotations

import json
import random
import time
from collections import Counter
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any, Iterable

from mathgraph.equations import parse_equation
from mathgraph.hashing import sha256_hex


EXECUTOR_WARNINGS = [
    "Finite countermodel results are exact for the checked finite table.",
    "Do not promote into the lawbook unless the certificate import/promoter accepts it.",
    "Finite search failure is not proof.",
]


@dataclass(frozen=True)
class FiniteCountermodelConfig:
    task_queue_jsonl: str
    out_jsonl: str
    max_tasks: int = 100
    max_order: int = 4
    random_tables_per_order: int = 0
    exhaustive_order_limit: int = 3
    include_deterministic_tables: bool = True
    stop_after_first: bool = True
    random_seed: int = 42

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_queue_jsonl": self.task_queue_jsonl,
            "out_jsonl": self.out_jsonl,
            "max_tasks": self.max_tasks,
            "max_order": self.max_order,
            "random_tables_per_order": self.random_tables_per_order,
            "exhaustive_order_limit": self.exhaustive_order_limit,
            "include_deterministic_tables": self.include_deterministic_tables,
            "stop_after_first": self.stop_after_first,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FiniteCountermodelConfig":
        return cls(
            task_queue_jsonl=str(data["task_queue_jsonl"]),
            out_jsonl=str(data["out_jsonl"]),
            max_tasks=int(data.get("max_tasks", 100)),
            max_order=int(data.get("max_order", 4)),
            random_tables_per_order=int(data.get("random_tables_per_order", 0)),
            exhaustive_order_limit=int(data.get("exhaustive_order_limit", 3)),
            include_deterministic_tables=bool(data.get("include_deterministic_tables", True)),
            stop_after_first=bool(data.get("stop_after_first", True)),
            random_seed=int(data.get("random_seed", 42)),
        )


@dataclass(frozen=True)
class FiniteCountermodelResult:
    task_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    route: str
    status: str
    terminal_form: str | None
    verification_status: str
    certificate_id: str | None
    countermodel: dict[str, Any] | None
    witness: dict[str, Any] | None
    tables_tried: int
    elapsed_sec: float
    failure_reason: str | None
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "route": self.route,
            "status": self.status,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "certificate_id": self.certificate_id,
            "countermodel": self.countermodel,
            "witness": self.witness,
            "tables_tried": self.tables_tried,
            "elapsed_sec": self.elapsed_sec,
            "failure_reason": self.failure_reason,
            "warnings": list(self.warnings),
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FiniteCountermodelResult":
        return cls(
            task_id=str(data["task_id"]),
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            route=str(data.get("route", "")),
            status=str(data["status"]),
            terminal_form=data.get("terminal_form"),
            verification_status=str(data.get("verification_status", "NOT_VERIFIED")),
            certificate_id=data.get("certificate_id"),
            countermodel=data.get("countermodel"),
            witness=data.get("witness"),
            tables_tried=int(data.get("tables_tried", 0)),
            elapsed_sec=float(data.get("elapsed_sec", 0.0)),
            failure_reason=data.get("failure_reason"),
            warnings=[str(item) for item in data.get("warnings", [])],
            evidence=dict(data.get("evidence", {})),
        )


@dataclass(frozen=True)
class FiniteCountermodelRunResult:
    results: list[dict[str, Any]]
    summary: dict[str, Any]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": list(self.results),
            "summary": dict(self.summary),
            "outputs": dict(self.outputs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FiniteCountermodelRunResult":
        return cls(
            results=list(data.get("results", [])),
            summary=dict(data.get("summary", {})),
            outputs=dict(data.get("outputs", {})),
        )


def run_finite_countermodel_tasks(
    config: FiniteCountermodelConfig | dict[str, Any],
) -> FiniteCountermodelRunResult:
    config = config if isinstance(config, FiniteCountermodelConfig) else FiniteCountermodelConfig.from_dict(config)
    started = time.perf_counter()
    rows = _read_jsonl(config.task_queue_jsonl)[: config.max_tasks]
    results = [_execute_row(row, config) for row in rows]
    elapsed = time.perf_counter() - started
    _write_jsonl(results, config.out_jsonl)
    summary_path = str(Path(config.out_jsonl).with_name("finite_countermodel_summary.json"))
    summary = _summary(results, elapsed)
    _write_json(summary, summary_path)
    return FiniteCountermodelRunResult(
        results=[result.to_dict() for result in results],
        summary=summary,
        outputs={"jsonl": str(config.out_jsonl), "summary": summary_path},
    )


def _execute_row(row: dict[str, Any], config: FiniteCountermodelConfig) -> FiniteCountermodelResult:
    started = time.perf_counter()
    task_id = str(row.get("task_id") or "")
    source = str(row.get("source", ""))
    target = str(row.get("target", ""))
    route = str(row.get("route", ""))
    if row.get("task_kind") != "finite_countermodel_search":
        return _result(
            row,
            status="skipped_non_countermodel_task",
            verification_status="NOT_VERIFIED",
            elapsed=time.perf_counter() - started,
            failure_reason="task_kind is not finite_countermodel_search",
        )
    try:
        source_eq = parse_equation(_normalize_equation(source))
        target_eq = parse_equation(_normalize_equation(target))
    except Exception as exc:
        return _result(
            row,
            status="parse_failed",
            verification_status="NOT_VERIFIED",
            elapsed=time.perf_counter() - started,
            failure_reason=str(exc),
        )

    tables_tried = 0
    first_found: dict[str, Any] | None = None
    additional_found_count = 0
    for table, family in _candidate_tables(config):
        tables_tried += 1
        from adapters.finite_magma_adapter import FiniteMagma

        magma = FiniteMagma.from_table(table, name=family)
        payload = magma.countermodel_certificate_payload(source_eq, target_eq)
        if payload is None:
            continue
        table_payload = payload["table"]
        table_hash = _table_hash(table_payload)
        witness = {
            "assignment": payload["assignment"],
            "target_left_value": payload["target_lhs"],
            "target_right_value": payload["target_rhs"],
        }
        countermodel = {
            "order": payload["carrier_order"],
            "table": table_payload,
            "table_hash": table_hash,
            "family": family,
        }
        certificate_id = sha256_hex(
            {
                "source": source,
                "target": target,
                "table_hash": table_hash,
                "witness": witness["assignment"],
                "route": route,
                "task_id": task_id,
            }
        )
        found = {
            "certificate_id": certificate_id,
            "countermodel": countermodel,
            "witness": witness,
            "table_invariants": payload["table_invariants"],
        }
        if first_found is None:
            first_found = found
            if config.stop_after_first:
                break
        else:
            additional_found_count += 1
    if first_found is not None:
        return _result(
            row,
            status="finite_countermodel_found",
            terminal_form="FINITE_COUNTERMODEL",
            verification_status="FINITE_VERIFIED",
            certificate_id=first_found["certificate_id"],
            countermodel=first_found["countermodel"],
            witness=first_found["witness"],
            tables_tried=tables_tried,
            elapsed=time.perf_counter() - started,
            evidence={
                "source_equation": str(source_eq),
                "target_equation": str(target_eq),
                "source_satisfied": True,
                "target_violated": True,
                "table_invariants": first_found["table_invariants"],
                "additional_countermodels_found": additional_found_count,
                "stop_after_first": config.stop_after_first,
            },
        )
    return _result(
        row,
        status="no_countermodel_found",
        verification_status="NOT_VERIFIED",
        tables_tried=tables_tried,
        elapsed=time.perf_counter() - started,
        failure_reason="no checked table satisfied source and violated target",
    )


def _candidate_tables(config: FiniteCountermodelConfig) -> Iterable[tuple[list[list[int]], str]]:
    seen: set[str] = set()
    rng = random.Random(config.random_seed)
    for n in range(1, config.max_order + 1):
        if config.include_deterministic_tables:
            for table, family in _deterministic_tables(n):
                key = _table_hash(table)
                if key not in seen:
                    seen.add(key)
                    yield table, family
        if n <= config.exhaustive_order_limit:
            for table in _exhaustive_tables(n):
                key = _table_hash(table)
                if key not in seen:
                    seen.add(key)
                    yield table, f"exhaustive_order_{n}"
        for index in range(config.random_tables_per_order):
            table = [[rng.randrange(n) for _ in range(n)] for _ in range(n)]
            key = _table_hash(table)
            if key not in seen:
                seen.add(key)
                yield table, f"random_order_{n}_{index}"


def _deterministic_tables(n: int) -> Iterable[tuple[list[list[int]], str]]:
    yield [[a for _b in range(n)] for a in range(n)], "left_projection"
    yield [[b for b in range(n)] for _a in range(n)], "right_projection"
    for c in range(n):
        yield [[c for _b in range(n)] for _a in range(n)], f"constant_{c}"
    yield [[(a + b) % n for b in range(n)] for a in range(n)], "add_mod_n"
    yield [[(a - b) % n for b in range(n)] for a in range(n)], "sub_mod_n"
    yield [[(b - a) % n for b in range(n)] for a in range(n)], "rsub_mod_n"
    yield [[min(a, b) for b in range(n)] for a in range(n)], "min"
    yield [[max(a, b) for b in range(n)] for a in range(n)], "max"
    if n == 2:
        yield [[a ^ b for b in range(n)] for a in range(n)], "xor_mod_2"
    if n >= 2:
        yield [[a if a != 0 else b for b in range(n)] for a in range(n)], "first_nonzero"
        yield [[b if b != 0 else a for b in range(n)] for a in range(n)], "second_nonzero"
    for c in range(n):
        yield [[c if a == c else a for _b in range(n)] for a in range(n)], f"left_absorb_{c}"
        yield [[c if b == c else b for b in range(n)] for _a in range(n)], f"right_absorb_{c}"


def _exhaustive_tables(n: int) -> Iterable[list[list[int]]]:
    for values in product(range(n), repeat=n * n):
        yield [list(values[i * n : (i + 1) * n]) for i in range(n)]


def _result(
    row: dict[str, Any],
    *,
    status: str,
    verification_status: str,
    terminal_form: str | None = None,
    certificate_id: str | None = None,
    countermodel: dict[str, Any] | None = None,
    witness: dict[str, Any] | None = None,
    tables_tried: int = 0,
    elapsed: float = 0.0,
    failure_reason: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> FiniteCountermodelResult:
    return FiniteCountermodelResult(
        task_id=str(row.get("task_id") or ""),
        source=str(row.get("source", "")),
        target=str(row.get("target", "")),
        source_idx=_optional_int(row.get("source_idx")),
        target_idx=_optional_int(row.get("target_idx")),
        route=str(row.get("route", "")),
        status=status,
        terminal_form=terminal_form,
        verification_status=verification_status,
        certificate_id=certificate_id,
        countermodel=countermodel,
        witness=witness,
        tables_tried=tables_tried,
        elapsed_sec=elapsed,
        failure_reason=failure_reason,
        warnings=list(EXECUTOR_WARNINGS),
        evidence={"task_queue_row": _compact_row(row), **(evidence or {})},
    )


def _summary(results: list[FiniteCountermodelResult], elapsed: float) -> dict[str, Any]:
    return {
        "result_count": len(results),
        "executed_count": sum(1 for item in results if item.status not in {"skipped_non_countermodel_task"}),
        "skipped_count": sum(1 for item in results if item.status == "skipped_non_countermodel_task"),
        "found_count": sum(1 for item in results if item.status == "finite_countermodel_found"),
        "not_found_count": sum(1 for item in results if item.status == "no_countermodel_found"),
        "parse_failed_count": sum(1 for item in results if item.status == "parse_failed"),
        "error_count": sum(1 for item in results if item.status == "error"),
        "by_status": dict(Counter(item.status for item in results)),
        "by_route": dict(Counter(item.route for item in results if item.route)),
        "by_order": dict(Counter(str(item.countermodel["order"]) for item in results if item.countermodel)),
        "total_tables_tried": sum(item.tables_tried for item in results),
        "elapsed_sec": elapsed,
        "warnings": list(EXECUTOR_WARNINGS),
    }


def _normalize_equation(source: str) -> str:
    return source.replace("◇", "*").replace("·", "*")


def _table_hash(table: Any) -> str:
    return sha256_hex(table)


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = ["task_id", "source", "target", "source_idx", "target_idx", "route", "task_kind", "priority"]
    return {key: row.get(key) for key in keys if key in row}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(results: list[FiniteCountermodelResult], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result.to_dict(), sort_keys=True) + "\n")


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

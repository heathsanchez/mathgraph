"""SQLite-backed persistent memory for verified MathGraph lawbook traces."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mathgraph.lawbook import CertificateLawbook
from mathgraph.trace import Trace


@dataclass(frozen=True)
class LawbookStoreStats:
    trace_count: int
    claim_count: int
    certificate_count: int
    pair_count: int
    source_count: int
    target_count: int
    route_counts: dict[str, int]
    terminal_form_counts: dict[str, int]
    verification_status_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_count": self.trace_count,
            "claim_count": self.claim_count,
            "certificate_count": self.certificate_count,
            "pair_count": self.pair_count,
            "source_count": self.source_count,
            "target_count": self.target_count,
            "route_counts": dict(self.route_counts),
            "terminal_form_counts": dict(self.terminal_form_counts),
            "verification_status_counts": dict(self.verification_status_counts),
        }


class LawbookStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim TEXT NOT NULL,
                claim_hash TEXT,
                source TEXT,
                target TEXT,
                source_idx TEXT,
                target_idx TEXT,
                compiled_route TEXT,
                terminal_form TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                promotion_status TEXT,
                lean_status TEXT,
                certificate_id TEXT,
                certificate_payload_keys_json TEXT NOT NULL,
                metadata_keys_json TEXT NOT NULL,
                trace_json TEXT NOT NULL,
                certificate_json TEXT,
                metadata_json TEXT NOT NULL,
                created TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_traces_claim ON traces(claim);
            CREATE INDEX IF NOT EXISTS idx_traces_claim_hash ON traces(claim_hash);
            CREATE INDEX IF NOT EXISTS idx_traces_source ON traces(source);
            CREATE INDEX IF NOT EXISTS idx_traces_target ON traces(target);
            CREATE INDEX IF NOT EXISTS idx_traces_pair ON traces(source, target);
            CREATE INDEX IF NOT EXISTS idx_traces_idx_pair ON traces(source_idx, target_idx);
            CREATE INDEX IF NOT EXISTS idx_traces_source_idx ON traces(source_idx);
            CREATE INDEX IF NOT EXISTS idx_traces_target_idx ON traces(target_idx);
            CREATE INDEX IF NOT EXISTS idx_traces_route ON traces(compiled_route);
            CREATE INDEX IF NOT EXISTS idx_traces_terminal ON traces(terminal_form);
            CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(verification_status);
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def import_traces_json(self, path: str | Path, replace: bool = False) -> LawbookStoreStats:
        return self.import_lawbook(CertificateLawbook.from_json(path), replace=replace)

    def import_lawbook(self, lawbook: CertificateLawbook, replace: bool = False) -> LawbookStoreStats:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM traces")
        rows = [_trace_row(trace) for trace in lawbook.traces]
        self.conn.executemany(
            """
            INSERT INTO traces (
                claim, claim_hash, source, target, source_idx, target_idx,
                compiled_route, terminal_form, verification_status, promotion_status,
                lean_status, certificate_id, certificate_payload_keys_json,
                metadata_keys_json, trace_json, certificate_json, metadata_json, created
            ) VALUES (
                :claim, :claim_hash, :source, :target, :source_idx, :target_idx,
                :compiled_route, :terminal_form, :verification_status, :promotion_status,
                :lean_status, :certificate_id, :certificate_payload_keys_json,
                :metadata_keys_json, :trace_json, :certificate_json, :metadata_json, :created
            )
            """,
            rows,
        )
        self.conn.commit()
        return self.stats()

    def stats(self) -> LawbookStoreStats:
        self.init_schema()
        rows = [dict(row) for row in self.conn.execute("SELECT * FROM traces")]
        return LawbookStoreStats(
            trace_count=len(rows),
            claim_count=len({row["claim"] for row in rows}),
            certificate_count=sum(1 for row in rows if row["certificate_json"]),
            pair_count=len({(row["source"], row["target"]) for row in rows}),
            source_count=len({row["source"] for row in rows if row["source"] is not None}),
            target_count=len({row["target"] for row in rows if row["target"] is not None}),
            route_counts=dict(Counter(row["compiled_route"] for row in rows if row["compiled_route"])),
            terminal_form_counts=dict(Counter(row["terminal_form"] for row in rows)),
            verification_status_counts=dict(Counter(row["verification_status"] for row in rows)),
        )

    def get_by_claim(self, claim: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM traces WHERE claim = ? OR claim_hash = ? ORDER BY id LIMIT 1",
            (claim, claim),
        ).fetchone()
        return _row_to_record(row) if row else None

    def get_by_pair(self, source: str, target: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM traces
            WHERE (source = ? AND target = ?) OR (source_idx = ? AND target_idx = ?)
            ORDER BY id LIMIT 1
            """,
            (str(source), str(target), str(source), str(target)),
        ).fetchone()
        return _row_to_record(row) if row else None

    def find_by_source(self, source: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("source = ? OR source_idx = ?", (str(source), str(source)), limit)

    def find_by_target(self, target: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("target = ? OR target_idx = ?", (str(target), str(target)), limit)

    def find_by_route(self, route: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("compiled_route = ?", (route,), limit)

    def find_by_terminal_form(self, terminal_form: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("terminal_form = ?", (terminal_form,), limit)

    def explain_claim(self, claim: str) -> dict[str, Any]:
        return self.get_by_claim(claim) or _missing_record(claim=claim)

    def explain_pair(self, source: str, target: str) -> dict[str, Any]:
        return self.get_by_pair(source, target) or _missing_record(source=source, target=target)

    def _find(self, where: str, params: tuple[Any, ...], limit: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"SELECT * FROM traces WHERE {where} ORDER BY id LIMIT ?",
            (*params, int(limit)),
        ).fetchall()
        return [_row_to_record(row) for row in rows]


def _trace_row(trace: Trace) -> dict[str, Any]:
    metadata = dict(trace.metadata or {})
    cert = trace.certificate.to_dict() if trace.certificate else None
    payload = trace.certificate.payload if trace.certificate else {}
    return {
        "claim": trace.claim,
        "claim_hash": _trace_value(trace, "claim_hash"),
        "source": trace.source or _trace_value(trace, "source_equation"),
        "target": trace.target or _trace_value(trace, "target_equation"),
        "source_idx": _trace_value(trace, "source_idx"),
        "target_idx": _trace_value(trace, "target_idx"),
        "compiled_route": _trace_value(trace, "compiled_route") or (trace.routes_tried[0] if trace.routes_tried else None),
        "terminal_form": trace.terminal_form.value,
        "verification_status": trace.verification_status.value,
        "promotion_status": _trace_value(trace, "promotion_status"),
        "lean_status": _trace_value(trace, "lean_status"),
        "certificate_id": str(payload.get("proof_id") or payload.get("certificate_id") or "") or None,
        "certificate_payload_keys_json": json.dumps(sorted(payload.keys()), sort_keys=True),
        "metadata_keys_json": json.dumps(sorted(metadata.keys()), sort_keys=True),
        "trace_json": json.dumps(trace.to_dict(), sort_keys=True),
        "certificate_json": json.dumps(cert, sort_keys=True) if cert else None,
        "metadata_json": json.dumps(metadata, sort_keys=True),
        "created": trace.created,
    }


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        "status": "hit",
        "claim": data["claim"],
        "claim_hash": data["claim_hash"],
        "source": data["source"],
        "target": data["target"],
        "source_idx": data["source_idx"],
        "target_idx": data["target_idx"],
        "route": data["compiled_route"],
        "compiled_route": data["compiled_route"],
        "terminal_form": data["terminal_form"],
        "verification_status": data["verification_status"],
        "promotion_status": data["promotion_status"],
        "lean_status": data["lean_status"],
        "certificate_id": data["certificate_id"],
        "certificate_payload_keys": json.loads(data["certificate_payload_keys_json"]),
        "metadata_keys": json.loads(data["metadata_keys_json"]),
        "created": data["created"],
        "trace": json.loads(data["trace_json"]),
        "certificate": json.loads(data["certificate_json"]) if data["certificate_json"] else None,
        "metadata": json.loads(data["metadata_json"]),
        "explanation": "Exact verified lawbook trace found.",
    }


def _missing_record(
    claim: str | None = None,
    source: str | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "missing",
        "claim": claim,
        "source": source,
        "target": target,
        "route": None,
        "terminal_form": "NAMED_OBSTRUCTION",
        "verification_status": "UNKNOWN",
        "explanation": "No exact verified lawbook trace found.",
    }


def _trace_value(trace: Trace, key: str) -> str | None:
    for payload in _payloads(trace):
        value = _nested_value(payload, key)
        if value is not None:
            return str(value)
    return None


def _payloads(trace: Trace) -> list[dict[str, Any]]:
    payloads = [trace.metadata]
    if trace.certificate is not None:
        payloads.append(trace.certificate.payload)
    if trace.obstruction is not None:
        payloads.append(trace.obstruction.payload)
    return [payload for payload in payloads if isinstance(payload, dict)]


def _nested_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload and payload[key] not in (None, ""):
        return payload[key]
    for nested_key in ("model", "record"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict) and nested.get(key) not in (None, ""):
            return nested.get(key)
    return None

"""In-memory corpus helpers for verified MathGraph traces."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from mathgraph.certificates import TerminalForm, VerificationStatus
from mathgraph.hashing import hash_trace
from mathgraph.ledger import JsonlLedger
from mathgraph.merkle import merkle_root
from mathgraph.trace import Trace


class CertificateCorpus:
    """Small replay/query layer for imported terminal traces.

    The corpus is intentionally in-memory. It supports quick inspection of
    imported certificates without becoming a database or verification authority.
    """

    def __init__(self) -> None:
        self.traces: list[Trace] = []

    @classmethod
    def from_traces(cls, traces: Iterable[Trace | dict[str, Any]]) -> "CertificateCorpus":
        corpus = cls()
        corpus.add_traces(traces)
        return corpus

    @classmethod
    def from_json(cls, path: str | Path) -> "CertificateCorpus":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            traces = data.get("traces", data.get("items", []))
        else:
            traces = data
        if not isinstance(traces, list):
            raise ValueError("corpus JSON must contain a list of traces")
        return cls.from_traces(traces)

    @classmethod
    def from_jsonl_ledger(cls, path: str | Path) -> "CertificateCorpus":
        return cls.from_traces(JsonlLedger(path).iter_traces())

    def add_trace(self, trace: Trace | dict[str, Any]) -> Trace:
        normalized = _coerce_trace(trace)
        self.traces.append(normalized)
        return normalized

    def add_traces(self, traces: Iterable[Trace | dict[str, Any]]) -> None:
        for trace in traces:
            self.add_trace(trace)

    def to_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [trace.to_dict() for trace in self.traces]
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def summary(self) -> dict[str, Any]:
        audit = self.audit_hashes()
        return {
            "trace_count": len(self.traces),
            "terminal_form_counts": self.terminal_form_counts(),
            "verification_status_counts": self.verification_status_counts(),
            "route_counts": self.route_counts(),
            "duplicate_hash_count": audit["duplicate_count"],
            "merkle_root": audit["merkle_root"],
        }

    def terminal_form_counts(self) -> dict[str, int]:
        return dict(Counter(trace.terminal_form.value for trace in self.traces))

    def verification_status_counts(self) -> dict[str, int]:
        return dict(Counter(trace.verification_status.value for trace in self.traces))

    def route_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for trace in self.traces:
            route = _trace_value(trace, "compiled_route")
            if route is not None:
                counts[str(route)] += 1
                continue
            for tried in trace.routes_tried:
                counts[str(tried)] += 1
        return dict(counts)

    def query(
        self,
        *,
        terminal_form: TerminalForm | str | None = None,
        verification_status: VerificationStatus | str | None = None,
        compiled_route: str | None = None,
        source_idx: str | int | None = None,
        target_idx: str | int | None = None,
        claim_hash: str | None = None,
        limit: int | None = None,
    ) -> list[Trace]:
        results: list[Trace] = []
        terminal_value = _enum_value(terminal_form)
        status_value = _enum_value(verification_status)

        for trace in self.traces:
            if terminal_value is not None and trace.terminal_form.value != terminal_value:
                continue
            if status_value is not None and trace.verification_status.value != status_value:
                continue
            if compiled_route is not None and _trace_value(trace, "compiled_route") != compiled_route:
                continue
            if source_idx is not None and _trace_value(trace, "source_idx") != str(source_idx):
                continue
            if target_idx is not None and _trace_value(trace, "target_idx") != str(target_idx):
                continue
            if claim_hash is not None and _trace_value(trace, "claim_hash") != claim_hash:
                continue
            results.append(trace)
            if limit is not None and len(results) >= limit:
                break
        return results

    def get_by_claim_hash(self, claim_hash: str) -> list[Trace]:
        return self.query(claim_hash=claim_hash)

    def get_by_pair(self, source_idx: str | int, target_idx: str | int) -> list[Trace]:
        return self.query(source_idx=source_idx, target_idx=target_idx)

    def audit_hashes(self) -> dict[str, Any]:
        hashes: list[str] = []
        skipped = 0
        for trace in self.traces:
            try:
                hashes.append(hash_trace(trace))
            except (TypeError, ValueError):
                skipped += 1

        counts = Counter(hashes)
        duplicate_hashes = {value: count for value, count in counts.items() if count > 1}
        duplicate_count = sum(count - 1 for count in duplicate_hashes.values())
        return {
            "trace_count": len(self.traces),
            "hash_count": len(hashes),
            "skipped_count": skipped,
            "duplicate_count": duplicate_count,
            "duplicate_hashes": duplicate_hashes,
            "trace_hashes": hashes,
            "merkle_root": merkle_root(hashes),
        }


def _coerce_trace(trace: Trace | dict[str, Any]) -> Trace:
    if isinstance(trace, Trace):
        return trace
    if not isinstance(trace, dict):
        raise TypeError("corpus traces must be Trace objects or dictionaries")
    if "trace" in trace and isinstance(trace["trace"], dict):
        return Trace.from_dict(trace["trace"])
    return Trace.from_dict(trace)


def _enum_value(value: TerminalForm | VerificationStatus | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (TerminalForm, VerificationStatus)):
        return value.value
    return str(value)


def _trace_value(trace: Trace, key: str) -> str | None:
    value = _nested_value(trace.metadata, key)
    if value is not None:
        return str(value)

    if trace.certificate is not None:
        value = _nested_value(trace.certificate.payload, key)
        if value is not None:
            return str(value)

    if trace.obstruction is not None:
        value = _nested_value(trace.obstruction.payload, key)
        if value is not None:
            return str(value)

    return None


def _nested_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload and payload[key] not in (None, ""):
        return payload[key]
    for nested_key in ("model", "record"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict) and key in nested and nested[key] not in (None, ""):
            return nested[key]
    return None

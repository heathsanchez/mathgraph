"""Ephemeral ledger helpers.

Persistent ledgers and run directories are intentionally excluded from git.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from mathgraph.certificates import Certificate
from mathgraph.hashing import hash_trace
from mathgraph.merkle import merkle_root
from mathgraph.trace import Trace


@dataclass
class Ledger:
    entries: list[Certificate] = field(default_factory=list)

    def append(self, certificate: Certificate) -> Certificate:
        self.entries.append(certificate)
        return certificate


class JsonlLedger:
    """Append-only JSONL trace ledger."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_trace(self, trace: Trace) -> Trace:
        entry = {
            "trace": trace.to_dict(),
            "trace_hash": hash_trace(trace),
            "created": trace.created,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            json.dump(entry, handle, sort_keys=True)
            handle.write("\n")
        return trace

    def iter_entries(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    yield {"bad_entry": True, "line_number": line_number, "error": str(exc)}
                    continue
                if "trace" not in entry:
                    entry = {
                        "trace": entry,
                        "trace_hash": hash_trace(entry),
                        "created": entry.get("created"),
                    }
                yield entry

    def iter_traces(self) -> Iterator[Trace]:
        for entry in self.iter_entries():
            if entry.get("bad_entry"):
                continue
            yield Trace.from_dict(entry["trace"])

    def load_all(self) -> list[Trace]:
        return list(self.iter_traces())

    def ledger_hashes(self) -> list[str]:
        return [
            str(entry["trace_hash"])
            for entry in self.iter_entries()
            if not entry.get("bad_entry") and "trace_hash" in entry
        ]

    def merkle_root(self) -> str | None:
        return merkle_root(self.ledger_hashes())

    def audit(self) -> dict[str, object]:
        entries = list(self.iter_entries())
        bad_entries: list[dict[str, object]] = []
        traces: list[Trace] = []
        trace_hashes: list[str] = []

        for index, entry in enumerate(entries):
            if entry.get("bad_entry"):
                bad_entries.append(entry)
                continue
            try:
                trace = Trace.from_dict(entry["trace"])
            except (KeyError, TypeError, ValueError) as exc:
                bad_entries.append({"index": index, "error": str(exc)})
                continue
            expected_hash = hash_trace(trace)
            stored_hash = entry.get("trace_hash")
            if stored_hash != expected_hash:
                bad_entries.append(
                    {
                        "index": index,
                        "error": "trace_hash_mismatch",
                        "stored_hash": stored_hash,
                        "expected_hash": expected_hash,
                    }
                )
                continue
            traces.append(trace)
            trace_hashes.append(expected_hash)

        terminal_counts = Counter(trace.terminal_form.value for trace in traces)
        status_counts = Counter(trace.verification_status.value for trace in traces)
        return {
            "path": str(self.path),
            "entry_count": len(entries),
            "trace_count": len(traces),
            "bad_entries": bad_entries,
            "trace_hashes": trace_hashes,
            "merkle_root": merkle_root(trace_hashes),
            "terminal_form_counts": dict(terminal_counts),
            "verification_status_counts": dict(status_counts),
        }

    def audit_summary(self) -> dict[str, object]:
        summary = self.audit()
        summary["n_traces"] = summary["trace_count"]
        summary["terminal_forms"] = [trace.terminal_form.value for trace in self.load_all()]
        return summary

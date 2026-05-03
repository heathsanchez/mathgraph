"""Ephemeral ledger helpers.

Persistent ledgers and run directories are intentionally excluded from git.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from mathgraph.certificates import Certificate
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
        with self.path.open("a", encoding="utf-8") as handle:
            json.dump(trace.to_dict(), handle, sort_keys=True)
            handle.write("\n")
        return trace

    def iter_traces(self) -> Iterator[Trace]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    yield Trace.from_dict(json.loads(stripped))

    def load_all(self) -> list[Trace]:
        return list(self.iter_traces())

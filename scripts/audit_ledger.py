#!/usr/bin/env python
"""Audit a MathGraph JSONL ledger."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph.replay import replay_ledger


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: audit_ledger.py PATH", file=sys.stderr)
        return 1

    summary = replay_ledger(argv[1])
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

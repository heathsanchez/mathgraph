#!/usr/bin/env python
"""Import or summarize external SAIR Stage 2 result tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.sair_stage2_adapter import (
    import_results,
    load_result_table,
    summarize_results,
)
from mathgraph.ledger import JsonlLedger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    records = load_result_table(args.input)
    if args.limit is not None:
        records = records[: args.limit]
    summary = summarize_results(records)

    if args.summary_only:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    imported = import_results(args.input, limit=args.limit)
    traces = imported["traces"]
    if args.out:
        ledger = JsonlLedger(args.out)
        for trace in traces:
            ledger.append_trace(trace)
    payload = {
        "summary": summary,
        "trace_count": len(traces),
        "validation": imported["validation"],
        "out": args.out,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

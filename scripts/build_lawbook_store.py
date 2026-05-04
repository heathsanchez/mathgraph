#!/usr/bin/env python
"""Build a persistent SQLite LawbookStore from trace JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger(
        "build_lawbook_store",
        log_jsonl=args.progress_jsonl,
        heartbeat_sec=args.heartbeat_sec,
        enabled=args.progress,
        quiet=args.quiet,
    )

    store = LawbookStore(args.out)
    try:
        with progress.stage("init_schema", output=args.out):
            store.init_schema()
        with progress.stage("import_traces_json", input=args.traces_json, replace=args.replace):
            stats = store.import_traces_json(args.traces_json, replace=args.replace)
        payload = stats.to_dict()
        if args.summary_json:
            with progress.stage("write_summary", output=args.summary_json):
                target = Path(args.summary_json)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

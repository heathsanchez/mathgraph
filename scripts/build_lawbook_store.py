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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--summary-json", default=None)
    args = parser.parse_args(argv)

    store = LawbookStore(args.out)
    try:
        store.init_schema()
        stats = store.import_traces_json(args.traces_json, replace=args.replace)
        payload = stats.to_dict()
        if args.summary_json:
            target = Path(args.summary_json)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

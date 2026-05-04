#!/usr/bin/env python
"""Import verified finite countermodel executor results into LawbookStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import CountermodelImportConfig, import_finite_countermodel_results
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-jsonl", required=True)
    parser.add_argument("--store-path", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--no-revalidate", action="store_true")
    parser.add_argument("--allow-duplicate-certificates", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("import_finite_countermodels", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    with progress.stage("import_finite_countermodels", input=args.results_jsonl, store=args.store_path):
        result = import_finite_countermodel_results(
            CountermodelImportConfig(
                results_jsonl=args.results_jsonl,
                store_path=args.store_path,
                out_json=args.out,
                max_rows=args.max_rows,
                revalidate=not args.no_revalidate,
                allow_duplicate_certificates=args.allow_duplicate_certificates,
            )
        )
    if not args.quiet:
        print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

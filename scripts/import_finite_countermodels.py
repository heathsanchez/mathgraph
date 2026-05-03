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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-jsonl", required=True)
    parser.add_argument("--store-path", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--no-revalidate", action="store_true")
    parser.add_argument("--allow-duplicate-certificates", action="store_true")
    args = parser.parse_args(argv)

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
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

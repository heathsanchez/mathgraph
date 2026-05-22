#!/usr/bin/env python3
"""Run Production Lawbook Admission over run or benchmark artifacts."""

from __future__ import annotations

import argparse
import json

from mathgraph.lawbook_promotion import promote_benchmark_outputs, promote_run_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir")
    parser.add_argument("--benchmark-report")
    parser.add_argument("--attempts-csv")
    parser.add_argument("--lawbook-path")
    parser.add_argument("--output-dir")
    strict = parser.add_mutually_exclusive_group()
    strict.add_argument("--strict", dest="strict", action="store_true", default=True)
    strict.add_argument("--non-strict", dest="strict", action="store_false")
    args = parser.parse_args()
    if args.benchmark_report:
        result = promote_benchmark_outputs(
            args.benchmark_report,
            attempts_csv_path=args.attempts_csv,
            lawbook_path=args.lawbook_path,
            output_dir=args.output_dir,
            strict=args.strict,
        )
    elif args.run_dir:
        result = promote_run_artifacts(
            args.run_dir,
            lawbook_path=args.lawbook_path,
            output_dir=args.output_dir,
            strict=args.strict,
        )
    else:
        parser.error("provide --run-dir or --benchmark-report")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


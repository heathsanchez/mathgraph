#!/usr/bin/env python
"""Run the advisory Root Constructor Validation Lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.root_constructor_lab import ROOT_LABELS, run_root_constructor_lab


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, help="Input JSONL pairs.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-pairs-per-root", type=int, default=50)
    parser.add_argument("--null-pairs-per-root", type=int, default=50)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument(
        "--roots",
        default=",".join(ROOT_LABELS),
        help="Comma-separated root labels.",
    )
    args = parser.parse_args(argv)

    try:
        pairs = _read_jsonl(args.pairs)
        roots = [item.strip() for item in args.roots.split(",") if item.strip()]
        report = run_root_constructor_lab(
            pairs,
            args.out_dir,
            root_labels=roots,
            max_pairs_per_root=args.max_pairs_per_root,
            null_pairs_per_root=args.null_pairs_per_root,
            max_countermodel_order=args.max_countermodel_order,
            random_seed=args.random_seed,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1

    summary = report.summary
    print(f"root_count: {summary['root_count']}")
    print(f"attempted_pairs: {summary['attempted_pairs']}")
    print(f"verified_false: {summary['verified_false']}")
    print(f"top_root: {summary['top_root']}")
    print(f"top_root_value_score: {summary['top_root_value_score']}")
    print(f"report_json: {report.outputs['root_constructor_lab_report_json']}")
    print(f"report_md: {report.outputs['root_constructor_lab_report_md']}")
    return 0


def _read_jsonl(path: str) -> list[dict]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Build a candidate frontier JSONL file for MathGraph scheduling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import FrontierBuilderConfig, build_candidate_frontier
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--equations-path", required=True)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--store-path", default=None)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-candidates", type=int, default=1000)
    parser.add_argument("--include-matrix-true", action="store_true")
    parser.add_argument("--no-matrix-false", action="store_true")
    parser.add_argument("--no-skip-known", action="store_true")
    parser.add_argument("--source-limit", type=int, default=None)
    parser.add_argument("--target-limit", type=int, default=None)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("build_candidate_frontier", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    with progress.stage("build_candidate_frontier", output=args.out):
        result = build_candidate_frontier(
            FrontierBuilderConfig(
                equations_path=args.equations_path,
                out_jsonl=args.out,
                store_path=args.store_path,
                matrix_path=args.matrix_path,
                max_candidates=args.max_candidates,
                source_limit=args.source_limit,
                target_limit=args.target_limit,
                include_matrix_false=not args.no_matrix_false,
                include_matrix_true=args.include_matrix_true,
                skip_known=not args.no_skip_known,
                random_seed=args.random_seed,
            )
        )
    if not args.quiet:
        print(json.dumps(result.to_dict()["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

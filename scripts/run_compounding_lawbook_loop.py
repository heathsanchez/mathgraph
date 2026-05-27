#!/usr/bin/env python
"""Run MathGraph Compounding Lawbook Engine v0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.compounding_lawbook_engine import run_compounding_lawbook_engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_compounding_lawbook_smoke")
    parser.add_argument("--equations-path", default=None)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--max-tasks", type=int, default=20)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--fallback-smoke", action="store_true")
    parser.add_argument("--use-real-sair-if-available", action="store_true")
    args = parser.parse_args(argv)
    seeds = tuple(int(part.strip()) for part in args.seeds.split(",") if part.strip())
    report = run_compounding_lawbook_engine(
        args.out_dir,
        equations_path=args.equations_path,
        matrix_path=args.matrix_path,
        seeds=seeds,
        max_tasks=args.max_tasks,
        use_real_sair_if_available=args.use_real_sair_if_available,
        fallback_smoke=args.fallback_smoke,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.advisory_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

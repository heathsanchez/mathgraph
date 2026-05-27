#!/usr/bin/env python
"""Run SAIR Compounding Lawbook Loop v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.sair_compounding_loop import run_sair_compounding_loop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--equations", default=None)
    parser.add_argument("--matrix", default=None)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_sair_compounding_demo")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--sample-size", type=int, default=12)
    args = parser.parse_args(argv)
    report = run_sair_compounding_loop(
        args.out_dir,
        fallback_demo=args.fallback_demo,
        equations_path=args.equations,
        matrix_path=args.matrix,
        seed=args.seed,
        sample_size=args.sample_size,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.advisory_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

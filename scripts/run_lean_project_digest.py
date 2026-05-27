#!/usr/bin/env python
"""Run Lean Project Digest v0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.lean_project_digest import run_lean_project_digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_lean_project_digest_demo")
    args = parser.parse_args(argv)
    report = run_lean_project_digest(args.out_dir, fallback_demo=args.fallback_demo, project_root=args.project_root)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.advisory_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

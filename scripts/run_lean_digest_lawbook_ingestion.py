#!/usr/bin/env python
"""Run Lean Digest Lawbook Ingestion v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.lean_digest_lawbook_ingestion import run_lean_digest_lawbook_ingestion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--digest-dir", default=None)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_lean_digest_lawbook_ingestion_demo")
    args = parser.parse_args(argv)
    result = run_lean_digest_lawbook_ingestion(args.out_dir, digest_dir=args.digest_dir, fallback_demo=args.fallback_demo)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.advisory_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

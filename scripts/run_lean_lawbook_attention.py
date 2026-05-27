#!/usr/bin/env python
"""Run Lean Lawbook Attention v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.lean_lawbook_attention import run_lean_lawbook_attention


def _load_queries(args: argparse.Namespace) -> list[str] | None:
    if args.queries_file:
        return [line.strip() for line in Path(args.queries_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.query:
        return [args.query]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--digest-dir", default=None)
    parser.add_argument("--query", default=None)
    parser.add_argument("--queries-file", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_lean_lawbook_attention_demo")
    args = parser.parse_args(argv)
    result = run_lean_lawbook_attention(
        args.out_dir,
        digest_dir=args.digest_dir,
        queries=_load_queries(args),
        fallback_demo=args.fallback_demo,
        top_k=args.top_k,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.attention_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Query a persistent MathGraph KernelOracle."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
import sys
from pathlib import Path

from mathgraph import KernelOracle, LawbookStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--target", default=None)
    parser.add_argument("--claim", default=None)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--finite-countermodels", action="store_true")
    parser.add_argument("--verified-proofs", action="store_true")
    parser.add_argument("--route", default=None)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)

    store = LawbookStore(args.store)
    try:
        store.init_schema()
        oracle = KernelOracle(store)
        if args.stats:
            payload = oracle.stats()
        elif args.claim:
            payload = oracle.explain_claim(args.claim).to_dict()
        elif args.source is not None and args.target is not None:
            payload = oracle.query(args.source, args.target).to_dict()
        elif args.finite_countermodels:
            payload = [answer.to_dict() for answer in oracle.finite_countermodels(args.limit)]
        elif args.verified_proofs:
            payload = [answer.to_dict() for answer in oracle.verified_proofs(args.limit)]
        elif args.route:
            payload = [answer.to_dict() for answer in oracle.route_examples(args.route, args.limit)]
        else:
            parser.error("provide --stats, --claim, --source/--target, --finite-countermodels, --verified-proofs, or --route")
        print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

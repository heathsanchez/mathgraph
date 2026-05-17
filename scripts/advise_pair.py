#!/usr/bin/env python
"""Produce conservative route advice for a source/target pair."""

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

from mathgraph import CertificateLawbook, advise_pair
from mathgraph.pair_advisor import save_pair_advice


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-routes", type=int, default=5)
    args = parser.parse_args(argv)

    lawbook = CertificateLawbook.from_json(args.traces_json)
    advice = advise_pair(lawbook, args.source, args.target, max_routes=args.max_routes)
    if args.out:
        save_pair_advice(args.out, advice)
    print(json.dumps(advice.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

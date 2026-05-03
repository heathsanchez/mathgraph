#!/usr/bin/env python
"""Build summary files from a MathGraph trace lawbook."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import CertificateLawbook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--traces-json", default=None)
    source.add_argument("--traces-jsonl", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--route-summary", default=None)
    args = parser.parse_args(argv)

    lawbook = (
        CertificateLawbook.from_json(args.traces_json)
        if args.traces_json
        else CertificateLawbook.from_jsonl(args.traces_jsonl)
    )
    payload = lawbook.to_summary_dict()

    if args.out:
        lawbook.save_summary(args.out)
    if args.route_summary:
        lawbook.save_route_summary(args.route_summary)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

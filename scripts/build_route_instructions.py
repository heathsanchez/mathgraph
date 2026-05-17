#!/usr/bin/env python
"""Build route instruction cards from a MathGraph lawbook."""

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

from mathgraph import CertificateLawbook, route_instruction_report
from mathgraph.route_instructor import save_route_instruction_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--sample-limit", type=int, default=5)
    args = parser.parse_args(argv)

    lawbook = CertificateLawbook.from_json(args.traces_json)
    report = route_instruction_report(lawbook, sample_limit=args.sample_limit)
    if args.out:
        save_route_instruction_report(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

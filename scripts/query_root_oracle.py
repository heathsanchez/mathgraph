#!/usr/bin/env python
"""Query a canonical root/reason/obstruction atlas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.root_oracle import RootNodeOracle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas-dir", required=True)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--top-roots", type=int)
    parser.add_argument("--top-reasons", type=int)
    parser.add_argument("--top-obstructions", type=int)
    parser.add_argument("--explain-root")
    args = parser.parse_args(argv)
    oracle = RootNodeOracle.from_json_dir(args.atlas_dir)
    if args.explain_root:
        payload = oracle.explain_root(args.explain_root)
    elif args.top_reasons:
        payload = {"reasons": oracle.top_reasons(args.top_reasons), "advisory_only": True}
    elif args.top_obstructions:
        payload = {"obstructions": oracle.top_obstructions(args.top_obstructions), "advisory_only": True}
    elif args.top_roots:
        payload = {"roots": oracle.top_roots(args.top_roots), "advisory_only": True}
    else:
        payload = oracle.summary()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

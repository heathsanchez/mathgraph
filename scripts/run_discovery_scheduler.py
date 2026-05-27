#!/usr/bin/env python
"""Run DiscoveryScheduler v0 / Taste Policy Ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.discovery_scheduler import run_discovery_scheduler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--candidates-jsonl", default=None)
    parser.add_argument("--mode", choices=("harvest", "frontier", "architectonic", "balanced"), default="balanced")
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_discovery_scheduler_demo")
    args = parser.parse_args(argv)
    result = run_discovery_scheduler(
        args.out_dir,
        candidates_jsonl=args.candidates_jsonl,
        fallback_demo=args.fallback_demo,
        mode=args.mode,
        beta=args.beta,
        top_k=args.top_k,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

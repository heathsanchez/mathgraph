#!/usr/bin/env python
"""Run SAIR Stage 2 conservative breakthrough policy search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.sair_stage2_breakthrough_search import SairStage2BreakthroughSearchConfig, run_sair_stage2_breakthrough_search


def parse_args(argv: Sequence[str] | None = None) -> SairStage2BreakthroughSearchConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seeds", default="")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--train-false", type=int, default=5000)
    parser.add_argument("--heldout-false", type=int, default=5000)
    parser.add_argument("--sample-true", type=int, default=1000)
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--repair-budget", type=int, default=40)
    parser.add_argument("--policy-search-rounds", type=int, default=5)
    parser.add_argument("--strict-admission", action="store_true")
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--fail-if-no-compounding", action="store_true")
    parser.add_argument("--min-total-gain", type=float, default=0.0)
    args = parser.parse_args(argv)
    seeds = [int(item) for item in args.seeds.split(",") if item.strip()] if args.seeds else None
    return SairStage2BreakthroughSearchConfig(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=args.out_dir,
        seeds=seeds,
        seed=args.seed,
        train_false=args.train_false,
        heldout_false=args.heldout_false,
        sample_true=args.sample_true,
        episodes=args.episodes,
        max_n=args.max_n,
        repair_budget=args.repair_budget,
        policy_search_rounds=args.policy_search_rounds,
        strict_admission=args.strict_admission,
        fallback_demo=args.fallback_demo,
        fail_if_no_compounding=args.fail_if_no_compounding,
        min_total_gain=args.min_total_gain,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        summary = run_sair_stage2_breakthrough_search(parse_args(argv))
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"benchmark_passed": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Run the canonical end-to-end MathGraph breakthrough validation pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.end_to_end_breakthrough_validation import BreakthroughValidationConfig, run_breakthrough_validation


def parse_args(argv: Sequence[str] | None = None) -> BreakthroughValidationConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--smoke-real", action="store_true")
    parser.add_argument("--full-real", action="store_true")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--seeds", default="")
    parser.add_argument("--train-pairs", type=int, default=2500)
    parser.add_argument("--heldout-pairs", type=int, default=2500)
    parser.add_argument("--true-pairs", type=int, default=1000)
    parser.add_argument("--repair-budget", type=int, default=40)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--max-proposals-per-basin", type=int, default=3)
    parser.add_argument("--max-pairs-per-proposal", type=int, default=100)
    parser.add_argument("--max-tables-per-proposal", type=int, default=32)
    parser.add_argument("--max-pairs-per-constructor", type=int, default=100)
    parser.add_argument("--max-conditioned-pairs", type=int, default=100)
    parser.add_argument("--max-conditioned-witnesses-per-pair", type=int, default=8)
    parser.add_argument("--max-conditioned-attempts-per-pair", type=int, default=32)
    parser.add_argument("--conditioned-max-steps", type=int, default=5000)
    parser.add_argument("--repair-max-steps", type=int, default=10000)
    parser.add_argument("--repair-max-violations", type=int, default=128)
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--heldout-dir")
    parser.add_argument("--active-discovery-dir")
    parser.add_argument("--certificate-dir")
    args = parser.parse_args(argv)
    seeds = [int(item) for item in args.seeds.split(",") if item.strip()] if args.seeds else None
    return BreakthroughValidationConfig(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=args.out_dir,
        fallback_demo=args.fallback_demo,
        smoke_real=args.smoke_real,
        full_real=args.full_real,
        seeds=seeds,
        seed=args.seed,
        train_pairs=args.train_pairs,
        heldout_pairs=args.heldout_pairs,
        true_pairs=args.true_pairs,
        repair_budget=args.repair_budget,
        max_n=args.max_n,
        max_proposals_per_basin=args.max_proposals_per_basin,
        max_pairs_per_proposal=args.max_pairs_per_proposal,
        max_tables_per_proposal=args.max_tables_per_proposal,
        max_pairs_per_constructor=args.max_pairs_per_constructor,
        max_conditioned_pairs=args.max_conditioned_pairs,
        max_conditioned_witnesses_per_pair=args.max_conditioned_witnesses_per_pair,
        max_conditioned_attempts_per_pair=args.max_conditioned_attempts_per_pair,
        conditioned_max_steps=args.conditioned_max_steps,
        repair_max_steps=args.repair_max_steps,
        repair_max_violations=args.repair_max_violations,
        reuse_existing=args.reuse_existing,
        heldout_dir=args.heldout_dir,
        active_discovery_dir=args.active_discovery_dir,
        certificate_dir=args.certificate_dir,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_breakthrough_validation(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

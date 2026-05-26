#!/usr/bin/env python
"""Run the official SAIR Stage 2 end-to-end evidence pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.sair_stage2_end_to_end import SairStage2EndToEndConfig, run_sair_stage2_end_to_end


def parse_args(argv: Sequence[str] | None = None) -> SairStage2EndToEndConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--train-false", type=int, default=5000)
    parser.add_argument("--heldout-false", type=int, default=5000)
    parser.add_argument("--sample-true", type=int, default=1000)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--repair-budget", type=int, default=40)
    parser.add_argument("--seeds", default="")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--strict-admission", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--smoke-real", action="store_true")
    parser.add_argument("--full-real", action="store_true")
    args = parser.parse_args(argv)
    seeds = [int(item) for item in args.seeds.split(",") if item.strip()] if args.seeds else None
    return SairStage2EndToEndConfig(
        equations=args.equations,
        matrix=args.matrix,
        out_dir=args.out_dir,
        episodes=args.episodes,
        train_false=args.train_false,
        heldout_false=args.heldout_false,
        sample_true=args.sample_true,
        max_n=args.max_n,
        repair_budget=args.repair_budget,
        seeds=seeds,
        seed=args.seed,
        fallback_demo=args.fallback_demo,
        strict_admission=args.strict_admission,
        write_report=args.write_report,
        smoke_real=args.smoke_real,
        full_real=args.full_real,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        summary = run_sair_stage2_end_to_end(parse_args(argv))
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"benchmark_passed": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the canonical MathGraph compounding loop."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.compounding_engine import CompoundingEngineConfig, run_compounding_loop


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_compounding_demo")
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--train-pairs", type=int, default=12)
    parser.add_argument("--eval-pairs", type=int, default=12)
    parser.add_argument("--attempt-budget", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--allow-fallback-demo", action="store_true")
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--max-runtime-sec", type=float)
    parser.add_argument("--reason-atlas-db")
    parser.add_argument("--lawbook-db")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--repeat-runs", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        report = run_compounding_loop(
            CompoundingEngineConfig(
                out_dir=args.out_dir,
                equations=args.equations,
                matrix=args.matrix,
                episodes=args.episodes,
                train_pairs=args.train_pairs,
                eval_pairs=args.eval_pairs,
                attempt_budget=args.attempt_budget,
                seed=args.seed,
                allow_fallback_demo=args.allow_fallback_demo,
                skip_plots=args.skip_plots,
                max_runtime_sec=args.max_runtime_sec,
                reason_atlas_db=args.reason_atlas_db,
                lawbook_db=args.lawbook_db,
            )
        )
    except FileNotFoundError as exc:
        print(json.dumps({"overall": "FAIL", "error": str(exc), "fallback_mode": False}, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    data = report.to_dict()
    best = _best_policy(data)
    print(
        json.dumps(
            {
                "overall": "PASS" if data["advisory_boundary_preserved"] else "FAIL",
                "source_mode": data["source_mode"],
                "fallback_mode": data["fallback_mode"],
                "compounding_signal_detected": data["compounding_signal_detected"],
                "best_policy": best,
                "output_dir": data["output_dir"],
                "artifacts": data["artifacts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _best_policy(report: dict) -> dict:
    policies = [p for ep in report.get("episodes", []) for p in ep.get("policy_results", []) if not p.get("skipped")]
    if not policies:
        return {}
    return max(policies, key=lambda row: (row.get("solved_or_refuted", 0), -row.get("attempts_used", 0)))


if __name__ == "__main__":
    raise SystemExit(main())

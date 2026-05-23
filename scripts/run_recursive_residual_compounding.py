#!/usr/bin/env python3
"""Run recursive residual-mined compounding and compact atlas evaluation."""

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

from mathgraph.recursive_residual_compounding import RecursiveResidualCompoundingEngine, RecursiveResidualConfig


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_recursive_residual_smoke")
    parser.add_argument("--profile", choices=("smoke", "fast", "transfer_fast"), default="smoke")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--seeds", default="")
    parser.add_argument("--generations", type=int, default=2)
    parser.add_argument("--base-magmas", type=int, default=20)
    parser.add_argument("--generic-route-size", type=int, default=4)
    parser.add_argument("--discover-false", type=int, default=12)
    parser.add_argument("--train-false", type=int, default=12)
    parser.add_argument("--heldout-false", type=int, default=12)
    parser.add_argument("--heldout-true", type=int, default=4)
    parser.add_argument("--new-per-generation", type=int, default=2)
    parser.add_argument("--candidate-budget", type=int, default=12)
    parser.add_argument("--allow-fallback-demo", action="store_true")
    parser.add_argument("--include-oracle-reference", action="store_true")
    parser.add_argument("--skip-sqlite", action="store_true")
    parser.add_argument("--skip-plots", action="store_true")
    args = parser.parse_args(argv)
    seeds = tuple(int(x) for x in args.seeds.split(",") if x.strip())
    try:
        report = RecursiveResidualCompoundingEngine(
            RecursiveResidualConfig(
                equations=args.equations,
                matrix=args.matrix,
                out_dir=args.out_dir,
                profile=args.profile,
                seed=args.seed,
                seeds=seeds,
                generations=args.generations,
                base_magmas=args.base_magmas,
                generic_route_size=args.generic_route_size,
                discover_false=args.discover_false,
                train_false=args.train_false,
                heldout_false=args.heldout_false,
                heldout_true=args.heldout_true,
                new_per_generation=args.new_per_generation,
                candidate_budget=args.candidate_budget,
                allow_fallback_demo=args.allow_fallback_demo,
                include_oracle_reference=args.include_oracle_reference,
                skip_sqlite=args.skip_sqlite,
                skip_plots=args.skip_plots,
            )
        ).run()
    except FileNotFoundError as exc:
        print(json.dumps({"overall": "FAIL", "error": str(exc), "fallback_mode": False}, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    data = report.to_dict()
    gates = {row["gate_id"]: row["passed"] for row in data["gate_results"]}
    overall = "PASS" if data["advisory_boundary_preserved"] and data["true_contamination_count"] == 0 else "FAIL"
    print(
        json.dumps(
            {
                "overall": overall,
                "source_mode": data["source_mode"],
                "fallback_mode": data["fallback_mode"],
                "generic_recoveries": data["generic_recoveries"],
                "recursive_full_recoveries": data["recursive_full_recoveries"],
                "best_compact_recoveries": data["best_compact_recoveries"],
                "residual_reduction": data["residual_reduction"],
                "oracle_gap_captured": data["oracle_gap_captured"],
                "true_contamination_count": data["true_contamination_count"],
                "advisory_boundary_preserved": data["advisory_boundary_preserved"],
                "gates": gates,
                "output_dir": str(args.out_dir),
                "artifact_manifest": data["artifact_manifest"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

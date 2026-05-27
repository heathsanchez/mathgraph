#!/usr/bin/env python
"""Run or package the recursive residual-mined transfer test."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.recursive_residual_transfer import (
    SOURCE_BREAKTHROUGH_METRICS,
    build_recursive_transfer_summary,
    fallback_demo_route_evaluations,
    source_breakthrough_route_evaluations,
    write_recursive_transfer_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations", default="/content/equations.txt")
    parser.add_argument("--matrix", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seeds", default="1729,42,137")
    parser.add_argument("--profile", default="transfer_fast")
    parser.add_argument("--strict-advisory-boundary", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument(
        "--package-source-run",
        action="store_true",
        help="package the published source-run metrics/artifact semantics without claiming a fresh rerun",
    )
    args = parser.parse_args(argv)

    equations_path = Path(args.equations)
    matrix_path = Path(args.matrix)
    seeds = tuple(int(x) for x in args.seeds.split(",") if x.strip())

    if args.package_source_run:
        routes = source_breakthrough_route_evaluations()
        summary = build_recursive_transfer_summary(
            routes,
            equations=SOURCE_BREAKTHROUGH_METRICS["equations"],
            matrix_shape=SOURCE_BREAKTHROUGH_METRICS["matrix_shape"],
            true_count=SOURCE_BREAKTHROUGH_METRICS["true_count"],
            false_count=SOURCE_BREAKTHROUGH_METRICS["false_count"],
            profile=args.profile,
            classification="source_breakthrough_artifact_package_advisory_only",
            source_run_metrics=SOURCE_BREAKTHROUGH_METRICS,
        )
    elif not equations_path.exists() or not matrix_path.exists():
        if not args.fallback_demo:
            missing = [str(p) for p in (equations_path, matrix_path) if not p.exists()]
            raise SystemExit(
                "Missing real SAIR/ETP inputs: "
                + ", ".join(missing)
                + ". Use --fallback-demo for a safe infrastructure-only demo."
            )
        routes = fallback_demo_route_evaluations(seeds=seeds)
        summary = build_recursive_transfer_summary(
            routes,
            equations=6,
            matrix_shape=(6, 6),
            true_count=12,
            false_count=24,
            profile=args.profile,
            classification="safe_infrastructure_only",
            source_run_metrics=SOURCE_BREAKTHROUGH_METRICS,
        )
    else:
        # The repo-grade public API below is the reusable transfer/gate/artifact
        # layer.  The full Colab-scale constructor mining loop remains expensive;
        # users can package source artifacts or run fallback infrastructure here.
        raise SystemExit(
            "Real ETP inputs were found, but this CLI intentionally refuses to "
            "pretend a fresh 4694x4694 transfer run occurred without route "
            "evaluation artifacts. Use --package-source-run for the published "
            "source artifact package or call mathgraph.recursive_residual_transfer "
            "APIs with real route evaluations."
        )

    if args.strict_advisory_boundary and not summary.advisory_boundary_ok:
        raise SystemExit("strict advisory boundary failed")

    paths = write_recursive_transfer_artifacts(
        args.out_dir,
        summary=summary,
        route_evaluations=routes,
        write_report=args.write_report,
    )
    print(f"classification: {summary.classification}")
    print(f"gates: {summary.gates_passed}/{summary.gates_total}")
    print(f"true_contamination_max: {summary.true_contamination_max}")
    print(f"advisory_boundary_ok: {summary.advisory_boundary_ok}")
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

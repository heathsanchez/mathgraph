#!/usr/bin/env python
"""Run a full local MathGraph metabolic cycle episode."""

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

from mathgraph.metabolic_cycle import MetabolicCycleConfig, run_metabolic_cycle  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--frontier")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--exhaustive-order-limit", type=int, default=3)
    parser.add_argument("--random-tables-per-order", type=int, default=0)
    parser.add_argument("--synthetic-seed", action="store_true")
    parser.add_argument("--no-derived-closure", action="store_true")
    parser.add_argument("--no-route-learning", action="store_true")
    parser.add_argument("--no-proof-atlas", action="store_true")
    parser.add_argument("--no-residual-analysis", action="store_true")
    parser.add_argument("--no-next-frontier", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    config = MetabolicCycleConfig(
        store_path=args.store,
        frontier_jsonl=args.frontier,
        out_dir=args.out_dir,
        max_tasks=args.max_tasks,
        max_countermodel_order=args.max_countermodel_order,
        exhaustive_order_limit=args.exhaustive_order_limit,
        random_tables_per_order=args.random_tables_per_order,
        allow_synthetic_seed=args.synthetic_seed or not args.frontier,
        run_derived_closure=not args.no_derived_closure,
        run_route_learning=not args.no_route_learning,
        run_proof_atlas=not args.no_proof_atlas,
        run_residual_analysis=not args.no_residual_analysis,
        run_next_frontier=not args.no_next_frontier,
    )
    result = run_metabolic_cycle(config)
    strict_errors = _strict_errors(result) if args.strict else []
    if args.json:
        print(json.dumps(result.summary, indent=2, sort_keys=True))
    else:
        print(
            "\n".join(
                [
                    f"MathGraph metabolic cycle: {result.run_id}",
                    f"Primitive countermodels: {result.summary.get('primitive_countermodels_added', 0)}",
                    f"Primitive proofs: {result.summary.get('primitive_proofs_added', 0)}",
                    f"Derived certificates: {result.summary.get('derived_certificates_added', 0)}",
                    f"Obstructions/residuals: {result.summary.get('obstructions_added', 0)}",
                    f"Better-shaped unknown: {result.summary.get('better_shaped_unknown', False)}",
                    f"Report: {result.artifacts.get('metabolic_cycle_report')}",
                ]
            )
        )
    if strict_errors:
        for error in strict_errors:
            print(f"STRICT: {error}", file=sys.stderr)
        return 2
    return 0


def _strict_errors(result) -> list[str]:
    summary = result.summary
    errors: list[str] = []
    if int(summary.get("contradiction_count", 0)) > 0:
        errors.append("contradictions were detected")
    if not result.artifacts:
        errors.append("no artifacts were written")
    if int(summary.get("authoritative_artifact_count", 0)) < (
        int(summary.get("primitive_countermodels_added", 0))
        + int(summary.get("primitive_proofs_added", 0))
        + int(summary.get("derived_certificates_added", 0))
    ):
        errors.append("authoritative artifact accounting is inconsistent")
    terminal_or_obstruction = (
        int(summary.get("primitive_countermodels_added", 0))
        + int(summary.get("primitive_proofs_added", 0))
        + int(summary.get("derived_certificates_added", 0))
        + int(summary.get("obstructions_added", 0))
    )
    if terminal_or_obstruction <= 0:
        errors.append("synthetic run produced no terminal form or named obstruction")
    if int(summary.get("advisory_artifact_count", 0)) < int(summary.get("proof_motifs_added", 0)) + int(
        summary.get("lemma_candidates_added", 0)
    ):
        errors.append("advisory artifact accounting is inconsistent")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())


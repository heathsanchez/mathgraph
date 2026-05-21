#!/usr/bin/env python
"""Run multi-seed SAIR V-operator H-Tilt calibration/evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.sair_v_operator_evaluation import SAIRVOperatorEvalConfig, evaluate_v_operators_multi_seed
from mathgraph.viability_operators import ViabilityOperatorKind


def _operator_set(value: str) -> tuple[str, ...]:
    if value == "quick":
        return ("null_v", "random_v", "failure_density_v", "rejection_pressure_v", "composite_static_v")
    if value == "all":
        return tuple(kind.value for kind in ViabilityOperatorKind)
    return tuple(part.strip() for part in value.split(",") if part.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations", default="/content/equations.txt")
    parser.add_argument("--matrix", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_sair_v_operator_eval")
    parser.add_argument("--reason-atlas-db", default=None)
    parser.add_argument("--train-pairs", type=int, default=250)
    parser.add_argument("--eval-pairs", type=int, default=250)
    parser.add_argument("--attempt-budget", type=int, default=12)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1729)
    parser.add_argument("--admit-motifs", action="store_true")
    parser.add_argument("--load-existing-atlas", action="store_true")
    parser.add_argument("--operator-set", default="all")
    parser.add_argument("--allow-fallback-demo", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--skip-plots", action="store_true")
    args = parser.parse_args(argv)

    operators = _operator_set("quick" if args.quick else args.operator_set)
    report = evaluate_v_operators_multi_seed(
        SAIRVOperatorEvalConfig(
            equations_path=args.equations,
            matrix_path=args.matrix,
            out_dir=args.out_dir,
            reason_atlas_db=args.reason_atlas_db,
            train_pairs=args.train_pairs,
            eval_pairs=args.eval_pairs,
            attempt_budget=args.attempt_budget,
            episodes=args.episodes,
            seeds=args.seeds,
            seed_start=args.seed_start,
            admit_motifs=args.admit_motifs,
            load_existing_atlas=args.load_existing_atlas,
            operator_set=operators,
            allow_fallback_demo=args.allow_fallback_demo,
            quick=args.quick,
            skip_plots=args.skip_plots,
        )
    )
    summary = {
        "overall": report.overall,
        "source_mode": report.source_mode,
        "seeds": report.seeds,
        "base_yield_mean": report.base_yield_mean,
        "persistent_atlas_yield_mean": report.persistent_atlas_yield_mean,
        "selected_best_operator": report.selected_best_operator,
        "best_htilt_yield_mean": report.best_htilt_yield_mean,
        "delta_vs_persistent_atlas": report.delta_vs_persistent_atlas,
        "residual_compression_vs_persistent_atlas": report.residual_compression_vs_persistent_atlas,
        "attempt_efficiency_gain_vs_persistent_atlas": report.attempt_efficiency_gain_vs_persistent_atlas,
        "oracle_fraction_captured": report.oracle_fraction_captured,
        "htilt_added_signal": report.htilt_added_signal,
        "advisory_boundary_ok": report.advisory_boundary_ok,
        "out_dir": args.out_dir,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report.overall in {"PASS", "PROMISING"} and report.advisory_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

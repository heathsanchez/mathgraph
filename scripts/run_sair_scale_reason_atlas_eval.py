#!/usr/bin/env python3
"""Run persistent SAIR Reason Atlas scale evaluation."""

from __future__ import annotations

import argparse
import json

from mathgraph.sair_scale_evaluation import SAIRScaleEvalConfig, run_sair_scale_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SAIR clean motif scale evaluation with persistent Reason Atlas priors.")
    parser.add_argument("--equations", default="/content/equations.txt")
    parser.add_argument("--matrix", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_sair_scale_reason_atlas_eval")
    parser.add_argument("--reason-atlas-db")
    parser.add_argument("--train-pairs", type=int, default=250)
    parser.add_argument("--eval-pairs", type=int, default=250)
    parser.add_argument("--attempt-budget", type=int, default=12)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--admit-motifs", action="store_true")
    parser.add_argument("--load-existing-atlas", action="store_true")
    parser.add_argument("--repeat-runs", type=int, default=3)
    parser.add_argument("--allow-fallback-demo", action="store_true")
    args = parser.parse_args()
    report = run_sair_scale_evaluation(
        SAIRScaleEvalConfig(
            equations_path=args.equations,
            matrix_path=args.matrix,
            out_dir=args.out_dir,
            reason_atlas_db=args.reason_atlas_db,
            train_pairs=args.train_pairs,
            eval_pairs=args.eval_pairs,
            attempt_budget=args.attempt_budget,
            episodes=args.episodes,
            seed=args.seed,
            admit_motifs=args.admit_motifs,
            load_existing_atlas=args.load_existing_atlas,
            repeat_runs=args.repeat_runs,
            allow_fallback_demo=args.allow_fallback_demo,
        )
    )
    print(json.dumps({
        "overall": report.overall,
        "source_mode": report.source_mode,
        "baseline_yield": report.baseline_yield,
        "clean_motif_yield": report.clean_motif_yield,
        "persistent_atlas_yield": report.persistent_atlas_yield,
        "combined_yield": report.combined_yield,
        "oracle_yield": report.oracle_yield,
        "admitted_reason_atlas_entries": report.admitted_reason_atlas_entries,
        "loaded_reason_atlas_entries": report.loaded_reason_atlas_entries,
        "advisory_boundary_ok": report.advisory_boundary_ok,
        "out_dir": args.out_dir,
    }, indent=2, sort_keys=True))
    return 0 if report.overall in {"PASS", "PROMISING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

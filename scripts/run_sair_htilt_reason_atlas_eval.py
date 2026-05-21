#!/usr/bin/env python
"""Run SAIR held-out evaluation with spectral H-Tilt Reason Atlas priorities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mathgraph.sair_htilt_scale_evaluation import SAIRHTiltScaleEvalConfig, run_sair_htilt_scale_evaluation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations", default="/content/equations.txt")
    parser.add_argument("--matrix", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_sair_htilt_reason_atlas_eval")
    parser.add_argument("--reason-atlas-db", default=None)
    parser.add_argument("--train-pairs", type=int, default=250)
    parser.add_argument("--eval-pairs", type=int, default=250)
    parser.add_argument("--attempt-budget", type=int, default=12)
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--repeat-runs", type=int, default=1)
    parser.add_argument("--admit-motifs", action="store_true")
    parser.add_argument("--load-existing-atlas", action="store_true")
    parser.add_argument("--apply-htilt", action="store_true")
    parser.add_argument("--allow-fallback-demo", action="store_true")
    args = parser.parse_args(argv)

    report = run_sair_htilt_scale_evaluation(
        SAIRHTiltScaleEvalConfig(
            equations_path=args.equations,
            matrix_path=args.matrix,
            out_dir=args.out_dir,
            reason_atlas_db=args.reason_atlas_db,
            train_pairs=args.train_pairs,
            eval_pairs=args.eval_pairs,
            attempt_budget=args.attempt_budget,
            episodes=args.episodes,
            seed=args.seed,
            repeat_runs=args.repeat_runs,
            admit_motifs=args.admit_motifs,
            load_existing_atlas=args.load_existing_atlas,
            apply_htilt=args.apply_htilt,
            allow_fallback_demo=args.allow_fallback_demo,
        )
    )
    summary = {
        "overall": report.overall,
        "source_mode": report.source_mode,
        "baseline_yield": report.baseline_yield,
        "persistent_atlas_yield": report.persistent_atlas_yield,
        "htilt_atlas_yield": report.htilt_atlas_yield,
        "htilt_plus_clean_yield": report.htilt_plus_clean_yield,
        "oracle_yield": report.oracle_yield,
        "delta_yield_vs_base": report.delta_yield_vs_base,
        "delta_yield_vs_persistent_atlas": report.delta_yield_vs_persistent_atlas,
        "delta_attempts_vs_base": report.delta_attempts_vs_base,
        "htilt_entry_count": report.htilt_entry_count,
        "htilt_estimate_converged": report.htilt_estimate_converged,
        "advisory_boundary_ok": report.advisory_boundary_ok,
        "out_dir": str(args.out_dir),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report.overall in {"PASS", "PROMISING"} and report.advisory_boundary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

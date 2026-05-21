#!/usr/bin/env python3
"""Run MathGraph SAIR Breakthrough Loop v1."""

from __future__ import annotations

import argparse
import json

from mathgraph.sair_breakthrough_runner import SAIRBreakthroughRunConfig, run_sair_breakthrough_loop


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SAIR-compatible finite-countermodel breakthrough loop.")
    parser.add_argument("--equations", default="/content/equations.txt")
    parser.add_argument("--matrix", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--attempt-budget", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    result = run_sair_breakthrough_loop(
        SAIRBreakthroughRunConfig(
            equations_path=args.equations,
            matrix_path=args.matrix,
            max_tasks=args.max_tasks,
            episodes=args.episodes,
            attempt_budget=args.attempt_budget,
            seed=args.seed,
            out_dir=args.out_dir,
        )
    )
    summary = result.summary
    keys = [
        "overall",
        "source_mode",
        "equations_loaded",
        "matrix_pairs_sampled",
        "initial_solved_or_refuted_count",
        "final_solved_or_refuted_count",
        "initial_residual_count",
        "final_residual_count",
        "promotion_gate_accepted",
        "promotion_gate_rejected",
        "feedback_event_count",
    ]
    print(json.dumps({key: summary.get(key) for key in keys}, indent=2, sort_keys=True))
    print(f"outputs: {result.output_paths.get('sair_report.md')}")
    return 0 if summary.get("overall") in {"PASS", "PROMISING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run clean SAIR motif mining plus held-out scheduler evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks
from mathgraph.sair_breakthrough_runner import SAIRBreakthroughRunConfig, run_sair_breakthrough_loop
from mathgraph.sair_clean_motif_mining import (
    deduplicate_subsumed_motifs,
    export_clean_motifs,
    mine_clean_constructor_motifs,
    score_clean_motifs,
)
from mathgraph.sair_constructor_bank import attach_preferred_constructors
from mathgraph.sair_motif_hygiene import clean_breakthrough_trace_rows, write_hygiene_audit
from mathgraph.sair_scheduler_evaluation import (
    SAIRSchedulerEvalConfig,
    evaluate_scheduler_policies,
    export_scheduler_eval_report,
    load_eval_tasks,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SAIR clean motif scheduler evaluation.")
    parser.add_argument("--equations", default="/content/equations.txt")
    parser.add_argument("--matrix", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--input-trace-csv")
    parser.add_argument("--out-dir", default="/tmp/mathgraph_sair_clean_motif_scheduler_eval")
    parser.add_argument("--train-pairs", type=int, default=80)
    parser.add_argument("--eval-pairs", type=int, default=80)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--attempt-budget", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--skip-existing-batches", action="store_true")
    parser.add_argument("--run-fresh-batches", action="store_true")
    parser.add_argument("--allow-fallback-demo", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_csv = Path(args.input_trace_csv) if args.input_trace_csv else None
    source_mode = "input_trace"
    run_summary = {}
    if trace_csv is None or args.run_fresh_batches:
        run = run_sair_breakthrough_loop(
            SAIRBreakthroughRunConfig(
                equations_path=args.equations,
                matrix_path=args.matrix,
                max_tasks=args.train_pairs,
                episodes=args.episodes,
                attempt_budget=args.attempt_budget,
                seed=args.seed,
                out_dir=out_dir / "train_batch",
            )
        )
        run_summary = run.summary
        source_mode = str(run.summary.get("source_mode"))
        if source_mode == "fallback_demo" and not args.allow_fallback_demo:
            raise SystemExit("real SAIR files missing; pass --allow-fallback-demo to run fallback smoke")
        trace_csv = Path(run.output_paths["sair_attempts.csv"])
    df = pd.read_csv(trace_csv)
    clean_df, hygiene = clean_breakthrough_trace_rows(df)
    write_hygiene_audit(clean_df, hygiene, out_dir)
    motifs = mine_clean_constructor_motifs(clean_df)
    motifs = score_clean_motifs(clean_df, motifs)
    motifs = deduplicate_subsumed_motifs(motifs)
    export_clean_motifs(clean_df, motifs, out_dir)

    if source_mode == "real_sair":
        eval_tasks = load_eval_tasks(args.equations, args.matrix, args.eval_pairs, args.seed + 1)
    else:
        eval_tasks = [task for task in builtin_breakthrough_tasks()][: args.eval_pairs]
    eval_tasks = attach_preferred_constructors(eval_tasks)
    report = evaluate_scheduler_policies(eval_tasks, motifs, SAIRSchedulerEvalConfig(attempt_budget=args.attempt_budget, seed=args.seed))
    export_scheduler_eval_report(report, out_dir)
    metadata = {
        "source_mode": source_mode,
        "trace_csv": str(trace_csv),
        "train_pairs": args.train_pairs,
        "eval_pairs": len(eval_tasks),
        "attempt_budget": args.attempt_budget,
        "run_summary": run_summary,
        "hygiene_report": hygiene.to_dict(),
        "scheduler_overall": report.overall,
        "policy_results": report.policy_results,
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "source_mode": source_mode,
        "clean_rows": len(clean_df),
        "motifs": len(motifs),
        "scheduler_overall": report.overall,
        "out_dir": str(out_dir),
    }, indent=2, sort_keys=True))
    return 0 if report.overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

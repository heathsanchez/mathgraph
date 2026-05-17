#!/usr/bin/env python
"""Run finite countermodel executor over task queue rows."""

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

from mathgraph import FiniteCountermodelConfig, run_finite_countermodel_tasks
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-queue-jsonl", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--max-order", type=int, default=4)
    parser.add_argument("--exhaustive-order-limit", type=int, default=3)
    parser.add_argument("--random-tables-per-order", type=int, default=0)
    parser.add_argument("--no-deterministic-tables", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stop-after-first", dest="stop_after_first", action="store_true", default=True)
    group.add_argument("--no-stop-after-first", dest="stop_after_first", action="store_false")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("run_finite_countermodel_tasks", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    with progress.stage("finite_countermodel_executor", output=args.out):
        result = run_finite_countermodel_tasks(
            FiniteCountermodelConfig(
                task_queue_jsonl=args.task_queue_jsonl,
                out_jsonl=args.out,
                max_tasks=args.max_tasks,
                max_order=args.max_order,
                exhaustive_order_limit=args.exhaustive_order_limit,
                random_tables_per_order=args.random_tables_per_order,
                include_deterministic_tables=not args.no_deterministic_tables,
                stop_after_first=args.stop_after_first,
                random_seed=args.random_seed,
            )
        )
    if not args.quiet:
        print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

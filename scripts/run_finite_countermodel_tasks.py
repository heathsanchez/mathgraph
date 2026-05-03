#!/usr/bin/env python
"""Run finite countermodel executor over task queue rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import FiniteCountermodelConfig, run_finite_countermodel_tasks


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
    args = parser.parse_args(argv)

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
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

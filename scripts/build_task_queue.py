#!/usr/bin/env python
"""Build constructor-ready task queue rows from scheduled candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import TaskQueueConfig, build_task_queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule-jsonl", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-tasks", type=int, default=1000)
    parser.add_argument("--min-priority", type=float, default=0.0)
    parser.add_argument("--include-known", action="store_true")
    args = parser.parse_args(argv)

    result = build_task_queue(
        TaskQueueConfig(
            schedule_jsonl=args.schedule_jsonl,
            out_jsonl=args.out,
            max_tasks=args.max_tasks,
            min_priority=args.min_priority,
            include_known=args.include_known,
        )
    )
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

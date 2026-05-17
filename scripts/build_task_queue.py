#!/usr/bin/env python
"""Build constructor-ready task queue rows from scheduled candidates."""

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

from mathgraph import TaskQueueConfig, build_task_queue
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule-jsonl", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-tasks", type=int, default=1000)
    parser.add_argument("--min-priority", type=float, default=0.0)
    parser.add_argument("--include-known", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("build_task_queue", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    with progress.stage("build_task_queue", output=args.out):
        result = build_task_queue(
            TaskQueueConfig(
                schedule_jsonl=args.schedule_jsonl,
                out_jsonl=args.out,
                max_tasks=args.max_tasks,
                min_priority=args.min_priority,
                include_known=args.include_known,
            )
        )
    if not args.quiet:
        print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

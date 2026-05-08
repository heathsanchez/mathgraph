#!/usr/bin/env python
"""Build an advisory Frontier v2 from a residual atlas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.frontier_v2 import build_frontier_v2_from_atlas


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--residual-atlas", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--include-suppressed", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        atlas = json.loads(Path(args.residual_atlas).read_text(encoding="utf-8"))
        report = build_frontier_v2_from_atlas(
            atlas,
            max_tasks=args.max_tasks,
            include_suppressed=args.include_suppressed,
            run_id=args.run_id,
            out_dir=args.out_dir,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1
    counts = report.summary.get("task_kind_counts", {})
    print(f"task_count: {report.task_count}")
    print(f"finite_countermodel_search: {counts.get('finite_countermodel_search', 0)}")
    print(f"obstruction_analysis: {counts.get('obstruction_analysis', 0)}")
    print(f"representation_shift_probe: {counts.get('representation_shift_probe', 0)}")
    print(f"top_priority: {report.summary.get('top_priority')}")
    print(f"report_json: {report.outputs.get('frontier_v2_report_json')}")
    print(f"tasks_jsonl: {report.outputs.get('frontier_v2_tasks_jsonl')}")
    print(f"task_queue_jsonl: {report.outputs.get('frontier_v2_task_queue_jsonl')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

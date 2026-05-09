#!/usr/bin/env python
"""Run the Multi-Episode Compounding Harness."""

from __future__ import annotations

import argparse
import json
import sys

from mathgraph.multi_episode_harness import MultiEpisodeConfig, run_multi_episode_harness


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initial-frontier-task-queue", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--max-tasks-per-episode", type=int, default=100)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--next-frontier-max-tasks", type=int, default=100)
    parser.add_argument("--no-audit", action="store_true")
    parser.add_argument("--no-stop-if-no-frontier", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = run_multi_episode_harness(
            MultiEpisodeConfig(
                initial_frontier_task_queue_jsonl=args.initial_frontier_task_queue,
                out_dir=args.out_dir,
                store_path=args.store,
                episodes=args.episodes,
                max_tasks_per_episode=args.max_tasks_per_episode,
                max_countermodel_order=args.max_countermodel_order,
                next_frontier_max_tasks=args.next_frontier_max_tasks,
                stop_if_no_frontier=not args.no_stop_if_no_frontier,
                audit_each_episode=not args.no_audit,
                run_id=args.run_id,
            )
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), sort_keys=True))
    else:
        print(f"run_id: {report.run_id}")
        print(f"episode_count: {report.episode_count}")
        print(f"compounding_confirmed: {str(report.compounding_confirmed).lower()}")
        print(f"compounding_score: {report.compounding_score}")
        print(f"total_promoted_certificates: {report.summary.get('total_promoted_certificates', 0)}")
        print(f"report_json: {report.outputs.get('multi_episode_report_json')}")
        print(f"report_md: {report.outputs.get('multi_episode_report_md')}")
        print(f"episode_summaries_jsonl: {report.outputs.get('episode_summaries_jsonl')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python
"""Run Episode Runner v2 over a Frontier v2 task queue."""

from __future__ import annotations

import argparse
import json
import sys

from mathgraph.episode_runner_v2 import EpisodeRunnerV2Config, run_episode_v2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier-task-queue", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--episode-id")
    parser.add_argument("--max-tasks", type=int, default=100)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--exhaustive-order-limit", type=int, default=3)
    parser.add_argument("--random-tables-per-order", type=int, default=0)
    parser.add_argument("--no-audit", action="store_true")
    parser.add_argument("--no-replay", action="store_true")
    parser.add_argument("--no-route-policy", action="store_true")
    parser.add_argument("--no-residual-atlas", action="store_true")
    parser.add_argument("--no-next-frontier", action="store_true")
    parser.add_argument("--next-frontier-max-tasks", type=int, default=100)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = run_episode_v2(
            EpisodeRunnerV2Config(
                frontier_task_queue_jsonl=args.frontier_task_queue,
                out_dir=args.out_dir,
                store_path=args.store,
                episode_id=args.episode_id,
                max_tasks=args.max_tasks,
                max_countermodel_order=args.max_countermodel_order,
                exhaustive_order_limit=args.exhaustive_order_limit,
                random_tables_per_order=args.random_tables_per_order,
                audit_after_import=not args.no_audit,
                build_replay=not args.no_replay,
                build_route_policy=not args.no_route_policy,
                build_residual_atlas=not args.no_residual_atlas,
                build_next_frontier=not args.no_next_frontier,
                next_frontier_max_tasks=args.next_frontier_max_tasks,
            )
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), sort_keys=True))
    else:
        print(f"episode_id: {report.episode_id}")
        print(f"attempted_tasks: {report.attempted_tasks}")
        print(f"executable_tasks: {report.executable_tasks}")
        print(f"advisory_tasks: {report.advisory_tasks}")
        print(f"promoted_certificates: {report.promoted_certificates}")
        print(f"verified_false: {report.verified_false}")
        print(f"constructor_failed: {report.constructor_failed}")
        print(f"episode_v2_report_json: {report.outputs.get('episode_v2_report_json')}")
        print(f"episode_v2_report_md: {report.outputs.get('episode_v2_report_md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


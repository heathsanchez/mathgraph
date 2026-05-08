#!/usr/bin/env python
"""Run the Milestone 0 certificate-factory loop over JSONL pair tasks."""

from __future__ import annotations

import argparse
import json
import sys

from mathgraph.m0_certificate_factory import M0EpisodeConfig, run_m0_episode


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--ledger")
    parser.add_argument("--report")
    parser.add_argument("--metrics-history")
    parser.add_argument("--episode-id")
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--random-tables-per-order", type=int, default=0)
    parser.add_argument("--exhaustive-order-limit", type=int, default=3)
    parser.add_argument("--working-dir")
    parser.add_argument("--no-construction", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_m0_episode(
            M0EpisodeConfig(
                pairs_jsonl=args.pairs,
                store_path=args.store,
                ledger_jsonl=args.ledger,
                report_json=args.report,
                metrics_history_jsonl=args.metrics_history,
                episode_id=args.episode_id,
                max_tasks=args.max_tasks,
                max_countermodel_order=args.max_countermodel_order,
                random_tables_per_order=args.random_tables_per_order,
                exhaustive_order_limit=args.exhaustive_order_limit,
                working_dir=args.working_dir,
                allow_construction=not args.no_construction,
            )
        )
    except Exception as exc:
        print(json.dumps({"status": "fatal_error", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    metrics = result.metrics.to_dict()
    summary = {
        "attempted": metrics["attempted"],
        "known_skipped": metrics["known_skipped"],
        "verified_false": metrics["verified_false"],
        "constructor_failed": metrics["constructor_failed"],
        "new_unique_certificates": metrics["new_unique_certificates"],
        "compounding_confirmed": metrics["compounding_confirmed"],
        "report": args.report,
        "store": args.store,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


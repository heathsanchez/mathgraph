#!/usr/bin/env python
"""Run the Milestone 0 certificate-factory loop over JSONL pair tasks."""

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

from mathgraph.m0_audit import audit_m0_store, write_audit_report
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
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--audit-report")
    parser.add_argument("--fail-on-critical-audit", action="store_true")
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
    audit_payload = None
    if args.audit:
        audit = audit_m0_store(args.store)
        audit_payload = audit.to_dict()
        if args.audit_report:
            write_audit_report(audit, args.audit_report)
        if args.report:
            _merge_audit_into_report(args.report, audit_payload)
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
    if audit_payload is not None:
        summary.update(
            {
                "audit_passed": audit_payload["passed"],
                "critical_count": audit_payload["critical_count"],
                "warning_count": audit_payload["warning_count"],
            }
        )
    print(json.dumps(summary, sort_keys=True))
    if audit_payload is not None and args.fail_on_critical_audit and audit_payload["critical_count"] > 0:
        return 2
    return 0


def _merge_audit_into_report(report_path: str, audit_payload: dict) -> None:
    try:
        with open(report_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        payload = {}
    payload["audit"] = audit_payload
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())

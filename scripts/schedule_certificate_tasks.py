#!/usr/bin/env python
"""Schedule certificate work with deterministic H-Tilt v1 pressure."""

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
from typing import Any

from mathgraph import HTiltScheduler, KernelOracle, LawbookStore, PairOutcome, RouteLearner
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs-jsonl", required=True)
    parser.add_argument("--out-tasks-json", default=None)
    parser.add_argument("--out-tasks-jsonl", default=None)
    parser.add_argument("--out-stats", default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--lawbook-store", default=None)
    parser.add_argument("--outcomes-jsonl", default=None)
    parser.add_argument("--policy-json", default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--skip-known", dest="skip_known", action="store_true", default=True)
    group.add_argument("--include-known", dest="skip_known", action="store_false")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("schedule_certificate_tasks", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    with progress.stage("read_pairs", input=args.pairs_jsonl):
        pairs = _read_jsonl(args.pairs_jsonl)
    store = LawbookStore(args.lawbook_store) if args.lawbook_store else None
    try:
        oracle = KernelOracle(store) if store is not None else None
        with progress.stage("load_policy_inputs"):
            outcomes = _read_outcomes(args.outcomes_jsonl) if args.outcomes_jsonl else None
            policy_cards = _read_json(args.policy_json) if args.policy_json else None
        route_learner = None
        if outcomes is not None:
            route_learner = RouteLearner(outcomes)
            with progress.stage("build_route_learner", total=len(outcomes)):
                route_learner.build_policy_cards()
        scheduler = HTiltScheduler(
            oracle=oracle,
            route_learner=route_learner,
            policy_cards=policy_cards,
            beta=args.beta,
        )
        with progress.stage("schedule", total=len(pairs)):
            tasks = scheduler.schedule(pairs, top_k=args.top_k, skip_known=args.skip_known)
            stats = scheduler.stats(tasks)
        if args.out_tasks_json:
            with progress.stage("write_tasks_json", total=len(tasks), output=args.out_tasks_json):
                scheduler.save_tasks_json(args.out_tasks_json, tasks)
        if args.out_tasks_jsonl:
            with progress.stage("write_tasks_jsonl", total=len(tasks), output=args.out_tasks_jsonl):
                scheduler.save_tasks_jsonl(args.out_tasks_jsonl, tasks)
        if args.out_stats:
            with progress.stage("write_stats", output=args.out_stats):
                scheduler.save_stats_json(args.out_stats, stats)
        payload = {
            "stats": stats.to_dict(),
            "task_count": len(tasks),
            "outputs": {
                "tasks_json": args.out_tasks_json,
                "tasks_jsonl": args.out_tasks_jsonl,
                "stats": args.out_stats,
            },
        }
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        if store is not None:
            store.close()
    return 0


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _read_outcomes(path: str | Path) -> list[PairOutcome]:
    return [PairOutcome.from_dict(row) for row in _read_jsonl(path)]


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())

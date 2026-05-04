#!/usr/bin/env python
"""Build pair outcome rows and compounding diagnostics from a LawbookStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore, OutcomeDatasetBuilder
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--out-jsonl", default=None)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--diagnostics", default=None)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--equation-count", type=int, default=None)
    parser.add_argument("--no-primitive", action="store_true")
    parser.add_argument("--no-derived", action="store_true")
    parser.add_argument("--unknown-pairs-json", default=None)
    parser.add_argument("--advisory-tasks-json", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("build_outcome_dataset", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    store = LawbookStore(args.store)
    try:
        builder = OutcomeDatasetBuilder(store)
        with progress.stage("build_outcomes"):
            outcomes = builder.build(
                include_primitive=not args.no_primitive,
                include_derived=not args.no_derived,
                unknown_pairs=_load_optional_list(args.unknown_pairs_json),
                advisory_tasks=_load_optional_list(args.advisory_tasks_json),
            )
        if args.limit is not None:
            outcomes = outcomes[: args.limit]
        with progress.stage("compute_stats", total=len(outcomes)):
            stats = builder.stats(outcomes)
            diagnostics = builder.diagnostics(
                outcomes,
                episode_id=args.episode_id,
                equation_count=args.equation_count,
            )
        if args.out_jsonl:
            with progress.stage("write_jsonl", total=len(outcomes), output=args.out_jsonl):
                builder.save_jsonl(outcomes, args.out_jsonl)
        if args.out_json:
            with progress.stage("write_json", total=len(outcomes), output=args.out_json):
                builder.save_json(outcomes, args.out_json)
        if args.diagnostics:
            with progress.stage("write_diagnostics", output=args.diagnostics):
                builder.save_diagnostics(diagnostics, args.diagnostics)
        payload = {
            "stats": stats.to_dict(),
            "diagnostics": diagnostics.to_dict(),
            "outputs": {
                "jsonl": args.out_jsonl,
                "json": args.out_json,
                "diagnostics": args.diagnostics,
            },
        }
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


def _load_optional_list(path: str | None) -> list[dict[str, Any]] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("items", "pairs", "tasks", "outcomes"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    if isinstance(data, list):
        return [dict(item) if isinstance(item, dict) else {"source": item[0], "target": item[1]} for item in data]
    raise ValueError(f"expected list or dict JSON at {path}")


if __name__ == "__main__":
    raise SystemExit(main())

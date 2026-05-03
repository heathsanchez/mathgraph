#!/usr/bin/env python
"""Run planned certificate tasks through the safe mock executor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph.task_runner import (
    execute_many_certificate_tasks,
    load_tasks_json,
    load_tasks_jsonl,
    residual_outcomes,
    summarize_task_outcomes,
    write_outcomes_json,
    write_outcomes_jsonl,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--tasks-json", default=None)
    source.add_argument("--tasks-jsonl", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--mode", default="mock")
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--outcomes-json", default=None)
    parser.add_argument("--outcomes-jsonl", default=None)
    parser.add_argument("--residual-json", default=None)
    args = parser.parse_args(argv)

    tasks = load_tasks_json(args.tasks_json) if args.tasks_json else load_tasks_jsonl(args.tasks_jsonl)
    try:
        outcomes = execute_many_certificate_tasks(tasks, mode=args.mode, limit=args.limit)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    residuals = residual_outcomes(outcomes)
    summary = summarize_task_outcomes(outcomes)
    paths = _resolve_output_paths(args)

    if paths["summary_json"]:
        _write_json(paths["summary_json"], summary.to_dict())
    if not args.summary_only or args.outcomes_json or args.outcomes_jsonl or args.residual_json:
        if paths["outcomes_json"]:
            write_outcomes_json(outcomes, paths["outcomes_json"])
        if paths["outcomes_jsonl"]:
            write_outcomes_jsonl(outcomes, paths["outcomes_jsonl"])
        if paths["residual_json"]:
            write_outcomes_json(residuals, paths["residual_json"])

    payload = {
        "summary": summary.to_dict(),
        "output_paths": paths,
        "outcome_count": len(outcomes),
        "residual_count": len(residuals),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _resolve_output_paths(args: argparse.Namespace) -> dict[str, str | None]:
    paths = {
        "summary_json": args.summary_json,
        "outcomes_json": args.outcomes_json,
        "outcomes_jsonl": args.outcomes_jsonl,
        "residual_json": args.residual_json,
    }
    if args.out:
        out = Path(args.out)
        if out.suffix:
            out = out.parent
        out.mkdir(parents=True, exist_ok=True)
        paths["summary_json"] = paths["summary_json"] or str(out / "summary.json")
        if not args.summary_only:
            paths["outcomes_json"] = paths["outcomes_json"] or str(out / "outcomes.json")
            paths["outcomes_jsonl"] = paths["outcomes_jsonl"] or str(out / "outcomes.jsonl")
            paths["residual_json"] = paths["residual_json"] or str(out / "residual.json")
    return paths


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

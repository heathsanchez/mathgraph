#!/usr/bin/env python
"""Compile advisory constructor plans from promoted roots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mathgraph.root_compiler import compile_constructor_plans


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots-json")
    group.add_argument("--roots-jsonl")
    parser.add_argument("--promotions-json", required=True)
    parser.add_argument("--telemetry-jsonl")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-jsonl")
    parser.add_argument("--summary")
    parser.add_argument("--max-replay-items", type=int, default=50)
    args = parser.parse_args(argv)
    roots = _read_json_or_jsonl(args.roots_json, args.roots_jsonl)
    promotions_payload = json.loads(Path(args.promotions_json).read_text(encoding="utf-8"))
    promotions = promotions_payload.get("promotion_records", promotions_payload)
    rows = _read_jsonl(args.telemetry_jsonl) if args.telemetry_jsonl else None
    plans = compile_constructor_plans(roots, promotions, rows=rows, max_replay_items=args.max_replay_items)
    plan_rows = [plan.to_dict() for plan in plans]
    summary = {"plan_count": len(plan_rows), "advisory_only": True}
    _write_json(args.out_json, {"constructor_plans": plan_rows, "summary": summary})
    if args.out_jsonl:
        _write_jsonl(args.out_jsonl, plan_rows)
    if args.summary:
        _write_json(args.summary, summary)
    return 0


def _read_jsonl(path: str | None) -> list[dict]:
    if not path:
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_json_or_jsonl(json_path: str | None, jsonl_path: str | None) -> list[dict]:
    if jsonl_path:
        return _read_jsonl(jsonl_path)
    data = json.loads(Path(str(json_path)).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("roots", "root_candidates", "canonical_roots"):
            if isinstance(data.get(key), list):
                return data[key]
    return data


def _write_json(path: str, payload) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: str, rows: list[dict]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

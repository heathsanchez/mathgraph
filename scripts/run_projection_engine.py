#!/usr/bin/env python
"""Run the lightweight MathGraph projection engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mathgraph.projection import (
    projection_trace_to_agent_experiences,
    projection_trace_to_alchemical_trace,
    run_projection_engine,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lawbook-json")
    parser.add_argument("--lawbook-jsonl")
    parser.add_argument("--residual-pairs-json")
    parser.add_argument("--residual-pairs-jsonl")
    parser.add_argument("--agent-id")
    parser.add_argument("--episode-id")
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--out-json")
    parser.add_argument("--out-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    lawbook_entries = _read_records(args.lawbook_json) + _read_jsonl_records(args.lawbook_jsonl)
    residual_pairs = _read_records(args.residual_pairs_json) + _read_jsonl_records(args.residual_pairs_jsonl)

    trace = run_projection_engine(
        lawbook_entries=lawbook_entries,
        residual_pairs=residual_pairs,
        agent_id=args.agent_id,
        episode_id=args.episode_id,
        max_candidates=args.max_candidates,
    )
    alchemical_trace = projection_trace_to_alchemical_trace(trace)
    experiences = projection_trace_to_agent_experiences(trace)
    report = check_roadmap_alignment(
        alchemical_traces=[alchemical_trace],
        agent_experiences=experiences,
        projection_traces=[trace],
        summary={
            "projection_engine": "m2",
            "projection_gain_total": trace.projection_gain_total(),
            "residual_compression_gain": trace.compression_gain_total(),
            "derived_amplification": trace.summary.get("derived_certificates", 0),
            "metadata": {"projection": "advisory-only unless verifier-bound or chain-audited"},
        },
    )

    if args.out_json:
        trace.write_json(args.out_json)
    if args.out_jsonl:
        trace.write_jsonl(args.out_jsonl)
    if args.out_alchemical_trace_json:
        _write_json(args.out_alchemical_trace_json, alchemical_trace.to_dict())
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [exp.to_dict() for exp in experiences])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any(
        [
            args.out_json,
            args.out_jsonl,
            args.out_alchemical_trace_json,
            args.out_agent_experiences_jsonl,
            args.alignment_report_json,
            args.alignment_report_md,
        ]
    ):
        sys.stdout.write(trace.to_json() + "\n")

    if args.fail_on_critical and report.critical_count() > 0:
        return 2
    return 0


def _read_records(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    source = Path(path)
    if not source.exists():
        return []
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [dict(item) for item in data]
    if isinstance(data, dict):
        for key in ("entries", "lawbook_entries", "residual_pairs", "pairs", "items", "traces"):
            if isinstance(data.get(key), list):
                return [dict(item) for item in data[key]]
        return [dict(data)]
    return []


def _read_jsonl_records(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    source = Path(path)
    if not source.exists():
        return []
    rows: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(dict(json.loads(line)))
    return rows


def _write_json(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

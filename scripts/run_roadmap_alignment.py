#!/usr/bin/env python
"""Run MathGraph roadmap-alignment checks over JSON/JSONL records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, TypeVar

from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.roadmap_alignment import check_roadmap_alignment

T = TypeVar("T")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alchemical-traces-jsonl")
    parser.add_argument("--agent-experiences-jsonl")
    parser.add_argument("--summary-json")
    parser.add_argument("--out-json")
    parser.add_argument("--out-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    traces = _read_jsonl(args.alchemical_traces_jsonl, AlchemicalTrace.from_jsonl_line)
    experiences = _read_jsonl(args.agent_experiences_jsonl, AgentExperience.from_jsonl_line)
    summary = _read_json(args.summary_json)

    report = check_roadmap_alignment(
        alchemical_traces=traces,
        agent_experiences=experiences,
        summary=summary,
    )

    if args.out_json:
        report.write_json(args.out_json)
    if args.out_md:
        report.write_markdown(args.out_md)
    if not args.out_json and not args.out_md:
        sys.stdout.write(report.to_json())

    if args.fail_on_critical and report.critical_count() > 0:
        return 2
    return 0


def _read_jsonl(path: str | None, loader: Callable[[str], T]) -> list[T]:
    if not path:
        return []
    source = Path(path)
    if not source.exists():
        return []
    rows: list[T] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(loader(line))
    return rows


def _read_json(path: str | None) -> dict:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        return {}
    return dict(json.loads(source.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())

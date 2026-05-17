#!/usr/bin/env python
"""Build a route telemetry ledger from verification episodes or events."""

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

from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.route_telemetry import (
    HTiltTelemetrySummary,
    RouteTelemetryEvent,
    build_route_telemetry_ledger,
    summarize_h_tilt_telemetry,
)
from mathgraph.verification_episode import VerificationEpisodeTrace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-json")
    parser.add_argument("--episodes-jsonl")
    parser.add_argument("--events-jsonl")
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--out-ledger-json")
    parser.add_argument("--out-ledger-jsonl")
    parser.add_argument("--out-htilt-summary-json")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    episodes: list[VerificationEpisodeTrace] = []
    events: list[RouteTelemetryEvent] = []
    if args.episodes_json:
        episodes.extend(_read_episodes_json(args.episodes_json))
    if args.episodes_jsonl:
        episodes.extend(VerificationEpisodeTrace.read_jsonl(args.episodes_jsonl))
    if args.events_jsonl:
        events.extend(_read_events_jsonl(args.events_jsonl))

    ledger = build_route_telemetry_ledger(episodes=episodes, events=events)
    htilt_summary = summarize_h_tilt_telemetry(ledger, beta=args.beta)

    if args.out_ledger_json:
        ledger.write_json(args.out_ledger_json)
    if args.out_ledger_jsonl:
        ledger.write_jsonl(args.out_ledger_jsonl)
    if args.out_htilt_summary_json:
        _write_json(args.out_htilt_summary_json, htilt_summary.to_dict())

    report = check_roadmap_alignment(
        route_telemetry_ledgers=[ledger],
        summary={
            "route_scores": htilt_summary.route_scores,
            "h_tilt_telemetry_summary": htilt_summary.to_dict(),
            "metadata": {
                "advisory_only": True,
                "full_spectral_h_tilt_future_work": True,
                "route_scores_are_not_truth": True,
            },
        },
    )
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not (args.out_ledger_json or args.out_ledger_jsonl or args.out_htilt_summary_json or args.alignment_report_json or args.alignment_report_md):
        sys.stdout.write(ledger.to_json() + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_episodes_json(path: str) -> list[VerificationEpisodeTrace]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [VerificationEpisodeTrace.from_dict(item) for item in data]
    return [VerificationEpisodeTrace.from_dict(data)]


def _read_events_jsonl(path: str) -> list[RouteTelemetryEvent]:
    source = Path(path)
    if not source.exists():
        return []
    events: list[RouteTelemetryEvent] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(RouteTelemetryEvent.from_jsonl_line(line))
    return events


def _write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


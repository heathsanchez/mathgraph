#!/usr/bin/env python
"""Estimate lightweight spectral H-tilt from a route telemetry ledger."""

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

from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.route_telemetry import build_route_telemetry_ledger, RouteTelemetryLedger
from mathgraph.spectral_htilt import (
    SpectralHTiltConfig,
    estimate_spectral_htilt,
    route_priorities_from_estimate,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-json")
    parser.add_argument("--ledger-jsonl")
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--damping", type=float, default=0.85)
    parser.add_argument("--kill-weight", type=float, default=1.0)
    parser.add_argument("--support-smoothing", type=float, default=1e-6)
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument("--tolerance", type=float, default=1e-9)
    parser.add_argument("--out-json")
    parser.add_argument("--out-priorities-json")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    ledger = _read_ledger(args.ledger_json, args.ledger_jsonl)
    config = SpectralHTiltConfig(
        beta=args.beta,
        damping=args.damping,
        kill_weight=args.kill_weight,
        support_smoothing=args.support_smoothing,
        max_iterations=args.max_iterations,
        tolerance=args.tolerance,
        metadata={"advisory_only": True, "not_truth_authority": True},
    )
    estimate = estimate_spectral_htilt(ledger, config=config)
    priorities = route_priorities_from_estimate(estimate)

    if args.out_json:
        estimate.write_json(args.out_json)
    if args.out_priorities_json:
        _write_json(args.out_priorities_json, {"priorities": priorities, "advisory": True})

    report = check_roadmap_alignment(spectral_htilt_estimates=[estimate])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not (args.out_json or args.out_priorities_json or args.alignment_report_json or args.alignment_report_md):
        sys.stdout.write(estimate.to_json() + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_ledger(json_path: str | None, jsonl_path: str | None) -> RouteTelemetryLedger:
    if json_path:
        return RouteTelemetryLedger.read_json(json_path)
    if jsonl_path:
        return RouteTelemetryLedger.read_jsonl(jsonl_path)
    return build_route_telemetry_ledger()


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


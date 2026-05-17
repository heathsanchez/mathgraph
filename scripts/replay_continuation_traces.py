#!/usr/bin/env python
"""Replay continuation traces into advisory route pressure."""

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

from mathgraph.replay_engine import replay_continuation_traces


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    try:
        report = replay_continuation_traces(args.traces, args.out_dir)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1
    strengthen = sum(1 for signal in report.route_signals if signal.recommendation == "strengthen_route")
    print(f"trace_count: {report.trace_count}")
    print(f"route_signal_count: {len(report.route_signals)}")
    print(f"strengthen_route_count: {strengthen}")
    print(f"obstruction_pressure_count: {len(report.obstruction_pressure)}")
    print(f"replay_report_json: {report.outputs.get('replay_report_json')}")
    print(f"replay_report_md: {report.outputs.get('replay_report_md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

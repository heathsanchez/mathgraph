#!/usr/bin/env python
"""Build advisory Route Policy v2 cards from continuation traces or replay."""

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

from mathgraph.route_policy_v2 import (
    build_route_policy_v2_from_replay,
    build_route_policy_v2_from_trace_store,
    write_route_policy_v2,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--traces")
    group.add_argument("--replay-report")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--beta", type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        if args.traces:
            report = build_route_policy_v2_from_trace_store(args.traces, out_dir=args.out_dir, beta=args.beta)
        else:
            replay = json.loads(Path(args.replay_report).read_text(encoding="utf-8"))
            report = build_route_policy_v2_from_replay(replay, beta=args.beta)
            outputs = write_route_policy_v2(report, args.out_dir)
            report = report.__class__(
                run_id=report.run_id,
                card_count=report.card_count,
                summary=report.summary,
                cards=report.cards,
                outputs=outputs,
                warnings=report.warnings,
            )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1
    counts = report.summary.get("recommendation_counts", {})
    print(f"card_count: {report.card_count}")
    print(f"top_route_key: {report.summary.get('top_route_key')}")
    print(f"top_priority: {report.summary.get('top_priority')}")
    print(f"recommendation_counts: {json.dumps(counts, sort_keys=True)}")
    print(f"report_json: {report.outputs.get('route_policy_v2_report_json')}")
    print(f"cards_jsonl: {report.outputs.get('route_policy_v2_cards_jsonl')}")
    print(f"report_md: {report.outputs.get('route_policy_v2_report_md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

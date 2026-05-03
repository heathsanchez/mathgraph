#!/usr/bin/env python
"""Run the reproducible MathGraph flywheel pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import FlywheelConfig, run_mathgraph_flywheel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--schedule-top-k", type=int, default=100)
    parser.add_argument("--unknown-pairs-jsonl", default=None)
    parser.add_argument("--derived-limit", type=int, default=None)
    parser.add_argument("--store-path", default=None)
    args = parser.parse_args(argv)

    config = FlywheelConfig(
        traces_json=args.traces_json,
        out_dir=args.out,
        store_path=args.store_path,
        derived_limit=args.derived_limit,
        unknown_pairs_jsonl=args.unknown_pairs_jsonl,
        schedule_top_k=args.schedule_top_k,
    )
    result = run_mathgraph_flywheel(config)
    report = result.to_dict()
    stages = {stage["name"]: stage for stage in report["stages"]}
    payload = {
        "final_report": report["outputs"]["report_json"],
        "store_path": report["outputs"]["store"],
        "primitive_count": stages["lawbook_store"]["summary"].get("trace_count", 0),
        "derived_count": stages["derived_certificates"]["summary"].get("total_derived_count", 0),
        "outcome_row_count": stages["outcome_dataset"]["summary"].get("row_count", 0),
        "schedule_count": stages["htilt_schedule"]["summary"].get("scheduled_count", 0),
        "warnings": report["warnings"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

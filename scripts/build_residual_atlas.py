#!/usr/bin/env python
"""Build an advisory residual atlas from traces or residual rows."""

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

from mathgraph.residual_atlas import build_residual_atlas_from_rows, build_residual_atlas_from_traces


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--traces")
    group.add_argument("--rows")
    parser.add_argument("--route-policy")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        route_policy = json.loads(Path(args.route_policy).read_text(encoding="utf-8")) if args.route_policy else None
        if args.traces:
            report = build_residual_atlas_from_traces(
                args.traces,
                route_policy=route_policy,
                out_dir=args.out_dir,
                run_id=args.run_id,
            )
        else:
            rows = _read_jsonl(args.rows)
            report = build_residual_atlas_from_rows(
                rows,
                route_policy=route_policy,
                out_dir=args.out_dir,
                run_id=args.run_id,
            )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1
    print(f"case_count: {report.case_count}")
    print(f"cluster_count: {report.cluster_count}")
    print(f"top_cluster: {report.summary.get('top_cluster')}")
    print(f"recommendation_counts: {json.dumps(report.summary.get('recommendation_counts', {}), sort_keys=True)}")
    print(f"report_json: {report.outputs.get('residual_atlas_report_json')}")
    print(f"cases_jsonl: {report.outputs.get('residual_cases_jsonl')}")
    print(f"clusters_jsonl: {report.outputs.get('residual_clusters_jsonl')}")
    return 0


def _read_jsonl(path: str) -> list[dict]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())

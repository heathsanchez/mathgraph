#!/usr/bin/env python
"""Run the advisory Root Constructor Validation Lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.replay_engine import replay_continuation_traces
from mathgraph.residual_atlas import build_residual_atlas_from_traces
from mathgraph.route_policy_v2 import build_route_policy_v2_from_replay, write_route_policy_v2
from mathgraph.root_constructor_lab import ROOT_LABELS, run_root_constructor_lab


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, help="Input JSONL pairs.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-pairs-per-root", type=int, default=50)
    parser.add_argument("--null-pairs-per-root", type=int, default=50)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--trace-store")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--replay-out-dir")
    parser.add_argument("--build-route-policy", action="store_true")
    parser.add_argument("--route-policy-out-dir")
    parser.add_argument("--build-residual-atlas", action="store_true")
    parser.add_argument("--residual-atlas-out-dir")
    parser.add_argument(
        "--roots",
        default=",".join(ROOT_LABELS),
        help="Comma-separated root labels.",
    )
    args = parser.parse_args(argv)

    try:
        pairs = _read_jsonl(args.pairs)
        roots = [item.strip() for item in args.roots.split(",") if item.strip()]
        trace_store = args.trace_store
        if (args.replay or args.build_route_policy or args.build_residual_atlas) and not trace_store:
            trace_store = str(Path(args.out_dir) / "continuation_traces.jsonl")
        report = run_root_constructor_lab(
            pairs,
            args.out_dir,
            root_labels=roots,
            max_pairs_per_root=args.max_pairs_per_root,
            null_pairs_per_root=args.null_pairs_per_root,
            max_countermodel_order=args.max_countermodel_order,
            random_seed=args.random_seed,
            trace_store_path=trace_store,
        )
        replay_report = None
        if args.replay or args.build_route_policy or args.build_residual_atlas:
            replay_out = args.replay_out_dir or str(Path(args.out_dir) / "replay")
            replay_report = replay_continuation_traces(trace_store, replay_out)
            _merge_replay_outputs(report.outputs["root_constructor_lab_report_json"], replay_report.outputs)
        policy = None
        policy_outputs = {}
        if args.build_route_policy:
            policy_out = args.route_policy_out_dir or str(Path(args.out_dir) / "route_policy_v2")
            policy = build_route_policy_v2_from_replay(replay_report)
            policy_outputs = write_route_policy_v2(policy, policy_out)
            _merge_replay_outputs(report.outputs["root_constructor_lab_report_json"], policy_outputs)
        if args.build_residual_atlas:
            if policy is None:
                policy = build_route_policy_v2_from_replay(replay_report)
                policy_out = args.route_policy_out_dir or str(Path(args.out_dir) / "route_policy_v2")
                policy_outputs = write_route_policy_v2(policy, policy_out)
                _merge_replay_outputs(report.outputs["root_constructor_lab_report_json"], policy_outputs)
            atlas_out = args.residual_atlas_out_dir or str(Path(args.out_dir) / "residual_atlas")
            atlas = build_residual_atlas_from_traces(trace_store, route_policy=policy, out_dir=atlas_out)
            _merge_replay_outputs(report.outputs["root_constructor_lab_report_json"], atlas.outputs)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}), file=sys.stderr)
        return 1

    summary = report.summary
    print(f"root_count: {summary['root_count']}")
    print(f"attempted_pairs: {summary['attempted_pairs']}")
    print(f"verified_false: {summary['verified_false']}")
    print(f"top_root: {summary['top_root']}")
    print(f"top_root_value_score: {summary['top_root_value_score']}")
    print(f"report_json: {report.outputs['root_constructor_lab_report_json']}")
    print(f"report_md: {report.outputs['root_constructor_lab_report_md']}")
    if args.replay:
        print(f"replay_report_json: {replay_report.outputs.get('replay_report_json')}")
    if args.build_route_policy:
        print(f"route_policy_v2_report_json: {policy_outputs.get('route_policy_v2_report_json')}")
    if args.build_residual_atlas:
        print(f"residual_atlas_report_json: {atlas.outputs.get('residual_atlas_report_json')}")
    return 0


def _read_jsonl(path: str) -> list[dict]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _merge_replay_outputs(report_json: str, replay_outputs: dict) -> None:
    path = Path(report_json)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.setdefault("outputs", {}).update(replay_outputs)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

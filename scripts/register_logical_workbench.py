#!/usr/bin/env python
"""Register LogiKEy-style or MathGraph workbench metadata in LawbookStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore  # noqa: E402
from mathgraph.logical_workbench import mathgraph_default_workbench  # noqa: E402
from mathgraph.workbench_presets import (  # noqa: E402
    build_logikey_style_workbench_bundle,
    build_mathgraph_etp_workbench_bundle,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--preset", choices=["logikey", "etp", "mathgraph"], required=True)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    store = LawbookStore(args.db)
    try:
        store.init_schema()
        if args.replace:
            _clear_preset_tables(store)
        if args.preset == "logikey":
            bundle = build_logikey_style_workbench_bundle()
        elif args.preset == "etp":
            bundle = build_mathgraph_etp_workbench_bundle()
        else:
            bundle = {"logical_workbenches": [mathgraph_default_workbench()]}
        counts = _persist_bundle(store, bundle)
        payload = {
            "status": "registered",
            "preset": args.preset,
            "counts": counts,
            "truth_boundary": "Workbench metadata is advisory; verifiers decide terminal forms.",
        }
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


def _persist_bundle(store: LawbookStore, bundle: dict[str, list[object]]) -> dict[str, int]:
    method_map = {
        "logical_workbenches": "add_logical_workbench",
        "embedding_strategy_profiles": "add_embedding_strategy_profile",
        "verifier_backend_profiles": "add_verifier_backend_profile",
        "faithfulness_assessments": "add_faithfulness_assessment",
        "benchmark_suites": "add_benchmark_suite",
    }
    counts: dict[str, int] = {}
    for key, rows in bundle.items():
        method_name = method_map.get(key)
        if not method_name or not hasattr(store, method_name):
            continue
        method = getattr(store, method_name)
        for row in rows:
            method(row)
        counts[key] = len(rows)
    return counts


def _clear_preset_tables(store: LawbookStore) -> None:
    for table in (
        "logical_workbenches",
        "embedding_strategy_profiles",
        "verifier_backend_profiles",
        "faithfulness_assessments",
        "benchmark_suites",
    ):
        store.conn.execute(f"DELETE FROM {table}")
    store.conn.commit()


if __name__ == "__main__":
    raise SystemExit(main())

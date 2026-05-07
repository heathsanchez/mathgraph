#!/usr/bin/env python
"""Build a persistent SQLite LawbookStore from traces or artifact directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore
from mathgraph.artifact_warehouse import (
    import_v16_6_2_elevated_false_dir,
    import_v16_7_root_atlas_dir,
)
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json")
    parser.add_argument("--out")
    parser.add_argument("--out-db")
    parser.add_argument("--v1662-dir")
    parser.add_argument("--v167-dir")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger(
        "build_lawbook_store",
        log_jsonl=args.progress_jsonl,
        heartbeat_sec=args.heartbeat_sec,
        enabled=args.progress,
        quiet=args.quiet,
    )

    db_path = args.out_db or args.out
    if not db_path:
        parser.error("--out-db or --out is required")
    if not args.traces_json and not args.v1662_dir and not args.v167_dir:
        parser.error("provide --traces-json and/or --v1662-dir/--v167-dir")

    store = LawbookStore(db_path)
    try:
        with progress.stage("init_schema", output=db_path):
            store.init_schema()
        imports: dict[str, object] = {}
        if args.traces_json:
            with progress.stage("import_traces_json", input=args.traces_json, replace=args.replace):
                imports["traces"] = store.import_traces_json(args.traces_json, replace=args.replace).to_dict()
        if args.v1662_dir:
            with progress.stage("import_v16_6_2", input=args.v1662_dir):
                imports["v16_6_2"] = import_v16_6_2_elevated_false_dir(
                    args.v1662_dir, store, limit=args.limit
                )
        if args.v167_dir:
            with progress.stage("import_v16_7", input=args.v167_dir):
                imports["v16_7"] = import_v16_7_root_atlas_dir(args.v167_dir, store, limit=args.limit)
        payload = {"store_path": str(db_path), "imports": imports, "summary": store.summary()}
        if "traces" in imports and isinstance(imports["traces"], dict):
            payload = {**imports["traces"], **payload}
        if not args.summary_json and args.out_db:
            args.summary_json = str(Path(args.out_db).with_suffix(".summary.json"))
        if args.summary_json:
            with progress.stage("write_summary", output=args.summary_json):
                target = Path(args.summary_json)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

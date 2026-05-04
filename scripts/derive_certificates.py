#!/usr/bin/env python
"""Derive certificates by logical composition of verified lawbook traces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import DerivedCertificateGenerator, LawbookStore
from mathgraph.progress import ProgressLogger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--out-jsonl", default=None)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--import-to-store", action="store_true")
    parser.add_argument("--max-per-rule", type=int, default=None)
    parser.add_argument("--no-true-transitivity", action="store_true")
    parser.add_argument("--no-false-source-weakening", action="store_true")
    parser.add_argument("--no-false-target-strengthening", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger("derive_certificates", args.progress_jsonl, args.heartbeat_sec, args.progress, args.quiet)

    store = LawbookStore(args.store)
    try:
        with progress.stage("init_schema", store=args.store):
            store.init_schema()
        generator = DerivedCertificateGenerator(store)
        with progress.stage("derive_all"):
            certificates, stats = generator.derive_all(
                max_per_rule=args.max_per_rule,
                include_true_transitivity=not args.no_true_transitivity,
                include_false_source_weakening=not args.no_false_source_weakening,
                include_false_target_strengthening=not args.no_false_target_strengthening,
            )
        if args.out_jsonl:
            with progress.stage("write_jsonl", total=len(certificates), output=args.out_jsonl):
                generator.save_jsonl(certificates, args.out_jsonl)
        if args.out_json:
            with progress.stage("write_json", total=len(certificates), output=args.out_json):
                generator.save_json(certificates, args.out_json)
        imported = None
        if args.import_to_store:
            with progress.stage("import_to_store", total=len(certificates)):
                imported = store.import_derived_certificates(certificates).to_dict()
        payload = {
            "stats": stats.to_dict(),
            "certificate_count": len(certificates),
            "outputs": {
                "jsonl": args.out_jsonl,
                "json": args.out_json,
                "imported_to_store": bool(args.import_to_store),
            },
            "imported_stats": imported,
        }
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

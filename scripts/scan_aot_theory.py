#!/usr/bin/env python
"""Scan an AOT repository for advisory Isabelle theory declarations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.aot_scanner import scan_aot_repository  # noqa: E402
from mathgraph.lawbook_store import LawbookStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aot-dir", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--domain-kernel-id", default="aot")
    parser.add_argument("--formal-world-id", default="formal_world_aot_precedent")
    args = parser.parse_args(argv)

    result = scan_aot_repository(args.aot_dir)
    store = LawbookStore(args.db)
    try:
        for declaration in result.declarations:
            store.add_theory_declaration(
                declaration.to_theory_declaration(
                    domain_kernel_id=args.domain_kernel_id,
                    formal_world_id=args.formal_world_id,
                )
            )
        for method in result.proof_methods:
            store.add_proof_method(method)
        for rule in result.inference_rules:
            store.add_inference_rule(rule)
        summary = {
            **result.summary(),
            "db": str(args.db),
            "stored_declarations": len(result.declarations),
            "stored_proof_methods": len(result.proof_methods),
            "stored_inference_rules": len(result.inference_rules),
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

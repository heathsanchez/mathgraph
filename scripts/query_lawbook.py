#!/usr/bin/env python
"""Query the v16.8 persistent MathGraph LawbookStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--claim", nargs=2, metavar=("SOURCE_IDX", "TARGET_IDX"))
    parser.add_argument("--refutation", nargs=2, metavar=("SOURCE_IDX", "TARGET_IDX"))
    parser.add_argument("--source-idx")
    parser.add_argument("--target-idx")
    parser.add_argument("--top-roots", type=int)
    parser.add_argument("--top-reasons", type=int)
    parser.add_argument("--top-obstructions", type=int)
    parser.add_argument("--root")
    parser.add_argument("--reason")
    parser.add_argument("--obstruction")
    parser.add_argument("--domain-kernels", action="store_true")
    parser.add_argument("--domain-kernel")
    args = parser.parse_args(argv)
    store = LawbookStore(args.db)
    try:
        store.init_schema()
        if args.summary:
            payload = store.summary()
        elif args.claim:
            payload = store.query_claim(args.claim[0], args.claim[1])
        elif args.refutation:
            payload = store.query_refutation(args.refutation[0], args.refutation[1])
        elif args.source_idx is not None and args.target_idx is not None:
            payload = _query_explicit_pair(store, args.source_idx, args.target_idx)
        elif args.top_roots:
            payload = store.top_roots(args.top_roots)
        elif args.top_reasons:
            payload = store.top_reasons(args.top_reasons)
        elif args.top_obstructions:
            payload = store.top_obstructions(args.top_obstructions)
        elif args.root:
            payload = store.explain_root(args.root)
        elif args.reason:
            payload = store.explain_reason(args.reason)
        elif args.obstruction:
            payload = store.explain_obstruction(args.obstruction)
        elif args.domain_kernels:
            payload = store.list_domain_kernels()
        elif args.domain_kernel:
            payload = store.get_domain_kernel(args.domain_kernel)
        else:
            parser.error("provide a query option")
        print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


def _query_explicit_pair(store: LawbookStore, source_idx: str, target_idx: str) -> dict:
    refutation = store.query_refutation(source_idx, target_idx)
    claim = store.query_claim(source_idx, target_idx)
    refutation_hit = refutation is not None
    claim_hit = claim.get("status") == "hit"
    terminal = None
    trust = None
    provenance = None
    explanation = "No exact claim or refutation found."
    if refutation_hit:
        terminal = refutation.get("terminal_form")
        trust = refutation.get("trust_level")
        provenance = refutation.get("provenance_type")
        explanation = "Exact finite refutation found."
    elif claim_hit:
        terminal = claim.get("terminal_form")
        trust = claim.get("trust_level")
        provenance = claim.get("provenance_type")
        explanation = "Exact claim found."
    return {
        "status": "hit" if (refutation_hit or claim_hit) else "missing",
        "source_idx": str(source_idx),
        "target_idx": str(target_idx),
        "claim_hit": claim_hit,
        "refutation_hit": refutation_hit,
        "terminal_form": terminal or "NAMED_OBSTRUCTION",
        "trust_level": trust,
        "provenance_type": provenance,
        "explanation": explanation,
        "refutation": refutation,
    }


if __name__ == "__main__":
    raise SystemExit(main())

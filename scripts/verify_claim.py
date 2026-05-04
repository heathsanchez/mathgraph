#!/usr/bin/env python
"""Verify or safely obstruct one MathGraph source/target implication."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import MathGraphVerifier, VerifyConfig, VerifyRequest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-path", default=None)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--no-construction", action="store_true")
    args = parser.parse_args(argv)

    result = MathGraphVerifier(VerifyConfig(store_path=args.store_path)).verify(
        VerifyRequest(
            source=args.source,
            target=args.target,
            allow_construction=not args.no_construction,
            max_countermodel_order=args.max_countermodel_order,
        )
    )
    payload = result.to_dict()
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    compact = {
        "status": result.status,
        "terminal_form": result.terminal_form,
        "trust_level": result.trust_level,
        "certificate_id": result.certificate_id,
        "route": result.route,
        "explanation": result.explanation,
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    return 0 if result.status != "ERROR" else 1


if __name__ == "__main__":
    raise SystemExit(main())

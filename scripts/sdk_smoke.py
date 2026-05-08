#!/usr/bin/env python
"""Run a tiny MathGraphClient submit/query smoke."""

from __future__ import annotations

import argparse
import json
import sys

from mathgraph import MathGraphClient, MathGraphClientConfig


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--source-idx", type=int)
    parser.add_argument("--target-idx", type=int)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        client = MathGraphClient(
            MathGraphClientConfig(
                store_path=args.store,
                default_max_countermodel_order=args.max_countermodel_order,
            )
        )
        first = client.submit_claim(
            args.source,
            args.target,
            source_idx=args.source_idx,
            target_idx=args.target_idx,
            max_countermodel_order=args.max_countermodel_order,
        )
        print(first.to_json())
        second = client.query_claim(
            args.source,
            args.target,
            source_idx=args.source_idx,
            target_idx=args.target_idx,
        )
        print(
            json.dumps(
                {
                    "status": second.status,
                    "terminal_form": second.terminal_form,
                    "trust_level": second.trust_level,
                    "certificate_id": second.certificate_id,
                },
                sort_keys=True,
            )
        )
    except Exception as exc:
        print(json.dumps({"status": "fatal_error", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    if first.status in {"REFUTED", "VERIFIED_FALSE", "KNOWN_CERTIFICATE_FOUND"} and first.terminal_form == "REFUTATION_CERTIFICATE":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

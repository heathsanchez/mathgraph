#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.mathlib_digest import run_mathlib_digest_accumulator


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mathlib-root")
    p.add_argument("--lawbook", required=True)
    p.add_argument("--pack-config", required=True)
    p.add_argument("--out-base", required=True)
    p.add_argument("--allow-live-lean", action="store_true")
    p.add_argument("--verify-constructors", action="store_true")
    p.add_argument("--timeout-sec", type=float, default=90.0)
    p.add_argument("--print-json", action="store_true")
    a = p.parse_args(argv)
    result = run_mathlib_digest_accumulator(
        lawbook=a.lawbook,
        pack_config=a.pack_config,
        out_base=a.out_base,
        mathlib_root=a.mathlib_root,
        allow_live_lean=a.allow_live_lean,
        verify_constructors=a.verify_constructors,
        timeout_sec=a.timeout_sec,
    )
    if a.print_json:
        print(json.dumps(result, sort_keys=True, default=str))
    else:
        s = result["summary"]
        print("MathGraph Mathlib Digest Accumulator")
        print(f"run_id: {result['run_id']}")
        print(f"run_dir: {result['run_dir']}")
        print(f"targets: {s['target_count']}")
        print(f"accepted_targets: {s['accepted_target_count']}")
        print(f"roots: {s['root_count']}")
        print(f"reasons: {s['reason_count']}")
        print(f"constructor_attempts: {s['constructor_attempt_count']}")
        print(f"verified_constructors: {s['verified_constructor_count']}")
        print(f"obstructions: {s['obstruction_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

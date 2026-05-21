#!/usr/bin/env python
"""Run a small deterministic root-operator induction smoke test."""

from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.arc_root_operator_demo import run_arc_root_operator_demo  # noqa: E402


def main() -> int:
    out_dir = Path("/tmp/mathgraph_root_operator_induction_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "root_operator_induction_smoke.json"
    summary = run_arc_root_operator_demo(out_path)
    print("MathGraph Root Operator Induction Smoke")
    for key in (
        "overall",
        "base_solve_rate",
        "literal_solve_rate",
        "root_schema_solve_rate",
        "oracle_solve_rate",
        "oracle_fraction_captured",
        "raw_schema_count",
        "promoted_schema_count",
    ):
        print(f"{key}: {summary.get(key)}")
    print(f"output: {out_path}")
    print(json.dumps({key: summary.get(key) for key in ("overall", "promoted_schema_count", "root_schema_solve_rate")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

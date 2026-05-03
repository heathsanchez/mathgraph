#!/usr/bin/env python
"""Run the end-to-end MathGraph finite-countermodel chewing smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import ChewingSmokeConfig, run_chewing_smoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--equations-path", required=True)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--traces-json", default=None)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-frontier-pairs", type=int, default=50)
    parser.add_argument("--top-k-schedule", type=int, default=25)
    parser.add_argument("--max-tasks", type=int, default=25)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--no-require-imported-countermodel", action="store_true")
    parser.add_argument("--no-rebuild-derived-after-import", action="store_true")
    args = parser.parse_args(argv)

    result = run_chewing_smoke(
        ChewingSmokeConfig(
            equations_path=args.equations_path,
            matrix_path=args.matrix_path,
            traces_json=args.traces_json,
            out_dir=args.out_dir,
            max_frontier_pairs=args.max_frontier_pairs,
            top_k_schedule=args.top_k_schedule,
            max_tasks=args.max_tasks,
            max_countermodel_order=args.max_countermodel_order,
            random_seed=args.random_seed,
            require_imported_countermodel=not args.no_require_imported_countermodel,
            rebuild_derived_after_import=not args.no_rebuild_derived_after_import,
        )
    )
    payload = {
        "ok": result.ok,
        "report_path": result.paths.get("report_json"),
        "store_path": result.paths.get("store"),
        "primitive_count": result.summary.get("lawbook_primitive_count_after_import"),
        "derived_count": result.summary.get("derived_count_after_import"),
        "outcome_row_count": result.summary.get("outcome_row_count_after_import"),
        "schedule_count": result.summary.get("scheduled_count"),
        "warnings": result.warnings,
        "summary": result.summary,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

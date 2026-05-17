#!/usr/bin/env python
"""Run a Certificate Processing and Assimilation Pipeline episode."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
import sys
from pathlib import Path

from mathgraph.certificate_assimilation import (  # noqa: E402
    CertificateAssimilationConfig,
    run_certificate_assimilation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--equations-path", required=True)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--frontier-mode", choices=["small_sample", "matrix_false", "structural"], default="small_sample")
    parser.add_argument("--frontier-scan-limit", type=int, default=500)
    parser.add_argument("--max-frontier-pairs", type=int, default=100)
    parser.add_argument("--top-k-schedule", type=int, default=50)
    parser.add_argument("--max-tasks", type=int, default=50)
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    parser.add_argument("--progress", action="store_true", default=True)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--replace", action="store_true", default=True)
    parser.add_argument("--no-replace", dest="replace", action="store_false")
    parser.add_argument("--import-derived-to-store", action="store_true")
    parser.add_argument("--max-derived-per-rule", type=int, default=None)
    parser.add_argument("--no-oracle-probe", dest="run_oracle_probe", action="store_false", default=True)
    parser.add_argument("--allow-synthetic-fallback", action="store_true")
    args = parser.parse_args(argv)

    result = run_certificate_assimilation(
        CertificateAssimilationConfig(
            traces_json=args.traces_json,
            equations_path=args.equations_path,
            matrix_path=args.matrix_path,
            out_dir=args.out_dir,
            frontier_mode=args.frontier_mode,
            frontier_scan_limit=args.frontier_scan_limit,
            max_frontier_pairs=args.max_frontier_pairs,
            top_k_schedule=args.top_k_schedule,
            max_tasks=args.max_tasks,
            max_countermodel_order=args.max_countermodel_order,
            heartbeat_sec=args.heartbeat_sec,
            progress=bool(args.progress and not args.quiet),
            progress_jsonl=args.progress_jsonl,
            replace=args.replace,
            import_derived_to_store=args.import_derived_to_store,
            max_derived_per_rule=args.max_derived_per_rule,
            run_oracle_probe=args.run_oracle_probe,
            allow_synthetic_fallback=args.allow_synthetic_fallback,
        )
    )
    print(json.dumps(result.summary.to_dict(), indent=2, sort_keys=True))
    return 0 if result.summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

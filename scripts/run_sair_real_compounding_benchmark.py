#!/usr/bin/env python3
"""Run the Real SAIR Compounding Benchmark v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mathgraph.sair_real_compounding_benchmark import run_sair_real_compounding_benchmark


def _parse_seeds(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def _default_out_dir() -> Path:
    drive = Path("/content/drive/MyDrive/SAIR_MathGraph/real_compounding_benchmark_v0")
    if drive.parent.exists():
        return drive
    return Path("/content/sair_real_compounding_benchmark_v0")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations-path", default="/content/equations.txt")
    parser.add_argument("--matrix-path", default="/content/etp_matrix_full_best_bool.npy")
    parser.add_argument("--out-dir", default=str(_default_out_dir()))
    parser.add_argument("--train-size", type=int, default=250)
    parser.add_argument("--heldout-size", type=int, default=250)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--max-attempts-per-mode", type=int, default=250)
    fallback = parser.add_mutually_exclusive_group()
    fallback.add_argument("--fallback-if-missing", dest="fallback_if_missing", action="store_true", default=True)
    fallback.add_argument("--no-fallback-if-missing", dest="fallback_if_missing", action="store_false")
    args = parser.parse_args()
    report = run_sair_real_compounding_benchmark(
        equations_path=args.equations_path,
        matrix_path=args.matrix_path,
        out_dir=args.out_dir,
        train_size=args.train_size,
        heldout_size=args.heldout_size,
        seeds=_parse_seeds(args.seeds),
        max_attempts_per_mode=args.max_attempts_per_mode,
        fallback_if_missing=args.fallback_if_missing,
    )
    printable = {
        "real_sair_used": report.real_sair_used,
        "fallback_mode": report.fallback_mode,
        "best_mode": report.aggregate_metrics.get("best_mode"),
        "mean_delta_vs_baseline": report.aggregate_metrics.get("mean_delta_vs_baseline"),
        "mean_delta_vs_persistent_atlas": report.aggregate_metrics.get("mean_delta_vs_persistent_atlas"),
        "compounding_signal_detected": report.aggregate_metrics.get("compounding_signal_detected"),
        "advisory_boundary_preserved": report.advisory_boundary_preserved,
        "outputs": report.outputs,
        "message": report.message,
    }
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


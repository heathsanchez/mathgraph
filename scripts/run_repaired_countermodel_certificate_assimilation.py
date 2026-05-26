#!/usr/bin/env python
"""Assimilate source-law repaired recoveries into countermodel certificates."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from mathgraph.repaired_countermodel_certificates import (
    build_repaired_countermodel_certificates,
    deduplicate_repaired_certificates,
    summarize_repaired_certificate_families,
    validate_repaired_certificate_boundary,
    write_repaired_certificate_lawbook,
)


@dataclass(frozen=True)
class RepairedCertificateCliConfig:
    input_dir: str | None
    equations: str | None
    out_dir: str
    source_mode: str | None = None
    fallback_demo: bool = False
    seed: int = 1729


def run_repaired_countermodel_certificate_assimilation(config: RepairedCertificateCliConfig) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    input_dir = Path(config.input_dir) if config.input_dir else out_dir / "_fallback_source_repair"
    if config.fallback_demo:
        _write_fallback_repair_outputs(input_dir)
    equations = _load_equations(config.equations)
    certificates, rejected = build_repaired_countermodel_certificates(
        input_dir,
        equations=equations,
        source_mode=config.source_mode or ("fallback_demo" if config.fallback_demo else None),
    )
    unique, duplicates = deduplicate_repaired_certificates(certificates)
    family_summary = summarize_repaired_certificate_families(unique)
    artifacts = write_repaired_certificate_lawbook(
        unique,
        rejected,
        family_summary,
        out_dir,
        manifest_metadata={"source_mode": config.source_mode or ("fallback_demo" if config.fallback_demo else ""), "input_dir": str(input_dir)},
    )
    boundary = validate_repaired_certificate_boundary(unique, rejected)
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        "source_mode": config.source_mode or ("fallback_demo" if config.fallback_demo else ""),
        "certificate_count": int(len(unique)),
        "rejected_count": int(len(rejected)),
        "duplicate_count": int(len(duplicates)),
        "unique_pair_count": int(unique["pair_id"].nunique()) if not unique.empty and "pair_id" in unique else 0,
        "unique_table_count": int(unique["table_hash"].nunique()) if not unique.empty and "table_hash" in unique else 0,
        "family_count": int(unique["source_family"].nunique()) if not unique.empty and "source_family" in unique else 0,
        "repair_strategy_count": int(unique["repair_strategy"].nunique()) if not unique.empty and "repair_strategy" in unique else 0,
        "finite_verified_count": int(len(unique)),
        "advisory_rejected_count": int(len(rejected)),
        "breakthrough_certificate_count": int(len(unique)),
        "safety_true_contamination_count": int(boundary["safety_true_contamination_count"]),
        "safety_advisory_promotion_count": int(boundary["safety_advisory_promotion_count"]),
        "safety_failed_search_true_count": int(boundary["safety_failed_search_true_count"]),
        "benchmark_passed": bool(len(unique) > 0 and boundary["boundary_preserved"]),
        "artifacts": artifacts,
    }
    (out_dir / "repaired_countermodel_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _write_fallback_repair_outputs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    table = [[0, 0], [1, 1]]
    rows = [
        {
            "repair_id": "repair:fallback:0:pressure_descent",
            "pair_id": "fallback:0",
            "constructor_id": "fallback:right_projection_bad:0",
            "family": "projection_completion_right",
            "n": 2,
            "source_equation": "(x * y) = x",
            "target_equation": "x = y",
            "original_table_hash": "bad",
            "repaired_table_hash": "left-projection",
            "repaired_table": table,
            "eq1_holds": True,
            "eq2_violated": True,
            "recovered": True,
            "finite_checked": True,
            "witness": {"x": 0, "y": 1},
            "trace": {
                "repair_id": "repair:fallback:0:pressure_descent",
                "started_source_violations": 2,
                "final_source_violations": 0,
                "target_violation_preserved": True,
                "completed": True,
                "recovered": True,
            },
            "terminal_form": "FINITE_COUNTERMODEL",
            "advisory_only": False,
            "can_promote_truth": True,
        },
        {
            "repair_id": "repair:fallback:1:pressure_descent",
            "pair_id": "fallback:1",
            "constructor_id": "fallback:bad:1",
            "family": "projection_completion_right",
            "n": 2,
            "source_equation": "(x * y) = x",
            "target_equation": "x = y",
            "original_table_hash": "bad",
            "repaired_table_hash": "bad",
            "repaired_table": [[0, 1], [0, 1]],
            "eq1_holds": False,
            "eq2_violated": True,
            "recovered": False,
            "finite_checked": True,
            "witness": {"x": 0, "y": 1},
            "trace": {
                "repair_id": "repair:fallback:1:pressure_descent",
                "started_source_violations": 2,
                "final_source_violations": 2,
                "target_violation_preserved": True,
                "completed": False,
                "recovered": False,
            },
            "terminal_form": "NONE",
            "advisory_only": True,
            "can_promote_truth": False,
        },
    ]
    pd.DataFrame(rows).to_csv(root / "source_law_repair_results.csv", index=False)
    pd.DataFrame([row["trace"] for row in rows]).to_csv(root / "source_law_repair_traces.csv", index=False)
    pd.DataFrame([{"pair_id": "fallback:0", "source_eq_idx": 0, "target_eq_idx": 1, "microbasin_key": "fallback", "basin": "fallback", "deep_ir_candidate": "repair"}]).to_csv(root / "residual_conditioned_pair_specs.csv", index=False)


def _load_equations(path: str | None) -> list[str]:
    if not path:
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args(argv: Sequence[str] | None = None) -> RepairedCertificateCliConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir")
    parser.add_argument("--equations")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--source-mode")
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args(argv)
    return RepairedCertificateCliConfig(args.input_dir, args.equations, args.out_dir, args.source_mode, args.fallback_demo, args.seed)


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_repaired_countermodel_certificate_assimilation(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

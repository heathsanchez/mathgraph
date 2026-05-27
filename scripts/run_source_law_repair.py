#!/usr/bin/env python
"""Run bounded source-law repair over residual-conditioned constructors."""

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

from mathgraph.persistent_exact_microbasin_lawbook import write_persistent_lawbook_sqlite
from mathgraph.repaired_countermodel_certificates import (
    build_repaired_countermodel_certificates,
    deduplicate_repaired_certificates,
    summarize_repaired_certificate_families,
    write_repaired_certificate_lawbook,
)
from mathgraph.source_law_repair import repair_conditioned_constructors, summarize_source_law_repair


@dataclass(frozen=True)
class SourceLawRepairCliConfig:
    input_dir: str | None
    out_dir: str
    repair_strategies: list[str]
    repair_max_steps: int = 10000
    repair_max_violations: int = 128
    seed: int = 20260524
    fallback_demo: bool = False
    assimilate_certificates: bool = False


def run_source_law_repair_cli(config: SourceLawRepairCliConfig) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    constructors = _fallback_constructors() if config.fallback_demo else _load_constructors(config.input_dir)
    results, traces = repair_conditioned_constructors(
        constructors,
        max_steps=config.repair_max_steps,
        max_violations=config.repair_max_violations,
        strategies=config.repair_strategies,
        seed=config.seed,
    )
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        "source_mode": "fallback_demo" if config.fallback_demo else "artifact_conditioned",
        **summarize_source_law_repair(results, traces),
    }
    summary["benchmark_passed"] = (
        summary["source_law_repair_attempt_count"] > 0
        and summary["true_contamination_count"] == 0
        and summary["terminal_claims_from_advisory_count"] == 0
        and summary["failed_search_promoted_true_count"] == 0
    )
    artifacts = {
        "source_law_repair_results.csv": out_dir / "source_law_repair_results.csv",
        "source_law_repair_traces.csv": out_dir / "source_law_repair_traces.csv",
        "source_law_repair_summary.json": out_dir / "source_law_repair_summary.json",
        "source_law_repair_report.md": out_dir / "source_law_repair_report.md",
        "source_law_repair.sqlite": out_dir / "source_law_repair.sqlite",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
    }
    _write_csv(artifacts["source_law_repair_results.csv"], results)
    _write_csv(artifacts["source_law_repair_traces.csv"], traces)
    write_persistent_lawbook_sqlite(
        artifacts["source_law_repair.sqlite"],
        {"repair_results": results, "repair_traces": traces, "summary": pd.DataFrame([summary])},
    )
    artifacts["source_law_repair_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["source_law_repair_report.md"].write_text(_report(summary), encoding="utf-8")
    artifacts["artifact_manifest.json"].write_text(
        json.dumps([{"artifact_name": name, "path": str(path), "exists": path.exists()} for name, path in artifacts.items() if name != "artifact_manifest.json"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if config.assimilate_certificates:
        cert_dir = out_dir / "repaired_countermodel_certificates"
        certs, rejected = build_repaired_countermodel_certificates(out_dir, source_mode=summary["source_mode"])
        unique, duplicates = deduplicate_repaired_certificates(certs)
        family_summary = summarize_repaired_certificate_families(unique)
        cert_artifacts = write_repaired_certificate_lawbook(
            unique,
            rejected,
            family_summary,
            cert_dir,
            manifest_metadata={"source_mode": summary["source_mode"], "input_dir": str(out_dir)},
        )
        summary.update(
            {
                "certificate_assimilation_enabled": True,
                "repaired_certificate_count": int(len(unique)),
                "repaired_certificate_unique_pair_count": int(unique["pair_id"].nunique()) if not unique.empty and "pair_id" in unique else 0,
                "repaired_certificate_lawbook": cert_artifacts["repaired_countermodel_lawbook.sqlite"],
                "repaired_certificate_manifest": cert_artifacts["repaired_countermodel_manifest.json"],
                "breakthrough_certificate_count": int(len(unique)),
                "repaired_certificate_duplicate_count": int(len(duplicates)),
            }
        )
        artifacts["source_law_repair_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    else:
        summary["certificate_assimilation_enabled"] = False
    return summary | {"artifacts": {name: str(path) for name, path in artifacts.items()}}


def _fallback_constructors() -> pd.DataFrame:
    rows = []
    table = [[0, 1], [0, 1]]
    for idx in range(5):
        rows.append(
            {
                "pair_id": f"fallback:{idx}",
                "constructor_id": f"fallback:right_projection_bad:{idx}",
                "family": "projection_completion_right",
                "n": 2,
                "table": table,
                "source_equation": "(x * y) = x",
                "target_equation": "x = y",
            }
        )
    return pd.DataFrame(rows)


def _load_constructors(input_dir: str | None) -> pd.DataFrame:
    if not input_dir:
        raise ValueError("--input-dir is required unless --fallback-demo is used")
    path = Path(input_dir) / "residual_conditioned_constructors.csv"
    if not path.exists():
        raise ValueError(f"missing residual-conditioned constructors: {path}")
    return pd.read_csv(path)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty and len(frame.columns) == 0:
        pd.DataFrame([{"empty": True}]).to_csv(path, index=False)
    else:
        safe = frame.copy()
        for col in safe.columns:
            safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value)
        safe.to_csv(path, index=False)


def _report(summary: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Source-Law Repair v1",
            "",
            f"- source_law_repair_attempt_count: {summary['source_law_repair_attempt_count']}",
            f"- source_law_repair_completed_count: {summary['source_law_repair_completed_count']}",
            f"- source_law_repair_recovered_pairs: {summary['source_law_repair_recovered_pairs']}",
            f"- source_law_repair_best_strategy: {summary['source_law_repair_best_strategy']}",
            "",
            "Repair traces are advisory. Only finite-checked source-holds/target-violates tables count as recoveries.",
            "",
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> SourceLawRepairCliConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--repair-strategies", default="pressure_descent,target_frozen_pressure_descent,diagonal_first_repair,row_col_repair,quotient_merge_repair,two_phase_repair")
    parser.add_argument("--repair-max-steps", type=int, default=10000)
    parser.add_argument("--repair-max-violations", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--assimilate-certificates", action="store_true")
    args = parser.parse_args(argv)
    return SourceLawRepairCliConfig(
        input_dir=args.input_dir,
        out_dir=args.out_dir,
        repair_strategies=[item for item in args.repair_strategies.split(",") if item],
        repair_max_steps=args.repair_max_steps,
        repair_max_violations=args.repair_max_violations,
        seed=args.seed,
        fallback_demo=args.fallback_demo,
        assimilate_certificates=args.assimilate_certificates,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_source_law_repair_cli(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

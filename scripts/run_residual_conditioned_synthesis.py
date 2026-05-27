#!/usr/bin/env python
"""Run residual-conditioned constructor synthesis."""

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
from mathgraph.residual_conditioned_synthesis import (
    evaluate_residual_conditioned_constructors,
    summarize_residual_conditioned_synthesis,
    synthesize_for_residual_pairs,
)
from mathgraph.source_law_repair import repair_conditioned_constructors, summarize_source_law_repair


@dataclass(frozen=True)
class ResidualConditionedCliConfig:
    equations: str | None
    input_dir: str | None
    out_dir: str
    max_n: int = 4
    max_pairs: int = 100
    max_witnesses_per_pair: int = 8
    max_attempts_per_pair: int = 32
    max_steps: int = 5000
    seed: int = 20260524
    fallback_demo: bool = False
    enable_source_law_repair: bool = False
    repair_strategies: list[str] | None = None
    repair_max_steps: int = 10000
    repair_max_violations: int = 128


def run_residual_conditioned_synthesis(config: ResidualConditionedCliConfig) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    residual_pairs, equations = _load_inputs(config)
    specs, attempts, constructors = synthesize_for_residual_pairs(
        residual_pairs,
        equations,
        max_n=config.max_n,
        max_pairs=config.max_pairs,
        max_witnesses_per_pair=config.max_witnesses_per_pair,
        max_attempts_per_pair=config.max_attempts_per_pair,
        max_steps=config.max_steps,
        seed=config.seed,
    )
    recoveries = evaluate_residual_conditioned_constructors(constructors, equations)
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        "source_mode": "fallback_demo" if config.fallback_demo else "artifact_conditioned",
        **summarize_residual_conditioned_synthesis(specs, attempts, constructors, recoveries),
    }
    repair_results = pd.DataFrame()
    repair_traces = pd.DataFrame()
    if config.enable_source_law_repair:
        repair_results, repair_traces = repair_conditioned_constructors(
            constructors,
            max_steps=config.repair_max_steps,
            max_violations=config.repair_max_violations,
            strategies=config.repair_strategies,
            seed=config.seed,
        )
        repair_summary = summarize_source_law_repair(repair_results, repair_traces)
        summary.update(repair_summary)
        summary["source_law_repair_breakthrough_candidate"] = bool(summary["source_law_repair_recovered_pairs"] > 0 and summary["source_mode"] != "fallback_demo")
        summary["conditioned_plus_repair_recovered_pairs"] = int(summary["residual_conditioned_recovered_pairs"]) + int(summary["source_law_repair_recovered_pairs"])
        summary["total_breakthrough_candidate"] = bool(summary["source_law_repair_breakthrough_candidate"])
    else:
        summary.update(
            {
                "source_law_repair_enabled": False,
                "source_law_repair_attempt_count": 0,
                "source_law_repair_completed_count": 0,
                "source_law_repair_recovered_pairs": 0,
                "source_law_repair_best_strategy": "",
                "source_law_repair_breakthrough_candidate": False,
                "conditioned_plus_repair_recovered_pairs": int(summary["residual_conditioned_recovered_pairs"]),
                "total_breakthrough_candidate": False,
            }
        )
    summary["benchmark_passed"] = (
        summary["residual_conditioned_pair_count"] > 0
        and summary["residual_conditioned_attempt_count"] > 0
        and summary["residual_conditioned_constructor_count"] > 0
        and summary["true_contamination_count"] == 0
        and summary["terminal_claims_from_advisory_count"] == 0
    )
    artifacts = {
        "residual_conditioned_pair_specs.csv": out_dir / "residual_conditioned_pair_specs.csv",
        "residual_conditioned_attempts.csv": out_dir / "residual_conditioned_attempts.csv",
        "residual_conditioned_constructors.csv": out_dir / "residual_conditioned_constructors.csv",
        "residual_conditioned_recoveries.csv": out_dir / "residual_conditioned_recoveries.csv",
        "residual_conditioned_summary.json": out_dir / "residual_conditioned_summary.json",
        "residual_conditioned_report.md": out_dir / "residual_conditioned_report.md",
        "residual_conditioned.sqlite": out_dir / "residual_conditioned.sqlite",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
    }
    if config.enable_source_law_repair:
        artifacts["source_law_repair_results.csv"] = out_dir / "source_law_repair_results.csv"
        artifacts["source_law_repair_traces.csv"] = out_dir / "source_law_repair_traces.csv"
        artifacts["source_law_repair_summary.json"] = out_dir / "source_law_repair_summary.json"
    _write_csv(artifacts["residual_conditioned_pair_specs.csv"], specs)
    _write_csv(artifacts["residual_conditioned_attempts.csv"], attempts)
    _write_csv(artifacts["residual_conditioned_constructors.csv"], constructors)
    _write_csv(artifacts["residual_conditioned_recoveries.csv"], recoveries)
    if config.enable_source_law_repair:
        _write_csv(artifacts["source_law_repair_results.csv"], repair_results)
        _write_csv(artifacts["source_law_repair_traces.csv"], repair_traces)
        artifacts["source_law_repair_summary.json"].write_text(json.dumps({k: summary[k] for k in summary if k.startswith("source_law_repair") or k in {"conditioned_plus_repair_recovered_pairs", "total_breakthrough_candidate"}}, indent=2, sort_keys=True), encoding="utf-8")
    write_persistent_lawbook_sqlite(
        artifacts["residual_conditioned.sqlite"],
        {
            "pair_specs": specs,
            "attempts": attempts,
            "constructors": constructors,
            "recoveries": recoveries,
            "source_law_repair_results": repair_results,
            "source_law_repair_traces": repair_traces,
            "summary": pd.DataFrame([summary]),
        },
    )
    artifacts["residual_conditioned_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["residual_conditioned_report.md"].write_text(_report(summary), encoding="utf-8")
    artifacts["artifact_manifest.json"].write_text(
        json.dumps([{"artifact_name": name, "path": str(path), "exists": path.exists()} for name, path in artifacts.items() if name != "artifact_manifest.json"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary | {"artifacts": {name: str(path) for name, path in artifacts.items()}}


def _load_inputs(config: ResidualConditionedCliConfig) -> tuple[pd.DataFrame, list[str]]:
    if config.fallback_demo:
        return _fallback_pairs(), _fallback_equations()
    if not config.input_dir:
        raise ValueError("--input-dir is required unless --fallback-demo is used")
    root = Path(config.input_dir)
    pairs = _read_first(root, ("heldout_pair_features.csv", "residual_pairs.csv", "residual_conditioned_pair_specs.csv", "synthesized_recoveries.csv"))
    equations = [line.strip() for line in Path(config.equations).read_text(encoding="utf-8").splitlines() if line.strip()] if config.equations else []
    return pairs, equations


def _fallback_pairs() -> pd.DataFrame:
    rows = []
    for idx in range(8):
        rows.append(
            {
                "pair_idx": idx,
                "source_eq_idx": 0,
                "target_eq_idx": 1 if idx % 2 == 0 else 2,
                "basin": "fallback_residual",
                "deep_ir_candidate": "conditioned",
                "microbasin_key": f"fallback_{idx % 3}",
                "recommended_family": "projection_completion_left",
            }
        )
    return pd.DataFrame(rows)


def _fallback_equations() -> list[str]:
    return ["x = x", "x = y", "(x * y) = x"]


def _read_first(root: Path, names: tuple[str, ...]) -> pd.DataFrame:
    for name in names:
        path = root / name
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


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
            "# Residual-Conditioned Constructor Synthesis",
            "",
            f"- residual_conditioned_pair_count: {summary['residual_conditioned_pair_count']}",
            f"- residual_conditioned_attempt_count: {summary['residual_conditioned_attempt_count']}",
            f"- residual_conditioned_constructor_count: {summary['residual_conditioned_constructor_count']}",
            f"- residual_conditioned_recovered_pairs: {summary['residual_conditioned_recovered_pairs']}",
            "",
            "Failed completion is residual evidence only. Checked recoveries require source holds and target violates.",
            "",
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> ResidualConditionedCliConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--input-dir")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--max-pairs", type=int, default=100)
    parser.add_argument("--max-witnesses-per-pair", type=int, default=8)
    parser.add_argument("--max-attempts-per-pair", type=int, default=32)
    parser.add_argument("--max-steps", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--fallback-demo", action="store_true")
    parser.add_argument("--enable-source-law-repair", action="store_true")
    parser.add_argument("--repair-strategies", default="pressure_descent,target_frozen_pressure_descent,diagonal_first_repair,row_col_repair,quotient_merge_repair,two_phase_repair")
    parser.add_argument("--repair-max-steps", type=int, default=10000)
    parser.add_argument("--repair-max-violations", type=int, default=128)
    args = parser.parse_args(argv)
    return ResidualConditionedCliConfig(
        equations=args.equations,
        input_dir=args.input_dir,
        out_dir=args.out_dir,
        max_n=args.max_n,
        max_pairs=args.max_pairs,
        max_witnesses_per_pair=args.max_witnesses_per_pair,
        max_attempts_per_pair=args.max_attempts_per_pair,
        max_steps=args.max_steps,
        seed=args.seed,
        fallback_demo=args.fallback_demo,
        enable_source_law_repair=args.enable_source_law_repair,
        repair_strategies=[item for item in args.repair_strategies.split(",") if item],
        repair_max_steps=args.repair_max_steps,
        repair_max_violations=args.repair_max_violations,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_residual_conditioned_synthesis(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

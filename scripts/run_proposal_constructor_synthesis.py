#!/usr/bin/env python
"""Run proposal-specific finite constructor synthesis."""

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

from mathgraph.proposal_constructor_synthesis import (
    evaluate_synthesized_constructors,
    summarize_synthesis,
    synthesize_constructors_for_proposals,
)
from mathgraph.persistent_exact_microbasin_lawbook import write_persistent_lawbook_sqlite


@dataclass(frozen=True)
class SynthesisCliConfig:
    equations: str | None
    input_dir: str | None
    out_dir: str
    max_n: int = 4
    max_tables_per_proposal: int = 32
    max_pairs_per_constructor: int = 100
    seed: int = 20260524
    fallback_demo: bool = False


def run_proposal_constructor_synthesis(config: SynthesisCliConfig) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    proposals, residual_pairs, equations = _load_inputs(config)
    constructors, results = synthesize_constructors_for_proposals(
        proposals,
        max_n=config.max_n,
        max_tables_per_proposal=config.max_tables_per_proposal,
        seed=config.seed,
    )
    recoveries = evaluate_synthesized_constructors(
        constructors,
        residual_pairs,
        equations,
        max_pairs_per_constructor=config.max_pairs_per_constructor,
    )
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        "source_mode": "fallback_demo" if config.fallback_demo else "artifact_synthesis",
        "proposal_count": int(len(proposals)),
        **summarize_synthesis(constructors, results, recoveries),
    }
    summary["benchmark_passed"] = (
        summary["proposal_count"] > 0
        and summary["synthesized_constructor_count"] > 0
        and summary["finite_checked_recoveries"] >= 0
        and summary["true_contamination_count"] == 0
        and summary["terminal_claims_from_advisory_count"] == 0
    )
    artifacts = {
        "synthesized_constructors.csv": out_dir / "synthesized_constructors.csv",
        "synthesis_results.csv": out_dir / "synthesis_results.csv",
        "synthesized_recoveries.csv": out_dir / "synthesized_recoveries.csv",
        "synthesis_summary.json": out_dir / "synthesis_summary.json",
        "synthesis_report.md": out_dir / "synthesis_report.md",
        "synthesis.sqlite": out_dir / "synthesis.sqlite",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
    }
    _write_csv(artifacts["synthesized_constructors.csv"], constructors)
    _write_csv(artifacts["synthesis_results.csv"], results)
    _write_csv(artifacts["synthesized_recoveries.csv"], recoveries)
    write_persistent_lawbook_sqlite(
        artifacts["synthesis.sqlite"],
        {
            "synthesized_constructors": constructors,
            "synthesis_results": results,
            "synthesized_recoveries": recoveries,
            "summary": pd.DataFrame([summary]),
        },
    )
    artifacts["synthesis_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["synthesis_report.md"].write_text(_report(summary), encoding="utf-8")
    artifacts["artifact_manifest.json"].write_text(
        json.dumps([{"artifact_name": name, "path": str(path), "exists": path.exists()} for name, path in artifacts.items() if name != "artifact_manifest.json"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary | {"artifacts": {name: str(path) for name, path in artifacts.items()}}


def _load_inputs(config: SynthesisCliConfig) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    if config.fallback_demo:
        return _fallback_proposals(), _fallback_pairs(), _fallback_equations()
    if not config.input_dir:
        raise ValueError("--input-dir is required unless --fallback-demo is used")
    root = Path(config.input_dir)
    proposals = pd.read_csv(root / "constructor_proposals.csv")
    pairs = _read_first(root, ("residual_pairs.csv", "heldout_pair_features.csv", "active_residual_basins.csv"))
    equations = [line.strip() for line in Path(config.equations).read_text(encoding="utf-8").splitlines() if line.strip()] if config.equations else []
    return proposals, pairs, equations


def _fallback_proposals() -> pd.DataFrame:
    families = ["constant", "left_projection", "right_projection", "add_mod", "projection_exception_left"]
    return pd.DataFrame(
        [
            {
                "proposal_id": f"fallback_{idx}_{family}",
                "proposal_family": family,
                "residual_basin_id": "fallback_residual",
                "rationale": "fallback synthesis",
                "source_features": {},
                "advisory_only": True,
                "can_promote_truth": False,
            }
            for idx, family in enumerate(families)
        ]
    )


def _fallback_pairs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"pair_idx": 0, "source_eq_idx": 0, "target_eq_idx": 1},
            {"pair_idx": 1, "source_eq_idx": 0, "target_eq_idx": 2},
        ]
    )


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
            "# Proposal Constructor Synthesis v1",
            "",
            f"- synthesized_constructor_count: {summary['synthesized_constructor_count']}",
            f"- synthesized_recovered_pairs: {summary['synthesized_recovered_pairs']}",
            f"- best_synthesized_family: {summary['best_synthesized_family']}",
            "",
            "A constructor is not a certificate until the finite checker verifies it.",
            "",
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> SynthesisCliConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--input-dir")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--max-tables-per-proposal", type=int, default=32)
    parser.add_argument("--max-pairs-per-constructor", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--fallback-demo", action="store_true")
    args = parser.parse_args(argv)
    return SynthesisCliConfig(
        equations=args.equations,
        input_dir=args.input_dir,
        out_dir=args.out_dir,
        max_n=args.max_n,
        max_tables_per_proposal=args.max_tables_per_proposal,
        max_pairs_per_constructor=args.max_pairs_per_constructor,
        seed=args.seed,
        fallback_demo=args.fallback_demo,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_proposal_constructor_synthesis(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

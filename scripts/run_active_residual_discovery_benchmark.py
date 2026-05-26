#!/usr/bin/env python
"""Run Active Residual Constructor Discovery v1."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from mathgraph.active_residual_discovery import (
    build_residual_basins,
    evaluate_constructor_proposals,
    load_discovery_inputs,
    propose_constructor_recipes,
    summarize_active_discovery,
)
from mathgraph.persistent_exact_microbasin_lawbook import write_persistent_lawbook_sqlite


@dataclass(frozen=True)
class ActiveResidualDiscoveryConfig:
    equations: str | None
    matrix: str | None
    input_dir: str | None
    out_dir: str
    min_support: int = 3
    max_proposals_per_basin: int = 3
    max_pairs_per_proposal: int = 100
    max_n: int = 4
    seed: int = 20260524
    fallback_demo: bool = False


def run_active_residual_discovery_benchmark(config: ActiveResidualDiscoveryConfig) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if config.fallback_demo:
        inputs = _fallback_inputs(config.seed)
        source_mode = "fallback_demo"
        real_corpus_used = False
    else:
        if not config.input_dir:
            raise ValueError("--input-dir is required unless --fallback-demo is used")
        inputs = load_discovery_inputs(Path(config.input_dir))
        source_mode = "real_etp" if config.equations and config.matrix else "artifact_proxy"
        real_corpus_used = bool(config.equations and config.matrix and Path(config.equations).exists() and Path(config.matrix).exists())
    equations = _load_equations(config.equations) if config.equations and Path(config.equations).exists() else None
    residual_basins = build_residual_basins(inputs["pair_features"], inputs["recovery_eval"], min_support=config.min_support)
    proposals = propose_constructor_recipes(residual_basins, max_proposals_per_basin=config.max_proposals_per_basin)
    evaluations = evaluate_constructor_proposals(
        proposals,
        inputs["pair_features"],
        inputs["recovery_eval"],
        equations=equations,
        matrix=None,
        max_n=config.max_n,
        max_pairs_per_proposal=config.max_pairs_per_proposal,
    )
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        "source_mode": source_mode,
        "real_corpus_used": real_corpus_used,
        "input_dir": str(config.input_dir or ""),
        **summarize_active_discovery(residual_basins, proposals, evaluations),
    }
    summary["benchmark_passed"] = (
        summary["residual_basin_count"] > 0
        and summary["proposal_count"] > 0
        and summary["evaluated_proposal_count"] > 0
        and summary["advisory_boundary_preserved"]
    )
    artifacts = {
        "active_residual_basins.csv": out_dir / "active_residual_basins.csv",
        "constructor_proposals.csv": out_dir / "constructor_proposals.csv",
        "proposal_evaluations.csv": out_dir / "proposal_evaluations.csv",
        "active_discovery_summary.json": out_dir / "active_discovery_summary.json",
        "active_discovery_report.md": out_dir / "active_discovery_report.md",
        "active_discovery.sqlite": out_dir / "active_discovery.sqlite",
        "artifact_manifest.json": out_dir / "artifact_manifest.json",
    }
    _write_csv(artifacts["active_residual_basins.csv"], residual_basins)
    _write_csv(artifacts["constructor_proposals.csv"], proposals)
    _write_csv(artifacts["proposal_evaluations.csv"], evaluations)
    write_persistent_lawbook_sqlite(
        artifacts["active_discovery.sqlite"],
        {
            "active_residual_basins": residual_basins,
            "constructor_proposals": proposals,
            "proposal_evaluations": evaluations,
            "summary": pd.DataFrame([summary]),
        },
    )
    manifest = [
        {"artifact_name": name, "path": str(path), "exists": path.exists()}
        for name, path in artifacts.items()
        if name != "artifact_manifest.json"
    ]
    artifacts["artifact_manifest.json"].write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["active_discovery_summary.json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["active_discovery_report.md"].write_text(_report(summary), encoding="utf-8")
    if not summary["advisory_boundary_preserved"]:
        raise RuntimeError("active residual discovery safety boundary failed")
    return summary | {"artifacts": {name: str(path) for name, path in artifacts.items()}}


def _fallback_inputs(seed: int) -> dict[str, pd.DataFrame]:
    features = pd.DataFrame(
        [
            {
                "seed": seed,
                "pair_idx": idx,
                "basin": basin,
                "deep_ir_candidate": deep,
                "quotient_pressure": q,
                "target_separation_pressure": sep,
                "fresh_variable_escape_count": fresh,
                "repeat_tail_pressure": repeat,
                "compression_pressure": comp,
                "expansion_pressure": exp,
                "active_discovery_family_hit": hit,
            }
            for idx, (basin, deep, q, sep, fresh, repeat, comp, exp, hit) in enumerate(
                [
                    ("fresh_escape", "fresh_gate", 1, 1, 3, 0, 0, 0, "quotient_fresh_gate"),
                    ("fresh_escape", "fresh_gate", 1, 1, 3, 0, 0, 0, "quotient_fresh_gate"),
                    ("fresh_escape", "fresh_gate", 1, 1, 3, 0, 0, 0, ""),
                    ("repeat_tail", "tail_pressure", 1, 1, 0, 4, 0, 0, "tail_coupled_projection"),
                    ("repeat_tail", "tail_pressure", 1, 1, 0, 4, 0, 0, ""),
                    ("repeat_tail", "tail_pressure", 1, 1, 0, 4, 0, 0, ""),
                    ("compression", "block", 1, 1, 0, 0, 4, 0, ""),
                    ("compression", "block", 1, 1, 0, 0, 4, 0, ""),
                    ("compression", "block", 1, 1, 0, 0, 4, 0, ""),
                ]
            )
        ]
    )
    recovery = features[["seed", "pair_idx", "active_discovery_family_hit"]].copy()
    recovery["generic_recovered"] = False
    recovery["heldout_lawbook_recovered"] = False
    recovery["advisory_only"] = True
    recovery["can_promote_truth"] = False
    return {
        "pair_features": features,
        "recovery_eval": recovery,
        "obstruction_atlas": pd.DataFrame(),
        "train_lawbook_manifest": pd.DataFrame(),
        "terminal_form_audit": pd.DataFrame(),
    }


def _load_equations(path: str | None) -> list[str] | None:
    if not path:
        return None
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty and len(frame.columns) == 0:
        pd.DataFrame([{"empty": True}]).to_csv(path, index=False)
    else:
        safe = frame.copy()
        for col in safe.columns:
            safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value)
        safe.to_csv(path, index=False)


def _report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Active Residual Constructor Discovery v1",
            "",
            f"- source_mode: {summary['source_mode']}",
            f"- residual_basin_count: {summary['residual_basin_count']}",
            f"- proposal_count: {summary['proposal_count']}",
            f"- accepted_route_count: {summary['accepted_route_count']}",
            f"- total_recovered_pairs: {summary['total_recovered_pairs']}",
            f"- best_proposal_family: {summary['best_proposal_family']}",
            "",
            "All proposals are advisory constructor pressure. Finite-search failure never implies TRUE.",
            "",
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> ActiveResidualDiscoveryConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equations")
    parser.add_argument("--matrix")
    parser.add_argument("--input-dir")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--min-support", type=int, default=3)
    parser.add_argument("--max-proposals-per-basin", type=int, default=3)
    parser.add_argument("--max-pairs-per-proposal", type=int, default=100)
    parser.add_argument("--max-n", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260524)
    parser.add_argument("--fallback-demo", action="store_true")
    args = parser.parse_args(argv)
    return ActiveResidualDiscoveryConfig(
        equations=args.equations,
        matrix=args.matrix,
        input_dir=args.input_dir,
        out_dir=args.out_dir,
        min_support=args.min_support,
        max_proposals_per_basin=args.max_proposals_per_basin,
        max_pairs_per_proposal=args.max_pairs_per_proposal,
        max_n=args.max_n,
        seed=args.seed,
        fallback_demo=args.fallback_demo,
    )


def main(argv: Sequence[str] | None = None) -> int:
    summary = run_active_residual_discovery_benchmark(parse_args(argv))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("benchmark_passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())

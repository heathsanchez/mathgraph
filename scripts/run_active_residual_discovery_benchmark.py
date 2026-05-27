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
from mathgraph.proposal_constructor_synthesis import (
    evaluate_synthesized_constructors,
    summarize_synthesis,
    synthesize_constructors_for_proposals,
)
from mathgraph.repaired_countermodel_certificates import (
    build_repaired_countermodel_certificates,
    deduplicate_repaired_certificates,
    summarize_repaired_certificate_families,
    write_repaired_certificate_lawbook,
)
from mathgraph.residual_conditioned_synthesis import (
    evaluate_residual_conditioned_constructors,
    summarize_residual_conditioned_synthesis,
    synthesize_for_residual_pairs,
)
from mathgraph.source_law_repair import repair_conditioned_constructors, summarize_source_law_repair


@dataclass(frozen=True)
class ActiveResidualDiscoveryConfig:
    equations: str | None
    matrix: str | None
    input_dir: str | None
    out_dir: str
    min_support: int = 3
    max_proposals_per_basin: int = 3
    max_pairs_per_proposal: int = 100
    synthesize_constructors: bool = False
    max_tables_per_proposal: int = 32
    max_pairs_per_constructor: int = 100
    residual_conditioned_synthesis: bool = False
    max_conditioned_pairs: int = 100
    max_conditioned_witnesses_per_pair: int = 8
    max_conditioned_attempts_per_pair: int = 32
    conditioned_max_steps: int = 5000
    enable_source_law_repair: bool = False
    repair_strategies: list[str] | None = None
    repair_max_steps: int = 10000
    repair_max_violations: int = 128
    assimilate_repaired_certificates: bool = False
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
    equations = _fallback_equations() if config.fallback_demo else (_load_equations(config.equations) if config.equations and Path(config.equations).exists() else None)
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
    synthesis_tables: dict[str, pd.DataFrame] = {}
    if config.synthesize_constructors:
        constructors, synthesis_results = synthesize_constructors_for_proposals(
            proposals,
            max_n=config.max_n,
            max_tables_per_proposal=config.max_tables_per_proposal,
            seed=config.seed,
        )
        residual_pairs = _residual_pairs(inputs["pair_features"], inputs["recovery_eval"])
        recoveries = evaluate_synthesized_constructors(
            constructors,
            residual_pairs,
            equations or [],
            max_pairs_per_constructor=config.max_pairs_per_constructor,
        )
        synthesis_summary = summarize_synthesis(constructors, synthesis_results, recoveries)
        synthesis_summary["breakthrough_candidate"] = bool(source_mode == "real_etp" and synthesis_summary["synthesized_recovered_pairs"] > 0)
        summary.update(synthesis_summary)
        summary["evaluation_mode"] = "finite_checked"
        synthesis_tables = {
            "synthesized_constructors.csv": constructors,
            "synthesis_results.csv": synthesis_results,
            "synthesized_recoveries.csv": recoveries,
        }
    else:
        summary.update(
            {
                "synthesis_enabled": False,
                "synthesized_constructor_count": 0,
                "unique_synthesized_table_count": 0,
                "synthesized_recovered_pairs": 0,
                "synthesized_recovery_rate": 0.0,
                "best_synthesized_family": "",
                "best_synthesized_constructor_id": "",
                "finite_checked_recoveries": 0,
                "breakthrough_candidate": False,
            }
        )
    conditioned_tables: dict[str, pd.DataFrame] = {}
    repair_tables: dict[str, pd.DataFrame] = {}
    if config.residual_conditioned_synthesis:
        residual_pairs = _residual_pairs(inputs["pair_features"], inputs["recovery_eval"])
        specs, attempts, conditioned_constructors = synthesize_for_residual_pairs(
            residual_pairs,
            equations or [],
            max_n=config.max_n,
            max_pairs=config.max_conditioned_pairs,
            max_witnesses_per_pair=config.max_conditioned_witnesses_per_pair,
            max_attempts_per_pair=config.max_conditioned_attempts_per_pair,
            max_steps=config.conditioned_max_steps,
            seed=config.seed,
        )
        conditioned_recoveries = evaluate_residual_conditioned_constructors(conditioned_constructors, equations or [])
        conditioned_summary = summarize_residual_conditioned_synthesis(specs, attempts, conditioned_constructors, conditioned_recoveries)
        conditioned_summary["residual_conditioned_breakthrough_candidate"] = bool(source_mode == "real_etp" and conditioned_summary["residual_conditioned_recovered_pairs"] > 0)
        conditioned_summary["total_synthesis_recovered_pairs"] = int(summary.get("synthesized_recovered_pairs", 0)) + int(conditioned_summary["residual_conditioned_recovered_pairs"])
        conditioned_summary["total_breakthrough_candidate"] = bool(summary.get("breakthrough_candidate", False) or conditioned_summary["residual_conditioned_breakthrough_candidate"])
        summary.update(conditioned_summary)
        summary["evaluation_mode"] = "finite_checked_conditioned"
        conditioned_tables = {
            "residual_conditioned_pair_specs.csv": specs,
            "residual_conditioned_attempts.csv": attempts,
            "residual_conditioned_constructors.csv": conditioned_constructors,
            "residual_conditioned_recoveries.csv": conditioned_recoveries,
        }
        if config.enable_source_law_repair:
            repair_results, repair_traces = repair_conditioned_constructors(
                conditioned_constructors,
                max_steps=config.repair_max_steps,
                max_violations=config.repair_max_violations,
                strategies=config.repair_strategies,
                seed=config.seed,
            )
            repair_summary = summarize_source_law_repair(repair_results, repair_traces)
            repair_summary["source_law_repair_breakthrough_candidate"] = bool(source_mode == "real_etp" and repair_summary["source_law_repair_recovered_pairs"] > 0)
            repair_summary["conditioned_plus_repair_recovered_pairs"] = int(conditioned_summary["residual_conditioned_recovered_pairs"]) + int(repair_summary["source_law_repair_recovered_pairs"])
            repair_summary["total_synthesis_recovered_pairs"] = int(summary.get("synthesized_recovered_pairs", 0)) + int(repair_summary["conditioned_plus_repair_recovered_pairs"])
            repair_summary["total_breakthrough_candidate"] = bool(summary.get("breakthrough_candidate", False) or conditioned_summary["residual_conditioned_breakthrough_candidate"] or repair_summary["source_law_repair_breakthrough_candidate"])
            summary.update(repair_summary)
            summary["evaluation_mode"] = "finite_checked_conditioned_repair"
            repair_tables = {
                "source_law_repair_results.csv": repair_results,
                "source_law_repair_traces.csv": repair_traces,
            }
        else:
            summary.update(
                {
                    "source_law_repair_enabled": False,
                    "source_law_repair_attempt_count": 0,
                    "source_law_repair_completed_count": 0,
                    "source_law_repair_recovered_pairs": 0,
                    "source_law_repair_best_strategy": "",
                    "source_law_repair_breakthrough_candidate": False,
                    "conditioned_plus_repair_recovered_pairs": int(conditioned_summary["residual_conditioned_recovered_pairs"]),
                }
            )
    else:
        summary.update(
            {
                "residual_conditioned_enabled": False,
                "residual_conditioned_pair_count": 0,
                "residual_conditioned_attempt_count": 0,
                "residual_conditioned_constructor_count": 0,
                "residual_conditioned_recovered_pairs": 0,
                "residual_conditioned_recovery_rate": 0.0,
                "residual_conditioned_best_family": "",
                "residual_conditioned_breakthrough_candidate": False,
                "total_synthesis_recovered_pairs": int(summary.get("synthesized_recovered_pairs", 0)),
                "total_breakthrough_candidate": bool(summary.get("breakthrough_candidate", False)),
                "source_law_repair_enabled": False,
                "source_law_repair_attempt_count": 0,
                "source_law_repair_completed_count": 0,
                "source_law_repair_recovered_pairs": 0,
                "source_law_repair_best_strategy": "",
                "source_law_repair_breakthrough_candidate": False,
                "conditioned_plus_repair_recovered_pairs": 0,
            }
        )
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
    for name in synthesis_tables:
        artifacts[name] = out_dir / name
    for name in conditioned_tables:
        artifacts[name] = out_dir / name
    for name in repair_tables:
        artifacts[name] = out_dir / name
    _write_csv(artifacts["active_residual_basins.csv"], residual_basins)
    _write_csv(artifacts["constructor_proposals.csv"], proposals)
    _write_csv(artifacts["proposal_evaluations.csv"], evaluations)
    for name, frame in synthesis_tables.items():
        _write_csv(artifacts[name], frame)
    for name, frame in conditioned_tables.items():
        _write_csv(artifacts[name], frame)
    for name, frame in repair_tables.items():
        _write_csv(artifacts[name], frame)
    if config.synthesize_constructors:
        artifacts["synthesis_summary.json"] = out_dir / "synthesis_summary.json"
        artifacts["synthesis_summary.json"].write_text(json.dumps({k: summary[k] for k in summary if k.startswith("synth") or k in {"best_synthesized_family", "best_synthesized_constructor_id", "finite_checked_recoveries", "breakthrough_candidate"}}, indent=2, sort_keys=True), encoding="utf-8")
    if config.residual_conditioned_synthesis:
        artifacts["residual_conditioned_summary.json"] = out_dir / "residual_conditioned_summary.json"
        artifacts["residual_conditioned_summary.json"].write_text(json.dumps({k: summary[k] for k in summary if k.startswith("residual_conditioned") or k in {"total_synthesis_recovered_pairs", "total_breakthrough_candidate"}}, indent=2, sort_keys=True), encoding="utf-8")
    if config.enable_source_law_repair:
        artifacts["source_law_repair_summary.json"] = out_dir / "source_law_repair_summary.json"
        artifacts["source_law_repair_summary.json"].write_text(json.dumps({k: summary[k] for k in summary if k.startswith("source_law_repair") or k in {"conditioned_plus_repair_recovered_pairs", "total_synthesis_recovered_pairs", "total_breakthrough_candidate"}}, indent=2, sort_keys=True), encoding="utf-8")
    if config.assimilate_repaired_certificates and config.enable_source_law_repair:
        cert_dir = out_dir / "repaired_countermodel_certificates"
        certs, rejected = build_repaired_countermodel_certificates(out_dir, equations=equations or [], source_mode=source_mode)
        unique, duplicates = deduplicate_repaired_certificates(certs)
        family_summary = summarize_repaired_certificate_families(unique)
        cert_artifacts = write_repaired_certificate_lawbook(
            unique,
            rejected,
            family_summary,
            cert_dir,
            manifest_metadata={"source_mode": source_mode, "input_dir": str(out_dir)},
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
        artifacts["repaired_countermodel_manifest.json"] = Path(cert_artifacts["repaired_countermodel_manifest.json"])
        artifacts["repaired_countermodel_lawbook.sqlite"] = Path(cert_artifacts["repaired_countermodel_lawbook.sqlite"])
    else:
        summary.setdefault("certificate_assimilation_enabled", False)
        summary.setdefault("repaired_certificate_count", 0)
        summary.setdefault("repaired_certificate_unique_pair_count", 0)
        summary.setdefault("breakthrough_certificate_count", 0)
    write_persistent_lawbook_sqlite(
        artifacts["active_discovery.sqlite"],
        {
            "active_residual_basins": residual_basins,
            "constructor_proposals": proposals,
            "proposal_evaluations": evaluations,
            **{name.removesuffix(".csv"): frame for name, frame in synthesis_tables.items()},
            **{name.removesuffix(".csv"): frame for name, frame in conditioned_tables.items()},
            **{name.removesuffix(".csv"): frame for name, frame in repair_tables.items()},
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
                "eq1_id": 0,
                "eq2_id": 1 if hit else 2,
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
    recovery["eq1_id"] = features["eq1_id"]
    recovery["eq2_id"] = features["eq2_id"]
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


def _fallback_equations() -> list[str]:
    return [
        "x = x",
        "x = y",
        "(x * y) = x",
    ]


def _residual_pairs(pair_features: pd.DataFrame, recovery_eval: pd.DataFrame) -> pd.DataFrame:
    from mathgraph.active_residual_discovery import _join_features_recovery  # local helper reuse
    from mathgraph.persistent_exact_microbasin_lawbook import normalize_recovery_frame

    joined = normalize_recovery_frame(_join_features_recovery(pair_features, recovery_eval))
    return joined[(~joined["generic_recovered_norm"]) & (~joined["lawbook_recovered_norm"])].copy()


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
    parser.add_argument("--synthesize-constructors", action="store_true")
    parser.add_argument("--max-tables-per-proposal", type=int, default=32)
    parser.add_argument("--max-pairs-per-constructor", type=int, default=100)
    parser.add_argument("--residual-conditioned-synthesis", action="store_true")
    parser.add_argument("--max-conditioned-pairs", type=int, default=100)
    parser.add_argument("--max-conditioned-witnesses-per-pair", type=int, default=8)
    parser.add_argument("--max-conditioned-attempts-per-pair", type=int, default=32)
    parser.add_argument("--conditioned-max-steps", type=int, default=5000)
    parser.add_argument("--enable-source-law-repair", action="store_true")
    parser.add_argument("--repair-strategies", default="pressure_descent,target_frozen_pressure_descent,diagonal_first_repair,row_col_repair,quotient_merge_repair,two_phase_repair")
    parser.add_argument("--repair-max-steps", type=int, default=10000)
    parser.add_argument("--repair-max-violations", type=int, default=128)
    parser.add_argument("--assimilate-repaired-certificates", action="store_true")
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
        synthesize_constructors=args.synthesize_constructors,
        max_tables_per_proposal=args.max_tables_per_proposal,
        max_pairs_per_constructor=args.max_pairs_per_constructor,
        residual_conditioned_synthesis=args.residual_conditioned_synthesis,
        max_conditioned_pairs=args.max_conditioned_pairs,
        max_conditioned_witnesses_per_pair=args.max_conditioned_witnesses_per_pair,
        max_conditioned_attempts_per_pair=args.max_conditioned_attempts_per_pair,
        conditioned_max_steps=args.conditioned_max_steps,
        enable_source_law_repair=args.enable_source_law_repair,
        repair_strategies=[item for item in args.repair_strategies.split(",") if item],
        repair_max_steps=args.repair_max_steps,
        repair_max_violations=args.repair_max_violations,
        assimilate_repaired_certificates=args.assimilate_repaired_certificates,
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

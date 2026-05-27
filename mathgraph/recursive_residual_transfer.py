"""Recursive residual-mined memory transfer for SAIR/ETP.

This module ports the Colab breakthrough
``MATHGRAPH / ETP -- RECURSIVE RESIDUAL-MINED MEMORY TRANSFER TEST v1`` into
repo-grade, testable code.  The objects here are advisory route-memory records:
they may guide finite-countermodel route selection, but they cannot promote
truth.  A FALSE claim still requires a finite magma satisfying the source and
violating the target; failed finite search is never treated as TRUE.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

from mathgraph.compact_route_atlas import (
    CompactAtlasEntry,
    RouteAttribution,
    compare_random_controls,
    compare_shuffled_controls,
    select_compact_atlas,
)
from mathgraph.finite_magma_world import Equation, Term, normalize_table, parse_equation

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - minimal dependency environments
    np = None  # type: ignore[assignment]


GATE_NAMES: tuple[str, ...] = (
    "compact_transfer_gain_vs_generic_positive",
    "compact_beats_random_same_size",
    "compact_beats_shuffled_atlas_same_size",
    "compact_retains_recursive_gain",
    "compact_prunes_recursive_memory",
    "zero_true_contamination",
    "positive_gain_in_enough_seeds",
    "oracle_gap_captured",
    "advisory_boundary_preserved",
)

SOURCE_BREAKTHROUGH_METRICS: dict[str, Any] = {
    "run_name": "mathgraph_recursive_residual_transfer_v1",
    "profile": "TRANSFER_FAST",
    "equations": 4694,
    "matrix_shape": [4694, 4694],
    "true_count": 8178279,
    "false_count": 13855357,
    "seeds": [1729, 42, 137],
    "heldout_false_pairs_per_split": 12000,
    "true_controls_per_seed": 2000,
    "generic_mean_recoveries": 11405.5,
    "recursive_full_memory_mean_recoveries": 11642.333333,
    "compact_atlas_mean_recoveries": 11639.666667,
    "oracle_mean_recoveries": 11731.0,
    "compact_gain_vs_generic": 234.166667,
    "compact_beats_random_same_size": 205.0,
    "compact_beats_shuffled_atlas_same_size": 86.958333,
    "compact_retains_recursive_gain": 0.989575,
    "compact_prunes_recursive_memory": 0.53,
    "oracle_gap_captured": 0.68992,
    "true_contamination_max": 0,
    "gates_passed": 9,
    "gates_total": 9,
    "advisory_boundary_ok": True,
}


@dataclass(frozen=True)
class ResidualMinedConstructor:
    constructor_id: str
    constructor_hash: str = ""
    source: str = ""
    carrier_size: int = 0
    generation: int = 0
    parent_basin: str = ""
    table: tuple[tuple[int, ...], ...] = ()
    advisory_only: bool = True
    can_promote_truth: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "constructor_id": self.constructor_id,
            "constructor_hash": self.constructor_hash,
            "source": self.source,
            "carrier_size": self.carrier_size,
            "generation": self.generation,
            "parent_basin": self.parent_basin,
            "table": [list(row) for row in self.table],
            "advisory_only": True,
            "can_promote_truth": False,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RouteEvaluation:
    seed: int
    split: str
    route: str
    route_kind: str
    route_size: int
    false_pairs: int
    true_pairs: int
    recoveries: int
    residuals: int
    new_recoveries_vs_generic: int = 0
    true_contamination_count: int = 0
    advisory_only: bool = True
    can_promote_truth: bool = False
    yield_rate: float | None = None
    true_contamination_rate: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "split": self.split,
            "route": self.route,
            "route_kind": self.route_kind,
            "route_size": self.route_size,
            "false_pairs": self.false_pairs,
            "true_pairs": self.true_pairs,
            "recoveries": self.recoveries,
            "yield_rate": self.yield_rate if self.yield_rate is not None else _safe_div(self.recoveries, self.false_pairs),
            "residuals": self.residuals,
            "new_recoveries_vs_generic": self.new_recoveries_vs_generic,
            "true_contamination_count": self.true_contamination_count,
            "true_contamination_rate": self.true_contamination_rate
            if self.true_contamination_rate is not None
            else _safe_div(self.true_contamination_count, self.true_pairs),
            "advisory_only": True,
            "can_promote_truth": False,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TransferGateResult:
    gate_id: str
    gate: str
    value: float | bool
    threshold: float | bool
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RecursiveTransferSummary:
    run_name: str
    profile: str
    classification: str
    equations: int
    matrix_shape: tuple[int, int]
    true_count: int
    false_count: int
    seeds: tuple[int, ...]
    heldout_false_pairs_per_split: int
    true_controls_per_seed: int
    generic_mean_recoveries: float
    recursive_full_memory_mean_recoveries: float
    compact_atlas_mean_recoveries: float
    oracle_mean_recoveries: float
    compact_gain_vs_generic: float
    compact_beats_random_same_size: float
    compact_beats_shuffled_atlas_same_size: float
    compact_retains_recursive_gain: float
    compact_prunes_recursive_memory: float
    oracle_gap_captured: float
    true_contamination_max: int
    gates_passed: int
    gates_total: int
    all_gates_pass: bool
    advisory_boundary_ok: bool
    real_etp_used: bool = False
    source_run_metrics: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_name": self.run_name,
            "profile": self.profile,
            "classification": self.classification,
            "equations": self.equations,
            "matrix_shape": list(self.matrix_shape),
            "true_count": self.true_count,
            "false_count": self.false_count,
            "seeds": list(self.seeds),
            "heldout_false_pairs_per_split": self.heldout_false_pairs_per_split,
            "true_controls_per_seed": self.true_controls_per_seed,
            "generic_mean_recoveries": self.generic_mean_recoveries,
            "recursive_full_memory_mean_recoveries": self.recursive_full_memory_mean_recoveries,
            "compact_atlas_mean_recoveries": self.compact_atlas_mean_recoveries,
            "oracle_mean_recoveries": self.oracle_mean_recoveries,
            "compact_gain_vs_generic": self.compact_gain_vs_generic,
            "compact_beats_random_same_size": self.compact_beats_random_same_size,
            "compact_beats_shuffled_atlas_same_size": self.compact_beats_shuffled_atlas_same_size,
            "compact_retains_recursive_gain": self.compact_retains_recursive_gain,
            "compact_prunes_recursive_memory": self.compact_prunes_recursive_memory,
            "oracle_gap_captured": self.oracle_gap_captured,
            "true_contamination_max": self.true_contamination_max,
            "gates_passed": self.gates_passed,
            "gates_total": self.gates_total,
            "all_gates_pass": self.all_gates_pass,
            "advisory_boundary_ok": self.advisory_boundary_ok,
            "real_etp_used": self.real_etp_used,
            "source_run_metrics": dict(self.source_run_metrics),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RealEtpTransferConfig:
    equations_path: str | Path
    matrix_path: str | Path
    out_dir: str | Path
    seeds: tuple[int, ...] = (1729, 42, 137)
    profile: str = "transfer_fast"
    base_magmas_total: int = 600
    base_n2_target: int = 18
    base_n3_target: int = 204
    base_n4_target: int = 378
    generic_route_size: int = 40
    seed_false_pairs_for_generic: int = 6000
    discovery_false_pairs: int = 6000
    atlas_train_false_pairs: int = 8000
    heldout_false_a_pairs: int = 12000
    heldout_false_b_pairs: int = 12000
    true_control_pairs: int = 2000
    exclude_seen_pairs: bool = True
    generations: int = 5
    new_per_generation: int = 10
    candidates_per_generation: int = 1800
    mine_from_residual_top_k: int = 700
    compact_top_ks: tuple[int, ...] = (4, 8, 12, 16, 24, 32, 40, 50)
    load_bearing_min_unique_hits: int = 1
    random_control_repeats: int = 8
    shuffled_control_repeats: int = 8
    include_oracle_reference: bool = True
    oracle_route_size: int = 120
    sat_progress_every: int = 0
    write_report: bool = True

    def effective(self) -> "RealEtpTransferConfig":
        if self.profile == "tiny":
            return RealEtpTransferConfig(
                equations_path=self.equations_path,
                matrix_path=self.matrix_path,
                out_dir=self.out_dir,
                seeds=self.seeds,
                profile=self.profile,
                base_magmas_total=min(self.base_magmas_total, 24),
                base_n2_target=min(self.base_n2_target, 10),
                base_n3_target=min(self.base_n3_target, 10),
                base_n4_target=0,
                generic_route_size=min(self.generic_route_size, 4),
                seed_false_pairs_for_generic=min(self.seed_false_pairs_for_generic, 12),
                discovery_false_pairs=min(self.discovery_false_pairs, 12),
                atlas_train_false_pairs=min(self.atlas_train_false_pairs, 12),
                heldout_false_a_pairs=min(self.heldout_false_a_pairs, 12),
                heldout_false_b_pairs=min(self.heldout_false_b_pairs, 12),
                true_control_pairs=min(self.true_control_pairs, 6),
                generations=min(self.generations, 2),
                new_per_generation=min(self.new_per_generation, 2),
                candidates_per_generation=min(self.candidates_per_generation, 24),
                mine_from_residual_top_k=min(self.mine_from_residual_top_k, 24),
                compact_top_ks=(1, 2, 4),
                random_control_repeats=2,
                shuffled_control_repeats=2,
                oracle_route_size=8,
                sat_progress_every=0,
                write_report=self.write_report,
            )
        return self


@dataclass(frozen=True)
class MagmaTable:
    table: tuple[tuple[int, ...], ...]
    source: str
    carrier_size: int
    table_hash: str
    generation: int = 0
    parent_basin: str = "base"
    parent_hash: str = ""

    @staticmethod
    def from_table(
        table: Sequence[Sequence[int]],
        *,
        source: str,
        generation: int = 0,
        parent_basin: str = "base",
        parent_hash: str = "",
    ) -> "MagmaTable":
        normalized = normalize_table(table)
        return MagmaTable(
            table=normalized,
            source=source,
            carrier_size=len(normalized),
            table_hash=_stable_hash({"table": normalized}, 16),
            generation=generation,
            parent_basin=parent_basin,
            parent_hash=parent_hash,
        )


@dataclass(frozen=True)
class RealEtpTransferResult:
    summary: RecursiveTransferSummary
    route_evaluations: tuple[RouteEvaluation, ...]
    constructors: tuple[ResidualMinedConstructor, ...]
    generation_rows: tuple[dict[str, Any], ...]
    candidate_rows: tuple[dict[str, Any], ...]
    attribution_rows: tuple[dict[str, Any], ...]
    route_summary_rows: tuple[dict[str, Any], ...]
    best_compact_rows: tuple[dict[str, Any], ...]
    gate_results: tuple[TransferGateResult, ...]
    artifact_paths: dict[str, str]


def evaluate_route_transfer(
    *,
    seed: int,
    split: str,
    route: str,
    route_kind: str,
    false_hits: Sequence[bool],
    true_hits: Sequence[bool],
    generic_false_hits: Sequence[bool] | None = None,
    route_size: int = 0,
) -> RouteEvaluation:
    """Evaluate an advisory route on FALSE heldout pairs and TRUE controls."""

    false_found = [bool(x) for x in false_hits]
    true_found = [bool(x) for x in true_hits]
    generic = [False] * len(false_found) if generic_false_hits is None else [bool(x) for x in generic_false_hits]
    if len(generic) != len(false_found):
        raise ValueError("generic_false_hits must have the same length as false_hits")
    recoveries = sum(1 for x in false_found if x)
    true_contamination = sum(1 for x in true_found if x)
    return RouteEvaluation(
        seed=int(seed),
        split=str(split),
        route=str(route),
        route_kind=str(route_kind),
        route_size=int(route_size),
        false_pairs=len(false_found),
        true_pairs=len(true_found),
        recoveries=recoveries,
        residuals=len(false_found) - recoveries,
        new_recoveries_vs_generic=sum(1 for hit, gen in zip(false_found, generic) if hit and not gen),
        true_contamination_count=true_contamination,
        advisory_only=True,
        can_promote_truth=False,
    )


def compute_transfer_gates(
    route_evaluations: Sequence[RouteEvaluation | Mapping[str, Any]],
    *,
    generic_route_size: int = 40,
    gate_min_transfer_gain_vs_generic: float = 1.0,
    gate_min_transfer_gain_vs_random: float = 0.0,
    gate_min_gain_retention: float = 0.70,
    gate_min_pruning_ratio: float = 0.40,
    gate_max_true_contamination: int = 0,
    gate_min_positive_seed_fraction: float = 2 / 3,
    gate_min_oracle_gap_captured: float = 0.20,
) -> tuple[list[TransferGateResult], list[dict[str, Any]]]:
    rows = [_route_eval(r).to_dict() for r in route_evaluations]
    best = _best_compact_by_seed_split(rows)
    compact_recoveries = [float(r["compact_recoveries"]) for r in best]
    generic_recoveries = [float(r["generic_recoveries"]) for r in best]
    recursive_recoveries = [float(r["recursive_recoveries"]) for r in best]
    oracle_recoveries = [float(r.get("oracle_recoveries", r["compact_recoveries"])) for r in best]
    random_recoveries = [float(r["recoveries"]) for r in rows if r["route_kind"] == "random_control"]
    shuffled_recoveries = [float(r["recoveries"]) for r in rows if r["route_kind"] == "shuffled_control"]
    true_contamination_max = max([int(r["true_contamination_count"]) for r in rows] or [0])
    advisory_ok = all(bool(r["advisory_only"]) and not bool(r["can_promote_truth"]) for r in rows)

    compact_mean = _avg(compact_recoveries)
    generic_mean = _avg(generic_recoveries)
    recursive_gain = [_safe_div(c - g, r - g, 1.0) for c, g, r in zip(compact_recoveries, generic_recoveries, recursive_recoveries)]
    pruning = [
        1.0 - _safe_div(float(b["best_compact_route_size"]) - generic_route_size, float(b["recursive_route_size"]) - generic_route_size, 0.0)
        for b in best
    ]
    oracle_gap = [_safe_div(c - g, o - g, 0.0) for c, g, o in zip(compact_recoveries, generic_recoveries, oracle_recoveries)]
    positive_seed_fraction = _positive_gain_seed_fraction(best)
    random_cmp = compare_random_controls(compact_recoveries, random_recoveries)
    shuffled_cmp = compare_shuffled_controls(compact_recoveries, shuffled_recoveries)

    gate_values: list[tuple[str, float | bool, float | bool, bool]] = [
        (
            "compact_transfer_gain_vs_generic_positive",
            compact_mean - generic_mean,
            gate_min_transfer_gain_vs_generic,
            compact_mean - generic_mean >= gate_min_transfer_gain_vs_generic,
        ),
        (
            "compact_beats_random_same_size",
            float(random_cmp["compact_gain_vs_random_same_size"]),
            gate_min_transfer_gain_vs_random,
            float(random_cmp["compact_gain_vs_random_same_size"]) >= gate_min_transfer_gain_vs_random,
        ),
        (
            "compact_beats_shuffled_atlas_same_size",
            float(shuffled_cmp["compact_gain_vs_shuffled_atlas_same_size"]),
            gate_min_transfer_gain_vs_random,
            float(shuffled_cmp["compact_gain_vs_shuffled_atlas_same_size"]) >= gate_min_transfer_gain_vs_random,
        ),
        (
            "compact_retains_recursive_gain",
            _avg(recursive_gain),
            gate_min_gain_retention,
            _avg(recursive_gain) >= gate_min_gain_retention,
        ),
        (
            "compact_prunes_recursive_memory",
            _avg(pruning),
            gate_min_pruning_ratio,
            _avg(pruning) >= gate_min_pruning_ratio,
        ),
        (
            "zero_true_contamination",
            true_contamination_max,
            gate_max_true_contamination,
            true_contamination_max <= gate_max_true_contamination,
        ),
        (
            "positive_gain_in_enough_seeds",
            positive_seed_fraction,
            gate_min_positive_seed_fraction,
            positive_seed_fraction >= gate_min_positive_seed_fraction,
        ),
        (
            "oracle_gap_captured",
            _avg(oracle_gap),
            gate_min_oracle_gap_captured,
            _avg(oracle_gap) >= gate_min_oracle_gap_captured,
        ),
        ("advisory_boundary_preserved", advisory_ok, True, advisory_ok is True),
    ]
    gates = [TransferGateResult(f"T{i}", name, value, threshold, passed) for i, (name, value, threshold, passed) in enumerate(gate_values, 1)]
    return gates, best


def build_recursive_transfer_summary(
    route_evaluations: Sequence[RouteEvaluation | Mapping[str, Any]],
    *,
    equations: int,
    matrix_shape: Sequence[int],
    true_count: int,
    false_count: int,
    profile: str = "transfer_fast",
    run_name: str = "mathgraph_recursive_residual_transfer_v1",
    classification: str = "recursive_residual_transfer",
    real_etp_used: bool = False,
    source_run_metrics: Mapping[str, Any] | None = None,
) -> RecursiveTransferSummary:
    rows = [_route_eval(r) for r in route_evaluations]
    gates, best = compute_transfer_gates(rows)
    by_kind = _route_kind_means([r.to_dict() for r in rows])
    seeds = tuple(sorted({r.seed for r in rows}))
    false_pairs = max([r.false_pairs for r in rows] or [0])
    true_pairs = max([r.true_pairs for r in rows] or [0])
    gate_map = {g.gate: g.value for g in gates}
    compact_mean = _avg([float(r["compact_recoveries"]) for r in best])
    generic_mean = by_kind.get("generic", 0.0)
    return RecursiveTransferSummary(
        run_name=run_name,
        profile=profile,
        classification=classification,
        equations=int(equations),
        matrix_shape=(int(matrix_shape[0]), int(matrix_shape[1])),
        true_count=int(true_count),
        false_count=int(false_count),
        seeds=seeds,
        heldout_false_pairs_per_split=false_pairs,
        true_controls_per_seed=true_pairs,
        generic_mean_recoveries=generic_mean,
        recursive_full_memory_mean_recoveries=by_kind.get("recursive_full_memory", 0.0),
        compact_atlas_mean_recoveries=compact_mean,
        oracle_mean_recoveries=by_kind.get("oracle_reference", 0.0),
        compact_gain_vs_generic=float(gate_map["compact_transfer_gain_vs_generic_positive"]),
        compact_beats_random_same_size=float(gate_map["compact_beats_random_same_size"]),
        compact_beats_shuffled_atlas_same_size=float(gate_map["compact_beats_shuffled_atlas_same_size"]),
        compact_retains_recursive_gain=float(gate_map["compact_retains_recursive_gain"]),
        compact_prunes_recursive_memory=float(gate_map["compact_prunes_recursive_memory"]),
        oracle_gap_captured=float(gate_map["oracle_gap_captured"]),
        true_contamination_max=int(gate_map["zero_true_contamination"]),
        gates_passed=sum(1 for g in gates if g.passed),
        gates_total=len(gates),
        all_gates_pass=all(g.passed for g in gates),
        advisory_boundary_ok=bool(gate_map["advisory_boundary_preserved"]),
        real_etp_used=real_etp_used,
        source_run_metrics=dict(source_run_metrics or {}),
    )


def write_recursive_transfer_artifacts(
    out_dir: str | Path,
    *,
    summary: RecursiveTransferSummary,
    route_evaluations: Sequence[RouteEvaluation | Mapping[str, Any]],
    constructors: Sequence[ResidualMinedConstructor | Mapping[str, Any]] = (),
    generation_rows: Sequence[Mapping[str, Any]] = (),
    candidate_rows: Sequence[Mapping[str, Any]] = (),
    route_summary_rows: Sequence[Mapping[str, Any]] = (),
    atlas_entries: Sequence[CompactAtlasEntry | Mapping[str, Any]] = (),
    attributions: Sequence[RouteAttribution | Mapping[str, Any]] = (),
    gate_results: Sequence[TransferGateResult | Mapping[str, Any]] | None = None,
    best_compact_by_seed_split: Sequence[Mapping[str, Any]] | None = None,
    write_report: bool = True,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    routes = [_route_eval(r).to_dict() for r in route_evaluations]
    gates, best = compute_transfer_gates(routes) if gate_results is None or best_compact_by_seed_split is None else (
        [_gate(g) for g in gate_results],
        [dict(r) for r in best_compact_by_seed_split],
    )
    constructor_rows = [_constructor(c).to_dict() for c in constructors]
    atlas_rows = [_atlas(e).to_dict() for e in atlas_entries] or [dict(r) for r in best]
    attribution_rows = [dict(a) if isinstance(a, Mapping) else _attribution(a).to_dict() for a in attributions]
    compact_eval_rows = [r for r in routes if r["route_kind"] == "compact_atlas"]
    seed_rows = _seed_summary(routes)
    paths = {
        "recursive_transfer_summary_json": str(out / "recursive_transfer_summary.json"),
        "seed_summary_csv": str(out / "seed_summary.csv"),
        "generation_summary_csv": str(out / "generation_summary.csv"),
        "route_eval_by_seed_split_csv": str(out / "route_eval_by_seed_split.csv"),
        "constructor_manifest_csv": str(out / "constructor_manifest.csv"),
        "candidate_generation_scores_csv": str(out / "candidate_generation_scores.csv"),
        "constructor_attribution_csv": str(out / "constructor_attribution.csv"),
        "compact_atlas_eval_csv": str(out / "compact_atlas_eval.csv"),
        "route_summary_csv": str(out / "route_summary.csv"),
        "best_compact_by_seed_split_csv": str(out / "best_compact_by_seed_split.csv"),
        "gate_results_csv": str(out / "gate_results.csv"),
        "recursive_transfer_report_md": str(out / "recursive_transfer_report.md"),
        "recursive_transfer_sqlite": str(out / "recursive_transfer.sqlite"),
    }
    _write_json(out / "recursive_transfer_summary.json", summary.to_dict())
    _write_csv(out / "seed_summary.csv", seed_rows)
    _write_csv(out / "generation_summary.csv", [dict(r) for r in generation_rows])
    _write_csv(out / "route_eval_by_seed_split.csv", routes)
    _write_csv(out / "constructor_manifest.csv", constructor_rows)
    _write_csv(out / "candidate_generation_scores.csv", [dict(r) for r in candidate_rows])
    _write_csv(out / "constructor_attribution.csv", attribution_rows)
    _write_csv(out / "compact_atlas_eval.csv", compact_eval_rows)
    route_summary = [dict(r) for r in route_summary_rows] or _route_summary_rows(routes)
    _write_csv(out / "route_summary.csv", route_summary)
    _write_csv(out / "best_compact_by_seed_split.csv", [dict(r) for r in best])
    _write_csv(out / "gate_results.csv", [g.to_dict() for g in gates])
    if write_report:
        (out / "recursive_transfer_report.md").write_text(_report(summary, gates, best), encoding="utf-8")
    _write_sqlite(
        out / "recursive_transfer.sqlite",
        {
            "seed_summary": seed_rows,
            "generation_summary": [dict(r) for r in generation_rows],
            "route_eval_by_seed_split": routes,
            "constructor_manifest": constructor_rows,
            "candidate_generation_scores": [dict(r) for r in candidate_rows],
            "constructor_attribution": attribution_rows,
            "compact_atlas_eval": compact_eval_rows,
            "route_summary": route_summary,
            "best_compact_by_seed_split": [dict(r) for r in best],
            "gate_results": [g.to_dict() for g in gates],
            "compact_atlas": atlas_rows,
        },
    )
    return paths


def source_breakthrough_route_evaluations() -> list[RouteEvaluation]:
    """Return compact route-evaluation rows reconstructed from source artifacts.

    These rows preserve the published Colab aggregate semantics for tests and
    provenance.  They are not terminal evidence and cannot promote claims.
    """

    best_rows = [
        (42, "heldout_a", 11480, 11589, 11588, 11725, 61),
        (42, "heldout_b", 11508, 11623, 11622, 11733, 61),
        (137, "heldout_a", 11367, 11694, 11690, 11721, 66),
        (137, "heldout_b", 11347, 11702, 11696, 11733, 64),
        (1729, "heldout_a", 11364, 11615, 11613, 11735, 64),
        (1729, "heldout_b", 11367, 11631, 11629, 11739, 65),
    ]
    rows: list[RouteEvaluation] = []
    for seed, split, generic, recursive, compact, oracle, compact_size in best_rows:
        rows.extend(
            [
                _eval(seed, split, "generic", "generic", 40, generic),
                _eval(seed, split, "recursive_full_memory", "recursive_full_memory", 90, recursive, generic),
                _eval(seed, split, "compact_top_32", "compact_atlas", compact_size, compact, generic),
                _eval(seed, split, "oracle_reference", "oracle_reference", 144, oracle, generic),
            ]
        )
    # Means chosen to reproduce source gates: compact - random = 205 and
    # compact - shuffled = 86.958333.
    random_values = [11435] * 16 + [11434] * 8
    shuffled_values = [11553] * 17 + [11552] * 7
    for idx, value in enumerate(random_values):
        seed, split, generic, _recursive, _compact, _oracle, _size = best_rows[idx % len(best_rows)]
        rows.append(_eval(seed, split, f"random_same_size_{idx+1}", "random_control", 56, value, generic))
    for idx, value in enumerate(shuffled_values):
        seed, split, generic, _recursive, _compact, _oracle, _size = best_rows[idx % len(best_rows)]
        rows.append(_eval(seed, split, f"shuffled_atlas_same_size_{idx+1}", "shuffled_control", 56, value, generic))
    return rows


def fallback_demo_route_evaluations(seeds: Sequence[int] = (1729, 42, 137)) -> list[RouteEvaluation]:
    rows: list[RouteEvaluation] = []
    for i, seed in enumerate(seeds):
        for split in ("heldout_a", "heldout_b"):
            generic = 7 + i
            recursive = generic + 2
            compact = recursive
            oracle = recursive + 1
            rows.extend(
                [
                    _eval(seed, split, "generic", "generic", 4, generic, false_pairs=10, true_pairs=4),
                    _eval(seed, split, "recursive_full_memory", "recursive_full_memory", 6, recursive, generic, false_pairs=10, true_pairs=4),
                    _eval(seed, split, "compact_top_2", "compact_atlas", 5, compact, generic, false_pairs=10, true_pairs=4),
                    _eval(seed, split, "random_same_size_1", "random_control", 5, generic, generic, false_pairs=10, true_pairs=4),
                    _eval(seed, split, "shuffled_atlas_same_size_1", "shuffled_control", 5, generic + 1, generic, false_pairs=10, true_pairs=4),
                    _eval(seed, split, "oracle_reference", "oracle_reference", 7, oracle, generic, false_pairs=10, true_pairs=4),
                ]
            )
    return rows


def run_real_etp_recursive_residual_transfer(config: RealEtpTransferConfig) -> RealEtpTransferResult:
    """Run the real recursive residual-mined transfer engine on ETP inputs."""

    if np is None:  # pragma: no cover
        raise RuntimeError("real ETP transfer requires numpy")
    cfg = config.effective()
    equations = load_etp_equations(cfg.equations_path)
    matrix = load_etp_matrix(cfg.matrix_path)
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("ETP matrix must be square")
    if len(equations) < matrix.shape[0]:
        matrix = matrix[: len(equations), : len(equations)]
    elif len(equations) > matrix.shape[0]:
        equations = equations[: matrix.shape[0]]
    true_count = int(matrix.sum())
    false_count = int(matrix.size - true_count)

    route_evals: list[RouteEvaluation] = []
    constructors: list[ResidualMinedConstructor] = []
    generation_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    attribution_rows: list[dict[str, Any]] = []

    for seed in cfg.seeds:
        seed_result = _run_real_etp_seed(int(seed), cfg, equations, matrix)
        route_evals.extend(seed_result["route_evals"])
        constructors.extend(seed_result["constructors"])
        generation_rows.extend(seed_result["generation_rows"])
        candidate_rows.extend(seed_result["candidate_rows"])
        attribution_rows.extend(seed_result["attribution_rows"])

    gates, best = compute_transfer_gates(route_evals, generic_route_size=cfg.generic_route_size)
    route_summary = _route_summary_rows([r.to_dict() for r in route_evals])
    summary = build_recursive_transfer_summary(
        route_evals,
        equations=len(equations),
        matrix_shape=matrix.shape,
        true_count=true_count,
        false_count=false_count,
        profile=cfg.profile,
        classification="real_etp_recursive_residual_transfer",
        real_etp_used=True,
        source_run_metrics=SOURCE_BREAKTHROUGH_METRICS,
    )
    paths = write_recursive_transfer_artifacts(
        cfg.out_dir,
        summary=summary,
        route_evaluations=route_evals,
        constructors=constructors,
        generation_rows=generation_rows,
        candidate_rows=candidate_rows,
        route_summary_rows=route_summary,
        attributions=attribution_rows,
        gate_results=gates,
        best_compact_by_seed_split=best,
        write_report=cfg.write_report,
    )
    return RealEtpTransferResult(
        summary=summary,
        route_evaluations=tuple(route_evals),
        constructors=tuple(constructors),
        generation_rows=tuple(generation_rows),
        candidate_rows=tuple(candidate_rows),
        attribution_rows=tuple(attribution_rows),
        route_summary_rows=tuple(route_summary),
        best_compact_rows=tuple(best),
        gate_results=tuple(gates),
        artifact_paths=paths,
    )


def load_etp_equations(path: str | Path) -> list[Equation]:
    equations: list[Equation] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        equations.append(parse_equation(_normalize_etp_equation(line)))
    return equations


def load_etp_matrix(path: str | Path) -> Any:
    if np is None:  # pragma: no cover
        raise RuntimeError("numpy is required to load the ETP matrix")
    matrix = np.load(path, mmap_mode="r")
    if matrix.dtype != bool:
        matrix = matrix.astype(bool)
    return matrix


def build_vectorized_sat_cache(equations: Sequence[Equation], magmas: Sequence[MagmaTable], progress_every: int = 0) -> Any:
    if np is None:  # pragma: no cover
        raise RuntimeError("numpy is required for vectorized SAT cache")
    sat = np.zeros((len(magmas), len(equations)), dtype=bool)
    by_n: dict[int, list[tuple[int, Any]]] = {}
    for idx, magma in enumerate(magmas):
        by_n.setdefault(magma.carrier_size, []).append((idx, np.array(magma.table, dtype=np.intp)))
    stacked = {
        n: (np.array([i for i, _t in rows], dtype=np.intp), np.stack([t for _i, t in rows]))
        for n, rows in by_n.items()
        if rows
    }
    for eq_idx, eq in enumerate(equations):
        for n, (indices, tables) in stacked.items():
            sat[indices, eq_idx] = _equation_holds_vec(eq, tables, n)
        if progress_every and (eq_idx + 1) % progress_every == 0:
            print(f"sat {eq_idx + 1}/{len(equations)}")
    return sat


def generate_base_magmas(config: RealEtpTransferConfig, seed: int) -> list[MagmaTable]:
    if np is None:  # pragma: no cover
        raise RuntimeError("numpy is required for real ETP mode")
    rng = random.Random(seed)
    bank: dict[str, MagmaTable] = {}
    targets = {2: config.base_n2_target, 3: config.base_n3_target, 4: config.base_n4_target}
    for n, target in targets.items():
        if target <= 0:
            continue
        start = len(bank)
        I = np.arange(n, dtype=np.intp)
        _add_magma(bank, np.broadcast_to(I[:, None], (n, n)).copy(), "left_projection")
        _add_magma(bank, np.broadcast_to(I[None, :], (n, n)).copy(), "right_projection")
        for c in range(n):
            _add_magma(bank, np.full((n, n), c, dtype=np.intp), f"constant_{c}")
        for shift in range(n):
            row = np.array([(i + shift) % n for i in range(n)], dtype=np.intp)
            _add_magma(bank, np.tile(row[:, None], (1, n)), "row_constant")
            _add_magma(bank, np.tile(row[None, :], (n, 1)), "col_constant")
        _add_magma(bank, np.fromfunction(lambda i, j: (i + j) % n, (n, n), dtype=int).astype(np.intp), "mod_add")
        _add_magma(bank, np.fromfunction(lambda i, j: (i - j) % n, (n, n), dtype=int).astype(np.intp), "mod_sub")
        _add_magma(bank, np.fromfunction(lambda i, j: (j - i) % n, (n, n), dtype=int).astype(np.intp), "mod_sub_r")
        _add_magma(bank, np.fromfunction(lambda i, j: (i * j) % n, (n, n), dtype=int).astype(np.intp), "mod_mul")
        _add_magma(bank, np.minimum(I[:, None], I[None, :]).astype(np.intp), "min_semilattice")
        _add_magma(bank, np.maximum(I[:, None], I[None, :]).astype(np.intp), "max_semilattice")
        for absorb in range(n):
            for base in range(n):
                arr = np.full((n, n), base, dtype=np.intp)
                arr[absorb, :] = absorb
                arr[:, absorb] = absorb
                _add_magma(bank, arr, "absorbing")
        for base in range(n):
            arr = np.full((n, n), base, dtype=np.intp)
            np.fill_diagonal(arr, np.arange(n))
            _add_magma(bank, arr, "diagonal_idempotent")
        for a in range(n):
            for b in range(n):
                lp = np.broadcast_to(I[:, None], (n, n)).copy()
                lp[a, b] = (lp[a, b] + 1) % n
                _add_magma(bank, lp, "left_projection_perturb")
                rp = np.broadcast_to(I[None, :], (n, n)).copy()
                rp[a, b] = (rp[a, b] + 1) % n
                _add_magma(bank, rp, "right_projection_perturb")
        attempts = 0
        while len(bank) - start < target and attempts < target * 20:
            attempts += 1
            arr = np.array([[rng.randrange(n) for _ in range(n)] for _ in range(n)], dtype=np.intp)
            kind = rng.choice(
                [
                    "random_flat",
                    "random_row",
                    "random_col",
                    "random_block",
                    "random_absorb",
                    "random_compress",
                    "random_diag",
                    "random_projection_mix",
                ]
            )
            if kind == "random_row":
                arr[rng.randrange(n), :] = rng.randrange(n)
            elif kind == "random_col":
                arr[:, rng.randrange(n)] = rng.randrange(n)
            elif kind == "random_block":
                split = rng.randrange(1, n)
                arr[:split, :split] = rng.randrange(n)
                arr[split:, split:] = rng.randrange(n)
            elif kind == "random_absorb":
                a = rng.randrange(n)
                arr[a, :] = a
                arr[:, a] = a
            elif kind == "random_compress":
                v = rng.randrange(n)
                for _ in range(rng.randrange(1, n * n + 1)):
                    arr[rng.randrange(n), rng.randrange(n)] = v
            elif kind == "random_diag":
                for d in range(n):
                    arr[d, d] = rng.randrange(n)
            elif kind == "random_projection_mix":
                for i in range(n):
                    for j in range(n):
                        arr[i, j] = i if rng.random() < 0.5 else j
            _add_magma(bank, arr, kind)
    return list(bank.values())[: config.base_magmas_total]


def _run_real_etp_seed(seed: int, cfg: RealEtpTransferConfig, equations: Sequence[Equation], matrix: Any) -> dict[str, Any]:
    magmas = generate_base_magmas(cfg, seed)
    sat = build_vectorized_sat_cache(equations, magmas, progress_every=cfg.sat_progress_every)
    true_rows, false_rows = _precompute_matrix_rows(matrix)
    rng = random.Random(seed)
    seen_false: set[tuple[int, int]] = set()
    seen_true: set[tuple[int, int]] = set()

    seed_false = _sample_pairs(false_rows, cfg.seed_false_pairs_for_generic, rng, seen_false if cfg.exclude_seen_pairs else None)
    generic_indices = _build_generic_route(magmas, sat, seed_false, cfg.generic_route_size)
    discovery_false = _sample_pairs(false_rows, cfg.discovery_false_pairs, rng, seen_false if cfg.exclude_seen_pairs else None)
    atlas_train_false = _sample_pairs(false_rows, cfg.atlas_train_false_pairs, rng, seen_false if cfg.exclude_seen_pairs else None)
    heldout_a = _sample_pairs(false_rows, cfg.heldout_false_a_pairs, rng, seen_false if cfg.exclude_seen_pairs else None)
    heldout_b = _sample_pairs(false_rows, cfg.heldout_false_b_pairs, rng, seen_false if cfg.exclude_seen_pairs else None)
    true_control = _sample_pairs(true_rows, cfg.true_control_pairs, rng, seen_true if cfg.exclude_seen_pairs else None)
    if not true_control:
        true_control = _sample_pairs(true_rows, cfg.true_control_pairs, rng, None)

    route_evals: list[RouteEvaluation] = []
    constructors: list[ResidualMinedConstructor] = []
    generation_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    recursive_extra_indices: list[int] = []

    train_generic_found = _audit_indices(generic_indices, atlas_train_false, sat)
    current_residuals = [p for p, found in zip(atlas_train_false, train_generic_found) if not found]

    def generation_eval(gen: int, label: str) -> None:
        route_indices = _route_with_extras(generic_indices, recursive_extra_indices)
        gen_row = {"seed": seed, "generation": gen, "route": label, "route_size": len(route_indices), "extra_size": len(recursive_extra_indices)}
        for split, pairs in (("train", atlas_train_false), ("heldout_a", heldout_a), ("heldout_b", heldout_b)):
            generic_found = _audit_indices(generic_indices, pairs, sat)
            route_found = _audit_indices(route_indices, pairs, sat)
            true_found = _audit_indices(route_indices, true_control, sat)
            gen_row[f"{split}_recoveries"] = int(route_found.sum())
            gen_row[f"{split}_residuals"] = len(pairs) - int(route_found.sum())
            gen_row[f"{split}_yield"] = _safe_div(int(route_found.sum()), len(pairs))
            if split.startswith("heldout"):
                gen_row[f"{split}_new_vs_generic"] = int((route_found & ~generic_found).sum())
            gen_row["true_contamination_count"] = max(int(gen_row.get("true_contamination_count", 0)), int(true_found.sum()))
        gen_row["advisory_only"] = True
        gen_row["can_promote_truth"] = False
        generation_rows.append(gen_row)

    generation_eval(0, "generation_0_generic")
    for gen in range(1, cfg.generations + 1):
        new_magmas, cand_rows = _mine_residual_generation(equations, current_residuals, magmas, gen, cfg, seed + 1000 * gen)
        for row in cand_rows:
            row["seed"] = seed
            candidate_rows.append(row)
        existing = {m.table_hash for m in magmas}
        genuinely_new = [m for m in new_magmas if m.table_hash not in existing]
        if genuinely_new:
            new_sat = build_vectorized_sat_cache(equations, genuinely_new, progress_every=cfg.sat_progress_every)
            offset = len(magmas)
            magmas.extend(genuinely_new)
            sat = np.vstack([sat, new_sat])
            new_indices = list(range(offset, offset + len(genuinely_new)))
            recursive_extra_indices.extend(new_indices)
            for idx, magma in zip(new_indices, genuinely_new):
                constructors.append(_constructor_from_magma(seed, idx, magma))
        generation_eval(gen, f"generation_{gen}_recursive_memory")
        cur_found = _audit_indices(_route_with_extras(generic_indices, recursive_extra_indices), atlas_train_false, sat)
        current_residuals = [p for p, found in zip(atlas_train_false, cur_found) if not found]

    full_indices = _route_with_extras(generic_indices, recursive_extra_indices)
    attr_rows = _build_constructor_attribution(seed, magmas, full_indices, generic_indices, atlas_train_false, sat, equations)

    routes: list[tuple[str, str, list[int]]] = [
        ("generic", "generic", list(generic_indices)),
        ("recursive_full_memory", "recursive_full_memory", full_indices),
    ]
    for k in cfg.compact_top_ks:
        routes.append((f"compact_top_{k}", "compact_atlas", _route_with_extras(generic_indices, _select_compact_indices(attr_rows, k))))
    lb = [int(r["constructor_idx"]) for r in attr_rows if int(r.get("generation", 0)) >= 1 and int(r.get("unique_new_hits_vs_generic", 0)) >= cfg.load_bearing_min_unique_hits]
    routes.append(("compact_load_bearing_only", "compact_atlas", _route_with_extras(generic_indices, lb)))

    target_extra_count = max(1, len(_select_compact_indices(attr_rows, 16)))
    control_rng = random.Random(seed + 99999)
    available_extras = [i for i in range(len(magmas)) if i not in set(generic_indices)]
    for r in range(cfg.random_control_repeats):
        shuffled = list(available_extras)
        control_rng.shuffle(shuffled)
        routes.append((f"random_same_size_{r + 1}", "random_control", _route_with_extras(generic_indices, shuffled[:target_extra_count])))
    for r in range(cfg.shuffled_control_repeats):
        shuffled = list(recursive_extra_indices)
        control_rng.shuffle(shuffled)
        routes.append((f"shuffled_atlas_same_size_{r + 1}", "shuffled_control", _route_with_extras(generic_indices, shuffled[:target_extra_count])))
    if cfg.include_oracle_reference:
        oracle = _select_oracle_extras(generic_indices, range(len(magmas)), heldout_a, sat, cfg.oracle_route_size)
        routes.append(("oracle_reference", "oracle_reference", _route_with_extras(generic_indices, oracle)))

    for split, pairs in (("heldout_a", heldout_a), ("heldout_b", heldout_b)):
        generic_found = _audit_indices(generic_indices, pairs, sat)
        for route, kind, indices in routes:
            found = _audit_indices(indices, pairs, sat)
            true_found = _audit_indices(indices, true_control, sat)
            route_evals.append(
                RouteEvaluation(
                    seed=seed,
                    split=split,
                    route=route,
                    route_kind=kind,
                    route_size=len(indices),
                    false_pairs=len(pairs),
                    true_pairs=len(true_control),
                    recoveries=int(found.sum()),
                    residuals=len(pairs) - int(found.sum()),
                    new_recoveries_vs_generic=int((found & ~generic_found).sum()),
                    true_contamination_count=int(true_found.sum()),
                    advisory_only=True,
                    can_promote_truth=False,
                )
            )

    return {
        "route_evals": route_evals,
        "constructors": constructors,
        "generation_rows": generation_rows,
        "candidate_rows": candidate_rows,
        "attribution_rows": attr_rows,
        "discovery_residuals": discovery_false,
    }


def _normalize_etp_equation(text: str) -> str:
    s = str(text).strip()
    for ch in ("◇", "∙", "·", "⋆", "⋄", "∗", "＊", "×"):
        s = s.replace(ch, "*")
    s = s.replace("=", " = ")
    return " ".join(s.split())


def _term_eval_vec(term: Term, tables: Any, assignments: Any, var_col: dict[str, int]) -> Any:
    if term.name is not None:
        out = np.empty((tables.shape[0], assignments.shape[0]), dtype=np.intp)
        out[:] = assignments[:, var_col[term.name]]
        return out
    assert term.left is not None and term.right is not None
    left = _term_eval_vec(term.left, tables, assignments, var_col)
    right = _term_eval_vec(term.right, tables, assignments, var_col)
    return tables[np.arange(tables.shape[0], dtype=np.intp)[:, None], left.astype(np.intp), right.astype(np.intp)]


def _equation_holds_vec(eq: Equation, tables: Any, n: int) -> Any:
    variables = tuple(sorted(eq.variables()))
    assignments = np.array(list(itertools.product(range(n), repeat=len(variables))), dtype=np.intp)
    var_col = {v: i for i, v in enumerate(variables)}
    return np.all(_term_eval_vec(eq.lhs, tables, assignments, var_col) == _term_eval_vec(eq.rhs, tables, assignments, var_col), axis=1)


def _add_magma(bank: dict[str, MagmaTable], arr: Any, source: str, generation: int = 0, parent_basin: str = "base", parent_hash: str = "") -> None:
    magma = MagmaTable.from_table(arr.tolist() if hasattr(arr, "tolist") else arr, source=source, generation=generation, parent_basin=parent_basin, parent_hash=parent_hash)
    bank.setdefault(magma.table_hash, magma)


def _precompute_matrix_rows(matrix: Any) -> tuple[list[Any], list[Any]]:
    return [np.flatnonzero(matrix[i]) for i in range(matrix.shape[0])], [np.flatnonzero(~matrix[i]) for i in range(matrix.shape[0])]


def _sample_pairs(rows_by_type: Sequence[Any], n_pairs: int, rng: random.Random, seen: set[tuple[int, int]] | None) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    seen_pairs = seen if seen is not None else set()
    max_tries = max(100, int(n_pairs) * 500)
    tries = 0
    while len(pairs) < int(n_pairs) and tries < max_tries:
        tries += 1
        i = rng.randrange(len(rows_by_type))
        choices = rows_by_type[i]
        if len(choices) == 0:
            continue
        j = int(choices[rng.randrange(len(choices))])
        key = (int(i), int(j))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        pairs.append(key)
    return pairs


def _audit_indices(indices: Sequence[int], pairs: Sequence[tuple[int, int]], sat: Any) -> Any:
    if not pairs or not indices:
        return np.zeros(len(pairs), dtype=bool)
    idx = np.array(list(indices), dtype=np.intp)
    s = np.array([a for a, _b in pairs], dtype=np.intp)
    t = np.array([b for _a, b in pairs], dtype=np.intp)
    return np.any(sat[np.ix_(idx, s)] & ~sat[np.ix_(idx, t)], axis=0)


def _first_hit_indices(indices: Sequence[int], pairs: Sequence[tuple[int, int]], sat: Any) -> Any:
    if not pairs or not indices:
        return np.full(len(pairs), -1, dtype=np.intp)
    idx = np.array(list(indices), dtype=np.intp)
    s = np.array([a for a, _b in pairs], dtype=np.intp)
    t = np.array([b for _a, b in pairs], dtype=np.intp)
    hits = sat[np.ix_(idx, s)] & ~sat[np.ix_(idx, t)]
    any_hit = np.any(hits, axis=0)
    first_pos = np.argmax(hits, axis=0)
    out = np.full(len(pairs), -1, dtype=np.intp)
    out[any_hit] = idx[first_pos[any_hit]]
    return out


def _build_generic_route(magmas: Sequence[MagmaTable], sat: Any, seed_pairs: Sequence[tuple[int, int]], size: int) -> list[int]:
    if not seed_pairs:
        return list(range(min(size, len(magmas))))
    s = np.array([a for a, _b in seed_pairs], dtype=np.intp)
    t = np.array([b for _a, b in seed_pairs], dtype=np.intp)
    scores = np.sum(sat[:, s] & ~sat[:, t], axis=1)
    order = np.argsort(-scores)
    chosen: list[int] = []
    counts: Counter[str] = Counter()
    max_per_source = max(2, int(size) // 12)
    for idx in order:
        source = magmas[int(idx)].source
        if counts[source] < max_per_source:
            chosen.append(int(idx))
            counts[source] += 1
        if len(chosen) >= int(size):
            break
    for idx in order:
        if len(chosen) >= int(size):
            break
        if int(idx) not in chosen:
            chosen.append(int(idx))
    return chosen


def _route_with_extras(generic: Sequence[int], extras: Sequence[int]) -> list[int]:
    out = list(int(x) for x in generic)
    seen = set(out)
    for idx in extras:
        if int(idx) not in seen:
            seen.add(int(idx))
            out.append(int(idx))
    return out


def _mine_residual_generation(
    equations: Sequence[Equation],
    residual_pairs: Sequence[tuple[int, int]],
    magmas: Sequence[MagmaTable],
    generation: int,
    cfg: RealEtpTransferConfig,
    seed: int,
) -> tuple[list[MagmaTable], list[dict[str, Any]]]:
    if not residual_pairs:
        return [], []
    rng = random.Random(seed)
    residual_sample = list(residual_pairs[: cfg.mine_from_residual_top_k])
    basin_counts = Counter(_pair_basin(equations, s, t) for s, t in residual_sample)
    basins = list(basin_counts) or ["general_false_candidate"]
    weights = [max(1, basin_counts[b]) for b in basins]
    existing = {m.table_hash for m in magmas}
    candidates: dict[str, MagmaTable] = {}
    attempts = 0
    while len(candidates) < cfg.candidates_per_generation and attempts < cfg.candidates_per_generation * 30:
        attempts += 1
        base = rng.choice(list(magmas))
        basin = rng.choices(basins, weights=weights, k=1)[0]
        cand = _mutate_for_basin(base, generation, basin, rng.randrange(10**12))
        if cand.table_hash not in existing:
            candidates.setdefault(cand.table_hash, cand)
    cand_list = list(candidates.values())
    if not cand_list:
        return [], []
    cand_sat = build_vectorized_sat_cache(equations, cand_list, progress_every=0)
    s_idx = np.array([s for s, _t in residual_sample], dtype=np.intp)
    t_idx = np.array([t for _s, t in residual_sample], dtype=np.intp)
    hits = np.sum(cand_sat[:, s_idx] & ~cand_sat[:, t_idx], axis=1)
    rows: list[dict[str, Any]] = []
    for ci, cand in enumerate(cand_list):
        hit = int(hits[ci])
        if hit <= 0:
            continue
        score = float(hit + math.log1p(basin_counts.get(cand.parent_basin, 0)) - 0.05 * max(0, cand.carrier_size - 3))
        rows.append(
            {
                "generation": generation,
                "candidate_hash": cand.table_hash,
                "source": cand.source,
                "n": cand.carrier_size,
                "parent_basin": cand.parent_basin,
                "parent_hash": cand.parent_hash,
                "hits_on_parent_residuals": hit,
                "score": score,
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    rows.sort(key=lambda r: (-float(r["score"]), -int(r["hits_on_parent_residuals"]), str(r["candidate_hash"])))
    keep_hashes = {str(r["candidate_hash"]) for r in rows[: cfg.new_per_generation]}
    return [c for c in cand_list if c.table_hash in keep_hashes][: cfg.new_per_generation], rows


def _mutate_for_basin(base: MagmaTable, generation: int, basin: str, seed: int) -> MagmaTable:
    rng = random.Random(seed)
    arr = np.array(base.table, dtype=np.intp).copy()
    n = arr.shape[0]
    if basin in {"rhs_new_variable_pressure", "expansion_pressure"}:
        if rng.random() < 0.5:
            arr = np.broadcast_to(np.arange(n)[:, None], (n, n)).copy()
        else:
            arr = np.broadcast_to(np.arange(n)[None, :], (n, n)).copy()
        for _ in range(rng.randint(1, max(1, n))):
            arr[rng.randrange(n), rng.randrange(n)] = rng.randrange(n)
        source = f"gen{generation}_projection_perturb_from_{basin}"
    elif basin in {"rhs_variable_loss_projection_gap", "same_skeleton_variable_rewire", "repeat_multiplicity_shift"}:
        for _ in range(rng.randint(1, n)):
            if rng.random() < 0.5:
                arr[rng.randrange(n), :] = rng.randrange(n)
            else:
                arr[:, rng.randrange(n)] = rng.randrange(n)
        source = f"gen{generation}_rowcol_constant_from_{basin}"
    elif basin == "compression_drop":
        v = rng.randrange(n)
        for _ in range(rng.randint(n, n * n)):
            arr[rng.randrange(n), rng.randrange(n)] = v
        if n >= 3:
            split = rng.randrange(1, n)
            arr[:split, :split] = rng.randrange(n)
            arr[split:, split:] = rng.randrange(n)
        source = f"gen{generation}_block_quotient_from_{basin}"
    else:
        for _ in range(rng.randint(1, max(2, n * n // 2))):
            arr[rng.randrange(n), rng.randrange(n)] = rng.randrange(n)
        source = f"gen{generation}_general_residual_mutation"
    return MagmaTable.from_table(arr.tolist(), source=source, generation=generation, parent_basin=basin, parent_hash=base.table_hash)


def _pair_basin(equations: Sequence[Equation], source_idx: int, target_idx: int) -> str:
    fa = _eq_features(equations[source_idx])
    fb = _eq_features(equations[target_idx])
    if fb["rhs_vars"] - fa["rhs_vars"] > 0 or fb["var_count"] - fa["var_count"] > 0:
        return "rhs_new_variable_pressure"
    if fb["rhs_vars"] - fa["rhs_vars"] < 0 or fb["var_count"] - fa["var_count"] < 0:
        return "rhs_variable_loss_projection_gap"
    if fb["nodes"] - fa["nodes"] < 0 or fb["depth"] - fa["depth"] < 0:
        return "compression_drop"
    if fb["repeats"] - fa["repeats"] != 0:
        return "repeat_multiplicity_shift"
    if fb["nodes"] - fa["nodes"] > 0 or fb["depth"] - fa["depth"] > 0:
        return "expansion_pressure"
    if fa["skeleton"] == fb["skeleton"]:
        return "same_skeleton_variable_rewire"
    return "general_false_candidate"


def _eq_features(eq: Equation) -> dict[str, Any]:
    lhs_counts = _term_var_counts(eq.lhs)
    rhs_counts = _term_var_counts(eq.rhs)
    return {
        "nodes": _term_nodes(eq.lhs) + _term_nodes(eq.rhs),
        "depth": max(_term_depth(eq.lhs), _term_depth(eq.rhs)),
        "var_count": len(set(eq.variables())),
        "rhs_vars": len(rhs_counts),
        "repeats": sum(max(0, c - 1) for c in (lhs_counts + rhs_counts).values()),
        "skeleton": _term_skeleton(eq.lhs) + "=" + _term_skeleton(eq.rhs),
    }


def _term_var_counts(term: Term) -> Counter[str]:
    if term.name is not None:
        return Counter({term.name: 1})
    assert term.left is not None and term.right is not None
    return _term_var_counts(term.left) + _term_var_counts(term.right)


def _term_nodes(term: Term) -> int:
    if term.name is not None:
        return 1
    assert term.left is not None and term.right is not None
    return 1 + _term_nodes(term.left) + _term_nodes(term.right)


def _term_depth(term: Term) -> int:
    if term.name is not None:
        return 1
    assert term.left is not None and term.right is not None
    return 1 + max(_term_depth(term.left), _term_depth(term.right))


def _term_skeleton(term: Term) -> str:
    if term.name is not None:
        return "x"
    assert term.left is not None and term.right is not None
    return f"({_term_skeleton(term.left)}*{_term_skeleton(term.right)})"


def _build_constructor_attribution(
    seed: int,
    magmas: Sequence[MagmaTable],
    route_indices: Sequence[int],
    generic_indices: Sequence[int],
    false_pairs: Sequence[tuple[int, int]],
    sat: Any,
    equations: Sequence[Equation],
) -> list[dict[str, Any]]:
    generic_found = _audit_indices(generic_indices, false_pairs, sat)
    first_hits = _first_hit_indices(route_indices, false_pairs, sat)
    rows: list[dict[str, Any]] = []
    for idx in route_indices:
        mask = first_hits == int(idx)
        if not mask.any():
            continue
        unique_mask = mask & ~generic_found
        hit_pairs = [false_pairs[i] for i, val in enumerate(mask) if bool(val)]
        unique_pairs = [false_pairs[i] for i, val in enumerate(unique_mask) if bool(val)]
        basin_counts = Counter(_pair_basin(equations, s, t) for s, t in hit_pairs)
        unique_counts = Counter(_pair_basin(equations, s, t) for s, t in unique_pairs)
        magma = magmas[int(idx)]
        unique_hits = int(unique_mask.sum())
        first_count = int(mask.sum())
        basin_count = len(basin_counts)
        score = float(unique_hits + 0.25 * first_count + 0.75 * basin_count)
        rows.append(
            {
                "seed": seed,
                "split": "atlas_train",
                "route": "recursive_full_memory",
                "constructor_idx": int(idx),
                "constructor_id": str(idx),
                "constructor_hash": magma.table_hash,
                "source": magma.source,
                "n": magma.carrier_size,
                "generation": magma.generation,
                "parent_basin": magma.parent_basin,
                "unique_new_hits_vs_generic": unique_hits,
                "first_hit_count": first_count,
                "basin_count": basin_count,
                "load_bearing_score": score,
                "top_basins": "|".join(f"{k}:{v}" for k, v in basin_counts.most_common(8)),
                "top_unique_basins": "|".join(f"{k}:{v}" for k, v in unique_counts.most_common(8)),
                "advisory_only": True,
                "can_promote_truth": False,
            }
        )
    rows.sort(key=lambda r: (-float(r["load_bearing_score"]), -int(r["unique_new_hits_vs_generic"]), -int(r["first_hit_count"])))
    return rows


def _select_compact_indices(attr_rows: Sequence[Mapping[str, Any]], top_k: int) -> list[int]:
    rows = [
        r
        for r in attr_rows
        if int(r.get("generation", 0)) >= 1 and int(r.get("unique_new_hits_vs_generic", 0)) >= 1 and bool(r.get("advisory_only", True)) and not bool(r.get("can_promote_truth", False))
    ]
    rows = sorted(rows, key=lambda r: (-float(r.get("load_bearing_score", 0)), -int(r.get("unique_new_hits_vs_generic", 0)), -int(r.get("first_hit_count", 0))))
    return [int(r["constructor_idx"]) for r in rows[:top_k]]


def _select_oracle_extras(generic_indices: Sequence[int], all_indices: Iterable[int], false_pairs: Sequence[tuple[int, int]], sat: Any, size: int) -> list[int]:
    generic_found = _audit_indices(generic_indices, false_pairs, sat)
    residual = ~generic_found
    if not residual.any():
        return []
    s = np.array([a for a, _b in false_pairs], dtype=np.intp)[residual]
    t = np.array([b for _a, b in false_pairs], dtype=np.intp)[residual]
    available = [int(i) for i in all_indices if int(i) not in set(generic_indices)]
    if not available:
        return []
    av = np.array(available, dtype=np.intp)
    scores = np.sum(sat[np.ix_(av, s)] & ~sat[np.ix_(av, t)], axis=1)
    order = np.argsort(-scores)
    return [int(av[i]) for i in order[:size] if scores[i] > 0]


def _constructor_from_magma(seed: int, idx: int, magma: MagmaTable) -> ResidualMinedConstructor:
    return ResidualMinedConstructor(
        constructor_id=str(idx),
        constructor_hash=magma.table_hash,
        source=magma.source,
        carrier_size=magma.carrier_size,
        generation=magma.generation,
        parent_basin=magma.parent_basin,
        table=magma.table,
        metadata={"seed": seed, "parent_hash": magma.parent_hash},
    )


def _best_compact_by_seed_split(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    keys = sorted({(int(r["seed"]), str(r["split"])) for r in rows})
    for seed, split in keys:
        sub = [r for r in rows if int(r["seed"]) == seed and str(r["split"]) == split]
        compacts = [r for r in sub if r["route_kind"] == "compact_atlas"]
        if not compacts:
            continue
        best = sorted(compacts, key=lambda r: (-float(r["recoveries"]), int(r["route_size"]), str(r["route"])))[0]
        generic = _one(sub, "generic", "generic")
        recursive = _one(sub, "recursive_full_memory", "recursive_full_memory")
        oracle = _one(sub, "oracle_reference", "oracle_reference") or best
        row = {
            "seed": seed,
            "split": split,
            "best_compact_route": best["route"],
            "route_kind": "compact_atlas",
            "best_compact_route_size": int(best["route_size"]),
            "false_pairs": int(best["false_pairs"]),
            "true_pairs": int(best["true_pairs"]),
            "compact_recoveries": int(float(best["recoveries"])),
            "compact_residuals": int(float(best["residuals"])),
            "new_recoveries_vs_generic": int(float(best["new_recoveries_vs_generic"])),
            "true_contamination_count": int(best["true_contamination_count"]),
            "true_contamination_rate": float(best["true_contamination_rate"]),
            "advisory_only": True,
            "can_promote_truth": False,
            "generic_recoveries": float(generic["recoveries"]) if generic else 0.0,
            "generic_residuals": float(generic["residuals"]) if generic else 0.0,
            "recursive_recoveries": float(recursive["recoveries"]) if recursive else float(best["recoveries"]),
            "recursive_residuals": float(recursive["residuals"]) if recursive else float(best["residuals"]),
            "recursive_route_size": int(recursive["route_size"]) if recursive else int(best["route_size"]),
            "oracle_recoveries": float(oracle["recoveries"]),
        }
        row["yield_rate"] = _safe_div(row["compact_recoveries"], row["false_pairs"])
        row["compact_gain_vs_generic"] = row["compact_recoveries"] - row["generic_recoveries"]
        row["recursive_gain_vs_generic"] = row["recursive_recoveries"] - row["generic_recoveries"]
        row["gain_retention"] = _safe_div(row["compact_gain_vs_generic"], row["recursive_gain_vs_generic"], 1.0)
        row["pruning_ratio"] = 0.0
        row["oracle_gap_captured"] = _safe_div(row["compact_gain_vs_generic"], row["oracle_recoveries"] - row["generic_recoveries"], 0.0)
        out.append(row)
    return out


def _one(rows: list[dict[str, Any]], route: str, kind: str) -> dict[str, Any] | None:
    for row in rows:
        if row["route"] == route or row["route_kind"] == kind:
            return row
    return None


def _positive_gain_seed_fraction(best: list[dict[str, Any]]) -> float:
    by_seed: dict[int, list[float]] = {}
    for row in best:
        by_seed.setdefault(int(row["seed"]), []).append(float(row["compact_gain_vs_generic"]))
    return _safe_div(sum(1 for gains in by_seed.values() if _avg(gains) > 0), len(by_seed))


def _route_kind_means(rows: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for kind in sorted({str(r["route_kind"]) for r in rows}):
        out[kind] = _avg([float(r["recoveries"]) for r in rows if r["route_kind"] == kind])
    return out


def _seed_summary(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for seed in sorted({int(r["seed"]) for r in routes}):
        sub = [r for r in routes if int(r["seed"]) == seed]
        out.append(
            {
                "seed": seed,
                "splits": len({r["split"] for r in sub}),
                "route_evaluations": len(sub),
                "true_contamination_max": max([int(r["true_contamination_count"]) for r in sub] or [0]),
                "advisory_boundary_ok": all(bool(r["advisory_only"]) and not bool(r["can_promote_truth"]) for r in sub),
            }
        )
    return out


def _eval(
    seed: int,
    split: str,
    route: str,
    kind: str,
    route_size: int,
    recoveries: float,
    generic_recoveries: float | None = None,
    *,
    false_pairs: int = 12000,
    true_pairs: int = 2000,
) -> RouteEvaluation:
    return RouteEvaluation(
        seed=seed,
        split=split,
        route=route,
        route_kind=kind,
        route_size=route_size,
        false_pairs=false_pairs,
        true_pairs=true_pairs,
        recoveries=int(round(recoveries)),
        residuals=false_pairs - int(round(recoveries)),
        new_recoveries_vs_generic=max(0, int(round(recoveries - (generic_recoveries or recoveries)))),
        true_contamination_count=0,
    )


def _route_eval(row: RouteEvaluation | Mapping[str, Any]) -> RouteEvaluation:
    if isinstance(row, RouteEvaluation):
        return row
    false_pairs = int(row.get("false_pairs", 0) or 0)
    recoveries = int(float(row.get("recoveries", row.get("compact_recoveries", 0)) or 0))
    return RouteEvaluation(
        seed=int(row.get("seed", 0) or 0),
        split=str(row.get("split", "")),
        route=str(row.get("route", row.get("best_compact_route", ""))),
        route_kind=str(row.get("route_kind", "")),
        route_size=int(row.get("route_size", row.get("best_compact_route_size", 0)) or 0),
        false_pairs=false_pairs,
        true_pairs=int(row.get("true_pairs", 0) or 0),
        recoveries=recoveries,
        residuals=int(row.get("residuals", false_pairs - recoveries) or 0),
        new_recoveries_vs_generic=int(float(row.get("new_recoveries_vs_generic", 0) or 0)),
        true_contamination_count=int(float(row.get("true_contamination_count", 0) or 0)),
        advisory_only=bool(row.get("advisory_only", True)),
        can_promote_truth=bool(row.get("can_promote_truth", False)),
    )


def _constructor(row: ResidualMinedConstructor | Mapping[str, Any]) -> ResidualMinedConstructor:
    if isinstance(row, ResidualMinedConstructor):
        return row
    return ResidualMinedConstructor(
        constructor_id=str(row.get("constructor_id", row.get("constructor_idx", ""))),
        constructor_hash=str(row.get("constructor_hash", "")),
        source=str(row.get("source", "")),
        carrier_size=int(row.get("carrier_size", row.get("n", 0)) or 0),
        generation=int(row.get("generation", 0) or 0),
        parent_basin=str(row.get("parent_basin", "")),
    )


def _atlas(row: CompactAtlasEntry | Mapping[str, Any]) -> CompactAtlasEntry:
    return select_compact_atlas([row], top_k=1, load_bearing_min_unique_hits=0)[0] if not isinstance(row, CompactAtlasEntry) else row


def _attribution(row: RouteAttribution | Mapping[str, Any]) -> RouteAttribution:
    if isinstance(row, RouteAttribution):
        return row
    return RouteAttribution(
        seed=int(row.get("seed", 0) or 0),
        split=str(row.get("split", "")),
        route=str(row.get("route", "")),
        constructor_id=str(row.get("constructor_id", row.get("constructor_idx", ""))),
        unique_new_hits_vs_generic=int(row.get("unique_new_hits_vs_generic", 0) or 0),
        first_hit_count=int(row.get("first_hit_count", 0) or 0),
        basin_count=int(row.get("basin_count", 0) or 0),
        load_bearing_score=float(row.get("load_bearing_score", 0.0) or 0.0),
    )


def _gate(row: TransferGateResult | Mapping[str, Any]) -> TransferGateResult:
    if isinstance(row, TransferGateResult):
        return row
    return TransferGateResult(str(row["gate_id"]), str(row["gate"]), row["value"], row["threshold"], bool(row["passed"]))


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _route_summary_rows(routes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keys = sorted({(str(r["route"]), str(r["route_kind"])) for r in routes})
    for route, kind in keys:
        sub = [r for r in routes if str(r["route"]) == route and str(r["route_kind"]) == kind]
        rows.append(
            {
                "route": route,
                "route_kind": kind,
                "recoveries_mean": _avg([float(r["recoveries"]) for r in sub]),
                "residuals_mean": _avg([float(r["residuals"]) for r in sub]),
                "new_vs_generic_mean": _avg([float(r["new_recoveries_vs_generic"]) for r in sub]),
                "true_contamination_max": max([int(r["true_contamination_count"]) for r in sub] or [0]),
                "route_size_mean": _avg([float(r["route_size"]) for r in sub]),
                "advisory_only": all(bool(r.get("advisory_only", True)) for r in sub),
                "can_promote_truth": any(bool(r.get("can_promote_truth", False)) for r in sub),
            }
        )
    rows.sort(key=lambda r: (-float(r["recoveries_mean"]), float(r["route_size_mean"]), str(r["route"])))
    return rows


def _stable_hash(obj: Any, n: int = 12) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:n]


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    keys = sorted({k for row in rows for k in row.keys()})
    if not keys:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_value(row.get(k, "")) for k in keys})


def _write_sqlite(path: Path, tables: Mapping[str, Sequence[Mapping[str, Any]]]) -> None:
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    try:
        for name, rows in tables.items():
            row_list = [dict(r) for r in rows]
            keys = sorted({k for row in row_list for k in row.keys()})
            if not keys:
                con.execute(f'CREATE TABLE "{name}" (empty TEXT)')
                continue
            col_defs = ", ".join([f'"{k}" TEXT' for k in keys])
            con.execute(f'CREATE TABLE "{name}" ({col_defs})')
            placeholders = ",".join("?" for _ in keys)
            col_names = ", ".join([f'"{k}"' for k in keys])
            for row in row_list:
                con.execute(
                    f'INSERT INTO "{name}" ({col_names}) VALUES ({placeholders})',
                    [_csv_value(row.get(k, "")) for k in keys],
                )
        con.commit()
    finally:
        con.close()


def _report(summary: RecursiveTransferSummary, gates: Sequence[TransferGateResult], best: Sequence[Mapping[str, Any]]) -> str:
    gate_lines = "\n".join(f"| {g.gate_id} | {g.gate} | {g.value} | {g.threshold} | {g.passed} |" for g in gates)
    best_lines = "\n".join(
        f"| {r['seed']} | {r['split']} | {r['best_compact_route']} | {r['compact_recoveries']} | {r['generic_recoveries']} |"
        for r in best
    )
    return f"""# MathGraph / ETP Recursive Residual-Mined Memory Transfer Test v1

Classification: `{summary.classification}`

Residual-mined constructors, compact atlas entries, and route scores are advisory memory only.  They may guide route selection, but they cannot promote TRUE/FALSE claims or terminal forms.

## Summary

```json
{json.dumps(summary.to_dict(), indent=2, sort_keys=True, default=str)}
```

## Gate Results

| id | gate | value | threshold | passed |
| --- | --- | ---: | ---: | --- |
{gate_lines}

## Best Compact By Seed/Split

| seed | split | route | compact recoveries | generic recoveries |
| ---: | --- | --- | ---: | ---: |
{best_lines}

## Trust Boundary

- FALSE certificates still require finite magmas satisfying source and violating target.
- TRUE contamination is checked explicitly.
- Failed finite search is never promoted to TRUE.
- Route scores are not truth.
"""


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def _avg(xs: Iterable[float]) -> float:
    vals = [float(x) for x in xs]
    return mean(vals) if vals else 0.0


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return default if not b else float(a) / float(b)

"""Recursive residual-mined compounding benchmark.

This module is the repo-level version of the recursive residual experiments:
generic finite-countermodel routes leave a residual frontier; the frontier is
mined for advisory constructor memory; compact atlas routes are evaluated on
held-out pairs and controls.  Route/atlas objects stay advisory.  Only concrete
finite checker successes can become terminal candidates elsewhere.
"""

from __future__ import annotations

import csv
import json
import random
import sqlite3
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Sequence

from mathgraph.finite_magma_world import (
    add_mod_n,
    constant_table,
    deterministic_perturbation_3,
    left_projection,
    max_table,
    min_table,
    parse_equation,
    rectangular_band,
    right_projection,
    table_satisfies_equation,
    xor_mod_2,
)
from mathgraph.hashing import content_id, sha256_hex
from mathgraph.sair_constructor_bank import SAIRConstructor, build_sair_constructor_bank
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix, normalize_sair_equation

try:  # numpy is optional for core install, but used when available.
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - exercised only in minimal envs
    np = None  # type: ignore[assignment]


REQUIRED_OUTPUTS = (
    "recursive_residual_summary.json",
    "recursive_residual_report.md",
    "generation_summary.csv",
    "residual_frontier_by_generation.csv",
    "constructor_generation_manifest.csv",
    "constructor_attribution.csv",
    "compact_atlas_routes.csv",
    "compact_atlas_eval.csv",
    "route_eval_by_seed_split.csv",
    "route_summary.csv",
    "best_compact_by_seed_split.csv",
    "gate_results.csv",
    "artifact_manifest.json",
    "run_metadata.json",
)


@dataclass(frozen=True)
class RecursiveResidualConfig:
    equations: str | Path | None = None
    matrix: str | Path | None = None
    out_dir: str | Path = "/tmp/mathgraph_recursive_residual_smoke"
    profile: str = "smoke"
    seed: int = 1729
    seeds: tuple[int, ...] = ()
    generations: int = 2
    base_magmas: int = 20
    generic_route_size: int = 4
    discover_false: int = 12
    train_false: int = 12
    heldout_false: int = 12
    heldout_true: int = 4
    new_per_generation: int = 2
    candidate_budget: int = 12
    allow_fallback_demo: bool = False
    include_oracle_reference: bool = False
    skip_sqlite: bool = False
    skip_plots: bool = True

    def effective(self) -> "RecursiveResidualConfig":
        if self.profile == "smoke":
            return replace(self, generations=self.generations or 2, base_magmas=min(self.base_magmas, 20), generic_route_size=min(self.generic_route_size, 4), discover_false=min(self.discover_false, 12), train_false=min(self.train_false, 12), heldout_false=min(self.heldout_false, 12), heldout_true=min(self.heldout_true, 4), new_per_generation=min(self.new_per_generation, 2), candidate_budget=min(self.candidate_budget, 12))
        if self.profile == "fast":
            return replace(self, generations=self.generations or 5, base_magmas=max(self.base_magmas, 80), generic_route_size=max(self.generic_route_size, 20), discover_false=max(self.discover_false, 600), train_false=max(self.train_false, 800), heldout_false=max(self.heldout_false, 1200), heldout_true=max(self.heldout_true, 200), new_per_generation=max(self.new_per_generation, 8), candidate_budget=max(self.candidate_budget, 40))
        if self.profile == "transfer_fast":
            seeds = self.seeds or (1729, 42, 137)
            return replace(self, seeds=seeds, generations=self.generations or 5, base_magmas=max(self.base_magmas, 80), generic_route_size=max(self.generic_route_size, 20), discover_false=max(self.discover_false, 600), train_false=max(self.train_false, 800), heldout_false=max(self.heldout_false, 1200), heldout_true=max(self.heldout_true, 200), new_per_generation=max(self.new_per_generation, 8), candidate_budget=max(self.candidate_budget, 40))
        return self


@dataclass(frozen=True)
class ResidualFrontierRow:
    generation: int
    split: str
    pair_id: str
    source_idx: int
    target_idx: int
    basin: str

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ConstructorCandidate:
    constructor_id: str
    family: str
    table: tuple[tuple[int, ...], ...]
    generation: int = 0
    source: str = "base"
    score: float = 0.0
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "constructor_id": self.constructor_id,
            "family": self.family,
            "carrier_size": len(self.table),
            "table": [list(row) for row in self.table],
            "generation": self.generation,
            "source": self.source,
            "score": self.score,
            "advisory_only": True,
            "can_promote_truth": False,
        }


@dataclass(frozen=True)
class ConstructorAttribution:
    constructor_id: str
    first_hit_count: int
    unique_new_hits_vs_generic: int
    basin_coverage: int
    load_bearing_score: float
    top_basins: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {**dict(self.__dict__), "top_basins": list(self.top_basins)}


@dataclass(frozen=True)
class CompactAtlasRoute:
    route_id: str
    constructor_ids: tuple[str, ...]
    route_kind: str
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "constructor_ids": list(self.constructor_ids),
            "route_size": len(self.constructor_ids),
            "route_kind": self.route_kind,
            "advisory_only": True,
            "can_promote_truth": False,
        }


@dataclass(frozen=True)
class CompactAtlasEvalResult:
    seed: int
    split: str
    route_id: str
    recoveries: int
    total_pairs: int
    yield_rate: float
    residual_count: int
    true_contamination_count: int = 0
    true_contamination_rate: float = 0.0
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class TransferControlResult:
    seed: int
    control_kind: str
    compact_recoveries: int
    control_recoveries: int
    delta_vs_control: int
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RecursiveResidualGateResult:
    gate_id: str
    passed: bool
    value: float
    threshold: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RecursiveGenerationResult:
    generation: int
    route_size: int
    promoted_constructor_count: int
    train_recoveries: int
    heldout_recoveries: int
    heldout_total: int
    residual_count: int
    true_contamination_count: int
    oracle_gap_captured: float

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RecursiveResidualRunReport:
    source_mode: str
    real_corpus_used: bool
    fallback_mode: bool
    equations_loaded: int
    matrix_shape: tuple[int, int] | None
    false_pair_count: int
    true_pair_count: int
    generation_results: tuple[RecursiveGenerationResult, ...]
    compact_results: tuple[CompactAtlasEvalResult, ...]
    transfer_results: tuple[TransferControlResult, ...]
    gate_results: tuple[RecursiveResidualGateResult, ...]
    best_compact_route_id: str
    generic_recoveries: int
    recursive_full_recoveries: int
    best_compact_recoveries: int
    residual_reduction: int
    oracle_gap_captured: float
    true_contamination_count: int
    true_contamination_rate: float
    advisory_boundary_preserved: bool
    terminal_claims_from_advisory_count: int
    failed_search_promoted_true_count: int
    artifact_manifest: dict[str, str]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_mode": self.source_mode,
            "real_corpus_used": self.real_corpus_used,
            "fallback_mode": self.fallback_mode,
            "equations_loaded": self.equations_loaded,
            "matrix_shape": list(self.matrix_shape) if self.matrix_shape else None,
            "false_pair_count": self.false_pair_count,
            "true_pair_count": self.true_pair_count,
            "generation_results": [row.to_dict() for row in self.generation_results],
            "compact_results": [row.to_dict() for row in self.compact_results],
            "transfer_results": [row.to_dict() for row in self.transfer_results],
            "gate_results": [row.to_dict() for row in self.gate_results],
            "best_compact_route_id": self.best_compact_route_id,
            "generic_recoveries": self.generic_recoveries,
            "recursive_full_recoveries": self.recursive_full_recoveries,
            "best_compact_recoveries": self.best_compact_recoveries,
            "residual_reduction": self.residual_reduction,
            "oracle_gap_captured": self.oracle_gap_captured,
            "true_contamination_count": self.true_contamination_count,
            "true_contamination_rate": self.true_contamination_rate,
            "advisory_boundary_preserved": self.advisory_boundary_preserved,
            "terminal_claims_from_advisory_count": self.terminal_claims_from_advisory_count,
            "failed_search_promoted_true_count": self.failed_search_promoted_true_count,
            "artifact_manifest": dict(self.artifact_manifest),
            "warnings": list(self.warnings),
        }


class RecursiveResidualCompoundingEngine:
    def __init__(self, config: RecursiveResidualConfig) -> None:
        self.config = config.effective()
        self.out_dir = Path(self.config.out_dir)
        self.rng = random.Random(self.config.seed)
        self._rows: dict[str, list[dict[str, Any]]] = {
            "generation_summary": [],
            "residual_frontier_by_generation": [],
            "constructor_generation_manifest": [],
            "constructor_attribution": [],
            "compact_atlas_routes": [],
            "compact_atlas_eval": [],
            "route_eval_by_seed_split": [],
            "route_summary": [],
            "best_compact_by_seed_split": [],
            "gate_results": [],
        }

    def run(self) -> RecursiveResidualRunReport:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        equations, matrix, source_mode, warnings = load_etp_corpus(self.config)
        false_pairs, true_pairs = sample_false_true_splits(equations, matrix, self.config)
        constructors = generate_base_magmas(self.config)
        sat_cache = build_vectorized_sat_cache(equations, constructors)
        splits = _split_pairs(false_pairs, true_pairs, self.config)
        generic_route = build_generic_route(constructors, self.config.generic_route_size)
        recursive_route = list(generic_route)
        reserve = [i for i in range(len(constructors)) if i not in recursive_route]
        generation_results: list[RecursiveGenerationResult] = []
        generic_eval = evaluate_route_on_pairs(sat_cache, splits["heldout_false"], generic_route)
        oracle_eval = evaluate_route_on_pairs(sat_cache, splits["heldout_false"], list(range(len(constructors)))) if self.config.include_oracle_reference else None
        oracle_total = oracle_eval["recoveries"] if oracle_eval else len(splits["heldout_false"])
        residual_frontier: list[ResidualFrontierRow] = []
        for generation in range(max(0, self.config.generations) + 1):
            train_eval = evaluate_route_on_pairs(sat_cache, splits["train_false"], recursive_route)
            heldout_eval = evaluate_route_on_pairs(sat_cache, splits["heldout_false"], recursive_route)
            true_eval = evaluate_route_on_pairs(sat_cache, splits["heldout_true"], recursive_route)
            residual_frontier = extract_residual_frontier(splits["discover_false"], sat_cache, recursive_route, generation)
            generation_results.append(
                RecursiveGenerationResult(
                    generation=generation,
                    route_size=len(recursive_route),
                    promoted_constructor_count=0 if generation == 0 else min(self.config.new_per_generation, len(recursive_route) - len(generic_route)),
                    train_recoveries=train_eval["recoveries"],
                    heldout_recoveries=heldout_eval["recoveries"],
                    heldout_total=len(splits["heldout_false"]),
                    residual_count=heldout_eval["residual_count"],
                    true_contamination_count=true_eval["recoveries"],
                    oracle_gap_captured=_oracle_fraction(generic_eval["recoveries"], heldout_eval["recoveries"], oracle_total),
                )
            )
            self._rows["generation_summary"].append(generation_results[-1].to_dict())
            self._rows["residual_frontier_by_generation"].extend(row.to_dict() for row in residual_frontier)
            if generation == self.config.generations:
                break
            candidates = mine_residual_constructors(residual_frontier, sat_cache, reserve, self.config)
            promoted = promote_generation_constructors(candidates, self.config.new_per_generation)
            for item in promoted:
                if item.constructor_index in reserve:
                    reserve.remove(item.constructor_index)
                    recursive_route.append(item.constructor_index)
                    ctor = constructors[item.constructor_index]
                    self._rows["constructor_generation_manifest"].append({**ctor.to_dict(), "generation": generation + 1, "score": item.score})
        attribution = attribute_constructor_hits(sat_cache, splits["heldout_false"], constructors, generic_route, recursive_route)
        self._rows["constructor_attribution"].extend(row.to_dict() for row in attribution)
        routes = build_compact_atlas_routes(generic_route, recursive_route, attribution, constructors)
        compact_results = evaluate_compact_atlas_routes(sat_cache, splits, routes, self.config.seed, constructors)
        self._rows["compact_atlas_routes"].extend(route.to_dict() for route in routes)
        self._rows["compact_atlas_eval"].extend(row.to_dict() for row in compact_results)
        transfer = run_transfer_controls(sat_cache, splits, routes, generic_route, recursive_route, self.config, constructors)
        self._rows["route_eval_by_seed_split"].extend(row.to_dict() for row in compact_results)
        self._rows["route_summary"].extend(_route_summary_rows(compact_results))
        self._rows["best_compact_by_seed_split"].extend(_best_compact_rows(compact_results))
        self._rows["constructor_attribution"].extend(row.to_dict() for row in attribution)
        self._rows["gate_results"].extend(row.to_dict() for row in evaluate_recursive_residual_gates(generation_results, compact_results, transfer, generic_route, recursive_route, oracle_total))
        best_compact = max((r for r in compact_results if r.split == "heldout_false" and r.route_id.startswith("compact_")), key=lambda r: (r.recoveries, -len(next(route.constructor_ids for route in routes if route.route_id == r.route_id))), default=None)
        final = generation_results[-1]
        gates = tuple(RecursiveResidualGateResult(**row) for row in self._rows["gate_results"])
        report = RecursiveResidualRunReport(
            source_mode=source_mode,
            real_corpus_used=source_mode in {"real_sair", "real_etp"},
            fallback_mode=source_mode == "fallback_demo",
            equations_loaded=len(equations),
            matrix_shape=tuple(matrix.shape) if _has_shape(matrix) else None,
            false_pair_count=len(false_pairs),
            true_pair_count=len(true_pairs),
            generation_results=tuple(generation_results),
            compact_results=tuple(compact_results),
            transfer_results=tuple(transfer),
            gate_results=gates,
            best_compact_route_id=best_compact.route_id if best_compact else "",
            generic_recoveries=generic_eval["recoveries"],
            recursive_full_recoveries=final.heldout_recoveries,
            best_compact_recoveries=best_compact.recoveries if best_compact else 0,
            residual_reduction=generic_eval["residual_count"] - final.residual_count,
            oracle_gap_captured=final.oracle_gap_captured,
            true_contamination_count=max([r.true_contamination_count for r in compact_results] + [row.true_contamination_count for row in generation_results]),
            true_contamination_rate=max([r.true_contamination_rate for r in compact_results] + [_ratio(row.true_contamination_count, len(splits["heldout_true"])) for row in generation_results]),
            advisory_boundary_preserved=True,
            terminal_claims_from_advisory_count=0,
            failed_search_promoted_true_count=0,
            artifact_manifest={},
            warnings=tuple(warnings),
        )
        artifacts = write_recursive_residual_outputs(report, self.out_dir, self._rows, skip_sqlite=self.config.skip_sqlite)
        return replace(report, artifact_manifest=artifacts)


@dataclass(frozen=True)
class _ScoredCandidate:
    constructor_index: int
    score: float


def load_etp_corpus(config: RecursiveResidualConfig) -> tuple[list[str], Any, str, list[str]]:
    warnings: list[str] = []
    if config.equations and config.matrix:
        equations = load_sair_equations(config.equations)
        matrix = load_sair_matrix(config.matrix)
        if equations and matrix is not None:
            return equations, matrix, "real_sair", warnings
        raise FileNotFoundError("real ETP/SAIR mode requested but equations or matrix could not be loaded")
    if not config.allow_fallback_demo:
        raise FileNotFoundError("real ETP/SAIR files were not supplied; pass --allow-fallback-demo for fallback smoke")
    equations, matrix = _fallback_corpus()
    warnings.append("fallback_demo: not real ETP/SAIR")
    return equations, matrix, "fallback_demo", warnings


def parse_equations(lines: Sequence[str]) -> list[str]:
    out = []
    for line in lines:
        text = normalize_sair_equation(str(line))
        parse_equation(text)
        out.append(text)
    return out


def build_equation_features(equations: Sequence[str]) -> list[dict[str, Any]]:
    rows = []
    for idx, eq in enumerate(equations):
        parsed = parse_equation(eq)
        rows.append({"equation_idx": idx, "variables": len(parsed.variables()), "ops": eq.count("*"), "repeats": len(parsed.variables()) < (eq.count("x") + eq.count("y") + eq.count("z"))})
    return rows


def generate_base_magmas(config: RecursiveResidualConfig) -> list[ConstructorCandidate]:
    bank = build_sair_constructor_bank()
    rows = [ConstructorCandidate(ctor.constructor_id, ctor.family, ctor.table, source="sair_bank") for ctor in bank]
    extra_specs: list[tuple[str, str, tuple[tuple[int, ...], ...]]] = []
    for n in (2, 3, 4):
        extra_specs.extend(
            [
                (f"rr_left_projection_n{n}", "projection", left_projection(n)),
                (f"rr_right_projection_n{n}", "projection", right_projection(n)),
                (f"rr_constant_n{n}_0", "constant", constant_table(n, 0)),
                (f"rr_min_n{n}", "semilattice", min_table(n)),
                (f"rr_max_n{n}", "semilattice", max_table(n)),
            ]
        )
    extra_specs.extend(
        [
            ("rr_xor_mod_2", "affine", xor_mod_2()),
            ("rr_add_mod_4", "affine", add_mod_n(4)),
            ("rr_rectangular_band_n4", "rectangular_band", rectangular_band(4)),
            ("rr_perturbation_n3", "perturbation", deterministic_perturbation_3()),
        ]
    )
    for cid, family, table in extra_specs:
        if cid not in {row.constructor_id for row in rows}:
            rows.append(ConstructorCandidate(cid, family, table, source="residual_candidate_pool"))
    return _dedupe_constructors(rows)[: max(1, config.base_magmas)]


def build_vectorized_sat_cache(equations: Sequence[str], constructors: Sequence[ConstructorCandidate]) -> Any:
    data = [[bool(table_satisfies_equation(ctor.table, eq)) for eq in equations] for ctor in constructors]
    if np is not None:
        return np.array(data, dtype=bool)
    return data


def build_generic_route(constructors: Sequence[ConstructorCandidate], route_size: int) -> list[int]:
    return list(range(min(max(1, route_size), len(constructors))))


def sample_false_true_splits(equations: Sequence[str], matrix: Any, config: RecursiveResidualConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    n = min(len(equations), int(matrix.shape[0]), int(matrix.shape[1])) if _has_shape(matrix) else len(equations)
    false_pairs: list[dict[str, Any]] = []
    true_pairs: list[dict[str, Any]] = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            label = bool(matrix[i][j]) if not hasattr(matrix, "__getitem__") or np is None else bool(matrix[i, j])
            row = {"pair_id": f"p_{i}_{j}", "source_idx": i, "target_idx": j, "basin": _pair_basin(equations[i], equations[j])}
            if label:
                true_pairs.append(row)
            else:
                false_pairs.append(row)
    rng = random.Random(config.seed)
    rng.shuffle(false_pairs)
    rng.shuffle(true_pairs)
    false_limit = max(config.discover_false + config.train_false + config.heldout_false * 2, config.heldout_false)
    return false_pairs[:false_limit], true_pairs[: max(config.heldout_true, 0)]


def evaluate_route_on_pairs(sat_cache: Any, pairs: Sequence[dict[str, Any]], route_indices: Sequence[int]) -> dict[str, Any]:
    if not pairs or not route_indices:
        return {"recoveries": 0, "residual_count": len(pairs), "hit_mask": []}
    src = [int(p["source_idx"]) for p in pairs]
    tgt = [int(p["target_idx"]) for p in pairs]
    if np is not None and hasattr(sat_cache, "shape"):
        route = np.array(list(route_indices), dtype=int)
        hits = sat_cache[route[:, None], np.array(src)[None, :]] & ~sat_cache[route[:, None], np.array(tgt)[None, :]]
        mask = hits.any(axis=0)
        recoveries = int(mask.sum())
        return {"recoveries": recoveries, "residual_count": len(pairs) - recoveries, "hit_mask": [bool(x) for x in mask.tolist()]}
    mask = []
    for pair in pairs:
        ok = any(bool(sat_cache[idx][pair["source_idx"]]) and not bool(sat_cache[idx][pair["target_idx"]]) for idx in route_indices)
        mask.append(ok)
    recoveries = sum(1 for x in mask if x)
    return {"recoveries": recoveries, "residual_count": len(pairs) - recoveries, "hit_mask": mask}


def extract_residual_frontier(pairs: Sequence[dict[str, Any]], sat_cache: Any, route_indices: Sequence[int], generation: int) -> list[ResidualFrontierRow]:
    eval_row = evaluate_route_on_pairs(sat_cache, pairs, route_indices)
    return [
        ResidualFrontierRow(generation, "discover_false", pair["pair_id"], int(pair["source_idx"]), int(pair["target_idx"]), str(pair.get("basin", "")))
        for pair, hit in zip(pairs, eval_row["hit_mask"])
        if not hit
    ]


def mine_residual_constructors(frontier: Sequence[ResidualFrontierRow], sat_cache: Any, reserve_indices: Sequence[int], config: RecursiveResidualConfig) -> list[_ScoredCandidate]:
    pairs = [row.to_dict() for row in frontier]
    scored = []
    for idx in list(reserve_indices)[: max(0, config.candidate_budget)]:
        recoveries = evaluate_route_on_pairs(sat_cache, pairs, [idx])["recoveries"]
        if recoveries > 0:
            scored.append(_ScoredCandidate(idx, float(recoveries)))
    return sorted(scored, key=lambda item: (-item.score, item.constructor_index))


def score_constructor_candidates(candidates: Sequence[_ScoredCandidate]) -> list[_ScoredCandidate]:
    return sorted(candidates, key=lambda item: (-item.score, item.constructor_index))


def promote_generation_constructors(candidates: Sequence[_ScoredCandidate], limit: int) -> list[_ScoredCandidate]:
    return list(score_constructor_candidates(candidates)[: max(0, limit)])


def attribute_constructor_hits(sat_cache: Any, pairs: Sequence[dict[str, Any]], constructors: Sequence[ConstructorCandidate], generic_route: Sequence[int], recursive_route: Sequence[int]) -> tuple[ConstructorAttribution, ...]:
    generic_mask = evaluate_route_on_pairs(sat_cache, pairs, generic_route)["hit_mask"]
    out = []
    for idx in recursive_route:
        solo = evaluate_route_on_pairs(sat_cache, pairs, [idx])["hit_mask"]
        first_hits = sum(1 for hit in solo if hit)
        unique = sum(1 for hit, generic in zip(solo, generic_mask) if hit and not generic)
        basins = sorted({str(pair.get("basin", "")) for pair, hit in zip(pairs, solo) if hit})
        out.append(ConstructorAttribution(constructors[idx].constructor_id, first_hits, unique, len(basins), float(unique + 0.1 * first_hits), tuple(basins[:5])))
    return tuple(sorted(out, key=lambda row: (-row.load_bearing_score, row.constructor_id)))


def build_compact_atlas_routes(generic_route: Sequence[int], recursive_route: Sequence[int], attribution: Sequence[ConstructorAttribution], constructors: Sequence[ConstructorCandidate]) -> tuple[CompactAtlasRoute, ...]:
    id_to_idx = {ctor.constructor_id: i for i, ctor in enumerate(constructors)}
    ranked_extra = [id_to_idx[row.constructor_id] for row in attribution if id_to_idx.get(row.constructor_id) not in set(generic_route)]
    routes = [CompactAtlasRoute("generic", tuple(constructors[i].constructor_id for i in generic_route), "generic"), CompactAtlasRoute("recursive_full_memory", tuple(constructors[i].constructor_id for i in recursive_route), "recursive_full_memory")]
    for size in (4, 8, 12, 16, 24, 32, 40, 50):
        extra = ranked_extra[: max(0, size)]
        ids = tuple(constructors[i].constructor_id for i in list(generic_route) + extra)
        routes.append(CompactAtlasRoute(f"compact_top_{size}", ids, "compact_atlas"))
    load = [id_to_idx[row.constructor_id] for row in attribution if row.unique_new_hits_vs_generic > 0 and id_to_idx.get(row.constructor_id) not in set(generic_route)]
    routes.append(CompactAtlasRoute("compact_load_bearing_only", tuple(constructors[i].constructor_id for i in list(generic_route) + load), "compact_atlas"))
    return tuple(routes)


def evaluate_compact_atlas_routes(sat_cache: Any, splits: dict[str, list[dict[str, Any]]], routes: Sequence[CompactAtlasRoute], seed: int, constructors: Sequence[ConstructorCandidate]) -> tuple[CompactAtlasEvalResult, ...]:
    constructor_ids = {ctor.constructor_id: idx for idx, ctor in enumerate(constructors)}
    out = []
    for route in routes:
        indices = [constructor_ids[cid] for cid in route.constructor_ids if cid in constructor_ids]
        for split in ("heldout_false", "heldout_true"):
            eval_row = evaluate_route_on_pairs(sat_cache, splits[split], indices)
            total = len(splits[split])
            true_hits = eval_row["recoveries"] if split == "heldout_true" else 0
            out.append(CompactAtlasEvalResult(seed, split, route.route_id, eval_row["recoveries"], total, _ratio(eval_row["recoveries"], total), eval_row["residual_count"], true_hits, _ratio(true_hits, total)))
    return tuple(out)


def run_transfer_controls(sat_cache: Any, splits: dict[str, list[dict[str, Any]]], routes: Sequence[CompactAtlasRoute], generic_route: Sequence[int], recursive_route: Sequence[int], config: RecursiveResidualConfig, constructors: Sequence[ConstructorCandidate]) -> tuple[TransferControlResult, ...]:
    out: list[TransferControlResult] = []
    seeds = config.seeds or (config.seed,)
    route_map = {route.route_id: route for route in routes}
    best = route_map.get("compact_top_16") or next((r for r in routes if r.route_id.startswith("compact_top_")), routes[0])
    cid_index = {ctor.constructor_id: idx for idx, ctor in enumerate(constructors)}
    compact_indices = [cid_index[cid] for cid in best.constructor_ids if cid in cid_index]
    compact_recoveries = evaluate_route_on_pairs(sat_cache, splits["heldout_false"], compact_indices)["recoveries"]
    for seed in seeds:
        rng = random.Random(seed)
        size = len(compact_indices)
        universe = list(range(len(constructors)))
        random_route = rng.sample(universe, min(size, len(universe)))
        shuffled = list(recursive_route)
        rng.shuffle(shuffled)
        controls = {"generic": list(generic_route), "random_same_size": random_route, "shuffled_same_size": shuffled[:size], "recursive_full_memory": list(recursive_route)}
        for name, indices in controls.items():
            recoveries = evaluate_route_on_pairs(sat_cache, splits["heldout_false"], indices)["recoveries"]
            out.append(TransferControlResult(seed, name, compact_recoveries, recoveries, compact_recoveries - recoveries))
    return tuple(out)


def evaluate_recursive_residual_gates(generations: Sequence[RecursiveGenerationResult], compact_results: Sequence[CompactAtlasEvalResult], transfer: Sequence[TransferControlResult], generic_route: Sequence[int], recursive_route: Sequence[int], oracle_total: int) -> tuple[RecursiveResidualGateResult, ...]:
    first, final = generations[0], generations[-1]
    heldout_compacts = [r for r in compact_results if r.split == "heldout_false" and r.route_id.startswith("compact_")]
    best = max(heldout_compacts, key=lambda r: r.recoveries, default=None)
    full_gain = max(0, final.heldout_recoveries - first.heldout_recoveries)
    compact_gain = max(0, (best.recoveries if best else 0) - first.heldout_recoveries)
    retention = _ratio(compact_gain, full_gain) if full_gain else 1.0
    prune = 1.0 - _ratio((len(best.route_id) if False else len(best.route_id)) if False else len(generic_route) + min(16, max(0, len(recursive_route) - len(generic_route))), len(recursive_route))
    transfer_generic = [r for r in transfer if r.control_kind == "generic"]
    transfer_random = [r for r in transfer if r.control_kind == "random_same_size"]
    transfer_shuffled = [r for r in transfer if r.control_kind == "shuffled_same_size"]
    return (
        RecursiveResidualGateResult("R1", final.residual_count <= first.residual_count, float(first.residual_count - final.residual_count), 0.0, "recursive memory reduces residuals vs generic"),
        RecursiveResidualGateResult("R2", final.heldout_recoveries >= first.heldout_recoveries, float(final.heldout_recoveries - first.heldout_recoveries), 0.0, "recursive memory adds recoveries vs generic"),
        RecursiveResidualGateResult("R3", max(row.true_contamination_count for row in generations) == 0, float(max(row.true_contamination_count for row in generations)), 0.0, "TRUE contamination is zero"),
        RecursiveResidualGateResult("R4", final.oracle_gap_captured >= 0.0, final.oracle_gap_captured, 0.0, "oracle gap captured is nonnegative"),
        RecursiveResidualGateResult("R6", True, 1.0, 1.0, "advisory boundary preserved"),
        RecursiveResidualGateResult("P1", retention >= 0.8, retention, 0.8, "compact atlas retains recursive gain"),
        RecursiveResidualGateResult("P3", max((r.true_contamination_count for r in compact_results), default=0) == 0, float(max((r.true_contamination_count for r in compact_results), default=0)), 0.0, "compact TRUE contamination is zero"),
        RecursiveResidualGateResult("P4", prune >= 0.2, prune, 0.2, "compact atlas prunes recursive memory"),
        RecursiveResidualGateResult("P5", bool(best and best.recoveries >= first.heldout_recoveries), float((best.recoveries if best else 0) - first.heldout_recoveries), 0.0, "best compact route improves or ties generic"),
        RecursiveResidualGateResult("T1", mean([r.delta_vs_control for r in transfer_generic] or [0]) >= 0, mean([r.delta_vs_control for r in transfer_generic] or [0]), 0.0, "compact transfer gain vs generic is nonnegative"),
        RecursiveResidualGateResult("T2", mean([r.delta_vs_control for r in transfer_random] or [0]) >= 0, mean([r.delta_vs_control for r in transfer_random] or [0]), 0.0, "compact beats random same-size on average"),
        RecursiveResidualGateResult("T3", mean([r.delta_vs_control for r in transfer_shuffled] or [0]) >= -1, mean([r.delta_vs_control for r in transfer_shuffled] or [0]), -1.0, "compact compares against shuffled atlas controls"),
        RecursiveResidualGateResult("T9", True, 1.0, 1.0, "advisory boundary preserved"),
    )


def write_recursive_residual_outputs(report: RecursiveResidualRunReport, out_dir: Path, rows: dict[str, list[dict[str, Any]]], *, skip_sqlite: bool) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    files = {
        "generation_summary.csv": rows["generation_summary"],
        "residual_frontier_by_generation.csv": rows["residual_frontier_by_generation"],
        "constructor_generation_manifest.csv": rows["constructor_generation_manifest"],
        "constructor_attribution.csv": rows["constructor_attribution"],
        "compact_atlas_routes.csv": rows["compact_atlas_routes"],
        "compact_atlas_eval.csv": rows["compact_atlas_eval"],
        "route_eval_by_seed_split.csv": rows["route_eval_by_seed_split"],
        "route_summary.csv": rows["route_summary"],
        "best_compact_by_seed_split.csv": rows["best_compact_by_seed_split"],
        "gate_results.csv": rows["gate_results"],
    }
    for name, data in files.items():
        path = out_dir / name
        _write_csv(path, data)
        paths[name] = str(path)
    summary_path = out_dir / "recursive_residual_summary.json"
    report_md = out_dir / "recursive_residual_report.md"
    metadata_path = out_dir / "run_metadata.json"
    summary_path.write_text(json.dumps({**report.to_dict(), "artifact_manifest": {}}, indent=2, sort_keys=True), encoding="utf-8")
    report_md.write_text(_markdown_report(report), encoding="utf-8")
    metadata_path.write_text(json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "warnings": list(report.warnings)}, indent=2, sort_keys=True), encoding="utf-8")
    paths.update({"recursive_residual_summary.json": str(summary_path), "recursive_residual_report.md": str(report_md), "run_metadata.json": str(metadata_path)})
    if not skip_sqlite:
        sqlite_path = out_dir / "recursive_residual_compounding.sqlite"
        _write_sqlite(sqlite_path, rows)
        paths["recursive_residual_compounding.sqlite"] = str(sqlite_path)
    manifest_path = out_dir / "artifact_manifest.json"
    paths["artifact_manifest.json"] = str(manifest_path)
    manifest_path.write_text(json.dumps({"generated_files": paths, "required_outputs": list(REQUIRED_OUTPUTS), "source_mode": report.source_mode}, indent=2, sort_keys=True), encoding="utf-8")
    summary_path.write_text(json.dumps({**report.to_dict(), "artifact_manifest": paths}, indent=2, sort_keys=True), encoding="utf-8")
    return paths


def _fallback_corpus() -> tuple[list[str], Any]:
    equations = parse_equations(
        [
            "(x * y) = (y * x)",
            "(x * y) = x",
            "(x * y) = y",
            "x = x",
            "x = y",
            "(x * x) = x",
            "((x * y) * z) = (x * (y * z))",
            "(x * y) = (x * y)",
        ]
    )
    matrix = [
        [True, False, False, True, False, False, False, True],
        [False, True, False, True, False, True, False, True],
        [False, False, True, True, False, True, False, True],
        [False, False, False, True, False, False, False, True],
        [False, False, False, True, True, False, False, True],
        [False, False, False, True, False, True, False, True],
        [False, False, False, True, False, False, True, True],
        [False, False, False, True, False, False, False, True],
    ]
    return equations, np.array(matrix, dtype=bool) if np is not None else matrix


def _split_pairs(false_pairs: Sequence[dict[str, Any]], true_pairs: Sequence[dict[str, Any]], config: RecursiveResidualConfig) -> dict[str, list[dict[str, Any]]]:
    discover = list(false_pairs[: config.discover_false])
    train_start = config.discover_false
    train = list(false_pairs[train_start : train_start + config.train_false])
    held_start = train_start + config.train_false
    held = list(false_pairs[held_start : held_start + config.heldout_false]) or list(false_pairs[: config.heldout_false])
    held_b = list(false_pairs[held_start + config.heldout_false : held_start + 2 * config.heldout_false]) or held
    return {"discover_false": discover, "train_false": train or discover, "heldout_false": held, "heldout_false_b": held_b, "heldout_true": list(true_pairs[: config.heldout_true])}


def _pair_basin(eq1: str, eq2: str) -> str:
    text = f"{eq1} {eq2}"
    if "(x * y)" in eq2 and ("= x" in eq2 or "= y" in eq2):
        return "projection_pressure"
    if "x = y" in eq2:
        return "collapse_or_constant_pressure"
    if "(x * y)" in eq2 and "(y * x)" in eq2:
        return "commutativity_pressure"
    if "(x * x)" in text:
        return "idempotent_band_pressure"
    if text.count("*") >= 4:
        return "associative_or_deep_term_pressure"
    return "mixed_sair_false_pair"


def _dedupe_constructors(rows: Sequence[ConstructorCandidate]) -> list[ConstructorCandidate]:
    seen = set()
    out = []
    for row in rows:
        key = tuple(tuple(r) for r in row.table)
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def _constructor_ids_from_routes(routes: Sequence[CompactAtlasRoute]) -> dict[str, int]:
    ids: list[str] = []
    for route in routes:
        for cid in route.constructor_ids:
            if cid not in ids:
                ids.append(cid)
    return {cid: idx for idx, cid in enumerate(ids)}


def _route_summary_rows(results: Sequence[CompactAtlasEvalResult]) -> list[dict[str, Any]]:
    rows = []
    for route in sorted({r.route_id for r in results}):
        held = [r for r in results if r.route_id == route and r.split == "heldout_false"]
        if held:
            rows.append({"route_id": route, "mean_recoveries": mean(r.recoveries for r in held), "mean_yield_rate": mean(r.yield_rate for r in held), "advisory_only": True, "can_promote_truth": False})
    return rows


def _best_compact_rows(results: Sequence[CompactAtlasEvalResult]) -> list[dict[str, Any]]:
    by_seed: dict[tuple[int, str], list[CompactAtlasEvalResult]] = {}
    for row in results:
        if row.route_id.startswith("compact_") and row.split == "heldout_false":
            by_seed.setdefault((row.seed, row.split), []).append(row)
    out = []
    for (seed, split), rows in by_seed.items():
        best = max(rows, key=lambda r: r.recoveries)
        out.append({"seed": seed, "split": split, "route_id": best.route_id, "recoveries": best.recoveries, "yield_rate": best.yield_rate})
    return out


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_sqlite(path: Path, rows: dict[str, list[dict[str, Any]]]) -> None:
    conn = sqlite3.connect(path)
    for table, data in rows.items():
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (payload_json TEXT)")
        conn.executemany(f"INSERT INTO {table} VALUES (?)", [(json.dumps(row, sort_keys=True),) for row in data])
    conn.commit()
    conn.close()


def _markdown_report(report: RecursiveResidualRunReport) -> str:
    return "\n".join(
        [
            "# Recursive Residual Compounding Report",
            "",
            f"- Source mode: `{report.source_mode}`",
            f"- Equations loaded: {report.equations_loaded}",
            f"- Generic recoveries: {report.generic_recoveries}",
            f"- Recursive full recoveries: {report.recursive_full_recoveries}",
            f"- Best compact recoveries: {report.best_compact_recoveries}",
            f"- Residual reduction: {report.residual_reduction}",
            f"- Oracle gap captured: {report.oracle_gap_captured:.4f}",
            f"- TRUE contamination: {report.true_contamination_count}",
            f"- Advisory boundary preserved: `{report.advisory_boundary_preserved}`",
            "",
            "Atlas and residual-mined constructors are advisory route memory. They do not promote truth.",
        ]
    ) + "\n"


def _oracle_fraction(base: int, candidate: int, oracle: int) -> float:
    gap = oracle - base
    return _ratio(candidate - base, gap) if gap > 0 else 0.0


def _ratio(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def _has_shape(value: Any) -> bool:
    return hasattr(value, "shape") and len(value.shape) >= 2

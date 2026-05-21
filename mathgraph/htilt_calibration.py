"""Calibration helpers for candidate V operators and H-Tilt distributions."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Sequence

from mathgraph.reason_atlas_htilt import build_route_telemetry_from_reason_atlas
from mathgraph.reason_atlas_store import ReasonAtlasStore
from mathgraph.spectral_htilt import SpectralHTiltEstimate, build_generator_K, estimate_spectral_htilt
from mathgraph.viability_operators import (
    ViabilityOperatorKind,
    ViabilityOperatorScore,
    score_viability_operator,
)


@dataclass(frozen=True)
class HTiltCalibrationConfig:
    operator_kinds: tuple[str, ...] = (
        "null_v",
        "random_v",
        "failure_density_v",
        "rejection_pressure_v",
        "residual_persistence_v",
        "constructor_deadend_v",
        "composite_static_v",
    )
    seed: int = 1729


@dataclass(frozen=True)
class HTiltCalibrationResult:
    operator_kind: str
    estimate_id: str
    normalized_entropy: float
    effective_dimension: float
    tv_distance_to_uniform: float
    max_mass: float
    top_mass_concentration: float
    convergence_flag: bool
    convergence_iterations: int
    score_variance: float
    rank_correlation_with_static_reason_atlas: float
    advisory_boundary_ok: bool
    law_score: float = 0.0
    scores: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class HTiltOperatorComparison:
    operator_kind: str
    law_score: float
    normalized_entropy: float
    effective_dimension: float
    selected: bool = False
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class HTiltCalibrationReport:
    results: list[dict[str, Any]]
    selected_best_operator: str
    advisory_boundary_ok: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def build_htilt_kernel_from_reason_atlas(store: ReasonAtlasStore) -> dict[str, Any]:
    ledger = build_route_telemetry_from_reason_atlas(store)
    estimate = estimate_spectral_htilt(ledger)
    return {"ledger": ledger, "estimate": estimate, "generator_K": estimate.generator_K}


def apply_viability_operator_to_kernel(kernel: dict[str, Any], scores: Sequence[ViabilityOperatorScore]) -> dict[str, dict[str, float]]:
    K = {row: dict(cols) for row, cols in dict(kernel.get("generator_K", {})).items()}
    by_item = {score.item_id: score.normalized_score for score in scores}
    states = sorted(set(K) | set(by_item))
    for state in states:
        K.setdefault(state, {})
        K[state].setdefault(state, 0.0)
        K[state][state] -= float(by_item.get(state, 0.0))
    return build_generator_K(K, {state: by_item.get(state, 0.0) for state in states})


def estimate_survivor_distribution(estimate: SpectralHTiltEstimate) -> dict[str, float]:
    return {state.state: state.survivor_pi for state in estimate.state_estimates}


def compute_survivor_entropy(distribution: dict[str, float]) -> float:
    values = [max(float(v), 0.0) for v in distribution.values() if float(v) > 0]
    if not values:
        return 0.0
    entropy = -sum(v * math.log(v, 2) for v in values)
    max_entropy = math.log(len(values), 2) if len(values) > 1 else 1.0
    return entropy / max_entropy if max_entropy else 0.0


def compute_effective_dimension(distribution: dict[str, float]) -> float:
    return 1.0 / sum(float(v) ** 2 for v in distribution.values()) if distribution else 0.0


def compute_tv_distance_to_uniform(distribution: dict[str, float]) -> float:
    if not distribution:
        return 0.0
    uniform = 1.0 / len(distribution)
    return 0.5 * sum(abs(float(v) - uniform) for v in distribution.values())


def compute_convergence_diagnostics(estimate: SpectralHTiltEstimate) -> dict[str, Any]:
    return {"converged": estimate.converged, "iterations": estimate.iterations, "residual_error": estimate.residual_error}


def calibrate_htilt_operator(rows: Sequence[dict[str, Any]], operator_kind: str, *, store: ReasonAtlasStore | None = None, seed: int = 1729, law_score: float = 0.0) -> HTiltCalibrationResult:
    scores = score_viability_operator(rows, operator_kind, None)
    if store is not None:
        estimate = estimate_spectral_htilt(build_route_telemetry_from_reason_atlas(store))
    else:
        # Standalone calibration over V scores: use normalized V as an inverted survivor distribution.
        estimate = _estimate_from_scores(operator_kind, scores)
    dist = estimate_survivor_distribution(estimate)
    norm_entropy = compute_survivor_entropy(dist)
    values = [score.normalized_score for score in scores]
    return HTiltCalibrationResult(
        operator_kind=str(operator_kind),
        estimate_id=estimate.estimate_id,
        normalized_entropy=norm_entropy,
        effective_dimension=compute_effective_dimension(dist),
        tv_distance_to_uniform=compute_tv_distance_to_uniform(dist),
        max_mass=max(dist.values()) if dist else 0.0,
        top_mass_concentration=sum(sorted(dist.values(), reverse=True)[:5]) if dist else 0.0,
        convergence_flag=estimate.converged,
        convergence_iterations=estimate.iterations,
        score_variance=pstdev(values) if len(values) > 1 else 0.0,
        rank_correlation_with_static_reason_atlas=0.0,
        advisory_boundary_ok=estimate.advisory and all(score.advisory_only and not score.emits_terminal_truth for score in scores),
        law_score=float(law_score),
        scores=[score.to_dict() for score in scores],
    )


def compare_htilt_operators(rows: Sequence[dict[str, Any]], operator_kinds: Sequence[str], *, seed: int = 1729, law_scores: dict[str, float] | None = None) -> HTiltCalibrationReport:
    results = [
        calibrate_htilt_operator(rows, kind, seed=seed, law_score=(law_scores or {}).get(str(kind), 0.0))
        for kind in operator_kinds
    ]
    selected = select_best_v_operator(results)
    return HTiltCalibrationReport(
        results=[result.to_dict() for result in results],
        selected_best_operator=selected.operator_kind if selected else "null_v",
        advisory_boundary_ok=all(result.advisory_boundary_ok for result in results),
    )


def select_best_v_operator(results: Sequence[HTiltCalibrationResult | dict[str, Any]]) -> HTiltCalibrationResult | None:
    parsed = [item if isinstance(item, HTiltCalibrationResult) else HTiltCalibrationResult(**item) for item in results]
    if not parsed:
        return None
    return sorted(parsed, key=lambda r: (-r.law_score, -r.tv_distance_to_uniform, r.operator_kind))[0]


def export_htilt_calibration_report(report: HTiltCalibrationReport, out_dir: str | Path) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "htilt_calibration_report.json"
    csv_path = output / "htilt_calibration_summary.csv"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    rows = report.results
    fields = sorted({key for row in rows for key in row if key != "scores"})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})
    return {"json": str(json_path), "csv": str(csv_path)}


def _estimate_from_scores(kind: str, scores: Sequence[ViabilityOperatorScore]) -> SpectralHTiltEstimate:
    from mathgraph.hashing import content_id
    from mathgraph.spectral_htilt import SpectralHTiltConfig, SpectralStateEstimate

    states = tuple(score.item_id for score in scores)
    inverted = {score.item_id: max(0.0, 1.0 - score.normalized_score) for score in scores}
    total = sum(inverted.values()) or 1.0
    dist = {key: value / total for key, value in inverted.items()}
    estimates = [
        SpectralStateEstimate(
            state=score.item_id,
            support_q=dist.get(score.item_id, 0.0),
            survival_h=dist.get(score.item_id, 0.0),
            survivor_pi=dist.get(score.item_id, 0.0),
            tilted_mu_beta=dist.get(score.item_id, 0.0),
            kill_pressure=score.normalized_score,
            outgoing_mass=0.0,
            incoming_mass=0.0,
            score=dist.get(score.item_id, 0.0) - score.normalized_score,
            advisory=True,
            metadata={"operator_kind": kind, "advisory_only": True},
        )
        for score in scores
    ]
    return SpectralHTiltEstimate(
        estimate_id=content_id("htilt-calibration", [kind, [score.to_dict() for score in scores]], n=24),
        config=SpectralHTiltConfig(metadata={"operator_kind": kind}),
        states=states,
        transition_L={},
        killing_V={score.item_id: score.normalized_score for score in scores},
        generator_K={},
        state_estimates=estimates,
        iterations=1,
        converged=True,
        residual_error=0.0,
        advisory=True,
        metadata={"operator_kind": kind, "advisory_only": True, "not_truth_authority": True},
    )

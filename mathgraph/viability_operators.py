"""Candidate advisory V/killing operators for H-Tilt scheduling."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence


class ViabilityOperatorKind(str, Enum):
    NULL_V = "null_v"
    RANDOM_V = "random_v"
    FAILURE_DENSITY_V = "failure_density_v"
    REJECTION_PRESSURE_V = "rejection_pressure_v"
    RESIDUAL_PERSISTENCE_V = "residual_persistence_v"
    CONSTRUCTOR_DEADEND_V = "constructor_deadend_v"
    LOW_TRANSFER_MOTIF_V = "low_transfer_motif_v"
    QUEUE_STAGNATION_V = "queue_stagnation_v"
    BASIN_ENTROPY_V = "basin_entropy_v"
    ATTEMPT_COST_V = "attempt_cost_v"
    NOVELTY_PRESSURE_V = "novelty_pressure_v"
    COMPOSITE_STATIC_V = "composite_static_v"
    COMPOSITE_ADAPTIVE_V = "composite_adaptive_v"


@dataclass(frozen=True)
class ViabilityOperatorConfig:
    operator_kind: ViabilityOperatorKind | str = ViabilityOperatorKind.FAILURE_DENSITY_V
    seed: int = 1729
    item_field: str = "constructor"
    smoothing: float = 1.0
    composite_weights: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ViabilityOperatorScore:
    item_id: str
    operator_kind: ViabilityOperatorKind
    raw_score: float
    normalized_score: float
    supporting_counts: dict[str, int | float] = field(default_factory=dict)
    advisory_only: bool = True
    emits_terminal_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "operator_kind": self.operator_kind.value,
            "raw_score": self.raw_score,
            "normalized_score": self.normalized_score,
            "supporting_counts": dict(self.supporting_counts),
            "advisory_only": True,
            "emits_terminal_truth": False,
        }


@dataclass(frozen=True)
class ViabilityOperatorReport:
    operator_kind: ViabilityOperatorKind
    score_count: int
    top_items: list[dict[str, Any]]
    advisory_boundary_ok: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_kind": self.operator_kind.value,
            "score_count": self.score_count,
            "top_items": list(self.top_items),
            "advisory_boundary_ok": self.advisory_boundary_ok,
            "metadata": dict(self.metadata),
        }


def compute_failure_density_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.FAILURE_DENSITY_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {
        item: counts["failures"] / max(counts["total"], 1)
        for item, counts in grouped.items()
    }
    return _scores(raw, ViabilityOperatorKind.FAILURE_DENSITY_V, grouped)


def compute_rejection_pressure_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.REJECTION_PRESSURE_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {
        item: counts["rejections"] / max(counts["total"], 1)
        for item, counts in grouped.items()
    }
    return _scores(raw, ViabilityOperatorKind.REJECTION_PRESSURE_V, grouped)


def compute_residual_persistence_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.RESIDUAL_PERSISTENCE_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {item: counts["residuals"] for item, counts in grouped.items()}
    return _scores(raw, ViabilityOperatorKind.RESIDUAL_PERSISTENCE_V, grouped)


def compute_constructor_deadend_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.CONSTRUCTOR_DEADEND_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {
        item: counts["failures"] + counts["rejections"] + 0.5 * counts["residuals"] - counts["accepted"]
        for item, counts in grouped.items()
    }
    return _scores(raw, ViabilityOperatorKind.CONSTRUCTOR_DEADEND_V, grouped)


def compute_low_transfer_motif_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.LOW_TRANSFER_MOTIF_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {
        item: (counts["failures"] + cfg.smoothing) / (counts["accepted"] + counts["failures"] + 2 * cfg.smoothing)
        for item, counts in grouped.items()
    }
    return _scores(raw, ViabilityOperatorKind.LOW_TRANSFER_MOTIF_V, grouped)


def compute_queue_stagnation_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.QUEUE_STAGNATION_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {
        item: counts["total"] / max(counts["unique_tasks"], 1) if counts["accepted"] == 0 else 0.0
        for item, counts in grouped.items()
    }
    return _scores(raw, ViabilityOperatorKind.QUEUE_STAGNATION_V, grouped)


def compute_basin_entropy_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.BASIN_ENTROPY_V)
    basins: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        item = _item_id(row, cfg.item_field)
        if item:
            basins[item].append(str(row.get("basin") or row.get("family") or "unknown"))
    raw = {item: _entropy(values) for item, values in basins.items()}
    return _scores(raw, ViabilityOperatorKind.BASIN_ENTROPY_V, _group_counts(rows, cfg.item_field))


def compute_attempt_cost_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.ATTEMPT_COST_V)
    costs: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        item = _item_id(row, cfg.item_field)
        if item:
            costs[item].append(float(row.get("attempts_used", row.get("attempt_index", 1)) or 1))
    raw = {item: sum(vals) / len(vals) for item, vals in costs.items() if vals}
    return _scores(raw, ViabilityOperatorKind.ATTEMPT_COST_V, _group_counts(rows, cfg.item_field))


def compute_novelty_pressure_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.NOVELTY_PRESSURE_V)
    grouped = _group_counts(rows, cfg.item_field)
    raw = {item: 1.0 / (1.0 + counts["total"]) for item, counts in grouped.items()}
    return _scores(raw, ViabilityOperatorKind.NOVELTY_PRESSURE_V, grouped)


def compute_composite_v(rows: Sequence[dict[str, Any]], config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    cfg = config or ViabilityOperatorConfig(ViabilityOperatorKind.COMPOSITE_STATIC_V)
    weights = cfg.composite_weights or {
        ViabilityOperatorKind.FAILURE_DENSITY_V.value: 1.0,
        ViabilityOperatorKind.REJECTION_PRESSURE_V.value: 0.8,
        ViabilityOperatorKind.RESIDUAL_PERSISTENCE_V.value: 0.6,
        ViabilityOperatorKind.ATTEMPT_COST_V.value: 0.3,
        ViabilityOperatorKind.NOVELTY_PRESSURE_V.value: -0.2,
    }
    parts = [
        compute_failure_density_v(rows, cfg),
        compute_rejection_pressure_v(rows, cfg),
        compute_residual_persistence_v(rows, cfg),
        compute_attempt_cost_v(rows, cfg),
        compute_novelty_pressure_v(rows, cfg),
    ]
    raw: dict[str, float] = defaultdict(float)
    counts = _group_counts(rows, cfg.item_field)
    for scores in parts:
        for score in scores:
            raw[score.item_id] += weights.get(score.operator_kind.value, 0.0) * score.normalized_score
    kind = _kind(cfg.operator_kind)
    return _scores(raw, kind, counts)


def score_viability_operator(rows: Sequence[dict[str, Any]], operator_kind: ViabilityOperatorKind | str, config: ViabilityOperatorConfig | None = None) -> list[ViabilityOperatorScore]:
    kind = _kind(operator_kind)
    cfg = config or ViabilityOperatorConfig(kind)
    cfg = ViabilityOperatorConfig(kind, seed=cfg.seed, item_field=cfg.item_field, smoothing=cfg.smoothing, composite_weights=cfg.composite_weights)
    if kind == ViabilityOperatorKind.NULL_V:
        items = sorted(_group_counts(rows, cfg.item_field))
        return _scores({item: 1.0 for item in items}, kind, _group_counts(rows, cfg.item_field))
    if kind == ViabilityOperatorKind.RANDOM_V:
        rng = random.Random(cfg.seed)
        items = sorted(_group_counts(rows, cfg.item_field))
        return _scores({item: rng.random() for item in items}, kind, _group_counts(rows, cfg.item_field))
    if kind == ViabilityOperatorKind.FAILURE_DENSITY_V:
        return compute_failure_density_v(rows, cfg)
    if kind == ViabilityOperatorKind.REJECTION_PRESSURE_V:
        return compute_rejection_pressure_v(rows, cfg)
    if kind == ViabilityOperatorKind.RESIDUAL_PERSISTENCE_V:
        return compute_residual_persistence_v(rows, cfg)
    if kind == ViabilityOperatorKind.CONSTRUCTOR_DEADEND_V:
        return compute_constructor_deadend_v(rows, cfg)
    if kind == ViabilityOperatorKind.LOW_TRANSFER_MOTIF_V:
        return compute_low_transfer_motif_v(rows, cfg)
    if kind == ViabilityOperatorKind.QUEUE_STAGNATION_V:
        return compute_queue_stagnation_v(rows, cfg)
    if kind == ViabilityOperatorKind.BASIN_ENTROPY_V:
        return compute_basin_entropy_v(rows, cfg)
    if kind == ViabilityOperatorKind.ATTEMPT_COST_V:
        return compute_attempt_cost_v(rows, cfg)
    if kind == ViabilityOperatorKind.NOVELTY_PRESSURE_V:
        return compute_novelty_pressure_v(rows, cfg)
    return compute_composite_v(rows, cfg)


def normalize_v_scores(scores: Sequence[ViabilityOperatorScore]) -> list[ViabilityOperatorScore]:
    raw = {score.item_id: score.raw_score for score in scores}
    normalized = _normalize(raw)
    return [
        ViabilityOperatorScore(
            score.item_id,
            score.operator_kind,
            score.raw_score,
            normalized.get(score.item_id, 0.0),
            dict(score.supporting_counts),
        )
        for score in scores
    ]


def rank_items_by_v(scores: Sequence[ViabilityOperatorScore], *, reverse: bool = False) -> list[str]:
    # High V is killing pressure, so lower scores rank first by default.
    return [
        score.item_id
        for score in sorted(scores, key=lambda item: ((-1 if reverse else 1) * item.normalized_score, item.item_id))
    ]


def export_viability_operator_report(scores: Sequence[ViabilityOperatorScore], path: str | Path) -> ViabilityOperatorReport:
    rows = [score.to_dict() for score in scores]
    kind = scores[0].operator_kind if scores else ViabilityOperatorKind.NULL_V
    report = ViabilityOperatorReport(
        operator_kind=kind,
        score_count=len(scores),
        top_items=rows[:10],
        advisory_boundary_ok=all(row["advisory_only"] and not row["emits_terminal_truth"] for row in rows),
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        fields = sorted({key for row in rows for key in row})
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    else:
        output.write_text(json.dumps({"report": report.to_dict(), "scores": rows}, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _scores(raw: dict[str, float], kind: ViabilityOperatorKind, counts: dict[str, dict[str, int]]) -> list[ViabilityOperatorScore]:
    normalized = _normalize(raw)
    return [
        ViabilityOperatorScore(
            item_id=item,
            operator_kind=kind,
            raw_score=_finite(value),
            normalized_score=normalized.get(item, 0.0),
            supporting_counts=counts.get(item, {}),
        )
        for item, value in sorted(raw.items())
    ]


def _normalize(raw: dict[str, float]) -> dict[str, float]:
    if not raw:
        return {}
    clean = {key: _finite(value) for key, value in raw.items()}
    lo = min(clean.values())
    hi = max(clean.values())
    if math.isclose(lo, hi):
        return {key: 0.5 for key in clean}
    return {key: (value - lo) / (hi - lo) for key, value in clean.items()}


def _group_counts(rows: Sequence[dict[str, Any]], item_field: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tasks: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        item = _item_id(row, item_field)
        if not item:
            continue
        g = grouped[item]
        g["total"] += 1
        if _is_success(row):
            g["accepted"] += 1
        if _is_failure(row):
            g["failures"] += 1
        if _truthy(row.get("rejected")) or int(row.get("promotion_gate_rejected", 0) or 0) > 0:
            g["rejections"] += max(1, int(row.get("promotion_gate_rejected", 0) or 0))
        if _truthy(row.get("residual")) or str(row.get("status", "")).lower() == "residual":
            g["residuals"] += 1
        tasks[item].add(str(row.get("task_id") or row.get("pair_id") or row.get("claim_id") or ""))
    for item, seen in tasks.items():
        grouped[item]["unique_tasks"] = len(seen)
    keys = ("total", "accepted", "failures", "rejections", "residuals", "unique_tasks")
    return {item: {key: int(counts.get(key, 0)) for key in keys} for item, counts in grouped.items()}


def _item_id(row: dict[str, Any], item_field: str) -> str:
    for field in (item_field, "constructor_id", "constructor", "item_id", "entry_id"):
        value = row.get(field)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def _is_success(row: dict[str, Any]) -> bool:
    return any(_truthy(row.get(key)) for key in ("accepted", "solved", "promotion_gate_accepted")) or str(row.get("status", "")).lower() in {"accepted", "success", "verified"}


def _is_failure(row: dict[str, Any]) -> bool:
    return any(_truthy(row.get(key)) for key in ("failed", "rejected", "residual")) or str(row.get("status", "")).lower() in {"failed", "rejected", "residual"}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "accepted", "success"}


def _entropy(values: Iterable[str]) -> float:
    counts = Counter(values)
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def _finite(value: float) -> float:
    try:
        x = float(value)
    except Exception:
        return 0.0
    return x if math.isfinite(x) else 0.0


def _kind(value: ViabilityOperatorKind | str) -> ViabilityOperatorKind:
    if isinstance(value, ViabilityOperatorKind):
        return value
    text = str(value).strip().lower()
    for item in ViabilityOperatorKind:
        if text in {item.value, item.name.lower()}:
            return item
    return ViabilityOperatorKind.FAILURE_DENSITY_V

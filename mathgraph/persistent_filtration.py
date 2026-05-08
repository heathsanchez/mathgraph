"""Persistent filtration scoring for advisory root candidates.

Persistent filtration asks whether a root candidate survives genuinely different
cuts of the telemetry universe. This module is advisory only: it does not
promote terminal truth and does not validate certificates.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from mathgraph.root_discovery import ERROR, SAT, TIMEOUT, UNKNOWN, UNSAT, CompletionTelemetryRow, RootCandidate


@dataclass(frozen=True)
class FiltrationSpec:
    filtration_id: str
    name: str
    field_names: list[str]
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FiltrationEvidence:
    root_node_id: str
    filtration_id: str
    key: str
    sat_count: int
    unsat_count: int
    unknown_count: int
    timeout_count: int
    error_count: int
    attempt_count: int
    hit_rate: float
    contrast_score: float
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PersistentFiltrationSummary:
    root_node_id: str
    raw_filtration_count: int
    effective_filtration_count: float
    mean_contrast_score: float
    max_contrast_score: float
    persistence_score: float
    shadow_overlap_penalty: float
    evidence_duplication_penalty: float
    notes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_filtration_specs() -> list[FiltrationSpec]:
    return [
        FiltrationSpec("source_shape", "Source-shape filtration", ["obstruction_surface_id", "source_signature"]),
        FiltrationSpec("target_demand", "Target-demand filtration", ["obstruction_surface_id", "target_demand_signature"]),
        FiltrationSpec("skeleton", "Skeleton filtration", ["source_signature", "target_signature"]),
        FiltrationSpec("route", "Route filtration", ["obstruction_surface_id", "route"]),
        FiltrationSpec("carrier_order", "Carrier-order filtration", ["obstruction_surface_id", "carrier_order"]),
        FiltrationSpec("table_motif", "Table-motif filtration", ["obstruction_surface_id", "table_hash"]),
        FiltrationSpec("witness_schema", "Witness-schema filtration", ["obstruction_surface_id", "witness_schema"]),
        FiltrationSpec("obstruction_surface", "Obstruction-surface filtration", ["obstruction_surface_id"]),
        FiltrationSpec("residual_basin", "Residual-basin filtration", ["obstruction_surface_id", "source_signature", "target_demand_signature"]),
        FiltrationSpec("sat_unsat_boundary", "SAT/UNSAT boundary filtration", ["obstruction_surface_id", "route", "target_demand_signature"]),
    ]


def build_filtration_evidence(
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]],
    root_candidates: Iterable[RootCandidate | dict[str, Any]],
    specs: list[FiltrationSpec] | None = None,
) -> list[FiltrationEvidence]:
    telemetry = [CompletionTelemetryRow.from_any(row) for row in rows]
    roots = [_root_from_any(root) for root in root_candidates]
    specs = specs or default_filtration_specs()
    background = _hit_rate(telemetry)
    evidence: list[FiltrationEvidence] = []
    for root in sorted(roots, key=lambda item: item.root_node_id):
        relevant = _relevant_rows(root, telemetry)
        for spec in specs:
            buckets: dict[str, list[CompletionTelemetryRow]] = defaultdict(list)
            for row in relevant:
                key = _filtration_key(row, spec.field_names)
                if _key_supports_root(key, row, root, spec.field_names):
                    buckets[key].append(row)
            if not buckets:
                continue
            key, cluster = _best_bucket(buckets, background)
            sat = _count(cluster, SAT)
            unsat = _count(cluster, UNSAT)
            unknown = _count(cluster, UNKNOWN)
            timeout = _count(cluster, TIMEOUT)
            error = _count(cluster, ERROR)
            attempts = len(cluster)
            hit_rate = sat / attempts if attempts else 0.0
            contrast = abs(hit_rate - background)
            evidence.append(
                FiltrationEvidence(
                    root_node_id=root.root_node_id,
                    filtration_id=spec.filtration_id,
                    key=key,
                    sat_count=sat,
                    unsat_count=unsat,
                    unknown_count=unknown,
                    timeout_count=timeout,
                    error_count=error,
                    attempt_count=attempts,
                    hit_rate=round(hit_rate, 6),
                    contrast_score=round(contrast, 6),
                    evidence={
                        "advisory_only": True,
                        "field_names": list(spec.field_names),
                        "background_hit_rate": round(background, 6),
                        "pairs": sorted((row.source_idx, row.target_idx) for row in cluster),
                    },
                )
            )
    return sorted(evidence, key=lambda item: (item.root_node_id, item.filtration_id, item.key))


def summarize_persistence(
    root_candidates: Iterable[RootCandidate | dict[str, Any]],
    filtration_evidence: Iterable[FiltrationEvidence | dict[str, Any]],
) -> list[PersistentFiltrationSummary]:
    roots = [_root_from_any(root) for root in root_candidates]
    evidence = [_evidence_from_any(item) for item in filtration_evidence]
    by_root: dict[str, list[FiltrationEvidence]] = defaultdict(list)
    for item in evidence:
        by_root[item.root_node_id].append(item)
    summaries: list[PersistentFiltrationSummary] = []
    for root in sorted(roots, key=lambda item: item.root_node_id):
        items = by_root.get(root.root_node_id, [])
        raw_count = len({item.filtration_id for item in items})
        duplication_penalty = _duplication_penalty(items)
        shadow_penalty = _single_dominance_penalty(root)
        effective_count = max(0.0, raw_count - duplication_penalty)
        contrasts = [item.contrast_score for item in items]
        mean_contrast = sum(contrasts) / len(contrasts) if contrasts else 0.0
        max_contrast = max(contrasts) if contrasts else 0.0
        residual_gain = float(root.residual_compression_gain or root.evidence.get("residual_compression_gain", 0.0) or 0.0)
        boundary_clarity = _boundary_clarity(items)
        persistence_score = (
            math.log1p(effective_count)
            + 2.0 * mean_contrast
            + max_contrast
            + boundary_clarity
            + 2.0 * residual_gain
            - shadow_penalty
        )
        notes = ["advisory_only", "not_terminal_truth"]
        if shadow_penalty:
            notes.append("single evidence channel dominance penalized")
        if duplication_penalty:
            notes.append("duplicated filtration evidence penalized")
        summaries.append(
            PersistentFiltrationSummary(
                root_node_id=root.root_node_id,
                raw_filtration_count=raw_count,
                effective_filtration_count=round(effective_count, 6),
                mean_contrast_score=round(mean_contrast, 6),
                max_contrast_score=round(max_contrast, 6),
                persistence_score=round(max(0.0, persistence_score), 6),
                shadow_overlap_penalty=round(shadow_penalty, 6),
                evidence_duplication_penalty=round(duplication_penalty, 6),
                notes=notes,
                evidence={
                    "advisory_only": True,
                    "filtration_ids": sorted({item.filtration_id for item in items}),
                    "root_load_bearing_score": root.load_bearing_score,
                    "residual_compression_gain": residual_gain,
                    "boundary_clarity": round(boundary_clarity, 6),
                },
            )
        )
    return sorted(summaries, key=lambda item: (-item.persistence_score, item.root_node_id))


def _root_from_any(root: RootCandidate | dict[str, Any]) -> RootCandidate:
    if isinstance(root, RootCandidate):
        return root
    return RootCandidate(**dict(root))


def _evidence_from_any(item: FiltrationEvidence | dict[str, Any]) -> FiltrationEvidence:
    if isinstance(item, FiltrationEvidence):
        return item
    return FiltrationEvidence(**dict(item))


def _relevant_rows(root: RootCandidate, rows: list[CompletionTelemetryRow]) -> list[CompletionTelemetryRow]:
    result = []
    for row in rows:
        if row.obstruction_surface_id != root.obstruction_surface_id:
            continue
        if root.route is not None and row.route != root.route:
            continue
        if row.source_signature == root.source_signature or row.target_demand_signature == root.target_demand_signature:
            result.append(row)
            continue
        if row.table_hash and row.table_hash in set(root.table_hashes):
            result.append(row)
            continue
        if row.witness_schema and row.witness_schema == root.witness_schema:
            result.append(row)
    return result


def _filtration_key(row: CompletionTelemetryRow, fields: list[str]) -> str:
    return "|".join(str(getattr(row, field, None)) for field in fields)


def _key_supports_root(key: str, row: CompletionTelemetryRow, root: RootCandidate, fields: list[str]) -> bool:
    if not fields:
        return False
    if "source_signature" in fields and root.source_signature and row.source_signature == root.source_signature:
        return True
    if "target_demand_signature" in fields and root.target_demand_signature and row.target_demand_signature == root.target_demand_signature:
        return True
    if "table_hash" in fields and row.table_hash and row.table_hash in set(root.table_hashes):
        return True
    if "witness_schema" in fields and root.witness_schema and row.witness_schema == root.witness_schema:
        return True
    if "carrier_order" in fields and row.carrier_order in set(root.orders):
        return True
    if "obstruction_surface_id" in fields and row.obstruction_surface_id == root.obstruction_surface_id:
        return True
    return bool(key)


def _best_bucket(buckets: dict[str, list[CompletionTelemetryRow]], background: float) -> tuple[str, list[CompletionTelemetryRow]]:
    def score(item: tuple[str, list[CompletionTelemetryRow]]) -> tuple[float, int, str]:
        key, rows = item
        hit = _hit_rate(rows)
        return (abs(hit - background), len(rows), key)

    return max(buckets.items(), key=score)


def _hit_rate(rows: list[CompletionTelemetryRow]) -> float:
    return _count(rows, SAT) / len(rows) if rows else 0.0


def _count(rows: list[CompletionTelemetryRow], status: str) -> int:
    return sum(1 for row in rows if row.solver_status == status)


def _duplication_penalty(items: list[FiltrationEvidence]) -> float:
    if not items:
        return 0.0
    keys = Counter(item.key for item in items)
    duplicated = sum(count - 1 for count in keys.values() if count > 1)
    return min(len(items) * 0.5, 0.35 * duplicated)


def _single_dominance_penalty(root: RootCandidate) -> float:
    penalty = 0.0
    if root.table_reuse_score >= 0.95 and root.sat_count <= 3:
        penalty += 0.4
    if root.source_burst_score >= 0.95 and root.sat_count <= 3:
        penalty += 0.4
    return penalty


def _boundary_clarity(items: list[FiltrationEvidence]) -> float:
    if not items:
        return 0.0
    rates = []
    for item in items:
        blocked = item.unsat_count + item.unknown_count + item.timeout_count
        rates.append(blocked / item.attempt_count if item.attempt_count else 0.0)
    return sum(rates) / len(rates)


def to_jsonable(items: Iterable[Any]) -> list[dict[str, Any]]:
    return [item.to_dict() if hasattr(item, "to_dict") else dict(item) for item in items]

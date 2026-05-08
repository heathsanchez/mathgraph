"""Contrastive root discovery over obstruction-surface completion telemetry.

This module is discovery-only. It never verifies a theorem, never validates a
countermodel, and never promotes a terminal claim into the lawbook. It distills
SAT/UNSAT/UNKNOWN/ERROR telemetry into candidate roots, obstructions,
constructor-family cards, and replay queues for later verifier/importer work.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from mathgraph.obstruction_atlas import ObstructionNode
from mathgraph.root_nodes import RootNode

SAT = "SAT"
UNSAT = "UNSAT"
UNKNOWN = "UNKNOWN"
ERROR = "ERROR"
TIMEOUT = "TIMEOUT"

DISCOVERY_STATUS = "discovery_candidate"

ROOT_TYPES = {
    "symbolic_closure_separator_root",
    "source_burst_root",
    "table_reuse_root",
    "witness_schema_root",
    "obstruction_boundary_root",
    "carrier_order_boundary_root",
    "derived_amplification_root",
    "residual_compression_root",
}

OBSTRUCTION_TYPES = {
    "unsat_boundary_obstruction",
    "unknown_frontier_obstruction",
    "route_block_obstruction",
    "carrier_order_block_obstruction",
    "target_demand_block_obstruction",
    "source_shape_block_obstruction",
}


@dataclass(frozen=True)
class CompletionTelemetryRow:
    run_id: str
    obstruction_surface_id: str
    source_idx: int
    target_idx: int
    source_equation: str | None = None
    target_equation: str | None = None
    carrier_order: int | None = None
    solver_status: str = UNKNOWN
    certificate_id: str | None = None
    table_hash: str | None = None
    table_json: str | dict[str, Any] | list[Any] | None = None
    witness_assignment: dict[str, Any] | None = None
    witness_schema: str | None = None
    source_signature: str | None = None
    target_signature: str | None = None
    target_demand_signature: str | None = None
    route: str | None = None
    elapsed_sec: float | None = None
    failure_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_any(cls, row: "CompletionTelemetryRow | dict[str, Any]") -> "CompletionTelemetryRow":
        if isinstance(row, cls):
            return row
        data = dict(row)
        return cls(
            run_id=str(data.get("run_id") or ""),
            obstruction_surface_id=str(data.get("obstruction_surface_id") or data.get("surface_id") or "unknown_surface"),
            source_idx=_int(data.get("source_idx")),
            target_idx=_int(data.get("target_idx")),
            source_equation=_optional_str(data.get("source_equation") or data.get("source")),
            target_equation=_optional_str(data.get("target_equation") or data.get("target")),
            carrier_order=_optional_int(data.get("carrier_order") or data.get("order")),
            solver_status=_status(data.get("solver_status") or data.get("status")),
            certificate_id=_optional_str(data.get("certificate_id")),
            table_hash=_optional_str(data.get("table_hash")),
            table_json=data.get("table_json") or data.get("table"),
            witness_assignment=data.get("witness_assignment") or data.get("witness"),
            witness_schema=_optional_str(data.get("witness_schema")),
            source_signature=_optional_str(data.get("source_signature")),
            target_signature=_optional_str(data.get("target_signature")),
            target_demand_signature=_optional_str(data.get("target_demand_signature")),
            route=_optional_str(data.get("route")),
            elapsed_sec=_optional_float(data.get("elapsed_sec")),
            failure_reason=_optional_str(data.get("failure_reason")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RootCandidate:
    root_node_id: str
    canonical_name: str
    root_type: str
    root_key: str
    obstruction_surface_id: str
    source_signature: str | None
    target_demand_signature: str | None
    route: str | None
    table_hashes: list[str]
    orders: list[int]
    witness_schema: str | None
    sat_count: int
    unsat_count: int
    unknown_count: int
    error_count: int
    attempt_count: int
    hit_rate: float
    table_reuse_score: float
    source_burst_score: float
    witness_reuse_score: float
    sat_unsat_contrast: float
    replay_gain: float
    derived_amplification_factor: float
    residual_compression_gain: float
    load_bearing_score: float
    status: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_root_node(self) -> RootNode:
        return RootNode(
            root_node_id=self.root_node_id,
            canonical_name=self.canonical_name,
            root_type=self.root_type,
            root_key=self.root_key,
            root_key_fields={
                "obstruction_surface_id": self.obstruction_surface_id,
                "source_signature": self.source_signature,
                "target_demand_signature": self.target_demand_signature,
                "route": self.route,
                "witness_schema": self.witness_schema,
            },
            table_motif=self.table_hashes[0] if self.table_hashes else "",
            support_count=self.sat_count,
            rows=self.attempt_count,
            unique_sources=len(self.evidence.get("source_signatures", [])),
            unique_targets=len(self.evidence.get("target_demand_signatures", [])),
            unique_tables=len(self.table_hashes),
            load_bearing_score=self.load_bearing_score,
            compression_ratio=self.residual_compression_gain,
            coverage_density=self.hit_rate,
            status=self.status,
            evidence=self.to_dict(),
            created_from_run_id=str(self.evidence.get("run_ids", [""])[0] if self.evidence.get("run_ids") else ""),
        )


@dataclass(frozen=True)
class ObstructionCandidate:
    obstruction_id: str
    canonical_name: str
    obstruction_surface_id: str
    obstruction_type: str
    route: str | None
    source_signature: str | None
    target_demand_signature: str | None
    unsat_count: int
    unknown_count: int
    sat_count: int
    attempt_count: int
    boundary_score: float
    negative_route_evidence: dict[str, Any]
    status: str = DISCOVERY_STATUS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_obstruction_node(self) -> ObstructionNode:
        return ObstructionNode(
            obstruction_id=self.obstruction_id,
            obstruction_signature=self.canonical_name,
            failure_reason=self.obstruction_type,
            derivation_rule=self.route or "",
            rows=self.attempt_count,
            unique_sources=len(self.negative_route_evidence.get("source_signatures", [])),
            unique_targets=len(self.negative_route_evidence.get("target_demand_signatures", [])),
            obstruction_pressure_score=self.boundary_score,
            next_constructor_pressure={
                "advisory_only": True,
                "route": self.route,
                "unknown_count": self.unknown_count,
            },
            evidence=self.to_dict(),
        )


@dataclass(frozen=True)
class ConstructorFamilyCard:
    family_id: str
    canonical_name: str
    root_node_id: str | None
    table_hashes: list[str]
    witness_schemas: list[str]
    source_signatures: list[str]
    target_demand_signatures: list[str]
    route: str | None
    replay_queue: list[dict[str, Any]]
    evidence: dict[str, Any]
    status: str = DISCOVERY_STATUS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def distill_root_candidates(
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]],
    *,
    local_background_hit_rate: float | None = None,
    min_sat_count: int = 2,
) -> list[RootCandidate]:
    telemetry = _normalize_rows(rows)
    if not telemetry:
        return []
    background = _background_hit_rate(telemetry) if local_background_hit_rate is None else float(local_background_hit_rate)
    by_key: dict[tuple[str, str | None, str | None, str | None], list[CompletionTelemetryRow]] = defaultdict(list)
    by_surface_route_demand: dict[tuple[str, str | None, str | None], list[CompletionTelemetryRow]] = defaultdict(list)
    for row in telemetry:
        by_key[(row.obstruction_surface_id, row.source_signature, row.target_demand_signature, row.route)].append(row)
        by_surface_route_demand[(row.obstruction_surface_id, row.route, row.target_demand_signature)].append(row)

    candidates: list[RootCandidate] = []
    for key in sorted(by_key, key=_sort_key):
        cluster = by_key[key]
        sat_rows = [row for row in cluster if row.solver_status == SAT]
        if len(sat_rows) < min_sat_count:
            continue
        surface, source_sig, demand_sig, route = key
        neighborhood = by_surface_route_demand[(surface, route, demand_sig)]
        unsat_count = sum(1 for row in neighborhood if row.solver_status == UNSAT)
        unknown_count = sum(1 for row in neighborhood if row.solver_status in {UNKNOWN, TIMEOUT})
        error_count = sum(1 for row in neighborhood if row.solver_status == ERROR)
        attempt_count = len(neighborhood)
        focused_hit_rate = _ratio(len(sat_rows), len(cluster))
        table_counts = Counter(row.table_hash for row in sat_rows if row.table_hash)
        witness_counts = Counter(row.witness_schema for row in sat_rows if row.witness_schema)
        source_counts = Counter(row.source_signature for row in sat_rows if row.source_signature)
        demand_counts = Counter(row.target_demand_signature for row in sat_rows if row.target_demand_signature)
        route_counts = Counter(row.route for row in sat_rows if row.route)
        table_reuse_score = _max_freq_ratio(table_counts, len(sat_rows))
        witness_reuse_score = _max_freq_ratio(witness_counts, len(sat_rows))
        source_burst_score = _max_freq_ratio(source_counts, len(sat_rows))
        sat_unsat_contrast = abs(focused_hit_rate - background)
        replay_gain = _max_metric(sat_rows, "replay_gain", 0.0)
        derived_amp = _max_metric(sat_rows, "derived_amplification_factor", 1.0)
        residual_gain = _max_metric(sat_rows, "residual_compression_gain", 0.0)
        broadness_penalty = _broadness_penalty(source_counts, demand_counts, route_counts)
        load_score = _load_bearing_score(
            sat_count=len(sat_rows),
            table_reuse_score=table_reuse_score,
            witness_reuse_score=witness_reuse_score,
            source_burst_score=source_burst_score,
            sat_unsat_contrast=sat_unsat_contrast,
            replay_gain=replay_gain,
            derived_amplification_factor=derived_amp,
            residual_compression_gain=residual_gain,
            broadness_penalty=broadness_penalty,
        )
        root_type = _choose_root_type(
            table_reuse_score=table_reuse_score,
            witness_reuse_score=witness_reuse_score,
            source_burst_score=source_burst_score,
            sat_unsat_contrast=sat_unsat_contrast,
            orders={row.carrier_order for row in sat_rows if row.carrier_order is not None},
            replay_gain=replay_gain,
            derived_amplification_factor=derived_amp,
            residual_compression_gain=residual_gain,
        )
        table_hashes = sorted(table_counts)
        orders = sorted({int(row.carrier_order) for row in sat_rows if row.carrier_order is not None})
        witness_schema = _first_sorted(witness_counts)
        root_key = "|".join(str(part) for part in (surface, source_sig, demand_sig, route, root_type))
        root_id = f"root_{_stable_hash(root_key)[:16]}"
        candidates.append(
            RootCandidate(
                root_node_id=root_id,
                canonical_name=f"ROOT_{root_type.upper()}_{_stable_hash(root_key)[:8]}",
                root_type=root_type,
                root_key=root_key,
                obstruction_surface_id=surface,
                source_signature=source_sig,
                target_demand_signature=demand_sig,
                route=route,
                table_hashes=table_hashes,
                orders=orders,
                witness_schema=witness_schema,
                sat_count=len(sat_rows),
                unsat_count=unsat_count,
                unknown_count=unknown_count,
                error_count=error_count,
                attempt_count=attempt_count,
                hit_rate=round(focused_hit_rate, 6),
                table_reuse_score=round(table_reuse_score, 6),
                source_burst_score=round(source_burst_score, 6),
                witness_reuse_score=round(witness_reuse_score, 6),
                sat_unsat_contrast=round(sat_unsat_contrast, 6),
                replay_gain=round(replay_gain, 6),
                derived_amplification_factor=round(derived_amp, 6),
                residual_compression_gain=round(residual_gain, 6),
                load_bearing_score=round(load_score, 6),
                status=DISCOVERY_STATUS,
                evidence={
                    "advisory_only": True,
                    "not_terminal_truth": True,
                    "doctrine": "Root nodes are SAT-clusters carved out by UNSAT boundaries.",
                    "run_ids": sorted({row.run_id for row in sat_rows if row.run_id}),
                    "source_signatures": sorted(source_counts),
                    "target_demand_signatures": sorted(demand_counts),
                    "routes": sorted(route_counts),
                    "certificate_ids": sorted(row.certificate_id for row in sat_rows if row.certificate_id),
                    "sat_pairs": sorted((row.source_idx, row.target_idx) for row in sat_rows),
                    "local_background_hit_rate": round(background, 6),
                    "broadness_penalty": round(broadness_penalty, 6),
                },
            )
        )
    return sorted(candidates, key=lambda item: (-item.load_bearing_score, item.root_node_id))


def distill_obstruction_candidates(
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]],
    *,
    min_unsat_count: int = 2,
) -> list[ObstructionCandidate]:
    telemetry = _normalize_rows(rows)
    groups: dict[tuple[str, str | None, str | None, str | None], list[CompletionTelemetryRow]] = defaultdict(list)
    for row in telemetry:
        groups[(row.obstruction_surface_id, row.route, row.source_signature, row.target_demand_signature)].append(row)

    candidates: list[ObstructionCandidate] = []
    for key in sorted(groups, key=_sort_key):
        cluster = groups[key]
        unsat = sum(1 for row in cluster if row.solver_status == UNSAT)
        unknown = sum(1 for row in cluster if row.solver_status in {UNKNOWN, TIMEOUT})
        sat = sum(1 for row in cluster if row.solver_status == SAT)
        if unsat < min_unsat_count and unknown < min_unsat_count:
            continue
        surface, route, source_sig, demand_sig = key
        obstruction_type = _choose_obstruction_type(cluster, unsat, unknown, sat)
        attempt_count = len(cluster)
        boundary_score = _obstruction_boundary_score(unsat, unknown, sat, attempt_count)
        obstruction_key = "|".join(str(part) for part in (surface, route, source_sig, demand_sig, obstruction_type))
        candidates.append(
            ObstructionCandidate(
                obstruction_id=f"obstruction_{_stable_hash(obstruction_key)[:16]}",
                canonical_name=f"OBSTRUCTION_{obstruction_type.upper()}_{_stable_hash(obstruction_key)[:8]}",
                obstruction_surface_id=surface,
                obstruction_type=obstruction_type,
                route=route,
                source_signature=source_sig,
                target_demand_signature=demand_sig,
                unsat_count=unsat,
                unknown_count=unknown,
                sat_count=sat,
                attempt_count=attempt_count,
                boundary_score=round(boundary_score, 6),
                negative_route_evidence={
                    "advisory_only": True,
                    "not_terminal_truth": True,
                    "source_signatures": sorted({row.source_signature for row in cluster if row.source_signature}),
                    "target_demand_signatures": sorted(
                        {row.target_demand_signature for row in cluster if row.target_demand_signature}
                    ),
                    "orders": sorted({row.carrier_order for row in cluster if row.carrier_order is not None}),
                    "failure_reasons": sorted({row.failure_reason for row in cluster if row.failure_reason}),
                    "statuses": dict(sorted(Counter(row.solver_status for row in cluster).items())),
                    "pairs": sorted((row.source_idx, row.target_idx) for row in cluster),
                },
            )
        )
    return sorted(candidates, key=lambda item: (-item.boundary_score, item.obstruction_id))


def build_constructor_family_cards(
    root_candidates: Iterable[RootCandidate],
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]],
) -> list[ConstructorFamilyCard]:
    telemetry = _normalize_rows(rows)
    cards: list[ConstructorFamilyCard] = []
    for root in sorted(root_candidates, key=lambda item: item.root_node_id):
        matched = _rows_for_root(root, telemetry)
        replay_queue = build_replay_queue([root], matched)
        key = f"{root.root_node_id}|{root.route}|{','.join(root.table_hashes)}"
        cards.append(
            ConstructorFamilyCard(
                family_id=f"family_{_stable_hash(key)[:16]}",
                canonical_name=f"FAMILY_{root.canonical_name}",
                root_node_id=root.root_node_id,
                table_hashes=list(root.table_hashes),
                witness_schemas=sorted({row.witness_schema for row in matched if row.witness_schema}),
                source_signatures=sorted({row.source_signature for row in matched if row.source_signature}),
                target_demand_signatures=sorted(
                    {row.target_demand_signature for row in matched if row.target_demand_signature}
                ),
                route=root.route,
                replay_queue=replay_queue,
                evidence={
                    "advisory_only": True,
                    "root_load_bearing_score": root.load_bearing_score,
                    "matched_rows": len(matched),
                    "sat_rows": sum(1 for row in matched if row.solver_status == SAT),
                    "unknown_rows": sum(1 for row in matched if row.solver_status in {UNKNOWN, TIMEOUT}),
                },
            )
        )
    return cards


def build_replay_queue(
    root_candidates: Iterable[RootCandidate],
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]],
    max_items: int = 50,
) -> list[dict[str, Any]]:
    telemetry = _normalize_rows(rows)
    queue: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for root in sorted(root_candidates, key=lambda item: (-item.load_bearing_score, item.root_node_id)):
        for row in _rows_for_root(root, telemetry):
            if row.solver_status not in {UNKNOWN, TIMEOUT, UNSAT}:
                continue
            key = (root.root_node_id, row.source_idx, row.target_idx)
            if key in seen:
                continue
            seen.add(key)
            queue.append(
                {
                    "root_node_id": root.root_node_id,
                    "obstruction_surface_id": row.obstruction_surface_id,
                    "source_idx": row.source_idx,
                    "target_idx": row.target_idx,
                    "source_equation": row.source_equation,
                    "target_equation": row.target_equation,
                    "route": row.route,
                    "carrier_order": row.carrier_order,
                    "solver_status": row.solver_status,
                    "reason": "Replay near contrastive root boundary; not a truth claim.",
                }
            )
            if len(queue) >= max_items:
                return queue
    return queue


def summarize_root_discovery(
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]],
    root_candidates: Iterable[RootCandidate],
    obstruction_candidates: Iterable[ObstructionCandidate],
) -> dict[str, Any]:
    telemetry = _normalize_rows(rows)
    roots = list(root_candidates)
    obstructions = list(obstruction_candidates)
    status_counts = Counter(row.solver_status for row in telemetry)
    return {
        "row_count": len(telemetry),
        "status_counts": dict(sorted(status_counts.items())),
        "root_candidate_count": len(roots),
        "obstruction_candidate_count": len(obstructions),
        "top_root_ids": [root.root_node_id for root in sorted(roots, key=lambda item: (-item.load_bearing_score, item.root_node_id))[:10]],
        "top_obstruction_ids": [
            obstruction.obstruction_id
            for obstruction in sorted(obstructions, key=lambda item: (-item.boundary_score, item.obstruction_id))[:10]
        ],
        "unknown_frontier_count": status_counts.get(UNKNOWN, 0) + status_counts.get(TIMEOUT, 0),
        "advisory_only": True,
        "verifier_boundary_unchanged": True,
        "doctrine": "The distiller creates discovery artifacts only; verifiers/importers decide terminal truth.",
    }


def _normalize_rows(rows: Iterable[CompletionTelemetryRow | dict[str, Any]]) -> list[CompletionTelemetryRow]:
    return [CompletionTelemetryRow.from_any(row) for row in rows]


def _rows_for_root(root: RootCandidate, rows: list[CompletionTelemetryRow]) -> list[CompletionTelemetryRow]:
    return [
        row
        for row in rows
        if row.obstruction_surface_id == root.obstruction_surface_id
        and row.route == root.route
        and row.target_demand_signature == root.target_demand_signature
        and (row.source_signature == root.source_signature or row.solver_status in {UNKNOWN, TIMEOUT, UNSAT})
    ]


def _choose_root_type(
    *,
    table_reuse_score: float,
    witness_reuse_score: float,
    source_burst_score: float,
    sat_unsat_contrast: float,
    orders: set[int],
    replay_gain: float,
    derived_amplification_factor: float,
    residual_compression_gain: float,
) -> str:
    if residual_compression_gain > 0:
        return "residual_compression_root"
    if derived_amplification_factor > 1.0:
        return "derived_amplification_root"
    if table_reuse_score >= 0.75:
        return "table_reuse_root"
    if witness_reuse_score >= 0.75:
        return "witness_schema_root"
    if source_burst_score >= 0.75:
        return "source_burst_root"
    if len(orders) == 1 and sat_unsat_contrast >= 0.25:
        return "carrier_order_boundary_root"
    if sat_unsat_contrast >= 0.25:
        return "obstruction_boundary_root"
    if replay_gain > 0:
        return "symbolic_closure_separator_root"
    return "source_burst_root"


def _choose_obstruction_type(cluster: list[CompletionTelemetryRow], unsat: int, unknown: int, sat: int) -> str:
    orders = {row.carrier_order for row in cluster if row.carrier_order is not None}
    sources = {row.source_signature for row in cluster if row.source_signature}
    demands = {row.target_demand_signature for row in cluster if row.target_demand_signature}
    routes = {row.route for row in cluster if row.route}
    if unknown > unsat and unknown >= sat:
        return "unknown_frontier_obstruction"
    if len(orders) == 1 and unsat > sat:
        return "carrier_order_block_obstruction"
    if len(demands) == 1 and unsat > sat:
        return "target_demand_block_obstruction"
    if len(sources) == 1 and unsat > sat:
        return "source_shape_block_obstruction"
    if len(routes) == 1 and unsat > sat:
        return "route_block_obstruction"
    return "unsat_boundary_obstruction"


def _load_bearing_score(
    *,
    sat_count: int,
    table_reuse_score: float,
    witness_reuse_score: float,
    source_burst_score: float,
    sat_unsat_contrast: float,
    replay_gain: float,
    derived_amplification_factor: float,
    residual_compression_gain: float,
    broadness_penalty: float,
) -> float:
    return (
        2.0 * math.log1p(sat_count)
        + 1.5 * table_reuse_score
        + 1.5 * witness_reuse_score
        + 1.5 * source_burst_score
        + 2.0 * sat_unsat_contrast
        + math.log1p(max(0.0, replay_gain))
        + math.log1p(max(0.0, derived_amplification_factor - 1.0))
        + 2.0 * residual_compression_gain
        - broadness_penalty
    )


def _obstruction_boundary_score(unsat: int, unknown: int, sat: int, attempt_count: int) -> float:
    blocked_rate = _ratio(unsat + 0.5 * unknown, attempt_count)
    sat_penalty = _ratio(sat, attempt_count)
    return 2.0 * math.log1p(unsat) + 1.0 * math.log1p(unknown) + blocked_rate - sat_penalty


def _broadness_penalty(*counters: Counter[Any]) -> float:
    penalty = 0.0
    for counter in counters:
        width = len([key for key in counter if key not in (None, "")])
        if width > 1:
            penalty += 0.25 * (width - 1)
    return penalty


def _background_hit_rate(rows: list[CompletionTelemetryRow]) -> float:
    return _ratio(sum(1 for row in rows if row.solver_status == SAT), len(rows))


def _max_freq_ratio(counter: Counter[Any], denom: int) -> float:
    if not counter:
        return 0.0
    return _ratio(max(counter.values()), denom)


def _max_metric(rows: list[CompletionTelemetryRow], key: str, default: float) -> float:
    values = []
    for row in rows:
        value = row.metadata.get(key)
        if value is not None:
            parsed = _optional_float(value)
            if parsed is not None:
                values.append(parsed)
    return max(values) if values else default


def _ratio(num: int | float, denom: int | float) -> float:
    return float(num) / float(denom) if denom else 0.0


def _first_sorted(counter: Counter[Any]) -> str | None:
    keys = sorted(key for key in counter if key not in (None, ""))
    return str(keys[0]) if keys else None


def _stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sort_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _status(value: Any) -> str:
    text = str(value or UNKNOWN).upper()
    if text in {"SAT", "FINITE_COUNTERMODEL_FOUND", "FOUND"}:
        return SAT
    if text in {"UNSAT", "NO_MODEL", "NO_COUNTERMODEL_EXISTS"}:
        return UNSAT
    if text in {"TIMEOUT"}:
        return TIMEOUT
    if text in {"ERROR", "MALFORMED"}:
        return ERROR
    return UNKNOWN


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    parsed = _optional_int(value)
    return int(parsed) if parsed is not None else 0


def _optional_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

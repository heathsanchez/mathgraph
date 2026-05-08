"""Compile promoted advisory roots into constructor-family plans."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from mathgraph.root_discovery import CompletionTelemetryRow, RootCandidate, build_replay_queue
from mathgraph.root_promotion import RootPromotionRecord


@dataclass(frozen=True)
class ConstructorPlan:
    plan_id: str
    root_node_id: str
    canonical_name: str
    constructor_type: str
    obstruction_surface_id: str | None
    route: str | None
    source_signature: str | None
    target_demand_signature: str | None
    table_hashes: list[str]
    witness_schema: str | None
    carrier_orders: list[int]
    replay_queue: list[dict[str, Any]]
    expected_yield_score: float
    verifier_requirements: list[str]
    advisory_only: bool = True
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_constructor_plans(
    root_candidates: Iterable[RootCandidate | dict[str, Any]],
    promotion_records: Iterable[RootPromotionRecord | dict[str, Any]],
    rows: Iterable[CompletionTelemetryRow | dict[str, Any]] | None = None,
    max_replay_items: int = 50,
) -> list[ConstructorPlan]:
    roots = {_root_from_any(root).root_node_id: _root_from_any(root) for root in root_candidates}
    promotions = [_promotion_from_any(record) for record in promotion_records]
    telemetry = [CompletionTelemetryRow.from_any(row) for row in rows] if rows is not None else []
    plans: list[ConstructorPlan] = []
    for record in sorted(promotions, key=lambda item: item.root_node_id):
        if not record.promoted or record.suggested_next_action != "compile_constructor_family":
            continue
        root = roots.get(record.canonical_root_id) or roots.get(record.root_node_id)
        if root is None:
            continue
        replay = build_replay_queue([root], telemetry, max_items=max_replay_items) if telemetry else []
        constructor_type = choose_constructor_type(root)
        plan_key = "|".join([root.root_node_id, constructor_type, root.route or "", ",".join(root.table_hashes)])
        expected_yield = root.load_bearing_score + record.persistence_score + len(replay) * 0.1
        plans.append(
            ConstructorPlan(
                plan_id=f"plan_{hashlib.sha256(plan_key.encode('utf-8')).hexdigest()[:16]}",
                root_node_id=root.root_node_id,
                canonical_name=f"PLAN_{root.canonical_name}",
                constructor_type=constructor_type,
                obstruction_surface_id=root.obstruction_surface_id,
                route=root.route,
                source_signature=root.source_signature,
                target_demand_signature=root.target_demand_signature,
                table_hashes=list(root.table_hashes),
                witness_schema=root.witness_schema,
                carrier_orders=list(root.orders),
                replay_queue=replay,
                expected_yield_score=round(expected_yield, 6),
                verifier_requirements=[
                    "candidate outputs must be checked by existing verifier/importer boundary",
                    "finite countermodels require source satisfaction and target violation replay",
                    "constructor plan is advisory scheduling pressure, not a certificate",
                ],
                advisory_only=True,
                evidence={
                    "promotion_record": record.to_dict(),
                    "root_load_bearing_score": root.load_bearing_score,
                    "root_persistence_score": record.persistence_score,
                    "not_terminal_truth": True,
                },
            )
        )
    return sorted(plans, key=lambda item: (-item.expected_yield_score, item.plan_id))


def choose_constructor_type(root_candidate: RootCandidate | dict[str, Any]) -> str:
    root = _root_from_any(root_candidate)
    mapping = {
        "table_reuse_root": "table_reuse_constructor",
        "witness_schema_root": "witness_schema_constructor",
        "source_burst_root": "source_burst_constructor",
        "carrier_order_boundary_root": "carrier_order_boundary_constructor",
        "residual_compression_root": "residual_compression_constructor",
        "derived_amplification_root": "derived_amplification_constructor",
        "obstruction_boundary_root": "obstruction_boundary_constructor",
        "symbolic_closure_separator_root": "symbolic_closure_separator_constructor",
    }
    return mapping.get(root.root_type, "obstruction_boundary_constructor")


def _root_from_any(root: RootCandidate | dict[str, Any]) -> RootCandidate:
    if isinstance(root, RootCandidate):
        return root
    return RootCandidate(**dict(root))


def _promotion_from_any(record: RootPromotionRecord | dict[str, Any]) -> RootPromotionRecord:
    if isinstance(record, RootPromotionRecord):
        return record
    return RootPromotionRecord(**dict(record))

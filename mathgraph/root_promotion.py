"""Advisory promotion records for persistent non-shadow root candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from mathgraph.persistent_filtration import PersistentFiltrationSummary
from mathgraph.root_discovery import RootCandidate
from mathgraph.root_shadow_collapse import RootShadowCollapseResult


@dataclass(frozen=True)
class RootPromotionPolicy:
    min_persistence_score: float = 2.0
    min_effective_filtration_count: float = 2.0
    min_load_bearing_score: float = 2.5
    min_sat_count: int = 2
    max_shadow_penalty: float = 0.75
    require_non_shadow: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RootPromotionRecord:
    root_node_id: str
    canonical_root_id: str
    status: str
    promoted: bool
    reasons: list[str]
    load_bearing_score: float
    persistence_score: float
    effective_filtration_count: float
    shadow_penalty: float
    root_type: str
    suggested_next_action: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def promote_roots(
    root_candidates: Iterable[RootCandidate | dict[str, Any]],
    persistence_summaries: Iterable[PersistentFiltrationSummary | dict[str, Any]],
    shadow_result: RootShadowCollapseResult | dict[str, Any],
    policy: RootPromotionPolicy | None = None,
) -> list[RootPromotionRecord]:
    policy = policy or RootPromotionPolicy()
    roots = [_root_from_any(root) for root in root_candidates]
    persistence = {_summary_from_any(item).root_node_id: _summary_from_any(item) for item in persistence_summaries}
    shadow_map = _shadow_map(shadow_result)
    records: list[RootPromotionRecord] = []
    for root in sorted(roots, key=lambda item: item.root_node_id):
        summary = persistence.get(root.root_node_id)
        canonical = shadow_map.get(root.root_node_id, root.root_node_id)
        is_shadow = canonical != root.root_node_id
        shadow_penalty = 1.0 if is_shadow else (summary.shadow_overlap_penalty if summary else 0.0)
        reasons: list[str] = []
        promoted = True
        if is_shadow and policy.require_non_shadow:
            promoted = False
            reasons.append("root is a retired shadow of canonical root")
        if root.load_bearing_score < policy.min_load_bearing_score:
            promoted = False
            reasons.append("load_bearing_score below policy threshold")
        if root.sat_count < policy.min_sat_count:
            promoted = False
            reasons.append("sat_count below policy threshold")
        persistence_score = summary.persistence_score if summary else 0.0
        effective_count = summary.effective_filtration_count if summary else 0.0
        if persistence_score < policy.min_persistence_score:
            promoted = False
            reasons.append("persistence_score below policy threshold")
        if effective_count < policy.min_effective_filtration_count:
            promoted = False
            reasons.append("effective_filtration_count below policy threshold")
        if shadow_penalty > policy.max_shadow_penalty:
            promoted = False
            reasons.append("shadow penalty above policy threshold")
        if promoted:
            status = "constructor_ready_root" if (root.table_hashes or root.witness_schema) else "promoted_root"
            reasons.append("persistent non-shadow root passed promotion policy")
        elif is_shadow:
            status = "retired_shadow"
        elif persistence_score >= policy.min_persistence_score and effective_count >= policy.min_effective_filtration_count:
            status = "persistent_candidate"
        else:
            status = "failed_promotion_obstruction"
        records.append(
            RootPromotionRecord(
                root_node_id=root.root_node_id,
                canonical_root_id=canonical,
                status=status,
                promoted=promoted,
                reasons=reasons,
                load_bearing_score=root.load_bearing_score,
                persistence_score=persistence_score,
                effective_filtration_count=effective_count,
                shadow_penalty=shadow_penalty,
                root_type=root.root_type,
                suggested_next_action=_next_action(root, promoted, is_shadow, persistence_score),
                evidence={
                    "advisory_only": True,
                    "not_terminal_truth": True,
                    "policy": policy.to_dict(),
                    "persistence": summary.to_dict() if summary else None,
                },
            )
        )
    return sorted(records, key=lambda item: (-int(item.promoted), item.status, item.root_node_id))


def promotion_summary(records: Iterable[RootPromotionRecord | dict[str, Any]]) -> dict[str, Any]:
    items = [_record_from_any(record) for record in records]
    status_counts: dict[str, int] = {}
    for record in items:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
    return {
        "record_count": len(items),
        "promoted_count": sum(1 for record in items if record.promoted),
        "status_counts": dict(sorted(status_counts.items())),
        "constructor_ready_count": sum(1 for record in items if record.status == "constructor_ready_root"),
        "advisory_only": True,
        "verifier_boundary_unchanged": True,
    }


def _next_action(root: RootCandidate, promoted: bool, is_shadow: bool, persistence_score: float) -> str:
    if is_shadow:
        return "use_canonical_root"
    if promoted and (root.table_hashes or root.witness_schema):
        return "compile_constructor_family"
    if persistence_score > 0 and root.sat_count < 2:
        return "narrow_completion_replay"
    return "collect_more_telemetry"


def _root_from_any(root: RootCandidate | dict[str, Any]) -> RootCandidate:
    if isinstance(root, RootCandidate):
        return root
    return RootCandidate(**dict(root))


def _summary_from_any(item: PersistentFiltrationSummary | dict[str, Any]) -> PersistentFiltrationSummary:
    if isinstance(item, PersistentFiltrationSummary):
        return item
    return PersistentFiltrationSummary(**dict(item))


def _record_from_any(item: RootPromotionRecord | dict[str, Any]) -> RootPromotionRecord:
    if isinstance(item, RootPromotionRecord):
        return item
    return RootPromotionRecord(**dict(item))


def _shadow_map(result: RootShadowCollapseResult | dict[str, Any]) -> dict[str, str]:
    if isinstance(result, RootShadowCollapseResult):
        return dict(result.canonical_by_shadow)
    return dict(result.get("canonical_by_shadow", {}))

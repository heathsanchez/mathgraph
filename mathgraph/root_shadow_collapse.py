"""Shadow collapse for advisory root candidates."""

from __future__ import annotations

import difflib
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from mathgraph.root_discovery import RootCandidate


@dataclass(frozen=True)
class ShadowLink:
    canonical_root_id: str
    shadow_root_id: str
    overlap_score: float
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RootShadowCollapseResult:
    canonical_roots: list[RootCandidate | dict[str, Any]]
    shadow_links: list[ShadowLink]
    alias_records: list[dict[str, Any]]
    canonical_by_shadow: dict[str, str]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_roots": [_to_dict(root) for root in self.canonical_roots],
            "shadow_links": [link.to_dict() for link in self.shadow_links],
            "alias_records": list(self.alias_records),
            "canonical_by_shadow": dict(self.canonical_by_shadow),
            "summary": dict(self.summary),
        }


def collapse_root_shadows(
    root_candidates: Iterable[RootCandidate | dict[str, Any]],
    overlap_threshold: float = 0.72,
) -> RootShadowCollapseResult:
    roots = sorted([_root_from_any(root) for root in root_candidates], key=lambda item: item.root_node_id)
    clusters: list[list[RootCandidate]] = []
    for root in roots:
        placed = False
        for cluster in clusters:
            if any(root_overlap_score(root, other)[0] >= overlap_threshold for other in cluster):
                cluster.append(root)
                placed = True
                break
        if not placed:
            clusters.append([root])

    canonical_roots: list[RootCandidate] = []
    links: list[ShadowLink] = []
    aliases: list[dict[str, Any]] = []
    by_shadow: dict[str, str] = {}
    for cluster in clusters:
        canonical = choose_canonical_root(cluster)
        canonical_roots.append(canonical)
        for root in sorted(cluster, key=lambda item: item.root_node_id):
            if root.root_node_id == canonical.root_node_id:
                continue
            score, reasons = root_overlap_score(canonical, root)
            links.append(
                ShadowLink(
                    canonical_root_id=canonical.root_node_id,
                    shadow_root_id=root.root_node_id,
                    overlap_score=round(score, 6),
                    reasons=reasons,
                    evidence={"advisory_only": True, "shadow_preserved": True},
                )
            )
            by_shadow[root.root_node_id] = canonical.root_node_id
            aliases.append(
                {
                    "alias": root.canonical_name,
                    "canonical_name": canonical.canonical_name,
                    "reason": "; ".join(reasons) or "root shadow overlap",
                    "evidence": {
                        "canonical_root_id": canonical.root_node_id,
                        "shadow_root_id": root.root_node_id,
                        "overlap_score": round(score, 6),
                        "advisory_only": True,
                    },
                }
            )
    return RootShadowCollapseResult(
        canonical_roots=sorted(canonical_roots, key=lambda item: item.root_node_id),
        shadow_links=sorted(links, key=lambda item: (item.canonical_root_id, item.shadow_root_id)),
        alias_records=sorted(aliases, key=lambda item: (item["canonical_name"], item["alias"])),
        canonical_by_shadow=dict(sorted(by_shadow.items())),
        summary={
            "input_roots": len(roots),
            "canonical_count": len(canonical_roots),
            "shadow_count": len(links),
            "overlap_threshold": overlap_threshold,
            "advisory_only": True,
        },
    )


def root_overlap_score(a: RootCandidate | dict[str, Any], b: RootCandidate | dict[str, Any]) -> tuple[float, list[str]]:
    left = _root_from_any(a)
    right = _root_from_any(b)
    score = 0.0
    reasons: list[str] = []

    def add(points: float, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)

    if left.root_key == right.root_key:
        add(0.25, "same root_key")
    if left.obstruction_surface_id == right.obstruction_surface_id:
        add(0.12, "same obstruction surface")
    if left.source_signature and left.source_signature == right.source_signature:
        add(0.10, "same source signature")
    if left.target_demand_signature and left.target_demand_signature == right.target_demand_signature:
        add(0.10, "same target-demand signature")
    if left.route and left.route == right.route:
        add(0.08, "same route")
    table_overlap = _jaccard(set(left.table_hashes), set(right.table_hashes))
    if table_overlap:
        add(0.12 * table_overlap, "overlapping table hashes")
    if left.witness_schema and left.witness_schema == right.witness_schema:
        add(0.10, "same witness schema")
    pair_overlap = _jaccard(set(map(tuple, left.evidence.get("sat_pairs", []))), set(map(tuple, right.evidence.get("sat_pairs", []))))
    if pair_overlap:
        add(0.10 * pair_overlap, "overlapping SAT pairs")
    name_similarity = difflib.SequenceMatcher(a=left.canonical_name, b=right.canonical_name).ratio()
    if name_similarity >= 0.8:
        add(0.07 * name_similarity, "similar canonical name")
    if left.root_type == right.root_type:
        add(0.06, "same root type")
    return min(1.0, score), reasons


def choose_canonical_root(cluster: Iterable[RootCandidate | dict[str, Any]]) -> RootCandidate:
    roots = [_root_from_any(root) for root in cluster]
    return sorted(
        roots,
        key=lambda item: (
            -float(item.load_bearing_score),
            -int(item.sat_count),
            -float(item.residual_compression_gain),
            item.root_node_id,
        ),
    )[0]


def _root_from_any(root: RootCandidate | dict[str, Any]) -> RootCandidate:
    if isinstance(root, RootCandidate):
        return root
    return RootCandidate(**dict(root))


def _to_dict(root: RootCandidate | dict[str, Any]) -> dict[str, Any]:
    return root.to_dict() if hasattr(root, "to_dict") else dict(root)


def _jaccard(a: set[Any], b: set[Any]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

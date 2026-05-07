"""Canonical root consolidation for v16.7 root-node candidates."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any, Iterable

from mathgraph.hashing import content_id
from mathgraph.obstruction_atlas import ObstructionNode
from mathgraph.reason_nodes import ReasonNode
from mathgraph.root_nodes import RootNode, RootObstructionLink, RootReasonLink


ROOT_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("ROOT_PROJECTION_LEFT", ("projection_left", "left_projection", "affine_1_0_0")),
    ("ROOT_PROJECTION_RIGHT", ("projection_right", "right_projection", "affine_0_1_0", "square_sensitive")),
    ("ROOT_CONSTANT_COLLAPSE", ("constant", "taildrop", "const_", "constant_collapse")),
    ("ROOT_ADDITIVE_PARITY", ("offdiag_add", "add_mod", "additive_parity")),
    ("ROOT_VARSET_RENAMING_BREAK", ("varset_renaming_break", "renaming")),
    ("ROOT_AFFINE_MODULAR", ("affine", "modular")),
    ("ROOT_ONE_SIDED_BOUNDARY_BREAK", ("one_sided_boundary",)),
    ("ROOT_TWO_SIDED_BOUNDARY_BREAK", ("two_sided_boundary",)),
    ("ROOT_ANCHOR_EXPANSION", ("anchor_expansion",)),
    ("ROOT_SUBTRACTIVE_PARITY", ("subtractive_parity", "sub_mod", "rsub_mod")),
    ("ROOT_ORDER_LATTICE", ("order_lattice", "min", "max")),
    ("ROOT_ZERO_ABSORPTION", ("zero_absorption", "first_nonzero", "second_nonzero")),
]


def canonicalize_root_key(row: RootNode | dict[str, Any]) -> str:
    data = row.to_dict() if isinstance(row, RootNode) else dict(row)
    text = " ".join(
        str(data.get(key, ""))
        for key in ("canonical_name", "root_key", "table_motif", "algebra_shape")
    ).lower()
    for canonical, needles in ROOT_RULES:
        if any(needle in text for needle in needles):
            return canonical
    raw = "|".join(
        str(data.get(key, ""))
        for key in ("table_motif", "algebra_shape", "source_target_basin", "forced_transition")
    )
    return f"ROOT_UNKNOWN_{hashlib.sha256(raw.encode()).hexdigest()[:8]}"


def root_alias_signature(row: RootNode | dict[str, Any]) -> str:
    data = row.to_dict() if isinstance(row, RootNode) else dict(row)
    return "|".join(
        str(data.get(key, ""))
        for key in ("canonical_name", "root_key", "table_motif", "algebra_shape")
    )


def consolidate_root_nodes(root_rows: Iterable[RootNode | dict[str, Any]]) -> list[RootNode]:
    groups: dict[str, list[RootNode]] = defaultdict(list)
    for row in root_rows:
        node = row if isinstance(row, RootNode) else RootNode.from_dict(row)
        groups[canonicalize_root_key(node)].append(node)
    return [score_canonical_root(group, canonical) for canonical, group in sorted(groups.items())]


def score_canonical_root(group: list[RootNode], canonical_name: str | None = None) -> RootNode:
    if not group:
        raise ValueError("Cannot score empty root group")
    canonical = canonical_name or canonicalize_root_key(group[0])
    total_rows = sum(node.rows or node.support_count for node in group)
    unique_pairs = _sum_unique(group, "unique_pairs")
    unique_sources = _sum_unique(group, "unique_sources")
    unique_targets = _sum_unique(group, "unique_targets")
    unique_tables = max((node.unique_tables for node in group), default=0)
    unique_motifs = max((node.unique_motifs for node in group), default=0)
    max_load = max((node.load_bearing_score for node in group), default=0.0)
    reason_support = sum(int(node.evidence.get("reason_support_count", 0)) for node in group)
    obstruction_pressure = sum(int(node.evidence.get("obstruction_pressure_count", 0)) for node in group)
    canonical_score = (
        math.log1p(unique_pairs)
        + math.log1p(unique_sources)
        + math.log1p(unique_targets)
        + 0.5 * math.log1p(unique_motifs)
        + 0.25 * reason_support
        + 0.25 * obstruction_pressure
        + max_load / 10.0
    )
    evidence = {
        "source_root_ids": [node.root_node_id for node in group],
        "canonical_root_score": canonical_score,
        "formula": "log1p(pairs)+log1p(sources)+log1p(targets)+0.5*log1p(motifs)+0.25*reasons+0.25*obstructions+max_load/10",
        "reason_support_count": reason_support,
        "obstruction_pressure_count": obstruction_pressure,
    }
    aliases = [
        {
            "alias": node.canonical_name,
            "root_node_id": node.root_node_id,
            "signature": root_alias_signature(node),
        }
        for node in group
    ]
    return RootNode(
        root_node_id=content_id("canonical_root", {"canonical_name": canonical, "aliases": aliases}),
        canonical_name=canonical,
        root_type="canonical_root",
        root_key=canonical,
        root_key_fields={"canonicalized_from": [node.root_key for node in group]},
        table_motif=group[0].table_motif,
        algebra_shape=group[0].algebra_shape,
        source_target_basin=group[0].source_target_basin,
        forced_transition=group[0].forced_transition,
        support_count=total_rows,
        rows=total_rows,
        unique_pairs=unique_pairs,
        unique_sources=unique_sources,
        unique_targets=unique_targets,
        unique_tables=unique_tables,
        unique_motifs=unique_motifs,
        load_bearing_score=max_load,
        compression_ratio=(total_rows / max(len(group), 1)),
        coverage_density=(unique_pairs / max(total_rows, 1)),
        status="canonical_candidate",
        evidence=evidence,
        aliases=aliases,
        created_from_run_id="root_consolidation_v1",
    )


def build_root_alias_map(grouped_roots: Iterable[RootNode]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for root in grouped_roots:
        mapping[root.root_node_id] = root.canonical_name
        mapping[root.canonical_name] = root.canonical_name
        for alias in root.aliases:
            if isinstance(alias, dict):
                mapping[str(alias.get("alias"))] = root.canonical_name
                if alias.get("root_node_id"):
                    mapping[str(alias["root_node_id"])] = root.canonical_name
    return mapping


def link_roots_to_reasons(
    roots: Iterable[RootNode], reasons: Iterable[ReasonNode | dict[str, Any]]
) -> list[RootReasonLink]:
    root_list = list(roots)
    reason_list = [r if isinstance(r, ReasonNode) else ReasonNode.from_dict(r) for r in reasons]
    links: list[RootReasonLink] = []
    for root in root_list:
        for reason in reason_list:
            if _shares_motif_or_transition(root.to_dict(), reason.to_dict()):
                links.append(
                    RootReasonLink(
                        root_node_id=root.root_node_id,
                        reason_node_id=reason.reason_node_id,
                        support_count=reason.support_count or reason.rows,
                        evidence={"advisory_only": True},
                    )
                )
    return links


def link_roots_to_obstructions(
    roots: Iterable[RootNode], obstructions: Iterable[ObstructionNode | dict[str, Any]]
) -> list[RootObstructionLink]:
    root_list = list(roots)
    obstruction_list = [
        o if isinstance(o, ObstructionNode) else ObstructionNode.from_dict(o) for o in obstructions
    ]
    links: list[RootObstructionLink] = []
    for root in root_list:
        for obstruction in obstruction_list:
            if _shares_motif_or_transition(root.to_dict(), obstruction.to_dict()):
                links.append(
                    RootObstructionLink(
                        root_node_id=root.root_node_id,
                        obstruction_id=obstruction.obstruction_id,
                        pressure_score=obstruction.obstruction_pressure_score,
                        evidence={"advisory_only": True},
                    )
                )
    return links


def _shares_motif_or_transition(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in ("table_motif", "forced_transition"):
        if left.get(key) and left.get(key) == right.get(key):
            return True
    return False


def _sum_unique(group: list[RootNode], attr: str) -> int:
    return sum(getattr(node, attr) for node in group)

"""Advisory constructor-route policies for ETP compounding."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Sequence

from mathgraph.finite_magma import FiniteMagma
from mathgraph.polarized_quotient_ir import build_pair_features
from mathgraph.sat_cache import compute_constructor_bandwidth


@dataclass(frozen=True)
class ConstructorPolicy:
    policy_name: str
    selected_constructor_indices: tuple[int, ...]
    advisory_only: bool = True
    can_promote_truth: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "selected_constructor_indices": list(self.selected_constructor_indices),
            "constructor_count": len(self.selected_constructor_indices),
            "advisory_only": True,
            "can_promote_truth": False,
            "metadata": dict(self.metadata),
        }


def build_policy_routes(
    constructors: Sequence[FiniteMagma],
    equations: Sequence[str],
    train_false_pairs: Sequence[tuple[int, int]],
    sat_cache: Any,
    route_size: int = 24,
    seed: int = 1729,
    residual_pairs: Sequence[tuple[int, int]] | None = None,
) -> list[ConstructorPolicy]:
    """Build deterministic advisory routes.

    Routes are scheduling objects only. They are never terminal evidence.
    """

    n = len(constructors)
    size = max(1, min(int(route_size), n))
    bandwidth_rows = compute_constructor_bandwidth(train_false_pairs, sat_cache)
    bandwidth_order = [int(row["constructor_index"]) for row in bandwidth_rows]
    feature_families = _recommended_families(equations, train_false_pairs)
    family_order = _order_by_family(constructors, feature_families)
    rng = random.Random(seed)
    shuffled = list(range(n))
    rng.shuffle(shuffled)
    routes = [
        ConstructorPolicy("generic", tuple(range(size)), metadata={"route_kind": "baseline"}),
        ConstructorPolicy("bandwidth", tuple(bandwidth_order[:size]), metadata={"route_kind": "train_bandwidth"}),
        ConstructorPolicy("family", tuple(family_order[:size]), metadata={"route_kind": "pqir_family", "recommended_families": feature_families}),
        ConstructorPolicy("root", tuple(_interleave([bandwidth_order, list(range(n))])[:size]), metadata={"route_kind": "root_baseline_mix"}),
        ConstructorPolicy("quotient", tuple(_prefer_names(constructors, ("quotient", "fresh", "projection"))[:size]), metadata={"route_kind": "quotient_pressure"}),
        ConstructorPolicy("goi", tuple(_prefer_names(constructors, ("tail", "head", "diagonal"))[:size]), metadata={"route_kind": "continuation_proxy"}),
        ConstructorPolicy("hybrid", tuple(_interleave([family_order, bandwidth_order, list(range(n))])[:size]), metadata={"route_kind": "family_bandwidth_mix"}),
        ConstructorPolicy("shuffled_control", tuple(shuffled[:size]), metadata={"route_kind": "null_control", "seed": seed}),
    ]
    if residual_pairs is not None:
        residual_order = [int(row["constructor_index"]) for row in compute_constructor_bandwidth(residual_pairs, sat_cache)]
        routes.append(ConstructorPolicy("residual_repair", tuple(_interleave([residual_order, bandwidth_order, family_order])[:size]), metadata={"route_kind": "residual_repair"}))
    routes.append(ConstructorPolicy("oracle_reference", tuple(bandwidth_order[: min(n, max(size, len(bandwidth_order)))]), metadata={"route_kind": "reference_not_truth"}))
    return [_dedupe_route(route) for route in routes]


def build_residual_repair_policy(
    constructors: Sequence[FiniteMagma],
    residual_pairs: Sequence[tuple[int, int]],
    sat_cache: Any,
    existing_indices: Sequence[int],
    new_count: int = 10,
) -> ConstructorPolicy:
    rows = compute_constructor_bandwidth(residual_pairs, sat_cache)
    existing = list(dict.fromkeys(int(i) for i in existing_indices))
    additions = [int(row["constructor_index"]) for row in rows if int(row["constructor_index"]) not in set(existing)]
    selected = existing + additions[: max(0, int(new_count))]
    return ConstructorPolicy("residual_repair", tuple(selected), metadata={"route_kind": "residual_repair", "new_count": new_count})


def _recommended_families(equations: Sequence[str], pairs: Sequence[tuple[int, int]]) -> list[str]:
    counts: dict[str, int] = {}
    for source_idx, target_idx in list(pairs)[:250]:
        try:
            row = build_pair_features(equations[int(source_idx)], equations[int(target_idx)])
        except Exception:
            continue
        for family in row.get("recommended_families", []) or []:
            counts[str(family)] = counts.get(str(family), 0) + 1
    return [family for family, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _order_by_family(constructors: Sequence[FiniteMagma], families: Sequence[str]) -> list[int]:
    priority = {family: i for i, family in enumerate(families)}
    return sorted(range(len(constructors)), key=lambda idx: (priority.get(constructors[idx].family, len(priority) + 1), idx))


def _prefer_names(constructors: Sequence[FiniteMagma], needles: Sequence[str]) -> list[int]:
    return sorted(
        range(len(constructors)),
        key=lambda idx: (
            0 if any(needle in constructors[idx].family or needle in constructors[idx].name for needle in needles) else 1,
            idx,
        ),
    )


def _interleave(sequences: Sequence[Sequence[int]]) -> list[int]:
    out: list[int] = []
    max_len = max((len(seq) for seq in sequences), default=0)
    for i in range(max_len):
        for seq in sequences:
            if i < len(seq):
                out.append(int(seq[i]))
    return list(dict.fromkeys(out))


def _dedupe_route(route: ConstructorPolicy) -> ConstructorPolicy:
    return ConstructorPolicy(route.policy_name, tuple(dict.fromkeys(route.selected_constructor_indices)), metadata=dict(route.metadata))

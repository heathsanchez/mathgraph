"""Compact residual-mined route atlas utilities.

The compact atlas is advisory memory.  It ranks residual-mined constructors for
route selection, compares them against same-size controls, and records
attribution.  It never promotes TRUE/FALSE claims or terminal forms.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class CompactAtlasEntry:
    constructor_id: str
    constructor_hash: str = ""
    source: str = ""
    carrier_size: int = 0
    generation: int = 0
    parent_basin: str = ""
    load_bearing_score: float = 0.0
    unique_new_hits_vs_generic: int = 0
    first_hit_count: int = 0
    basin_count: int = 0
    advisory_only: bool = True
    can_promote_truth: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "constructor_id": self.constructor_id,
            "constructor_hash": self.constructor_hash,
            "source": self.source,
            "carrier_size": self.carrier_size,
            "generation": self.generation,
            "parent_basin": self.parent_basin,
            "load_bearing_score": self.load_bearing_score,
            "unique_new_hits_vs_generic": self.unique_new_hits_vs_generic,
            "first_hit_count": self.first_hit_count,
            "basin_count": self.basin_count,
            "advisory_only": True,
            "can_promote_truth": False,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RouteAttribution:
    seed: int
    split: str
    route: str
    constructor_id: str
    unique_new_hits_vs_generic: int
    first_hit_count: int
    basin_count: int
    load_bearing_score: float
    top_basins: tuple[str, ...] = ()
    advisory_only: bool = True
    can_promote_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "split": self.split,
            "route": self.route,
            "constructor_id": self.constructor_id,
            "unique_new_hits_vs_generic": self.unique_new_hits_vs_generic,
            "first_hit_count": self.first_hit_count,
            "basin_count": self.basin_count,
            "load_bearing_score": self.load_bearing_score,
            "top_basins": "|".join(self.top_basins),
            "advisory_only": True,
            "can_promote_truth": False,
        }


def select_compact_atlas(
    entries: Sequence[CompactAtlasEntry | Mapping[str, Any]],
    *,
    top_k: int = 32,
    generation_min: int = 1,
    load_bearing_min_unique_hits: int = 1,
) -> list[CompactAtlasEntry]:
    """Select load-bearing residual-mined constructors.

    Selection mirrors the Colab compact atlas: prefer mined constructors
    (generation >= 1), require at least one unique hit by default, then sort by
    load-bearing score, unique hits, and first-hit count.
    """

    normalized = [_entry(e) for e in entries]
    filtered = [
        e
        for e in normalized
        if e.generation >= generation_min
        and e.unique_new_hits_vs_generic >= load_bearing_min_unique_hits
        and e.advisory_only
        and not e.can_promote_truth
    ]
    filtered.sort(
        key=lambda e: (
            -float(e.load_bearing_score),
            -int(e.unique_new_hits_vs_generic),
            -int(e.first_hit_count),
            e.constructor_id,
        )
    )
    return filtered[: max(0, int(top_k))]


def compare_random_controls(
    compact_recoveries: Sequence[float],
    random_control_recoveries: Sequence[float],
) -> dict[str, float | bool]:
    compact_mean = _mean(compact_recoveries)
    control_mean = _mean(random_control_recoveries)
    return {
        "compact_mean_recoveries": compact_mean,
        "random_control_mean_recoveries": control_mean,
        "compact_gain_vs_random_same_size": compact_mean - control_mean,
        "passed": compact_mean > control_mean,
    }


def compare_shuffled_controls(
    compact_recoveries: Sequence[float],
    shuffled_control_recoveries: Sequence[float],
) -> dict[str, float | bool]:
    compact_mean = _mean(compact_recoveries)
    control_mean = _mean(shuffled_control_recoveries)
    return {
        "compact_mean_recoveries": compact_mean,
        "shuffled_control_mean_recoveries": control_mean,
        "compact_gain_vs_shuffled_atlas_same_size": compact_mean - control_mean,
        "passed": compact_mean > control_mean,
    }


def make_same_size_random_control(
    constructor_ids: Sequence[str],
    *,
    compact_size: int,
    seed: int,
    excluded_constructor_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    excluded = set(excluded_constructor_ids)
    pool = [str(x) for x in constructor_ids if str(x) not in excluded]
    rng = random.Random(int(seed))
    rng.shuffle(pool)
    return tuple(pool[: max(0, int(compact_size))])


def make_shuffled_atlas_control(
    atlas_constructor_ids: Sequence[str],
    *,
    compact_size: int,
    seed: int,
) -> tuple[str, ...]:
    pool = [str(x) for x in atlas_constructor_ids]
    rng = random.Random(int(seed))
    rng.shuffle(pool)
    return tuple(pool[: max(0, int(compact_size))])


def _entry(value: CompactAtlasEntry | Mapping[str, Any]) -> CompactAtlasEntry:
    if isinstance(value, CompactAtlasEntry):
        return value
    cid = str(value.get("constructor_id", value.get("constructor_idx", "")))
    return CompactAtlasEntry(
        constructor_id=cid,
        constructor_hash=str(value.get("constructor_hash", "")),
        source=str(value.get("source", "")),
        carrier_size=int(value.get("carrier_size", value.get("n", 0)) or 0),
        generation=int(value.get("generation", 0) or 0),
        parent_basin=str(value.get("parent_basin", "")),
        load_bearing_score=float(value.get("load_bearing_score", 0.0) or 0.0),
        unique_new_hits_vs_generic=int(value.get("unique_new_hits_vs_generic", 0) or 0),
        first_hit_count=int(value.get("first_hit_count", 0) or 0),
        basin_count=int(value.get("basin_count", 0) or 0),
        advisory_only=bool(value.get("advisory_only", True)),
        can_promote_truth=bool(value.get("can_promote_truth", False)),
        metadata=dict(value.get("metadata", {}) or {}),
    )


def _mean(xs: Sequence[float]) -> float:
    vals = [float(x) for x in xs]
    return sum(vals) / len(vals) if vals else 0.0

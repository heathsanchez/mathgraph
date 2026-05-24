"""Satisfaction cache for finite magma constructor banks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from mathgraph.finite_magma import FiniteMagma, equation_holds


@dataclass(frozen=True)
class SatCache:
    constructors: tuple[FiniteMagma, ...]
    equations: tuple[str, ...]
    sat: Any

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.constructors), len(self.equations))

    def to_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for ci, magma in enumerate(self.constructors):
            for ei, equation in enumerate(self.equations):
                rows.append(
                    {
                        "constructor_index": ci,
                        "constructor_id": magma.cid,
                        "constructor_family": magma.family,
                        "equation_index": ei,
                        "equation": equation,
                        "satisfied": bool(self.sat[ci][ei]),
                    }
                )
        return rows


def build_sat_cache(constructors: Sequence[FiniteMagma], equations: Sequence[str]) -> SatCache:
    import numpy as np

    rows: list[list[bool]] = []
    for magma in constructors:
        rows.append([_safe_holds(equation, magma) for equation in equations])
    return SatCache(tuple(constructors), tuple(str(eq) for eq in equations), np.asarray(rows, dtype=bool))


def save_sat_cache(cache: SatCache, path: str | Path) -> None:
    import numpy as np

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, cache.sat)


def load_sat_matrix(path: str | Path) -> Any:
    import numpy as np

    return np.load(Path(path), allow_pickle=False)


def save_sat_cache_csv(cache: SatCache, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["constructor_index", "constructor_id", "constructor_family", "equation_index", "equation", "satisfied"])
        writer.writeheader()
        writer.writerows(cache.to_rows())


def route_recoveries(false_pairs: Iterable[tuple[int, int]], sat: Any, constructor_indices: Sequence[int]) -> list[bool]:
    import numpy as np

    pairs = list(false_pairs)
    if not pairs or not constructor_indices:
        return [False for _ in pairs]
    src = np.asarray([int(i) for i, _ in pairs], dtype=int)
    tgt = np.asarray([int(j) for _, j in pairs], dtype=int)
    route = np.asarray([int(i) for i in constructor_indices], dtype=int)
    hits = sat[route][:, src] & ~sat[route][:, tgt]
    return [bool(v) for v in hits.any(axis=0)]


def evaluate_route(false_pairs: Iterable[tuple[int, int]], true_pairs: Iterable[tuple[int, int]], sat: Any, constructor_indices: Sequence[int]) -> dict[str, Any]:
    false_list = list(false_pairs)
    true_list = list(true_pairs)
    recovered = route_recoveries(false_list, sat, constructor_indices)
    contaminated = route_recoveries(true_list, sat, constructor_indices)
    solved = sum(1 for x in recovered if x)
    true_bad = sum(1 for x in contaminated if x)
    return {
        "attempted_pairs": len(false_list),
        "solved_or_refuted": solved,
        "certificate_yield": solved,
        "yield_rate": solved / len(false_list) if false_list else 0.0,
        "residual_count": len(false_list) - solved,
        "attempts_used": len(false_list) * len(constructor_indices),
        "true_contamination_count": true_bad,
        "true_contamination_rate": true_bad / len(true_list) if true_list else 0.0,
    }


def residual_pairs(false_pairs: Sequence[tuple[int, int]], sat: Any, constructor_indices: Sequence[int]) -> list[tuple[int, int]]:
    hits = route_recoveries(false_pairs, sat, constructor_indices)
    return [pair for pair, recovered in zip(false_pairs, hits) if not recovered]


def compute_constructor_bandwidth(eval_false_pairs: Iterable[tuple[int, int]], sat_cache: SatCache) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pairs = list(eval_false_pairs)
    for idx, magma in enumerate(sat_cache.constructors):
        recovered = route_recoveries(pairs, sat_cache.sat, [idx])
        count = sum(1 for value in recovered if value)
        rows.append(
            {
                "constructor_index": idx,
                "constructor_id": magma.cid,
                "constructor_family": magma.family,
                "recoveries": count,
                "bandwidth": count / len(pairs) if pairs else 0.0,
            }
        )
    return sorted(rows, key=lambda row: (-int(row["recoveries"]), str(row["constructor_family"]), int(row["constructor_index"])))


def true_contamination_count(true_pairs: Iterable[tuple[int, int]], sat: Any, constructor_indices: Sequence[int]) -> int:
    return sum(1 for value in route_recoveries(list(true_pairs), sat, constructor_indices) if value)


def _safe_holds(equation: str, magma: FiniteMagma) -> bool:
    try:
        return equation_holds(equation, magma)
    except Exception:
        return False

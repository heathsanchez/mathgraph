"""Deterministic finite magma constructor families for ETP compounding."""

from __future__ import annotations

import random
from typing import Iterable

from mathgraph.constructor_families import normalize_family_name
from mathgraph.finite_magma import FiniteMagma


def build_base_constructor_bank(max_n: int = 5, seed: int = 1729) -> list[FiniteMagma]:
    """Return a deterministic, small-but-diverse magma constructor bank."""

    magmas: list[FiniteMagma] = []
    for n in range(2, max(2, int(max_n)) + 1):
        magmas.extend(_constant_magmas(n))
        magmas.extend([_left_projection(n), _right_projection(n)])
        magmas.extend([_add_mod(n), _sub_mod(n), _linear_combo_mod(n, 1, 2)])
        if n == 2 or (n & (n - 1) == 0):
            magmas.append(_xor_mod(n))
        magmas.extend(
            [
                _diagonal_spike(n),
                _projection_exception_left(n),
                _projection_exception_right(n),
                _quotient_fresh_gate(n),
                _random_fresh_sink(n, seed + n),
                _random_fresh_collapse(n, seed + 17 * n),
                _idempotent_random(n, seed + 29 * n),
                _head_coupled_projection(n),
                _tail_coupled_projection(n),
            ]
        )
    magmas.extend(build_random_constructor_bank(max_n=max_n, count_per_n=2, seed=seed))
    return dedupe_constructors(magmas)


def build_random_constructor_bank(max_n: int = 5, count_per_n: int = 3, seed: int = 1729) -> list[FiniteMagma]:
    out: list[FiniteMagma] = []
    for n in range(2, max(2, int(max_n)) + 1):
        for k in range(max(0, int(count_per_n))):
            rng = random.Random(seed + 1009 * n + k)
            table = tuple(tuple(rng.randrange(n) for _ in range(n)) for _ in range(n))
            out.append(FiniteMagma(table, "random_seeded", f"random_seeded_n{n}_{k}", source="seeded_random"))
    return out


def dedupe_constructors(constructors: Iterable[FiniteMagma]) -> list[FiniteMagma]:
    seen: set[str] = set()
    out: list[FiniteMagma] = []
    for magma in constructors:
        key = f"{magma.n}:{magma.table_hash}"
        if key in seen:
            continue
        seen.add(key)
        out.append(magma)
    return out


def _magma(table: list[list[int]], family: str, name: str, **metadata: object) -> FiniteMagma:
    family = normalize_family_name(family) if family != "random_seeded" else family
    return FiniteMagma(tuple(tuple(row) for row in table), family, name, metadata=dict(metadata))


def _constant_magmas(n: int) -> list[FiniteMagma]:
    return [_magma([[c for _ in range(n)] for _ in range(n)], "constant", f"constant_n{n}_{c}", constant=c) for c in range(n)]


def _left_projection(n: int) -> FiniteMagma:
    return _magma([[i for _ in range(n)] for i in range(n)], "left_projection", f"left_projection_n{n}")


def _right_projection(n: int) -> FiniteMagma:
    return _magma([[j for j in range(n)] for _ in range(n)], "right_projection", f"right_projection_n{n}")


def _add_mod(n: int) -> FiniteMagma:
    return _magma([[(i + j) % n for j in range(n)] for i in range(n)], "add_mod", f"add_mod_n{n}")


def _sub_mod(n: int) -> FiniteMagma:
    return _magma([[(i - j) % n for j in range(n)] for i in range(n)], "sub_mod", f"sub_mod_n{n}")


def _xor_mod(n: int) -> FiniteMagma:
    return _magma([[(i ^ j) % n for j in range(n)] for i in range(n)], "xor_mod", f"xor_mod_n{n}")


def _linear_combo_mod(n: int, a: int, b: int) -> FiniteMagma:
    return _magma([[(a * i + b * j) % n for j in range(n)] for i in range(n)], "linear_combo_mod", f"linear_combo_{a}_{b}_n{n}")


def _diagonal_spike(n: int) -> FiniteMagma:
    table = [[i if i == j else 0 for j in range(n)] for i in range(n)]
    return _magma(table, "diagonal_spike", f"diagonal_spike_n{n}")


def _projection_exception_left(n: int) -> FiniteMagma:
    table = [[i for _ in range(n)] for i in range(n)]
    if n >= 2:
        table[n - 1][n - 1] = 0
    return _magma(table, "projection_exception_left", f"projection_exception_left_n{n}")


def _projection_exception_right(n: int) -> FiniteMagma:
    table = [[j for j in range(n)] for _ in range(n)]
    if n >= 2:
        table[n - 1][n - 1] = 0
    return _magma(table, "projection_exception_right", f"projection_exception_right_n{n}")


def _quotient_fresh_gate(n: int) -> FiniteMagma:
    fresh = n - 1
    table = [[fresh if i == fresh or j == fresh else i for j in range(n)] for i in range(n)]
    return _magma(table, "quotient_fresh_gate", f"quotient_fresh_gate_n{n}")


def _random_fresh_sink(n: int, seed: int) -> FiniteMagma:
    rng = random.Random(seed)
    fresh = n - 1
    table = [[fresh if i == fresh or j == fresh else rng.randrange(n) for j in range(n)] for i in range(n)]
    return _magma(table, "random_fresh_sink", f"random_fresh_sink_n{n}")


def _random_fresh_collapse(n: int, seed: int) -> FiniteMagma:
    rng = random.Random(seed)
    table = [[0 if i == n - 1 or j == n - 1 else rng.randrange(n) for j in range(n)] for i in range(n)]
    return _magma(table, "random_fresh_collapse", f"random_fresh_collapse_n{n}")


def _idempotent_random(n: int, seed: int) -> FiniteMagma:
    rng = random.Random(seed)
    table = [[i if i == j else rng.randrange(n) for j in range(n)] for i in range(n)]
    return _magma(table, "idempotent_random", f"idempotent_random_n{n}")


def _head_coupled_projection(n: int) -> FiniteMagma:
    table = [[i if i <= j else j for j in range(n)] for i in range(n)]
    return _magma(table, "head_coupled_projection", f"head_coupled_projection_n{n}")


def _tail_coupled_projection(n: int) -> FiniteMagma:
    table = [[j if i <= j else i for j in range(n)] for i in range(n)]
    return _magma(table, "tail_coupled_projection", f"tail_coupled_projection_n{n}")

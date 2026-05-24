"""Finite magma representation and checked equation implication certificates."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from mathgraph.etp_terms import ETPEquation, ETPTerm, parse_equation, parse_term
from mathgraph.hashing import content_id, sha256_hex


@dataclass(frozen=True)
class FiniteCountermodelCertificate:
    eq1: str
    eq2: str
    eq1_holds: bool
    eq2_violated: bool
    witness_env: dict[str, int]
    table: tuple[tuple[int, ...], ...]
    cid: str
    certificate_status: str
    advisory_only: bool = False
    can_promote_truth: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "eq1": self.eq1,
            "eq2": self.eq2,
            "eq1_holds": self.eq1_holds,
            "eq2_violated": self.eq2_violated,
            "witness_env": dict(self.witness_env),
            "table": [list(row) for row in self.table],
            "cid": self.cid,
            "certificate_status": self.certificate_status,
            "advisory_only": self.advisory_only,
            "can_promote_truth": self.can_promote_truth,
        }


@dataclass(frozen=True)
class FiniteMagma:
    table: tuple[tuple[int, ...], ...]
    family: str
    name: str
    cid: str = ""
    source: str = "constructor_bank"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        table = normalize_table(self.table)
        object.__setattr__(self, "table", table)
        object.__setattr__(self, "cid", self.cid or content_id("finite-magma", {"family": self.family, "name": self.name, "table": table_hash(table)}))

    @property
    def n(self) -> int:
        return len(self.table)

    @property
    def table_hash(self) -> str:
        return table_hash(self.table)

    def evaluate_term(self, term: ETPTerm | str, assignment: dict[str, int]) -> int:
        t = parse_term(term) if isinstance(term, str) else term
        return evaluate_term(t, self, assignment)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cid": self.cid,
            "name": self.name,
            "family": self.family,
            "n": self.n,
            "source": self.source,
            "table_hash": self.table_hash,
            "table": [list(row) for row in self.table],
            "metadata": dict(self.metadata),
        }


def normalize_table(table: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    rows = tuple(tuple(int(x) for x in row) for row in table)
    if not rows or any(len(row) != len(rows) for row in rows):
        raise ValueError("finite magma table must be nonempty and square")
    n = len(rows)
    if any(x < 0 or x >= n for row in rows for x in row):
        raise ValueError("table entries must lie in carrier range")
    return rows


def table_hash(table: Sequence[Sequence[int]]) -> str:
    return sha256_hex([list(row) for row in normalize_table(table)])


def evaluate_term(term: ETPTerm, magma: FiniteMagma, assignment: dict[str, int]) -> int:
    if term.var is not None:
        return int(assignment[term.var])
    assert term.left is not None and term.right is not None
    left = evaluate_term(term.left, magma, assignment)
    right = evaluate_term(term.right, magma, assignment)
    return magma.table[left][right]


def equation_holds(equation: ETPEquation | str, magma: FiniteMagma) -> bool:
    eq = parse_equation(equation) if isinstance(equation, str) else equation
    return all(_equation_holds_at(eq, magma, env) for env in _assignments(eq.variables(), magma.n))


def equation_violated_with_witness(equation: ETPEquation | str, magma: FiniteMagma) -> dict[str, int] | None:
    eq = parse_equation(equation) if isinstance(equation, str) else equation
    for env in _assignments(eq.variables(), magma.n):
        if not _equation_holds_at(eq, magma, env):
            return env
    return None


def implication_false_certificate(eq1: ETPEquation | str, eq2: ETPEquation | str, magma: FiniteMagma) -> FiniteCountermodelCertificate:
    source = parse_equation(eq1) if isinstance(eq1, str) else eq1
    target = parse_equation(eq2) if isinstance(eq2, str) else eq2
    eq1_ok = equation_holds(source, magma)
    witness = equation_violated_with_witness(target, magma) if eq1_ok else None
    valid = bool(eq1_ok and witness is not None)
    return FiniteCountermodelCertificate(
        eq1=source.normalized or source.canonical(),
        eq2=target.normalized or target.canonical(),
        eq1_holds=eq1_ok,
        eq2_violated=witness is not None,
        witness_env=dict(witness or {}),
        table=magma.table,
        cid=magma.cid,
        certificate_status="finite_countermodel_found" if valid else "not_a_countermodel",
        advisory_only=not valid,
        can_promote_truth=valid,
    )


def _equation_holds_at(eq: ETPEquation, magma: FiniteMagma, env: dict[str, int]) -> bool:
    return evaluate_term(eq.lhs, magma, env) == evaluate_term(eq.rhs, magma, env)


def _assignments(variables: Iterable[str], n: int) -> Iterable[dict[str, int]]:
    vars_ = tuple(sorted(set(variables)))
    for values in itertools.product(range(n), repeat=len(vars_)):
        yield dict(zip(vars_, values))

"""Small deterministic finite magma world for executable implication checks."""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class Term:
    name: str | None = None
    left: "Term | None" = None
    right: "Term | None" = None

    def is_var(self) -> bool:
        return self.name is not None

    def variables(self) -> tuple[str, ...]:
        if self.name is not None:
            return (self.name,)
        assert self.left is not None and self.right is not None
        return tuple(sorted(set(self.left.variables()) | set(self.right.variables())))

    def to_string(self) -> str:
        if self.name is not None:
            return self.name
        assert self.left is not None and self.right is not None
        return f"({self.left.to_string()} * {self.right.to_string()})"


@dataclass(frozen=True)
class Equation:
    lhs: Term
    rhs: Term
    raw: str = ""

    def variables(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.lhs.variables()) | set(self.rhs.variables())))

    def to_string(self) -> str:
        return self.raw or f"{self.lhs.to_string()} = {self.rhs.to_string()}"


@dataclass(frozen=True)
class FiniteCountermodelResult:
    source_equation: str
    target_equation: str
    table: tuple[tuple[int, ...], ...]
    satisfies_source: bool
    violates_target: bool
    witness_env: dict[str, int] = field(default_factory=dict)
    terminal_candidate_ok: bool = False
    diagnostic: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_equation": self.source_equation,
            "target_equation": self.target_equation,
            "table": [list(row) for row in self.table],
            "carrier_size": len(self.table),
            "satisfies_source": self.satisfies_source,
            "violates_target": self.violates_target,
            "witness_env": dict(self.witness_env),
            "terminal_candidate_ok": self.terminal_candidate_ok,
            "diagnostic": self.diagnostic,
        }


class TermParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def parse(self) -> Term:
        term = self._term()
        self._ws()
        if self.i != len(self.text):
            raise ValueError(f"unexpected input at {self.i}: {self.text[self.i:]}")
        return term

    def _term(self) -> Term:
        term = self._atom()
        self._ws()
        while self._peek() == "*":
            self.i += 1
            right = self._atom()
            term = Term(left=term, right=right)
            self._ws()
        return term

    def _atom(self) -> Term:
        self._ws()
        if self._peek() == "(":
            self.i += 1
            term = self._term()
            self._ws()
            if self._peek() != ")":
                raise ValueError(f"expected ')' at {self.i}")
            self.i += 1
            return term
        if self._peek().isalpha():
            start = self.i
            while self.i < len(self.text) and (self.text[self.i].isalnum() or self.text[self.i] == "_"):
                self.i += 1
            return Term(name=self.text[start : self.i])
        raise ValueError(f"expected term at {self.i}")

    def _ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1

    def _peek(self) -> str:
        return self.text[self.i] if self.i < len(self.text) else ""


def parse_term(text: str) -> Term:
    return TermParser(text).parse()


def parse_equation(text: str) -> Equation:
    if "=" not in text:
        raise ValueError("equation must contain '='")
    lhs, rhs = text.split("=", 1)
    return Equation(parse_term(lhs.strip()), parse_term(rhs.strip()), raw=" ".join(text.strip().split()))


def normalize_table(table: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    rows = tuple(tuple(int(x) for x in row) for row in table)
    if not rows or any(len(row) != len(rows) for row in rows):
        raise ValueError("finite magma table must be nonempty and square")
    n = len(rows)
    if any(x < 0 or x >= n for row in rows for x in row):
        raise ValueError("table entries must lie in carrier range")
    return rows


def eval_term(term: Term, table: Sequence[Sequence[int]], env: dict[str, int]) -> int:
    t = normalize_table(table)
    if term.name is not None:
        return int(env[term.name])
    assert term.left is not None and term.right is not None
    return t[eval_term(term.left, t, env)][eval_term(term.right, t, env)]


def equation_holds_at(equation: Equation, table: Sequence[Sequence[int]], env: dict[str, int]) -> bool:
    t = normalize_table(table)
    return eval_term(equation.lhs, t, env) == eval_term(equation.rhs, t, env)


def all_environments(variables: Iterable[str], n: int) -> Iterable[dict[str, int]]:
    vars_ = tuple(sorted(set(variables)))
    for values in itertools.product(range(n), repeat=len(vars_)):
        yield dict(zip(vars_, values))


def table_satisfies_equation(table: Sequence[Sequence[int]], equation: Equation | str) -> bool:
    eq = parse_equation(equation) if isinstance(equation, str) else equation
    t = normalize_table(table)
    return all(equation_holds_at(eq, t, env) for env in all_environments(eq.variables(), len(t)))


def find_violation(table: Sequence[Sequence[int]], equation: Equation | str) -> dict[str, int] | None:
    eq = parse_equation(equation) if isinstance(equation, str) else equation
    t = normalize_table(table)
    for env in all_environments(eq.variables(), len(t)):
        if not equation_holds_at(eq, t, env):
            return env
    return None


def table_violates_equation(table: Sequence[Sequence[int]], equation: Equation | str) -> bool:
    return find_violation(table, equation) is not None


def check_finite_countermodel(eq1: Equation | str, eq2: Equation | str, table: Sequence[Sequence[int]]) -> FiniteCountermodelResult:
    source = parse_equation(eq1) if isinstance(eq1, str) else eq1
    target = parse_equation(eq2) if isinstance(eq2, str) else eq2
    t = normalize_table(table)
    source_ok = table_satisfies_equation(t, source)
    witness = find_violation(t, target) if source_ok else None
    target_bad = witness is not None
    ok = bool(source_ok and target_bad)
    if ok:
        diagnostic = "valid finite countermodel: source holds globally and target fails at witness"
    elif not source_ok:
        diagnostic = "candidate table rejected: source equation does not hold globally"
    else:
        diagnostic = "candidate table rejected: target equation was not violated"
    return FiniteCountermodelResult(
        source_equation=source.to_string(),
        target_equation=target.to_string(),
        table=t,
        satisfies_source=source_ok,
        violates_target=target_bad,
        witness_env=dict(witness or {}),
        terminal_candidate_ok=ok,
        diagnostic=diagnostic,
    )


def left_projection(n: int = 2) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(i for _j in range(n)) for i in range(n))


def right_projection(n: int = 2) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(j for j in range(n)) for _i in range(n))


def constant_table(n: int = 2, c: int = 0) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(c for _j in range(n)) for _i in range(n))


def xor_mod_2() -> tuple[tuple[int, ...], ...]:
    return ((0, 1), (1, 0))


def add_mod_n(n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((i + j) % n for j in range(n)) for i in range(n))


def sub_mod_n(n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((i - j) % n for j in range(n)) for i in range(n))


def min_table(n: int = 3) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(min(i, j) for j in range(n)) for i in range(n))


def max_table(n: int = 3) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(max(i, j) for j in range(n)) for i in range(n))


def rectangular_band(n: int = 4) -> tuple[tuple[int, ...], ...]:
    if n != 4:
        raise ValueError("rectangular_band currently uses carrier size 4")
    return tuple(tuple(2 * (i // 2) + (j % 2) for j in range(4)) for i in range(4))


def commutative_nonassociative_3() -> tuple[tuple[int, ...], ...]:
    return (
        (0, 0, 1),
        (0, 1, 2),
        (1, 2, 0),
    )


def deterministic_perturbation_3() -> tuple[tuple[int, ...], ...]:
    return (
        (0, 1, 0),
        (2, 1, 2),
        (1, 0, 2),
    )


def table_json_hash_payload(table: Sequence[Sequence[int]]) -> str:
    return json.dumps([list(row) for row in normalize_table(table)], sort_keys=True)

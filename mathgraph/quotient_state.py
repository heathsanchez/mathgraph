"""Bounded symbolic quotient-state utilities for magma terms."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any, Iterable

from mathgraph.etp_terms import ETPTerm, parse_equation


class UnionFind:
    def __init__(self, items: Iterable[str] = ()) -> None:
        self.parent = {str(item): str(item) for item in items}
        self.reason: dict[tuple[str, str], str] = {}

    def add(self, x: str) -> None:
        self.parent.setdefault(x, x)

    def find(self, x: str) -> str:
        self.add(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str, reason: str = "") -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if rb < ra:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.reason[(ra, rb)] = reason
        return True


@dataclass(frozen=True)
class BoundedTermUniverse:
    variables: tuple[str, ...]
    max_depth: int
    terms: tuple[str, ...]

    @classmethod
    def build(cls, variables: Iterable[str], max_depth: int = 2) -> "BoundedTermUniverse":
        vars_ = tuple(sorted(set(variables))) or ("x",)
        by_depth: list[set[str]] = [set(vars_)]
        all_terms = set(vars_)
        for depth in range(1, max_depth + 1):
            current: set[str] = set()
            for left_depth in range(depth):
                right_depth = depth - 1
                for l, r in product(by_depth[left_depth], by_depth[right_depth]):
                    current.add(f"({l} * {r})")
            by_depth.append(current)
            all_terms |= current
        return cls(vars_, max_depth, tuple(sorted(all_terms)))


@dataclass
class CongruenceClosure:
    universe: BoundedTermUniverse
    uf: UnionFind = field(init=False)
    explanations: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.uf = UnionFind(self.universe.terms)

    def add_equation(self, lhs: ETPTerm | str, rhs: ETPTerm | str, reason: str = "source_equation") -> None:
        l = lhs.to_string() if isinstance(lhs, ETPTerm) else str(lhs)
        r = rhs.to_string() if isinstance(rhs, ETPTerm) else str(rhs)
        if self.uf.union(l, r, reason):
            self.explanations.append({"lhs": l, "rhs": r, "reason": reason})
            self.close_under_congruence()

    def close_under_congruence(self) -> None:
        changed = True
        while changed:
            changed = False
            for a in self.universe.terms:
                parsed_a = _split_binary(a)
                if not parsed_a:
                    continue
                al, ar = parsed_a
                for b in self.universe.terms:
                    parsed_b = _split_binary(b)
                    if not parsed_b:
                        continue
                    bl, br = parsed_b
                    if self.uf.find(al) == self.uf.find(bl) and self.uf.find(ar) == self.uf.find(br):
                        if self.uf.union(a, b, "congruence"):
                            self.explanations.append({"lhs": a, "rhs": b, "reason": "congruence", "from": [al, ar, bl, br]})
                            changed = True

    def are_equal(self, lhs: ETPTerm | str, rhs: ETPTerm | str) -> bool:
        l = lhs.to_string() if isinstance(lhs, ETPTerm) else str(lhs)
        r = rhs.to_string() if isinstance(rhs, ETPTerm) else str(rhs)
        return self.uf.find(l) == self.uf.find(r)

    def explain(self, lhs: ETPTerm | str, rhs: ETPTerm | str) -> dict[str, Any]:
        l = lhs.to_string() if isinstance(lhs, ETPTerm) else str(lhs)
        r = rhs.to_string() if isinstance(rhs, ETPTerm) else str(rhs)
        return {"lhs": l, "rhs": r, "equal": self.are_equal(l, r), "trace": list(self.explanations[-20:]), "advisory_only": True}


def closure_from_equation(equation_text: str, max_depth: int = 2) -> CongruenceClosure:
    eq = parse_equation(equation_text)
    universe = BoundedTermUniverse.build(eq.variables(), max_depth=max_depth)
    closure = CongruenceClosure(universe)
    closure.add_equation(eq.lhs, eq.rhs, reason="source_equation")
    return closure


def _split_binary(text: str) -> tuple[str, str] | None:
    s = text.strip()
    if not (s.startswith("(") and s.endswith(")")):
        return None
    inner = s[1:-1]
    depth = 0
    for i, ch in enumerate(inner):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "*" and depth == 0:
            return inner[:i].strip(), inner[i + 1 :].strip()
    return None

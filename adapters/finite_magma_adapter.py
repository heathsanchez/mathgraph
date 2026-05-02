"""Finite magma adapter for small equational checks."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Sequence

from mathgraph.equations import Equation


@dataclass(frozen=True)
class FiniteMagma:
    """A finite magma represented by a square Cayley table of integers."""

    table: tuple[tuple[int, ...], ...]
    name: str = "finite_magma"

    @classmethod
    def from_table(cls, table: Sequence[Sequence[int]], name: str = "finite_magma") -> "FiniteMagma":
        normalized = tuple(tuple(row) for row in table)
        magma = cls(normalized, name=name)
        magma.validate()
        return magma

    @property
    def size(self) -> int:
        return len(self.table)

    def validate(self) -> None:
        n = len(self.table)
        if n == 0:
            raise ValueError("magma table must be non-empty")
        for row in self.table:
            if len(row) != n:
                raise ValueError("magma table must be square")
            for value in row:
                if not isinstance(value, int) or not 0 <= value < n:
                    raise ValueError("magma table entries must be integers in 0..n-1")

    def op(self, left: int, right: int) -> int:
        return self.table[left][right]

    def satisfies(self, equation: Equation) -> bool:
        return equation.holds_for_all(range(self.size), self.op)

    def invariants(self) -> dict[str, bool | int | str]:
        return {
            "name": self.name,
            "carrier_order": self.size,
            "closed": True,
            "associative": self._is_associative(),
            "commutative": self._is_commutative(),
            "idempotent": self._is_idempotent(),
        }

    def _is_associative(self) -> bool:
        for a, b, c in product(range(self.size), repeat=3):
            if self.op(self.op(a, b), c) != self.op(a, self.op(b, c)):
                return False
        return True

    def _is_commutative(self) -> bool:
        for a, b in product(range(self.size), repeat=2):
            if self.op(a, b) != self.op(b, a):
                return False
        return True

    def _is_idempotent(self) -> bool:
        return all(self.op(a, a) == a for a in range(self.size))

    def counterexample_to_equation(self, equation: Equation) -> dict[str, object] | None:
        variables = sorted(equation.variables())
        for values in product(range(self.size), repeat=len(variables)):
            assignment = dict(zip(variables, values))
            lhs = equation.lhs.evaluate(assignment, self.op)
            rhs = equation.rhs.evaluate(assignment, self.op)
            if lhs != rhs:
                return {"assignment": assignment, "lhs": lhs, "rhs": rhs}
        return None

    def counterexample_to_implication(
        self,
        premises: Sequence[Equation],
        conclusion: Equation,
    ) -> dict[str, object] | None:
        variables = sorted(set().union(*(p.variables() for p in premises), conclusion.variables()))
        for values in product(range(self.size), repeat=len(variables)):
            assignment = dict(zip(variables, values))
            if all(p.holds(assignment, self.op) for p in premises) and not conclusion.holds(
                assignment, self.op
            ):
                return {
                    "name": self.name,
                    "size": self.size,
                    "carrier_order": self.size,
                    "table": [list(row) for row in self.table],
                    "assignment": assignment,
                    "premise_equations": [str(p) for p in premises],
                    "premises_satisfied": True,
                    "conclusion_equation": str(conclusion),
                    "conclusion_violated": True,
                    "conclusion_lhs": conclusion.lhs.evaluate(assignment, self.op),
                    "conclusion_rhs": conclusion.rhs.evaluate(assignment, self.op),
                    "table_invariants": self.invariants(),
                }
        return None

    def countermodel_certificate_payload(
        self,
        source: Equation,
        target: Equation,
    ) -> dict[str, object] | None:
        """Return an implication countermodel when this magma validates source and refutes target."""

        if not self.satisfies(source):
            return None

        witness = self.counterexample_to_equation(target)
        if witness is None:
            return None

        return {
            "name": self.name,
            "table": [list(row) for row in self.table],
            "carrier_order": self.size,
            "source_equation": str(source),
            "target_equation": str(target),
            "source_satisfied": True,
            "target_violated": True,
            "assignment": witness["assignment"],
            "target_lhs": witness["lhs"],
            "target_rhs": witness["rhs"],
            "table_invariants": self.invariants(),
        }

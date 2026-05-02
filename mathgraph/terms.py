"""Terms for the first MathGraph equational testbed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True, order=True)
class Term:
    """A variable or an operation term.

    The initial testbed uses one binary operation named ``*``.
    """

    symbol: str
    args: tuple["Term", ...] = ()

    @property
    def is_variable(self) -> bool:
        return not self.args

    def variables(self) -> set[str]:
        if self.is_variable:
            return {self.symbol}
        names: set[str] = set()
        for arg in self.args:
            names.update(arg.variables())
        return names

    def evaluate(self, assignment: Mapping[str, int], operation: Callable[[int, int], int]) -> int:
        if self.is_variable:
            return assignment[self.symbol]
        if self.symbol != "*" or len(self.args) != 2:
            raise ValueError(f"unsupported operation term: {self}")
        return operation(
            self.args[0].evaluate(assignment, operation),
            self.args[1].evaluate(assignment, operation),
        )

    def __str__(self) -> str:
        if self.is_variable:
            return self.symbol
        left, right = self.args
        return f"({left} * {right})"


class _TermParser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0

    def parse(self) -> Term:
        term = self._parse_product()
        self._skip_ws()
        if self.pos != len(self.source):
            raise ValueError(f"unexpected text at position {self.pos}: {self.source[self.pos:]!r}")
        return term

    def _parse_product(self) -> Term:
        left = self._parse_atom()
        while True:
            self._skip_ws()
            if not self._consume("*"):
                return left
            right = self._parse_atom()
            left = Term("*", (left, right))

    def _parse_atom(self) -> Term:
        self._skip_ws()
        if self._consume("("):
            term = self._parse_product()
            self._skip_ws()
            if not self._consume(")"):
                raise ValueError("missing closing parenthesis")
            return term

        start = self.pos
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] == "_"
        ):
            self.pos += 1
        if start == self.pos:
            raise ValueError(f"expected term at position {self.pos}")
        return Term(self.source[start:self.pos])

    def _skip_ws(self) -> None:
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1

    def _consume(self, token: str) -> bool:
        if self.source.startswith(token, self.pos):
            self.pos += len(token)
            return True
        return False


def parse_term(source: str) -> Term:
    """Parse a variable/product term such as ``x * (y * z)``."""

    return _TermParser(source).parse()

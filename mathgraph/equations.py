"""Equations and equational implication helpers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Mapping

from mathgraph.terms import Term, parse_term


@dataclass(frozen=True)
class Equation:
    lhs: Term
    rhs: Term

    def variables(self) -> set[str]:
        return self.lhs.variables() | self.rhs.variables()

    def holds(self, assignment: Mapping[str, int], operation: Callable[[int, int], int]) -> bool:
        return self.lhs.evaluate(assignment, operation) == self.rhs.evaluate(assignment, operation)

    def holds_for_all(self, universe: range, operation: Callable[[int, int], int]) -> bool:
        variables = sorted(self.variables())
        for values in product(universe, repeat=len(variables)):
            assignment = dict(zip(variables, values))
            if not self.holds(assignment, operation):
                return False
        return True

    def __str__(self) -> str:
        return f"{self.lhs} = {self.rhs}"


def terms_alpha_equivalent(source: Term, target: Term, mapping: dict[str, str]) -> bool:
    """Check skeleton-preserving variable relabeling with a bijective map."""

    if source.is_variable and target.is_variable:
        existing = mapping.get(source.symbol)
        if existing is not None:
            return existing == target.symbol
        if target.symbol in mapping.values():
            return False
        mapping[source.symbol] = target.symbol
        return True

    if source.symbol != target.symbol or len(source.args) != len(target.args):
        return False

    return all(
        terms_alpha_equivalent(source_arg, target_arg, mapping)
        for source_arg, target_arg in zip(source.args, target.args)
    )


def equations_alpha_equivalent(source: Equation, target: Equation) -> bool:
    mapping: dict[str, str] = {}
    return terms_alpha_equivalent(source.lhs, target.lhs, mapping) and terms_alpha_equivalent(
        source.rhs, target.rhs, mapping
    )


def equations_swapped(source: Equation, target: Equation) -> bool:
    return source.lhs == target.rhs and source.rhs == target.lhs


def equations_swapped_alpha_equivalent(source: Equation, target: Equation) -> bool:
    mapping: dict[str, str] = {}
    return terms_alpha_equivalent(source.lhs, target.rhs, mapping) and terms_alpha_equivalent(
        source.rhs, target.lhs, mapping
    )


def parse_equation(source: str) -> Equation:
    if source.count("=") != 1:
        raise ValueError("equation must contain exactly one '='")
    lhs, rhs = source.split("=")
    return Equation(parse_term(lhs.strip()), parse_term(rhs.strip()))

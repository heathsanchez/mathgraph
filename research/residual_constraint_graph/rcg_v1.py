#!/usr/bin/env python3
"""Minimal executable Residual Constraint Graph v1.

The engine intentionally does not infer mechanisms from text similarity. It operates
only on explicit verified constraints supplied with provenance. It finds minimal
constraint intersections that cover multiple unresolved residuals and are not
already satisfied by an existing operator signature.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from itertools import combinations
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class Residual:
    name: str
    constraints: FrozenSet[str]
    weight: float = 1.0
    verified: bool = True


@dataclass(frozen=True)
class Operator:
    name: str
    properties: FrozenSet[str]


@dataclass(frozen=True)
class Obstruction:
    constraints: FrozenSet[str]
    covered: tuple[str, ...]
    mass: float
    closure_satisfied: bool


def intersections(residuals: Iterable[Residual], operators: Iterable[Operator], min_cover: int = 2):
    rs = [r for r in residuals if r.verified]
    ops = list(operators)
    out = []
    for k in range(2, len(rs) + 1):
        for subset in combinations(rs, k):
            common = frozenset.intersection(*(r.constraints for r in subset))
            if not common:
                continue
            covered = tuple(r.name for r in rs if common <= r.constraints)
            if len(covered) < min_cover:
                continue
            closure = any(common <= op.properties for op in ops)
            mass = sum(r.weight for r in rs if r.name in covered)
            out.append(Obstruction(common, covered, mass, closure))

    # Keep only non-closure-satisfied candidates, de-duplicate, then Pareto/minimality prune:
    # a candidate is redundant when a strict subset of its constraints has identical coverage.
    uniq = {}
    for o in out:
        if o.closure_satisfied:
            continue
        key = (o.constraints, o.covered)
        if key not in uniq or o.mass > uniq[key].mass:
            uniq[key] = o
    vals = list(uniq.values())
    pruned = []
    for o in vals:
        redundant = any(
            p.covered == o.covered and p.constraints < o.constraints
            for p in vals
        )
        if not redundant:
            pruned.append(o)
    return sorted(pruned, key=lambda o: (-o.mass, len(o.constraints), sorted(o.constraints)))


def self_test():
    residuals = [
        Residual('capacity_flat', frozenset({'structural','representation','capacity-independent','cache-related'})),
        Residual('source_pointer_unsound', frozenset({'structural','identity','semantic-identity-required','cache-related','sound'})),
        Residual('structural_key_cost', frozenset({'structural','representation','semantic-identity-required','duplicate-key-computation-prohibited','cache-related'})),
        Residual('cache_bypass_bad', frozenset({'structural','reuse-essential','cache-related'})),
        Residual('tiny_state_mass', frozenset({'structural','representation','tiny-state','cache-related'})),
    ]
    operators = [
        Operator('source_pointer', frozenset({'structural','cache-related','reuse-essential'})),
        Operator('full_structural_key', frozenset({'structural','cache-related','semantic-identity-required','sound'})),
    ]
    obs = intersections(residuals, operators)
    assert obs
    assert any('cache-related' in o.constraints and len(o.covered) >= 3 for o in obs)
    print('RCG_SELF_TEST_PASS')
    for o in obs[:10]:
        print({'constraints': sorted(o.constraints), 'covered': o.covered, 'mass': o.mass})


if __name__ == '__main__':
    self_test()

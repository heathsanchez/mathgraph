"""SAIR-oriented finite magma constructor bank."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from mathgraph.breakthrough_loop import BreakthroughTask
from mathgraph.finite_magma_world import (
    add_mod_n,
    commutative_nonassociative_3,
    constant_table,
    deterministic_perturbation_3,
    left_projection,
    max_table,
    min_table,
    normalize_table,
    rectangular_band,
    right_projection,
    sub_mod_n,
    xor_mod_2,
)


@dataclass(frozen=True)
class SAIRConstructor:
    constructor_id: str
    family: str
    carrier_size: int
    table: tuple[tuple[int, ...], ...]
    advisory_atoms: tuple[str, ...] = ()
    expected_basin_tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "constructor_id": self.constructor_id,
            "family": self.family,
            "carrier_size": self.carrier_size,
            "table": [list(row) for row in self.table],
            "advisory_atoms": list(self.advisory_atoms),
            "expected_basin_tags": list(self.expected_basin_tags),
            "metadata": dict(self.metadata),
        }


def build_sair_constructor_bank() -> list[SAIRConstructor]:
    specs = [
        ("left_projection_n2", "projection", left_projection(2), ("projection", "variable_drop"), ("projection_pressure",)),
        ("right_projection_n2", "projection", right_projection(2), ("projection", "variable_drop"), ("projection_pressure",)),
        ("left_projection_n3", "projection", left_projection(3), ("projection", "variable_drop"), ("projection_pressure",)),
        ("right_projection_n3", "projection", right_projection(3), ("projection", "variable_drop"), ("projection_pressure",)),
        ("constant_n2_0", "constant", constant_table(2, 0), ("constant", "collapse"), ("collapse_or_constant_pressure",)),
        ("constant_n2_1", "constant", constant_table(2, 1), ("constant", "collapse"), ("collapse_or_constant_pressure",)),
        ("constant_n3_0", "constant", constant_table(3, 0), ("constant", "collapse"), ("collapse_or_constant_pressure",)),
        ("constant_n3_1", "constant", constant_table(3, 1), ("constant", "collapse"), ("collapse_or_constant_pressure",)),
        ("xor_mod_2", "affine", xor_mod_2(), ("affine", "mod2"), ("commutativity_pressure",)),
        ("add_mod_2", "affine", add_mod_n(2), ("affine", "mod2"), ("commutativity_pressure",)),
        ("add_mod_3", "affine", add_mod_n(3), ("affine", "mod3"), ("commutativity_pressure",)),
        ("sub_mod_2", "affine", sub_mod_n(2), ("subtractive", "mod2"), ("mixed_sair_false_pair",)),
        ("sub_mod_3", "affine", sub_mod_n(3), ("subtractive", "mod3"), ("mixed_sair_false_pair",)),
        ("min_n2", "semilattice", min_table(2), ("semilattice", "min"), ("idempotent_band_pressure",)),
        ("max_n2", "semilattice", max_table(2), ("semilattice", "max"), ("idempotent_band_pressure",)),
        ("min_n3", "semilattice", min_table(3), ("semilattice", "min"), ("idempotent_band_pressure",)),
        ("max_n3", "semilattice", max_table(3), ("semilattice", "max"), ("idempotent_band_pressure",)),
        ("rectangular_band_n4", "band", rectangular_band(4), ("band", "rectangular"), ("associative_or_deep_term_pressure",)),
        ("comm_nonassoc_n3", "perturbation", commutative_nonassociative_3(), ("commutative", "nonassociative"), ("associative_or_deep_term_pressure",)),
        ("perturbation_n3", "perturbation", deterministic_perturbation_3(), ("mixed", "perturbation"), ("mixed_sair_false_pair",)),
    ]
    return [
        SAIRConstructor(cid, family, len(table), normalize_table(table), tuple(atoms), tuple(tags))
        for cid, family, table, atoms, tags in specs
    ]


def constructor_table_dict(constructors: Sequence[SAIRConstructor] | None = None) -> dict[str, tuple[tuple[int, ...], ...]]:
    return {ctor.constructor_id: ctor.table for ctor in (constructors or build_sair_constructor_bank())}


def preferred_constructors_for_task(task: BreakthroughTask | dict[str, Any], constructors: Sequence[SAIRConstructor] | None = None) -> list[str]:
    t = task if isinstance(task, BreakthroughTask) else BreakthroughTask.from_dict(task)
    bank = list(constructors or build_sair_constructor_bank())
    family = t.family
    scored: list[tuple[float, str]] = []
    for ctor in bank:
        score = 0.0
        if family in ctor.expected_basin_tags:
            score += 10.0
        score += _feature_score(t, ctor)
        scored.append((score, ctor.constructor_id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [cid for _score, cid in scored]


def attach_preferred_constructors(tasks: Sequence[BreakthroughTask | dict[str, Any]], constructors: Sequence[SAIRConstructor] | None = None) -> list[BreakthroughTask]:
    out = []
    bank = list(constructors or build_sair_constructor_bank())
    for item in tasks:
        task = item if isinstance(item, BreakthroughTask) else BreakthroughTask.from_dict(item)
        preferred = preferred_constructors_for_task(task, bank)
        out.append(
            BreakthroughTask(
                task_id=task.task_id,
                source_equation=task.source_equation,
                target_equation=task.target_equation,
                family=task.family,
                metadata={**dict(task.metadata), "preferred_constructors": preferred},
            )
        )
    return out


def _feature_score(task: BreakthroughTask, ctor: SAIRConstructor) -> float:
    text = f"{task.source_equation} {task.target_equation}"
    if ctor.family == "projection" and any(pattern in task.target_equation for pattern in ("= x", "= y", "= z", "x =", "y =", "z =")):
        return 3.0
    if ctor.family == "constant" and any(pattern in task.target_equation for pattern in ("x = y", "y = z", "x = z")):
        return 2.5
    if ctor.family == "semilattice" and "(x * x)" in text:
        return 2.0
    if ctor.family == "affine" and "(x * y)" in text and "(y * x)" in text:
        return 1.5
    if ctor.family == "perturbation":
        return 0.5
    return 0.0

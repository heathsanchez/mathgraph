from mathgraph.breakthrough_loop import BreakthroughTask
from mathgraph.finite_magma_world import table_satisfies_equation
from mathgraph.sair_constructor_bank import (
    attach_preferred_constructors,
    build_sair_constructor_bank,
    constructor_table_dict,
    preferred_constructors_for_task,
)


def test_constructor_bank_valid_tables_and_atoms():
    bank = build_sair_constructor_bank()
    assert bank
    ids = [ctor.constructor_id for ctor in bank]
    assert len(ids) == len(set(ids))
    for ctor in bank:
        assert ctor.advisory_atoms
        assert len(ctor.table) == ctor.carrier_size
        table_satisfies_equation(ctor.table, "x = x")


def test_constructor_ids_stable():
    assert [c.constructor_id for c in build_sair_constructor_bank()] == [c.constructor_id for c in build_sair_constructor_bank()]


def test_heuristic_mapper_projection():
    task = BreakthroughTask("t", "(x * x) = x", "(x * y) = x", family="projection_pressure")
    preferred = preferred_constructors_for_task(task)
    assert preferred[0].startswith("left_projection") or preferred[0].startswith("right_projection")


def test_heuristic_mapper_mixed_fallback():
    task = BreakthroughTask("t", "x = x", "((x * y) * z) = (x * (z * y))", family="unknown")
    preferred = preferred_constructors_for_task(task)
    assert preferred
    assert "perturbation_n3" in preferred


def test_attach_preferred_constructors():
    task = BreakthroughTask("t", "x = x", "x = y", family="collapse_or_constant_pressure")
    out = attach_preferred_constructors([task])
    assert out[0].metadata["preferred_constructors"]
    assert constructor_table_dict()

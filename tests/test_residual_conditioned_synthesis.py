import pandas as pd

from mathgraph.residual_conditioned_synthesis import (
    build_residual_pair_specs,
    complete_partial_table,
    evaluate_residual_conditioned_constructors,
    force_target_violation_constraints,
    generate_witness_candidates,
    synthesize_for_residual_pairs,
)


EQUATIONS = ["x = x", "x = y", "(x * y) = x"]


def _pairs():
    return pd.DataFrame(
        [
            {
                "pair_idx": 0,
                "source_eq_idx": 0,
                "target_eq_idx": 1,
                "basin": "toy",
                "deep_ir_candidate": "diag",
                "microbasin_key": "toy_diag",
                "recommended_family": "diagonal_spike_completion",
            }
        ]
    )


def test_residual_pair_spec_builds_from_toy_pairs():
    specs = build_residual_pair_specs(_pairs(), EQUATIONS)
    assert len(specs) == 1
    assert specs[0].source_equation == "x = x"
    assert specs[0].target_equation == "x = y"


def test_witness_candidates_are_deterministic_and_include_core_strategies():
    spec = build_residual_pair_specs(_pairs(), EQUATIONS)[0]
    first = generate_witness_candidates(spec, seed=7)
    second = generate_witness_candidates(spec, seed=7)
    assert [w.assignment for w in first] == [w.assignment for w in second]
    rationales = {w.rationale for w in first}
    assert {"variable_split", "diagonal_split"}.issubset(rationales)


def test_target_violation_constraints_are_produced():
    spec = build_residual_pair_specs(_pairs(), EQUATIONS)[0]
    witness = generate_witness_candidates(spec)[0]
    constraints = force_target_violation_constraints(spec, witness)
    assert constraints
    assert all(c.kind == "target_violation" for c in constraints)


def test_completion_records_contradiction_for_conflict():
    spec = build_residual_pair_specs(_pairs(), EQUATIONS)[0]
    witness = generate_witness_candidates(spec)[0]
    constraints = force_target_violation_constraints(spec, witness)
    if constraints:
        constraints = [constraints[0], type(constraints[0])("conflict", "target_violation", constraints[0].cell, (constraints[0].value + 1) % witness.n, "conflict", "test")]
    attempt, constructor = complete_partial_table(spec, witness, constraints, "projection_completion_left", witness.n)
    assert attempt.contradiction_found is True
    assert constructor is None


def test_completions_produce_valid_tables_and_diagonal_spike_changes_diagonal():
    spec = build_residual_pair_specs(_pairs(), EQUATIONS)[0]
    witness = generate_witness_candidates(spec)[0]
    constraints = force_target_violation_constraints(spec, witness)
    attempt, constructor = complete_partial_table(spec, witness, constraints, "diagonal_spike_completion", witness.n)
    assert attempt.completed is True
    assert constructor is not None
    assert len(constructor.table) == witness.n
    assert any(constructor.table[i][i] != i for i in range(witness.n))


def test_finite_checker_verifies_known_countermodel_and_no_truth_from_failure():
    specs, attempts, constructors = synthesize_for_residual_pairs(_pairs(), EQUATIONS, max_n=2, max_pairs=1)
    recoveries = evaluate_residual_conditioned_constructors(constructors, EQUATIONS)
    assert not recoveries.empty
    assert recoveries["finite_checked"].map(bool).all()
    assert recoveries["recovered"].map(bool).any()
    failed = recoveries[~recoveries["recovered"].map(bool)]
    assert not (failed["terminal_form"] == "VERIFIED_PROOF").any()

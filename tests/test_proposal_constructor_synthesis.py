import pandas as pd

from mathgraph.proposal_constructor_synthesis import (
    evaluate_synthesized_constructors,
    synthesize_constructors_for_proposal,
    synthesize_constructors_for_proposals,
    summarize_synthesis,
)


CORE_FAMILIES = [
    "constant",
    "left_projection",
    "right_projection",
    "projection_exception_left",
    "projection_exception_right",
    "quotient_spike",
    "quotient_fresh_gate",
    "fresh_absorber",
    "random_fresh_sink",
    "random_fresh_collapse",
    "diagonal_spike",
    "diag_perturb_right",
    "diag_perturb_left",
    "tail_coupled_projection",
    "head_coupled_projection",
    "row_erasure_family",
    "col_erasure_family",
    "block_selector",
    "block_selector_dual",
    "linear_combo_mod",
    "add_mod",
    "sub_mod",
    "xor_mod",
    "prior",
]


def test_each_core_family_generates_at_least_one_table():
    for family in CORE_FAMILIES:
        rows = synthesize_constructors_for_proposal({"proposal_id": family, "proposal_family": family}, max_n=3, seed=1)
        assert rows, family
        assert all(row.advisory_only and not row.can_promote_truth for row in rows)


def test_generation_deterministic_and_deduped():
    proposal = {"proposal_id": "p", "proposal_family": "random_fresh_sink"}
    first = synthesize_constructors_for_proposal(proposal, max_n=4, seed=99)
    second = synthesize_constructors_for_proposal(proposal, max_n=4, seed=99)
    assert [row.table_hash for row in first] == [row.table_hash for row in second]
    assert len({row.table_hash for row in first}) == len(first)


def test_modular_tables_are_valid_shapes():
    proposals = pd.DataFrame(
        [
            {"proposal_id": "add", "proposal_family": "add_mod", "residual_basin_id": "r"},
            {"proposal_id": "sub", "proposal_family": "sub_mod", "residual_basin_id": "r"},
            {"proposal_id": "xor", "proposal_family": "xor_mod", "residual_basin_id": "r"},
        ]
    )
    constructors, _ = synthesize_constructors_for_proposals(proposals, max_n=4)
    assert not constructors.empty
    for _, row in constructors.iterrows():
        table = row["table"]
        assert len(table) == int(row["n"])
        assert all(len(inner) == int(row["n"]) for inner in table)


def test_projection_exception_differs_from_projection():
    left = synthesize_constructors_for_proposal({"proposal_id": "l", "proposal_family": "left_projection"}, max_n=2)[0]
    exc = synthesize_constructors_for_proposal({"proposal_id": "e", "proposal_family": "projection_exception_left"}, max_n=2)[0]
    assert left.table != exc.table


def test_fresh_absorber_uses_fresh_element():
    row = synthesize_constructors_for_proposal({"proposal_id": "f", "proposal_family": "fresh_absorber"}, max_n=3)[0]
    fresh = row.n - 1
    assert any(fresh in inner for inner in row.table)


def test_finite_evaluator_verifies_simple_countermodel():
    proposals = pd.DataFrame([{"proposal_id": "add", "proposal_family": "add_mod", "residual_basin_id": "r"}])
    constructors, results = synthesize_constructors_for_proposals(proposals, max_n=2)
    pairs = pd.DataFrame([{"pair_idx": 0, "source_eq_idx": 0, "target_eq_idx": 1}])
    recoveries = evaluate_synthesized_constructors(constructors, pairs, ["x = x", "x = y"])
    assert recoveries["finite_checked"].map(bool).all()
    assert recoveries["recovered"].map(bool).any()
    summary = summarize_synthesis(constructors, results, recoveries)
    assert summary["synthesized_recovered_pairs"] > 0
    assert summary["terminal_claims_from_advisory_count"] == 0

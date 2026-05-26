import pandas as pd

from mathgraph.active_residual_discovery import (
    build_residual_basins,
    evaluate_constructor_proposals,
    propose_constructor_recipes,
    summarize_active_discovery,
)


def _frames():
    features = pd.DataFrame(
        [
            {
                "seed": 1,
                "pair_idx": 0,
                "basin": "fresh_escape",
                "deep_ir_candidate": "fresh_gate",
                "fresh_variable_escape_count": 3,
                "target_separation_pressure": 1,
                "repeat_tail_pressure": 0,
                "active_discovery_family_hit": "quotient_fresh_gate",
            },
            {
                "seed": 1,
                "pair_idx": 1,
                "basin": "fresh_escape",
                "deep_ir_candidate": "fresh_gate",
                "fresh_variable_escape_count": 3,
                "target_separation_pressure": 1,
                "repeat_tail_pressure": 0,
                "active_discovery_family_hit": "",
            },
            {
                "seed": 1,
                "pair_idx": 2,
                "basin": "repeat_tail",
                "deep_ir_candidate": "tail_pressure",
                "fresh_variable_escape_count": 0,
                "target_separation_pressure": 1,
                "repeat_tail_pressure": 4,
                "active_discovery_family_hit": "tail_coupled_projection",
            },
            {
                "seed": 1,
                "pair_idx": 3,
                "basin": "repeat_tail",
                "deep_ir_candidate": "tail_pressure",
                "fresh_variable_escape_count": 0,
                "target_separation_pressure": 1,
                "repeat_tail_pressure": 4,
                "active_discovery_family_hit": "",
            },
            {
                "seed": 1,
                "pair_idx": 4,
                "basin": "resolved",
                "deep_ir_candidate": "done",
                "fresh_variable_escape_count": 0,
                "target_separation_pressure": 0,
                "repeat_tail_pressure": 0,
                "active_discovery_family_hit": "",
            },
        ]
    )
    recovery = features[["seed", "pair_idx", "active_discovery_family_hit"]].copy()
    recovery["generic_recovered"] = [False, False, False, False, True]
    recovery["heldout_lawbook_recovered"] = [False, False, False, False, True]
    return features, recovery


def test_residual_basin_builder_only_uses_unresolved_pairs_and_names_obstructions():
    features, recovery = _frames()
    basins = build_residual_basins(features, recovery, min_support=2)
    assert len(basins) == 2
    assert basins["support"].sum() == 4
    assert basins["obstruction_name"].str.contains("active_residual_unresolved").all()
    assert bool(basins["advisory_only"].all()) is True
    assert bool(basins["can_promote_truth"].any()) is False


def test_proposal_generator_is_deterministic_and_geometry_aware():
    features, recovery = _frames()
    basins = build_residual_basins(features, recovery, min_support=2)
    first = propose_constructor_recipes(basins, max_proposals_per_basin=2)
    second = propose_constructor_recipes(basins, max_proposals_per_basin=2)
    assert first["proposal_id"].tolist() == second["proposal_id"].tolist()
    assert "quotient_fresh_gate" in set(first["proposal_family"])
    assert "tail_coupled_projection" in set(first["proposal_family"])
    assert bool(first["advisory_only"].all()) is True
    assert bool(first["can_promote_truth"].any()) is False


def test_proposal_evaluation_proxy_counts_positive_hits_and_safety():
    features, recovery = _frames()
    basins = build_residual_basins(features, recovery, min_support=2)
    proposals = propose_constructor_recipes(basins, max_proposals_per_basin=2)
    evaluations = evaluate_constructor_proposals(proposals, features, recovery)
    assert evaluations["recovered_pairs"].sum() >= 2
    assert "proxy" in set(evaluations["evaluation_mode"])
    summary = summarize_active_discovery(basins, proposals, evaluations)
    assert summary["total_recovered_pairs"] >= 2
    assert summary["true_contamination_count"] == 0
    assert summary["terminal_claims_from_advisory_count"] == 0

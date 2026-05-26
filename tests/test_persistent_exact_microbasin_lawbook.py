import pandas as pd

from mathgraph.persistent_exact_microbasin_lawbook import (
    add_microbasin_keys,
    build_microbasin_key,
    build_persistent_lawbook,
    detect_recovery_columns,
    evaluate_persistent_replay,
    normalize_recovery_frame,
    replay_persistent_lawbook,
)


def _frame(seed: int = 1729, episode: int = 0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "seed": seed,
                "episode": episode,
                "pair_idx": 0,
                "basin": "projection_pressure",
                "deep_ir_candidate": "high_gradient",
                "quotient_pressure": 2,
                "target_separation_pressure": 3,
                "ir_constraint_loss": 2,
                "fresh_variable_escape_count": 0,
                "repeat_tail_pressure": 1,
                "skeleton_equal": False,
                "generic_recovered": False,
                "heldout_lawbook_recovered": True,
                "lawbook_gain_hit": True,
                "lawbook_gain_constructor_id": "c_exact_projection",
                "lawbook_gain_constructor_family": "projection_exception_left",
            },
            {
                "seed": seed,
                "episode": episode,
                "pair_idx": 1,
                "basin": "fresh_escape",
                "deep_ir_candidate": "fresh_gate",
                "generic_recovered": True,
                "heldout_lawbook_recovered": True,
                "lawbook_gain_hit": False,
                "lawbook_gain_constructor_id": "",
                "lawbook_gain_constructor_family": "",
            },
        ]
    )


def test_microbasin_key_is_deterministic():
    row = _frame().iloc[0].to_dict()
    assert build_microbasin_key(row) == build_microbasin_key(dict(reversed(list(row.items()))))
    keyed = add_microbasin_keys(_frame())
    assert keyed["microbasin_key"].iloc[0] == build_microbasin_key(row)


def test_recovery_alias_normalization_detects_exact_gain():
    df = _frame().rename(columns={"heldout_lawbook_recovered": "lawbook_recovered"})
    cols = detect_recovery_columns(df)
    assert cols["lawbook_recovered"] == "lawbook_recovered"
    norm = normalize_recovery_frame(df)
    assert bool(norm["lawbook_gain_hit_norm"].iloc[0]) is True
    assert norm["lawbook_gain_constructor_family_norm"].iloc[0] == "projection_exception_left"
    assert bool(norm["advisory_only"].all()) is True
    assert bool(norm["can_promote_truth"].any()) is False


def test_persistent_lawbook_entries_are_advisory():
    lawbook = build_persistent_lawbook([_frame()])
    assert not lawbook.empty
    row = lawbook.iloc[0]
    assert row["constructor_id"] == "c_exact_projection"
    assert row["status"] == "persistent_exact_microbasin_route_advisory"
    assert bool(row["advisory_only"]) is True
    assert bool(row["can_promote_truth"]) is False


def test_replay_uses_prior_lawbook_and_evaluates_reuse():
    prior = build_persistent_lawbook([_frame(seed=1, episode=0)])
    current = _frame(seed=2, episode=1)
    replay = replay_persistent_lawbook(current, prior)
    metrics = evaluate_persistent_replay(replay)
    assert metrics["exact_recipe_reuse_count"] >= 1
    assert metrics["persistent_gain_over_generic_proxy"] >= 1
    assert metrics["true_contamination_count"] == 0
    assert metrics["terminal_claims_from_advisory_count"] == 0
    assert metrics["failed_search_promoted_true_count"] == 0


def test_no_current_episode_leakage_pattern():
    prior = build_persistent_lawbook([_frame(seed=1, episode=0)])
    assert int(prior["last_seen_episode"].max()) == 0
    current = _frame(seed=2, episode=1)
    replay = replay_persistent_lawbook(current, prior)
    assert bool(replay["persistent_route_available"].iloc[0]) is True

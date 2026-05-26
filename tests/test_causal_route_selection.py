import pandas as pd

from mathgraph.causal_route_selection import (
    apply_causal_route_policy,
    build_route_evidence,
    evaluate_causal_policy,
    score_causal_routes,
    select_causal_routes,
)


def _evidence() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "microbasin_key": "stable",
                "constructor_family": "stable_family",
                "constructor_id": "stable_c",
                "episode": 0,
                "seed": 1,
                "support": 3,
                "gain_over_generic": 1,
                "gain_over_lawbook": 0,
            },
            {
                "microbasin_key": "stable",
                "constructor_family": "stable_family",
                "constructor_id": "stable_c",
                "episode": 1,
                "seed": 2,
                "support": 3,
                "gain_over_generic": 1,
                "gain_over_lawbook": 0,
            },
            {
                "microbasin_key": "overfit",
                "constructor_family": "overfit_family",
                "constructor_id": "overfit_c",
                "episode": 0,
                "seed": 1,
                "support": 3,
                "gain_over_generic": 2,
                "gain_over_lawbook": 0,
            },
            {
                "microbasin_key": "negative",
                "constructor_family": "negative_family",
                "constructor_id": "negative_c",
                "episode": 0,
                "seed": 1,
                "support": 3,
                "gain_over_generic": 1,
                "gain_over_lawbook": 0,
            },
            {
                "microbasin_key": "negative",
                "constructor_family": "negative_family",
                "constructor_id": "negative_c",
                "episode": 1,
                "seed": 2,
                "support": 3,
                "gain_over_generic": -1,
                "gain_over_lawbook": -1,
            },
        ]
    )


def test_causal_score_selects_stable_positive_routes():
    scores = score_causal_routes(_evidence())
    selected = select_causal_routes(scores)
    assert set(selected["microbasin_key"]) == {"stable"}
    assert bool(selected["advisory_only"].all()) is True
    assert bool(selected["can_promote_truth"].any()) is False


def test_causal_score_rejects_overfit_and_negative_routes():
    scores = score_causal_routes(_evidence())
    rejected = scores[~scores["selected"]]
    reasons = dict(zip(rejected["microbasin_key"], rejected["rejection_reason"]))
    assert reasons["overfit"] == "episode_count_below_threshold"
    assert reasons["negative"] in {"non_regression_rate_below_threshold", "negative_generic_regression"}


def test_apply_causal_policy_and_evaluate():
    heldout = pd.DataFrame(
        [
            {
                "microbasin_key": "stable",
                "generic_recovered": False,
                "heldout_lawbook_recovered": True,
                "lawbook_gain_hit": True,
                "lawbook_gain_constructor_id": "stable_c",
                "lawbook_gain_constructor_family": "stable_family",
            }
        ]
    )
    selected = select_causal_routes(score_causal_routes(_evidence()))
    replay = apply_causal_route_policy(heldout, selected)
    metrics = evaluate_causal_policy(replay)
    assert metrics["v2_causal_yield_proxy"] == 1
    assert metrics["v2_gain_over_generic"] == 1
    assert metrics["terminal_claims_from_advisory_count"] == 0


def test_build_route_evidence_from_replay_rows():
    replay = pd.DataFrame(
        [
            {
                "microbasin_key": "stable",
                "persistent_recommended_family": "stable_family",
                "persistent_recommended_constructor_id": "stable_c",
                "generic_recovered_norm": False,
                "lawbook_recovered_norm": True,
                "persistent_recovered_proxy": True,
            }
        ]
    )
    evidence = build_route_evidence(replay, episode_idx=0, seed=1)
    assert evidence["gain_over_generic"].iloc[0] == 1
    assert bool(evidence["advisory_only"].iloc[0]) is True
    assert bool(evidence["can_promote_truth"].iloc[0]) is False

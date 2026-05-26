from __future__ import annotations

import pandas as pd

from mathgraph.sair_stage2_policy_selector import apply_policy_to_scorecard, learn_canonical_policy


def test_negative_component_is_rejected():
    frame = pd.DataFrame(
        [
            {"component": "baseline", "marginal_gain": 0, "support": 10},
            {"component": "repair", "marginal_gain": -5, "support": 5},
        ]
    )
    policy = learn_canonical_policy(frame)
    assert "repair" in [row["component"] for row in policy["rejected_components"]]


def test_positive_component_is_selected():
    frame = pd.DataFrame(
        [
            {"component": "baseline", "marginal_gain": 0, "support": 10},
            {"component": "lawbook", "marginal_gain": 2, "support": 12},
        ]
    )
    policy = learn_canonical_policy(frame)
    assert "lawbook" in [row["component"] for row in policy["selected_components"]]


def test_insufficient_support_component_is_rejected():
    frame = pd.DataFrame(
        [
            {"component": "baseline", "marginal_gain": 0, "support": 10},
            {"component": "microbasin", "marginal_gain": 1, "support": 0},
        ]
    )
    policy = learn_canonical_policy(frame, min_support=1)
    assert policy["rejected_components"][0]["reason"] == "insufficient held-out support"


def test_policy_never_promotes_truth():
    frame = pd.DataFrame([{"component": "baseline", "marginal_gain": 0, "support": 10}])
    policy = learn_canonical_policy(frame)
    assert policy["advisory_only"] is True
    assert policy["can_promote_truth"] is False


def test_apply_policy_can_gate_harmful_repair_to_positive_gain():
    policy = {
        "selected_components": [{"component": "baseline"}, {"component": "lawbook"}],
        "rejected_components": [{"component": "repair"}],
    }
    adjusted = apply_policy_to_scorecard(
        {
            "real_sair_used": True,
            "strict_admission_passed": True,
            "episode_0_certificates": 10,
            "episode_1_certificates": 12,
            "episode_2_certificates": 11,
            "episode_3_certificates": 5,
            "total_gain_over_baseline": -5,
        },
        policy,
    )
    assert adjusted["total_gain_over_baseline"] == 2
    assert adjusted["final_classification"] == "verified_memory_compounding_breakthrough"

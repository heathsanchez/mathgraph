from mathgraph.route_priors import SmoothedRoutePriorConfig, build_smoothed_route_prior


def test_empty_outcomes_returns_near_uniform_probabilities():
    prior = build_smoothed_route_prior([], route_families=["a", "b", "c"])
    assert set(prior.route_probabilities) == {"a", "b", "c"}
    assert all(abs(p - 1 / 3) < 0.05 for p in prior.route_probabilities.values())


def test_single_successful_route_does_not_collapse_to_one():
    prior = build_smoothed_route_prior(
        [{"route": "a", "terminal_form": "VERIFIED_PROOF", "verification_status": "VERIFIED"}],
        route_families=["a", "b"],
    )
    assert prior.route_probabilities["a"] < 1.0
    assert prior.route_probabilities["b"] > 0.0


def test_entropy_floor_works():
    outcomes = [{"route": "a", "terminal_form": "VERIFIED_PROOF", "verification_status": "VERIFIED"}] * 20
    prior = build_smoothed_route_prior(
        outcomes,
        route_families=["a", "b", "c"],
        config=SmoothedRoutePriorConfig(min_entropy=0.50),
    )
    assert prior.entropy >= 0.50


def test_repeated_failures_lower_route_score():
    prior = build_smoothed_route_prior(
        [{"route": "a", "terminal_form": "NAMED_OBSTRUCTION", "verification_status": "FAILED"}] * 3,
        route_families=["a", "b"],
    )
    assert prior.route_scores["a"] < prior.route_scores["b"]


def test_probabilities_sum_to_one():
    prior = build_smoothed_route_prior([], route_families=["a", "b"])
    assert abs(sum(prior.route_probabilities.values()) - 1.0) < 1e-9

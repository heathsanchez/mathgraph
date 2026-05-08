from mathgraph.route_policy_scheduler_adapter import match_priority_hint, route_policy_to_priority_hints
from mathgraph.route_policy_v2 import build_route_policy_v2_from_replay
from tests.test_route_policy_v2 import _replay, _signal


def test_scheduler_adapter_produces_priority_hints():
    policy = build_route_policy_v2_from_replay(
        _replay([_signal(verified=3, promoted=1, certificate_yield=1.0, recommendation="strengthen_route")])
    )

    hints = route_policy_to_priority_hints(policy)

    assert hints
    assert hints[0].root_label == "root"
    assert hints[0].constructor_family == "family"
    assert hints[0].evidence["advisory_only"] is True


def test_match_priority_hint_finds_exact_root_constructor_match():
    policy = build_route_policy_v2_from_replay(
        _replay([_signal(verified=3, promoted=1, certificate_yield=1.0, recommendation="strengthen_route")])
    )
    hints = route_policy_to_priority_hints(policy)

    match = match_priority_hint("x=x", "x=x", "root", "family", hints)

    assert match is not None
    assert match.route_key == "root|family|finite_countermodel_search"


def test_match_priority_hint_returns_none_for_missing_root():
    policy = build_route_policy_v2_from_replay(_replay([_signal()]))
    hints = route_policy_to_priority_hints(policy)

    assert match_priority_hint("x=x", "x=x", "other", "family", hints) is None

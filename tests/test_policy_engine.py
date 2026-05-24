from mathgraph.magma_constructors import build_base_constructor_bank
from mathgraph.policy_engine import build_policy_routes
from mathgraph.sat_cache import build_sat_cache


def test_policy_routes_are_advisory_and_include_required_policies():
    equations = ["(x * y) = (y * x)", "(x * y) = x", "(x * y) = y", "x = x"]
    constructors = build_base_constructor_bank(max_n=2, seed=4)
    cache = build_sat_cache(constructors, equations)

    routes = build_policy_routes(constructors, equations, [(0, 1), (0, 2)], cache, route_size=5, seed=4)
    names = {route.policy_name for route in routes}

    assert {"generic", "bandwidth", "family", "hybrid", "oracle_reference"} <= names
    assert all(route.advisory_only for route in routes)
    assert all(not route.can_promote_truth for route in routes)
    assert all(route.selected_constructor_indices for route in routes)


def test_policy_routes_are_deterministic():
    equations = ["(x * y) = (y * x)", "(x * y) = x"]
    constructors = build_base_constructor_bank(max_n=2, seed=4)
    cache = build_sat_cache(constructors, equations)

    a = build_policy_routes(constructors, equations, [(0, 1)], cache, route_size=4, seed=99)
    b = build_policy_routes(constructors, equations, [(0, 1)], cache, route_size=4, seed=99)

    assert [route.to_dict() for route in a] == [route.to_dict() for route in b]

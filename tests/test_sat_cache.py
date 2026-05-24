from mathgraph.magma_constructors import build_base_constructor_bank
from mathgraph.sat_cache import build_sat_cache, evaluate_route, route_recoveries


def test_sat_cache_shape_and_route_recovery():
    equations = ["(x * y) = (y * x)", "(x * y) = x", "(x * y) = y"]
    constructors = build_base_constructor_bank(max_n=2, seed=3)
    cache = build_sat_cache(constructors, equations)

    assert cache.shape == (len(constructors), len(equations))
    recovered = route_recoveries([(0, 1)], cache.sat, list(range(len(constructors))))
    assert recovered == [True]


def test_route_evaluation_true_controls_remain_separate():
    equations = ["(x * y) = (y * x)", "(x * y) = x"]
    constructors = build_base_constructor_bank(max_n=2, seed=3)
    cache = build_sat_cache(constructors, equations)

    result = evaluate_route([(0, 1)], [(0, 0), (1, 1)], cache.sat, list(range(len(constructors))))

    assert result["certificate_yield"] >= 1
    assert result["true_contamination_count"] == 0


def test_vectorized_route_matches_reference():
    equations = ["(x * y) = (y * x)", "(x * y) = x", "x = x"]
    constructors = build_base_constructor_bank(max_n=2, seed=9)
    cache = build_sat_cache(constructors, equations)
    pairs = [(0, 1), (1, 0), (2, 1)]
    route = [0, 1, 2, 3]

    vectorized = route_recoveries(pairs, cache.sat, route)
    reference = []
    for source, target in pairs:
        reference.append(any(bool(cache.sat[idx][source]) and not bool(cache.sat[idx][target]) for idx in route))

    assert vectorized == reference

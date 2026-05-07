from mathgraph.logic_combinations import ConflictPolicy, LogicCombination


def test_logic_combination_readiness_is_strict():
    combo = LogicCombination("lc1", "hybrid", ["aot", "etp"])
    assert not combo.is_ready_for_truth_transfer()
    assert "unsafe" in combo.advisory_warning()
    ready = LogicCombination(
        "lc2",
        "ready",
        ["a", "b"],
        faithfulness_status="MECHANIZED",
        benchmark_status="PASSED",
    )
    assert ready.is_ready_for_truth_transfer()
    assert ConflictPolicy.RECORD_OBSTRUCTION.value == "RECORD_OBSTRUCTION"

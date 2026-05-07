from mathgraph import ConstructorPressure, ObstructionNode


def test_obstruction_node_retains_failure_reason_and_pressure():
    pressure = ConstructorPressure("source_preserving_countermodel", 0.8, "source weakening failed")
    obstruction = ObstructionNode.from_dict(
        {
            "obstruction_id": "o1",
            "failure_reason": "table_does_not_satisfy_derived_source",
            "next_constructor_pressure": pressure.to_dict(),
        }
    )
    assert obstruction.failure_reason == "table_does_not_satisfy_derived_source"
    assert obstruction.next_constructor_pressure["constructor"] == "source_preserving_countermodel"

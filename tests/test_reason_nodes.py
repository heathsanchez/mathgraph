from mathgraph import ReasonNode


def test_reason_node_serializes_with_explanation_template():
    reason = ReasonNode.from_dict({"reason_node_id": "why1", "reason_type": "motif_reason"})
    data = reason.to_dict()
    assert data["reason_node_id"] == "why1"
    assert data["explanation_template"]

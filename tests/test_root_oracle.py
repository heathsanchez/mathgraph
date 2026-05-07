import json

from mathgraph import ObstructionNode, ReasonNode, RootNode, RootNodeOracle


def test_root_oracle_loads_and_explains(tmp_path):
    root = RootNode.from_dict(
        {
            "root_node_id": "root1",
            "canonical_name": "ROOT_PROJECTION_LEFT",
            "table_motif": "projection_left",
            "unique_pairs": 7,
            "unique_tables": 1,
            "unique_motifs": 1,
        }
    )
    reason = ReasonNode.from_dict(
        {"reason_node_id": "reason1", "reason_type": "motif", "table_motif": "projection_left"}
    )
    obstruction = ObstructionNode.from_dict(
        {"obstruction_id": "obs1", "failure_reason": "residual", "table_motif": "projection_left"}
    )
    (tmp_path / "canonical_root_nodes.json").write_text(json.dumps([root.to_dict()]), encoding="utf-8")
    (tmp_path / "reason_nodes.json").write_text(json.dumps([reason.to_dict()]), encoding="utf-8")
    (tmp_path / "obstructions.json").write_text(json.dumps([obstruction.to_dict()]), encoding="utf-8")
    oracle = RootNodeOracle.from_json_dir(tmp_path)
    assert oracle.summary()["root_count"] == 1
    assert oracle.top_roots(1)[0]["canonical_name"] == "ROOT_PROJECTION_LEFT"
    explanation = oracle.explain_root("root1")
    assert explanation["advisory_only"] is True
    assert "certificate pairs" in explanation["explanation"]
    assert oracle.reasons_for_root("root1")
    assert oracle.obstructions_for_root("root1")

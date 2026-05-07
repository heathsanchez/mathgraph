from mathgraph import RootNode, consolidate_root_nodes


def test_root_node_serializes_and_consolidates_projection_aliases():
    roots = [
        RootNode.from_dict(
            {
                "root_node_id": "r1",
                "canonical_name": "left_projection_n2",
                "table_motif": "projection_left",
                "rows": 10,
                "unique_pairs": 5,
                "unique_sources": 3,
                "unique_targets": 4,
                "unique_tables": 1,
                "unique_motifs": 1,
                "load_bearing_score": 8,
            }
        ),
        RootNode.from_dict(
            {
                "root_node_id": "r2",
                "canonical_name": "affine_1_0_0_n2",
                "table_motif": "projection_left",
                "rows": 8,
                "unique_pairs": 4,
                "unique_sources": 2,
                "unique_targets": 3,
                "unique_tables": 1,
                "unique_motifs": 1,
            }
        ),
    ]
    canonical = consolidate_root_nodes(roots)
    assert len(canonical) == 1
    assert canonical[0].canonical_name == "ROOT_PROJECTION_LEFT"
    assert canonical[0].evidence["canonical_root_score"] > 0
    assert canonical[0].to_dict()["aliases"]


def test_root_advice_is_not_truth():
    root = RootNode.from_dict({"canonical_name": "projection_left", "table_motif": "projection_left"})
    assert root.to_dict()["status"] == "candidate"
    assert "terminal_form" not in root.to_dict()

import csv

from mathgraph import LawbookStore, RootNodeOracle
from mathgraph.artifact_warehouse import import_v16_7_root_atlas_dir


def test_import_v167_root_atlas_dir_consolidates_aliases(tmp_path):
    artifact_dir = tmp_path / "v167"
    artifact_dir.mkdir()
    roots = artifact_dir / "root_node_candidates.csv"
    with roots.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["root_node_id", "canonical_name", "table_motif", "rows", "unique_pairs"])
        writer.writeheader()
        writer.writerow({"root_node_id": "r1", "canonical_name": "left_projection_n2", "table_motif": "projection_left", "rows": 4, "unique_pairs": 3})
        writer.writerow({"root_node_id": "r2", "canonical_name": "affine_1_0_0_n2", "table_motif": "projection_left", "rows": 2, "unique_pairs": 2})
    reasons = artifact_dir / "reason_node_candidates.csv"
    with reasons.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["reason_node_id", "reason_type", "table_motif", "reason_score"])
        writer.writeheader()
        writer.writerow({"reason_node_id": "why1", "reason_type": "motif", "table_motif": "projection_left", "reason_score": 5})
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        summary = import_v16_7_root_atlas_dir(artifact_dir, store)
        assert summary["roots"]["imported"] == 1
        assert store.top_roots(1)[0]["canonical_name"] == "ROOT_PROJECTION_LEFT"
        assert store.warehouse_summary()["root_aliases"] >= 1
        assert store.top_reasons(1)[0]["reason_node_id"] == "why1"
        oracle = RootNodeOracle.from_store(store)
        assert oracle.summary()["root_count"] == 1
    finally:
        store.close()

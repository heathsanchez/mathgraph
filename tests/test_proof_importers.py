from pathlib import Path

from mathgraph.lawbook_store import LawbookStore
from mathgraph.proof_importers import (
    discover_true_proof_artifacts,
    import_true_proof_artifacts_to_store,
    load_true_proof_rows,
    normalize_true_proof_row,
)


def test_true_proof_importers_csv_and_aliases(tmp_path):
    row = normalize_true_proof_row({"eq1_idx": "1", "eq2_idx": "2", "route_name": "projection_left"})
    assert row["source_idx"] == 1
    assert row["target_idx"] == 2
    assert row["proof_route"] == "projection_left"

    csv_path = tmp_path / "true_proofs.csv"
    csv_path.write_text(
        "source_idx,target_idx,proof_route,source_basin,target_basin,theorem_name\n"
        "1,2,variable_identification,same,same,thm\n",
        encoding="utf-8",
    )
    assert discover_true_proof_artifacts(tmp_path)[0]["path"] == str(csv_path)
    rows = load_true_proof_rows(csv_path)
    assert rows[0]["theorem_name"] == "thm"

    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        summary = import_true_proof_artifacts_to_store(store, csv_path)
        assert summary["row_count"] == 1
        assert len(store.list_proof_motifs()) == 1
        assert len(store.list_lemma_candidates()) == 1
    finally:
        store.close()

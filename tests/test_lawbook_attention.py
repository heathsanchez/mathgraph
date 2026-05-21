from mathgraph.lawbook_attention import retrieve_lawbook_attention
from mathgraph.lawbook_store import LawbookStore


def test_sparse_attention_retrieves_same_basin_and_explains(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    store.insert_artifact({"artifact_id": "v", "domain": "sair", "basin": "b", "terminal_form": "FINITE_COUNTERMODEL", "trust_level": 100, "boundary_type": "finite_model_checker"})
    store.insert_artifact({"artifact_id": "a", "domain": "sair", "basin": "b", "terminal_form": "ADVISORY", "trust_level": 1, "boundary_type": "advisory"})

    result = retrieve_lawbook_attention(store, {"domain": "sair", "basin": "b"}, max_artifacts=1)

    assert result.artifacts[0]["artifact_id"] == "v"
    assert result.attention_trace[0]["why_retrieved"]
    assert result.attention_trace[0]["verified"] is True
    store.close()


def test_attention_limits_respected(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    for i in range(5):
        store.insert_artifact({"artifact_id": f"a{i}", "domain": "sair", "basin": "b", "terminal_form": "ADVISORY"})
    result = retrieve_lawbook_attention(store, {"domain": "sair", "basin": "b"}, max_artifacts=2)
    assert len(result.artifacts) == 2
    store.close()

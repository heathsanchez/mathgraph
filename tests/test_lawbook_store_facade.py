import tomllib

from mathgraph.lawbook_store import LawbookStore, LawbookStoreStats


def test_lawbook_store_facade_imports_and_compounding_methods_exist(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")

    assert LawbookStoreStats
    for name in (
        "init_compounding_schema",
        "insert_artifact",
        "query_artifacts",
        "list_durable_artifacts",
        "list_advisory_artifacts",
        "count_by_admission_level",
        "record_artifact_reuse",
        "export_manifest",
    ):
        assert hasattr(store, name)


def test_lawbook_store_facade_persists_admission_metadata(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    row = store.insert_artifact(
        {
            "artifact_id": "a1",
            "domain": "demo",
            "claim_id": "claim",
            "terminal_form": "ADVISORY",
            "trust_level": 10,
            "admission_level": "advisory_only",
            "durable": False,
            "artifact_kind": "advisory_route",
            "payload": {"route": "baseline"},
        }
    )

    assert row["admission_level"] == "advisory_only"
    rows = store.query_artifacts(domain="demo")
    assert rows[0]["artifact_id"] == "a1"
    assert store.count_by_admission_level()["advisory_only"] == 1


def test_pyproject_optional_dependencies_parse():
    with open("pyproject.toml", "rb") as handle:
        data = tomllib.load(handle)
    optional = data["project"]["optional-dependencies"]

    assert "dev" in optional
    assert "sair" in optional
    assert "plots" in optional
    assert "all" in optional

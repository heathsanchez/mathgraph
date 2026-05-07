import csv

from mathgraph import LawbookStore
from mathgraph.artifact_warehouse import import_v16_6_2_elevated_false_dir


def test_import_v1662_elevated_false_dir(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    path = artifact_dir / "elevated_derived_false_certificates_v16_6_2.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "certificate_id",
                "source_id",
                "target_id",
                "table_hash",
                "table",
                "witness",
                "derivation_rule",
                "elevation_method",
                "verification_status",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "certificate_id": "cert1",
                "source_id": "10",
                "target_id": "20",
                "table_hash": "hash1",
                "table": "[[0, 1], [1, 0]]",
                "witness": "{\"x\": 0, \"y\": 1}",
                "derivation_rule": "false_target_strengthening",
                "elevation_method": "seed_table_replay",
                "verification_status": "FINITE_VERIFIED",
            }
        )
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        summary = import_v16_6_2_elevated_false_dir(artifact_dir, store)
        assert summary["refutations"]["imported"] == 1
        hit = store.query_refutation(10, 20)
        assert hit["table_hash"] == "hash1"
        assert hit["verification_status"] == "FINITE_VERIFIED"
        assert hit["derivation_rule"] == "false_target_strengthening"
    finally:
        store.close()

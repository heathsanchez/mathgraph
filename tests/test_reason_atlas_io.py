from mathgraph.contact_promotion import ContactPromotionEngine
from mathgraph.reason_atlas_io import (
    load_probe_results_csv,
    read_json_field,
    write_csv,
    write_json_field,
)


def _engine() -> ContactPromotionEngine:
    engine = ContactPromotionEngine()
    engine.ingest_probe_rows(
        [
            {
                "probe_id": "p1",
                "level": "L2_STRICT_CONTACT",
                "shape": "shape_a",
                "theorem_decl": "Nat.good",
                "repair_strategy": "exact_existing",
                "strict_success": "true",
                "marker_start": "true",
                "marker_ok": "true",
                "marker_end": "true",
            },
            {
                "probe_id": "p2",
                "shape": "shape_a",
                "theorem_decl": "Nat.bad",
                "repair_strategy": "exact_existing",
                "strict_success": "false",
                "failure_class": "type_mismatch",
            },
        ]
    )
    return engine


def test_csv_roundtrip_for_seeds(tmp_path):
    path = tmp_path / "seeds.csv"
    write_csv(path, _engine().to_contact_seed_rows())
    rows = load_probe_results_csv(path)
    assert rows[0]["kind"] == "STRICT_CONTACT_SEED"


def test_csv_roundtrip_for_obstructions(tmp_path):
    path = tmp_path / "obstructions.csv"
    write_csv(path, _engine().to_obstruction_rows())
    rows = load_probe_results_csv(path)
    assert rows[0]["failure_class"] == "type_mismatch"


def test_csv_roundtrip_for_promoted_laws(tmp_path):
    engine = ContactPromotionEngine()
    rows = []
    for idx in range(3):
        rows.append(
            {
                "probe_id": str(idx),
                "level": "L2_STRICT_CONTACT",
                "shape": "shape_a",
                "theorem_decl": f"Nat.good{idx}",
                "repair_strategy": "exact_existing",
                "strict_success": "true",
                "marker_start": "true",
                "marker_ok": "true",
                "marker_end": "true",
            }
        )
    engine.ingest_probe_rows(rows)
    path = tmp_path / "laws.csv"
    write_csv(path, engine.to_route_law_rows())
    assert load_probe_results_csv(path)[0]["law_kind"] == "PROMOTED_ROUTE_LAW"


def test_json_fields_survive_roundtrip():
    payload = {"a": [1, 2], "b": True}
    encoded = write_json_field(payload)
    assert read_json_field(encoded) == payload

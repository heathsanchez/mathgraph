from pathlib import Path

from mathgraph.constructor_atlas import build_constructor_atlas, export_constructor_atlas
from mathgraph.lawbook_accumulator import connect_lawbook, seed_synthetic_lawbook
from mathgraph.reason_atlas import build_reason_atlas, export_reason_atlas


def test_reason_and_constructor_atlas_from_synthetic_rows(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    conn = connect_lawbook(db)
    seed_synthetic_lawbook(conn)
    constructor = build_constructor_atlas(conn)
    reason = build_reason_atlas(conn)
    conn.close()
    assert constructor["verified_constructor_total"] == 1
    assert constructor["constructor_atlas"][0]["best_template_id"] == "exact_existing"
    assert reason["reason_atlas"][0]["verified_constructor_count"] == 1
    out = tmp_path / "exports"
    cpaths = export_constructor_atlas(db, out)
    rpaths = export_reason_atlas(db, out)
    assert Path(cpaths["json"]).exists()
    assert Path(cpaths["obstructions"]).exists()
    assert Path(rpaths["json"]).exists()
    assert Path(rpaths["roots"]).exists()

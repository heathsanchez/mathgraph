from pathlib import Path

from mathgraph.digest_exports import export_all_digest_artifacts, export_lawbook_summary
from mathgraph.digest_scheduler import export_next_pack_config, propose_next_packs
from mathgraph.lawbook_accumulator import connect_lawbook, seed_synthetic_lawbook


def test_digest_exports_and_scheduler(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    conn = connect_lawbook(db)
    seed_synthetic_lawbook(conn)
    conn.close()
    out = tmp_path / "exports"
    summary = export_lawbook_summary(db, out, html=True)
    assert Path(summary["json"]).exists()
    assert Path(summary["markdown"]).exists()
    assert Path(summary["html"]).exists()
    packs = propose_next_packs(db, strategy="highest_obstruction_count_first")
    assert packs and packs[0]["status"] == "PENDING"
    sched = export_next_pack_config(db, out)
    assert Path(sched["next_pack_config"]).exists()
    all_paths = export_all_digest_artifacts(db, out / "all")
    assert all_paths

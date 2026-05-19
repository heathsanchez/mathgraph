from mathgraph.lawbook_accumulator import *


def test_stable_id_and_schema_and_upsert(tmp_path):
    assert stable_id("x", "a") == stable_id("x", "a")
    db = tmp_path / "lawbook.sqlite"
    conn = connect_lawbook(db)
    initialize_lawbook_schema(conn)
    seed_synthetic_lawbook(conn)
    seed_synthetic_lawbook(conn)
    summary = summarize_lawbook(conn)
    assert summary["total_runs"] == 1
    assert summary["total_targets"] == 1
    assert summary["accepted_targets"] == 1
    assert summary["verified_constructors"] == 1
    assert summary["obstructions"] == 1
    assert "MathGraph Digest Lawbook Summary" in render_lawbook_summary_markdown(summary)
    conn.close()

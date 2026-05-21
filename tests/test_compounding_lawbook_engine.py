import json
import sqlite3

from mathgraph.compounding_lawbook_engine import run_compounding_lawbook_engine


def test_compounding_lawbook_engine_fallback_runs(tmp_path):
    report = run_compounding_lawbook_engine(tmp_path / "run", seeds=(0,), max_tasks=8, fallback_smoke=True)
    assert report.fallback_mode is True
    assert report.advisory_boundary_preserved is True
    assert report.outputs
    assert (tmp_path / "run" / "lawbook.sqlite").exists()
    assert (tmp_path / "run" / "compounding_report.json").exists()
    data = json.loads((tmp_path / "run" / "compounding_report.json").read_text())
    assert "baseline_yield" in data
    conn = sqlite3.connect(tmp_path / "run" / "lawbook.sqlite")
    try:
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] >= 1
        assert conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= 1
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] >= 1
        assert conn.execute("SELECT COUNT(*) FROM compounding_reasons").fetchone()[0] >= 1
    finally:
        conn.close()

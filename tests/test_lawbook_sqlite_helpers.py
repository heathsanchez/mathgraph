from mathgraph.lawbook import init_lawbook, upsert_episode_summary, upsert_run_summary, write_dataframe


def test_sqlite_lawbook_initializes_required_tables(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    conn = init_lawbook(db)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert {"runs", "episodes", "constructors", "policy_eval", "finite_countermodels", "obstruction_atlas", "residual_queue"} <= tables


def test_write_dataframe_is_safe_for_empty_rows(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    conn = init_lawbook(db)

    assert write_dataframe(conn, "empty_aux_table", []) == 0
    assert write_dataframe(conn, "policy_eval", []) == 0
    conn.close()


def test_sqlite_lawbook_writes_canonical_rows(tmp_path):
    db = tmp_path / "lawbook.sqlite"
    conn = init_lawbook(db)
    upsert_run_summary(conn, "run1", {"ok": True})
    upsert_episode_summary(conn, "run1", 0, {"residual_count": 2})
    write_dataframe(conn, "policy_eval", [{"run_id": "run1", "episode": 0, "policy": "generic", "yield_rate": 1.0}])

    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM policy_eval").fetchone()[0] == 1
    conn.close()

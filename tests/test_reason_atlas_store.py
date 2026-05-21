from mathgraph.reason_atlas_store import (
    ReasonAtlasEntry,
    ReasonAtlasEntryKind,
    ReasonAtlasEntryStatus,
    ReasonAtlasFeedbackEvent,
    ReasonAtlasFeedbackOutcome,
    ReasonAtlasQuery,
    ReasonAtlasStore,
)


def _entry(entry_id="e1"):
    return ReasonAtlasEntry(entry_id=entry_id, kind=ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA, name="move_recolor", atoms=["move", "recolor"], pattern="move;recolor", support=1)


def test_store_lifecycle_and_queries(tmp_path):
    store = ReasonAtlasStore(tmp_path / "atlas.sqlite")
    store.initialize()
    entry = store.upsert_entry(_entry())
    assert store.get_entry(entry.entry_id).name == "move_recolor"
    assert store.query(ReasonAtlasQuery(kind=ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA)).total_count == 1
    assert store.query(ReasonAtlasQuery(atom="move")).total_count == 1
    store.close()


def test_feedback_recompute_and_exports(tmp_path):
    store = ReasonAtlasStore(tmp_path / "atlas.sqlite")
    store.initialize()
    entry = store.upsert_entry(_entry())
    store.add_feedback(ReasonAtlasFeedbackEvent.create(entry.entry_id, ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS))
    rescored = store.recompute_entry_scores(entry.entry_id)
    assert rescored.priority_score > 0
    atlas_path = tmp_path / "atlas.jsonl"
    queue_path = tmp_path / "queue.jsonl"
    store.export_reason_atlas_jsonl(atlas_path)
    rows = store.export_next_queue_rows(queue_path)
    assert atlas_path.exists()
    assert rows and rows[0]["advisory_only"] is True


def test_retire_supersede_stats_and_boundary(tmp_path):
    store = ReasonAtlasStore(tmp_path / "atlas.sqlite")
    store.initialize()
    e1 = store.upsert_entry(_entry("e1"))
    e2 = store.upsert_entry(_entry("e2"))
    store.retire_entry(e1.entry_id, "stale")
    store.supersede_entry(e2.entry_id, "e3", "better")
    assert store.get_entry("e1").status == ReasonAtlasEntryStatus.RETIRED
    stats = store.stats()
    assert stats.entry_count == 2
    assert stats.advisory_boundary_ok is True

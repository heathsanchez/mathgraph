from mathgraph.reason_atlas_feedback_loop import ReasonAtlasFeedbackLoop
from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind


def test_loop_ingest_feedback_tasks_and_export(tmp_path):
    loop = ReasonAtlasFeedbackLoop(tmp_path / "atlas.sqlite")
    entry = ReasonAtlasEntry("e1", ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA, "schema", atoms=["move"], pattern="move")
    loop.ingest_entries([entry])
    before = loop.store.get_entry("e1").priority_score
    loop.record_transfer_result("e1", True, residual_before=10, residual_after=7)
    loop.record_verifier_result("e1", True)
    loop.record_obstruction("e1", "type_mismatch")
    loop.rescore()
    after = loop.store.get_entry("e1").priority_score
    assert after != before
    tasks = loop.next_advisory_tasks(limit=5)
    assert tasks and tasks[0]["advisory_only"] is True
    outputs = loop.export_all(tmp_path / "exports")
    assert outputs["entries"]
    loop.close()

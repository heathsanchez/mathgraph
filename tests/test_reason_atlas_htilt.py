from mathgraph.reason_atlas_htilt import (
    ReasonAtlasHTiltConfig,
    apply_htilt_scores_to_reason_atlas,
    build_route_telemetry_from_reason_atlas,
    estimate_htilt_for_reason_atlas,
    export_htilt_augmented_queue,
    score_reason_entry_with_htilt,
)
from mathgraph.reason_atlas_store import (
    ReasonAtlasEntry,
    ReasonAtlasEntryKind,
    ReasonAtlasFeedbackEvent,
    ReasonAtlasFeedbackOutcome,
    ReasonAtlasQuery,
    ReasonAtlasStore,
)


def test_reason_atlas_htilt_builds_telemetry_and_estimate(tmp_path):
    store = _store(tmp_path)

    ledger = build_route_telemetry_from_reason_atlas(store)
    estimate = estimate_htilt_for_reason_atlas(store)

    assert ledger.events
    assert estimate.advisory is True
    assert estimate.state_estimates
    assert any(state.state == "entry-good" for state in estimate.state_estimates)


def test_htilt_maps_scores_and_updates_entries(tmp_path):
    store = _store(tmp_path)
    before = store.get_entry("entry-good")
    estimate = estimate_htilt_for_reason_atlas(store)

    score = score_reason_entry_with_htilt(before, estimate, ReasonAtlasHTiltConfig())
    report = apply_htilt_scores_to_reason_atlas(store, estimate, ReasonAtlasHTiltConfig())
    after = store.get_entry("entry-good")

    assert score.entry_id == "entry-good"
    assert report.scored_entry_count >= 2
    assert after.priority_score != before.priority_score
    assert after.metadata["htilt_estimate_id"] == estimate.estimate_id
    assert after.advisory_only is True
    assert after.verifier_promoted is False


def test_htilt_augmented_queue_is_advisory(tmp_path):
    store = _store(tmp_path)
    estimate = estimate_htilt_for_reason_atlas(store)
    apply_htilt_scores_to_reason_atlas(store, estimate)

    rows = export_htilt_augmented_queue(store, estimate, tmp_path / "queue.jsonl", limit=10)

    assert rows
    assert all(row["advisory_only"] is True for row in rows)
    assert all("terminal_form" not in row for row in rows)
    assert any("htilt_survivor_pi" in row for row in rows)


def test_priority_ordering_can_change_with_survivor_pressure(tmp_path):
    store = _store(tmp_path)
    before = [entry.entry_id for entry in store.query(ReasonAtlasQuery(limit=10)).entries]
    estimate = estimate_htilt_for_reason_atlas(store)
    apply_htilt_scores_to_reason_atlas(store, estimate, ReasonAtlasHTiltConfig(base_priority_weight=0.0, survivor_weight=20.0))
    after = [entry.entry_id for entry in store.query(ReasonAtlasQuery(limit=10)).entries]

    assert set(before) == set(after)
    assert store.stats().advisory_boundary_ok is True


def _store(tmp_path):
    store = ReasonAtlasStore(tmp_path / "atlas.sqlite")
    store.initialize()
    good = ReasonAtlasEntry(
        "entry-good",
        ReasonAtlasEntryKind.CONSTRUCTOR_HINT,
        "good",
        atoms=["constructor:left_projection_n2"],
        support=5,
        priority_score=1.0,
    )
    bad = ReasonAtlasEntry(
        "entry-bad",
        ReasonAtlasEntryKind.CONSTRUCTOR_HINT,
        "bad",
        atoms=["constructor:constant_n2_0"],
        support=2,
        priority_score=1.0,
    )
    store.upsert_entry(good)
    store.upsert_entry(bad)
    store.add_feedback(ReasonAtlasFeedbackEvent.create("entry-good", ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS, residual_delta=2))
    store.add_feedback(ReasonAtlasFeedbackEvent.create("entry-good", ReasonAtlasFeedbackOutcome.VERIFIER_SUCCESS))
    store.add_feedback(ReasonAtlasFeedbackEvent.create("entry-bad", ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE))
    store.add_feedback(ReasonAtlasFeedbackEvent.create("entry-bad", ReasonAtlasFeedbackOutcome.OBSTRUCTION_FOUND))
    return store

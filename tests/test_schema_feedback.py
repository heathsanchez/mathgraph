from dataclasses import replace

from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind, ReasonAtlasFeedbackEvent, ReasonAtlasFeedbackOutcome
from mathgraph.schema_feedback import (
    apply_feedback_to_entry,
    compute_obstruction_penalty,
    compute_priority_score,
    compute_transfer_rate,
    compute_verifier_rate,
    oracle_fraction_captured,
    residual_compression_delta,
    should_deprecate_entry,
    should_promote_advisory_entry,
)


def _entry():
    return ReasonAtlasEntry("e", ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA, "schema")


def test_rates_and_penalties():
    entry = replace(_entry(), transfer_successes=2, transfer_failures=1, verifier_successes=1, verifier_failures=1, obstruction_count=3)
    assert compute_transfer_rate(entry) == 2 / 3
    assert compute_verifier_rate(entry) == 0.5
    assert compute_obstruction_penalty(entry) == 3


def test_residual_and_oracle_helpers():
    assert residual_compression_delta(10, 4) == 6
    assert abs(oracle_fraction_captured(0.2, 0.6, 1.0) - 0.5) < 1e-9


def test_priority_changes_with_feedback():
    entry = _entry()
    success = apply_feedback_to_entry(entry, ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS))
    failure = entry
    for _ in range(3):
        failure = apply_feedback_to_entry(failure, ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE))
    assert compute_priority_score(success) > compute_priority_score(entry)
    assert compute_priority_score(failure) <= compute_priority_score(success)


def test_deletion_feedback_changes_value():
    hurt = apply_feedback_to_entry(_entry(), ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.DELETION_HURT))
    safe = apply_feedback_to_entry(_entry(), ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.DELETION_SAFE))
    assert compute_priority_score(hurt) > compute_priority_score(safe)


def test_deprecate_and_promote_remain_advisory():
    entry = _entry()
    for _ in range(4):
        entry = apply_feedback_to_entry(entry, ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE))
    assert should_deprecate_entry(entry)
    promoted = apply_feedback_to_entry(_entry(), ReasonAtlasFeedbackEvent.create("e", ReasonAtlasFeedbackOutcome.TRANSFER_SUCCESS))
    assert should_promote_advisory_entry(replace(promoted, residual_compression_total=10.0))
    assert promoted.advisory_only is True

from mathgraph.sair_v17_terminal_boundary import (
    decide_terminal_boundary,
    is_terminal_true_record,
)


def test_lean_verified_true_is_terminal():
    record = {
        "terminal_form": "VERIFIED_PROOF",
        "certificate_status": "lean_verified",
        "official_true": True,
    }
    decision = decide_terminal_boundary(record)
    assert decision.terminal_safe
    assert decision.may_update_truth_mask
    assert is_terminal_true_record(record)


def test_named_obstruction_is_not_truth_terminal():
    record = {
        "terminal_form": "NAMED_OBSTRUCTION",
        "certificate_status": "named_obstruction_pattern",
    }
    decision = decide_terminal_boundary(record)
    assert not decision.terminal_safe
    assert not decision.may_update_truth_mask


def test_official_false_verified_row_rejected():
    record = {
        "terminal_form": "VERIFIED_PROOF",
        "certificate_status": "lean_verified",
        "official_true": False,
    }
    decision = decide_terminal_boundary(record)
    assert not decision.terminal_safe
    assert not decision.may_update_truth_mask

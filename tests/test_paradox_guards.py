from mathgraph.paradox_guards import (
    GuardSeverity,
    aot_complex_term_guard,
    semantic_embedding_artifact_guard,
    set_collapse_guard,
)


def test_aot_complex_term_guard_blocks_patterns():
    guard = aot_complex_term_guard()
    result = guard.check_text("unguarded_definite_description(the F)")
    assert result.status == "BLOCK"
    assert guard.is_blocking_result(result)


def test_guard_presets_construct():
    assert semantic_embedding_artifact_guard().severity is GuardSeverity.WARNING
    assert set_collapse_guard().check_text("plain safe text").status == "PASS"

from mathgraph.interpretation_choice import ChoicePointStatus, InterpretationChoicePoint


def test_interpretation_choice_point_resolution():
    open_choice = InterpretationChoicePoint("ch0", "k", None, "world")
    assert not open_choice.has_selected_reading()
    assert not open_choice.is_resolved()
    selected = InterpretationChoicePoint(
        "ch1",
        "k",
        None,
        "world",
        candidate_readings=[{"id": "r"}],
        selected_reading_id="r",
        status=ChoicePointStatus.SELECTED,
    )
    assert selected.has_selected_reading()
    assert selected.is_resolved()
    assert selected.summary()["candidate_count"] == 1

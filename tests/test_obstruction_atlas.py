from mathgraph.obstruction_atlas import failed_constructor_rules, make_obstruction_name, residual_queue, summarize_obstructions


def test_obstruction_name_shape():
    assert make_obstruction_name("projection_pressure", "fresh_escape", "pqir") == "projection_pressure__fresh_escape__pqir_unresolved"


def test_summarize_obstructions_is_advisory():
    records = summarize_obstructions(
        [
            {"pair_id": "p1", "basin": "projection_pressure", "deep_ir_candidate": "shallow", "failed_constructor": "constant"},
            {"pair_id": "p2", "basin": "projection_pressure", "deep_ir_candidate": "shallow", "failed_constructor": "constant"},
        ],
        stage="pqir",
    )

    assert len(records) == 1
    rec = records[0]
    assert rec.status == "named_obstruction_advisory"
    assert rec.advisory_only is True
    assert rec.can_promote_truth is False
    assert rec.support_count == 2
    assert rec.failed_constructor_rules == ("constant:2",)


def test_residual_queue_and_failed_rules():
    records = summarize_obstructions([{"basin": "b", "deep_ir_candidate": "d", "constructor_family": "prior"}])
    queue = residual_queue(records)

    assert failed_constructor_rules([{"constructor_family": "prior"}]) == ["prior:1"]
    assert queue[0]["task_kind"] == "obstruction_analysis"
    assert queue[0]["can_promote_truth"] is False

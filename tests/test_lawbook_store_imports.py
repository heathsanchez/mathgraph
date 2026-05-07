from mathgraph import KernelOracle, LawbookStore, ObstructionNode, ReasonNode, RootNode


def test_import_refutation_preserves_table_witness_and_derivation(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.import_refutations(
            [
                {
                    "certificate_id": "f1",
                    "source_idx": 1,
                    "target_idx": 2,
                    "source": "x = x",
                    "target": "x = y",
                    "table_hash": "tableabc",
                    "table": [[0, 1], [1, 0]],
                    "witness": {"x": 0, "y": 1},
                    "derivation_rule": "false_target_strengthening",
                    "elevation_method": "seed_table_replay",
                    "verification_status": "FINITE_VERIFIED",
                }
            ]
        )
        hit = store.query_refutation(1, 2)
        assert hit["table_hash"] == "tableabc"
        assert hit["table"] == [[0, 1], [1, 0]]
        assert hit["witness"] == {"x": 0, "y": 1}
        assert hit["derivation_rule"] == "false_target_strengthening"
        assert hit["elevation_method"] == "seed_table_replay"
        answer = KernelOracle(store).query("1", "2")
        assert answer.status == "REFUTED"
        assert answer.terminal_form == "FINITE_COUNTERMODEL"
    finally:
        store.close()


def test_import_roots_reasons_obstructions_are_advisory(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.import_roots([RootNode.from_dict({"root_node_id": "r1", "canonical_name": "ROOT_PROJECTION_LEFT", "load_bearing_score": 4})])
        store.import_reasons([ReasonNode.from_dict({"reason_node_id": "why1", "reason_score": 3})])
        store.import_obstructions([ObstructionNode.from_dict({"obstruction_id": "o1", "failure_reason": "blocked", "obstruction_pressure_score": 2})])
        assert store.top_roots(1)[0]["root_node_id"] == "r1"
        assert store.explain_root("r1")["advisory_only"] is True
        assert store.explain_reason("why1")["advisory_only"] is True
        assert store.explain_obstruction("o1")["advisory_only"] is True
    finally:
        store.close()

from mathgraph import LawbookStore


def test_v168_schema_initializes_and_summary(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.init_schema()
        summary = store.summary()
        assert summary["warehouse"]["claims"] == 0
        assert summary["warehouse"]["roots"] == 0
        assert "truth_boundary" in summary
    finally:
        store.close()


def test_trust_provenance_terminal_status_are_orthogonal_in_store(tmp_path):
    store = LawbookStore(tmp_path / "lawbook.sqlite")
    try:
        store.import_claims(
            [
                {
                    "claim_id": "c1",
                    "source_idx": 0,
                    "target_idx": 1,
                    "terminal_form": "FINITE_COUNTERMODEL",
                    "verification_status": "FINITE_VERIFIED",
                    "trust_level": "FINITE_VERIFIED",
                    "provenance_type": "DERIVED",
                }
            ]
        )
        hit = store.query_claim(0, 1)
        assert hit["terminal_form"] == "FINITE_COUNTERMODEL"
        assert hit["verification_status"] == "FINITE_VERIFIED"
        assert hit["trust_level"] == "FINITE_VERIFIED"
        assert hit["provenance_type"] == "DERIVED"
    finally:
        store.close()

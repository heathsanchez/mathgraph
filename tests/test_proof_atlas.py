from mathgraph.proof_atlas import build_proof_atlas_from_true_rows


def test_build_proof_atlas_groups_true_rows():
    rows = [
        {"source_idx": 1, "target_idx": 2, "proof_route": "variable_identification", "source_basin": "same", "target_basin": "same"},
        {"source_idx": 3, "target_idx": 4, "proof_route": "variable_identification", "source_basin": "same", "target_basin": "same"},
        {"source_idx": 5, "target_idx": 6, "proof_route": "projection_left", "source_basin": "proj", "target_basin": "collapse"},
    ]
    atlas = build_proof_atlas_from_true_rows(rows)
    assert len(atlas.proof_motifs) == 2
    assert atlas.top_motifs(1)[0].support_count == 2
    assert len(atlas.lemma_candidates) == 2
    assert atlas.top_lemma_candidates(1)[0].expected_covered_claims >= 1
    assert atlas.verified_lemmas() == []

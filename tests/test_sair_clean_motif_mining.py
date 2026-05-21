import json

import pandas as pd

from mathgraph.sair_clean_motif_mining import (
    deduplicate_subsumed_motifs,
    mine_clean_constructor_motifs,
    motif_to_reason_atlas_entry,
    score_clean_motifs,
)


def _clean_df():
    rows = [
        {"task_id": "a", "batch_id": "b1", "atoms_json": json.dumps(["constructor:left_projection_n2", "constructor_family:projection", "basin:projection_pressure", "carrier:n2"])},
        {"task_id": "b", "batch_id": "b1", "atoms_json": json.dumps(["constructor:left_projection_n2", "constructor_family:projection", "basin:projection_pressure", "carrier:n2"])},
        {"task_id": "c", "batch_id": "b2", "atoms_json": json.dumps(["constructor:right_projection_n2", "constructor_family:projection", "basin:projection_pressure", "carrier:n2"])},
    ]
    return pd.DataFrame(rows)


def test_motifs_mined_from_clean_rows_only():
    motifs = mine_clean_constructor_motifs(_clean_df())
    assert not motifs.empty
    assert all("unknown" not in row for row in motifs["atoms_json"])


def test_score_lift_and_cross_batch():
    clean = _clean_df()
    motifs = score_clean_motifs(clean, mine_clean_constructor_motifs(clean))
    assert "lift" in motifs.columns
    assert motifs["score"].max() > 0


def test_subsumed_deduplication():
    clean = _clean_df()
    motifs = score_clean_motifs(clean, mine_clean_constructor_motifs(clean))
    deduped = deduplicate_subsumed_motifs(motifs)
    assert len(deduped) <= len(motifs)


def test_reason_atlas_entry_advisory():
    clean = _clean_df()
    motifs = score_clean_motifs(clean, mine_clean_constructor_motifs(clean))
    entry = motif_to_reason_atlas_entry(motifs.iloc[0].to_dict())
    assert entry["advisory_only"] is True
    assert entry["verifier_promoted"] is False
    assert entry["kind"] == "CONSTRUCTOR_HINT"

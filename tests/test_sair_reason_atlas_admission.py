import json

import pandas as pd

from mathgraph.sair_reason_atlas_admission import (
    SAIRReasonAtlasAdmissionConfig,
    admit_clean_motifs_to_reason_atlas,
    clean_motif_to_reason_atlas_entry,
    load_sair_reason_atlas_priors,
)


def _motifs():
    return pd.DataFrame([
        {"motif_id": "m1", "atoms_json": json.dumps(["constructor:left_projection_n2", "constructor_family:projection", "basin:projection_pressure", "carrier:n2"]), "support": 3, "score": 5.0, "advisory_only": True},
        {"motif_id": "m2", "atoms_json": json.dumps(["constructor:constant_n2_0", "constructor_family:constant"]), "support": 1, "score": 0.2, "advisory_only": True},
    ])


def test_clean_motif_converts_to_advisory_entry():
    entry = clean_motif_to_reason_atlas_entry(_motifs().iloc[0].to_dict())
    assert entry.advisory_only is True
    assert entry.verifier_promoted is False
    assert "terminal_form" not in entry.to_dict()
    assert entry.metadata["terminal_form"] == "ADVISORY_ONLY"


def test_admission_dedup_and_priors(tmp_path):
    cfg = SAIRReasonAtlasAdmissionConfig(tmp_path / "ra.sqlite")
    r1 = admit_clean_motifs_to_reason_atlas(_motifs(), cfg)
    assert r1.admitted_entries == 1
    assert r1.rejected_low_quality == 1
    r2 = admit_clean_motifs_to_reason_atlas(_motifs(), cfg)
    assert r2.duplicate_entries >= 1
    priors = load_sair_reason_atlas_priors(cfg.db_path)
    assert not priors.empty
    assert "constructor:left_projection_n2" in priors.iloc[0]["atoms_json"]


def test_stronger_motif_supersedes(tmp_path):
    cfg = SAIRReasonAtlasAdmissionConfig(tmp_path / "ra.sqlite")
    admit_clean_motifs_to_reason_atlas(_motifs().head(1), cfg)
    stronger = _motifs().head(1).copy()
    stronger.loc[0, "support"] = 10
    stronger.loc[0, "score"] = 15.0
    report = admit_clean_motifs_to_reason_atlas(stronger, cfg)
    assert report.superseded_entries == 1


def test_boundary_violation_rejected(tmp_path):
    bad = _motifs().head(1).copy()
    bad.loc[0, "terminal_form"] = "VERIFIED_PROOF"
    report = admit_clean_motifs_to_reason_atlas(bad, SAIRReasonAtlasAdmissionConfig(tmp_path / "ra.sqlite"))
    assert report.rejected_boundary_violation == 1

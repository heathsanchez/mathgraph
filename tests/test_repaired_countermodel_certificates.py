from pathlib import Path

import pandas as pd

from mathgraph.repaired_countermodel_certificates import (
    build_repaired_countermodel_certificates,
    deduplicate_repaired_certificates,
    summarize_repaired_certificate_families,
    validate_repaired_certificate_boundary,
    write_repaired_certificate_lawbook,
)


def _repair_dir(tmp_path: Path) -> Path:
    root = tmp_path / "repair"
    root.mkdir()
    rows = [
        {
            "repair_id": "repair:0:ctor:pressure_descent",
            "pair_id": "p0",
            "constructor_id": "ctor",
            "family": "projection_completion_right",
            "n": 2,
            "source_equation": "(x * y) = x",
            "target_equation": "x = y",
            "repaired_table_hash": "h0",
            "repaired_table": [[0, 0], [1, 1]],
            "eq1_holds": True,
            "eq2_violated": True,
            "recovered": True,
            "finite_checked": True,
            "witness": {"x": 0, "y": 1},
            "trace": {"repair_id": "repair:0:ctor:pressure_descent", "target_violation_preserved": True, "started_source_violations": 2, "final_source_violations": 0},
        },
        {
            "repair_id": "repair:1:ctor:pressure_descent",
            "pair_id": "p1",
            "constructor_id": "ctor",
            "family": "projection_completion_right",
            "n": 2,
            "source_equation": "(x * y) = x",
            "target_equation": "x = y",
            "repaired_table_hash": "h1",
            "repaired_table": [[0, 1], [0, 1]],
            "eq1_holds": False,
            "eq2_violated": True,
            "recovered": False,
            "finite_checked": True,
            "witness": {"x": 0, "y": 1},
            "trace": {"repair_id": "repair:1:ctor:pressure_descent", "target_violation_preserved": True, "started_source_violations": 2, "final_source_violations": 2},
        },
    ]
    pd.DataFrame(rows).to_csv(root / "source_law_repair_results.csv", index=False)
    pd.DataFrame([row["trace"] for row in rows]).to_csv(root / "source_law_repair_traces.csv", index=False)
    pd.DataFrame([{"pair_id": "p0", "source_eq_idx": 0, "target_eq_idx": 1, "microbasin_key": "m0", "basin": "b", "deep_ir_candidate": "d"}]).to_csv(root / "residual_conditioned_pair_specs.csv", index=False)
    return root


def test_accepted_repaired_certificate_requires_finite_checked_source_and_target(tmp_path: Path):
    certs, rejected = build_repaired_countermodel_certificates(_repair_dir(tmp_path))
    assert len(certs) == 1
    assert len(rejected) == 1
    row = certs.iloc[0]
    assert row["terminal_form"] == "FINITE_COUNTERMODEL"
    assert row["trust_level"] == "FINITE_VERIFIED"
    assert bool(row["finite_checked"]) and bool(row["eq1_holds"]) and bool(row["eq2_violated"])


def test_rejected_rows_cannot_promote_truth(tmp_path: Path):
    _certs, rejected = build_repaired_countermodel_certificates(_repair_dir(tmp_path))
    assert not rejected["can_promote_truth"].map(bool).any()
    assert rejected["advisory_only"].map(bool).all()


def test_deduplication_removes_duplicate_pair_table_witness(tmp_path: Path):
    certs, _rejected = build_repaired_countermodel_certificates(_repair_dir(tmp_path))
    doubled = pd.concat([certs, certs], ignore_index=True)
    unique, dupes = deduplicate_repaired_certificates(doubled)
    assert len(unique) == 1
    assert len(dupes) == 1


def test_family_summary_groups_by_family_and_strategy(tmp_path: Path):
    certs, _rejected = build_repaired_countermodel_certificates(_repair_dir(tmp_path))
    summary = summarize_repaired_certificate_families(certs)
    assert len(summary) == 1
    assert summary.iloc[0]["source_family"] == "projection_completion_right"
    assert summary.iloc[0]["repair_strategy"] == "pressure_descent"


def test_boundary_validation_catches_unsafe_accepted_rows(tmp_path: Path):
    certs, rejected = build_repaired_countermodel_certificates(_repair_dir(tmp_path))
    bad = certs.copy()
    bad.loc[bad.index[0], "eq1_holds"] = False
    boundary = validate_repaired_certificate_boundary(bad, rejected)
    assert boundary["boundary_preserved"] is False
    assert boundary["unsafe_accepted_count"] == 1


def test_write_repaired_certificate_lawbook_writes_artifacts(tmp_path: Path):
    certs, rejected = build_repaired_countermodel_certificates(_repair_dir(tmp_path))
    summary = summarize_repaired_certificate_families(certs)
    artifacts = write_repaired_certificate_lawbook(certs, rejected, summary, tmp_path / "out")
    assert Path(artifacts["repaired_countermodel_certificates.csv"]).exists()
    assert Path(artifacts["repaired_countermodel_lawbook.sqlite"]).exists()

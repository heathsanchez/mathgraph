from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from mathgraph.sair_stage2_end_to_end import (
    EXPECTED_ARTIFACTS,
    SairStage2EndToEndConfig,
    _build_trust_audit,
    classify_sair_stage2,
    run_sair_stage2_end_to_end,
)


def _fake_breakthrough(out_dir: str) -> dict:
    root = Path(out_dir)
    cert_dir = root / "02_active_residual_discovery" / "repaired_countermodel_certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "certificate_id": "cert_1",
                "source_eq_idx": 0,
                "target_eq_idx": 1,
                "source_equation": "x=x",
                "target_equation": "x*y=x",
                "terminal_form": "FINITE_COUNTERMODEL",
                "trust_level": "FINITE_VERIFIED",
                "carrier_size": 2,
                "table_hash": "abc",
                "witness": '{"x":0,"y":1}',
                "finite_checked": True,
                "eq1_holds": True,
                "eq2_violated": True,
                "source_family": "projection_exception_left",
                "repair_strategy": "pressure_descent",
            }
        ]
    ).to_csv(cert_dir / "repaired_countermodel_certificates.csv", index=False)
    (cert_dir / "repaired_countermodel_manifest.json").write_text(json.dumps({"certificate_count": 1, "unique_pair_count": 1}), encoding="utf-8")
    active_dir = root / "02_active_residual_discovery"
    pd.DataFrame([{"obstruction_name": "demo_obstruction", "microbasin_key": "demo"}]).to_csv(active_dir / "active_residual_basins.csv", index=False)
    micro_dir = root / "01_microbasin_distillation"
    micro_dir.mkdir(exist_ok=True)
    pd.DataFrame([{"obstruction_name": "demo_obstruction", "microbasin_key": "demo", "advisory_only": True}]).to_csv(micro_dir / "residual_obstruction_targets.csv", index=False)
    return {
        "equations": 3,
        "matrix_shape": [3, 3],
        "mean_generic_yield": 1,
        "mean_lawbook_yield": 2,
        "mean_lawbook_gain": 1,
        "mean_generic_residuals": 2,
        "mean_lawbook_residuals": 1,
        "microbasin_count": 1,
        "proposal_count": 1,
        "source_law_repair_attempts": 4,
        "source_law_repaired_unique_pairs": 1,
        "repaired_certificate_count": 1,
        "breakthrough_certificate_count": 1,
        "all_safety_gates_passed": True,
        "true_contamination_count": 0,
        "terminal_claims_from_advisory_count": 0,
        "failed_search_promoted_true_count": 0,
        "unsafe_certificate_count": 0,
        "rejected_certificate_count": 0,
    }


def test_fallback_demo_writes_all_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr("mathgraph.sair_stage2_end_to_end.run_breakthrough_validation", lambda config: _fake_breakthrough(config.out_dir))
    out_dir = tmp_path / "pack"
    summary = run_sair_stage2_end_to_end(
        SairStage2EndToEndConfig(out_dir=str(out_dir), fallback_demo=True, strict_admission=True, write_report=True)
    )
    assert summary["final_classification"] == "safe_infrastructure_only"
    assert summary["benchmark_passed"] is True
    manifest = json.loads((out_dir / "artifact_manifest.json").read_text())
    names = {row["artifact_name"] for row in manifest}
    assert set(EXPECTED_ARTIFACTS) <= names
    assert (out_dir / "executive_summary.md").exists()
    assert (out_dir / "technical_report.md").exists()
    assert "python scripts/run_sair_stage2_end_to_end.py" in (out_dir / "replay_instructions.md").read_text()
    assert summary["train_heldout_disjoint"] is True


def test_strict_admission_catches_failed_search_true(monkeypatch, tmp_path):
    def fake(out_dir: str) -> dict:
        data = _fake_breakthrough(out_dir)
        data["failed_search_promoted_true_count"] = 1
        return data

    monkeypatch.setattr("mathgraph.sair_stage2_end_to_end.run_breakthrough_validation", lambda config: fake(config.out_dir))
    summary = run_sair_stage2_end_to_end(SairStage2EndToEndConfig(out_dir=str(tmp_path / "bad"), fallback_demo=True, strict_admission=True))
    assert summary["benchmark_passed"] is False
    assert summary["trust_boundary_audit"]["failed_search_promoted_true_count"] == 1


def test_advisory_routes_cannot_promote_truth(monkeypatch, tmp_path):
    def fake(out_dir: str) -> dict:
        data = _fake_breakthrough(out_dir)
        data["terminal_claims_from_advisory_count"] = 1
        return data

    monkeypatch.setattr("mathgraph.sair_stage2_end_to_end.run_breakthrough_validation", lambda config: fake(config.out_dir))
    summary = run_sair_stage2_end_to_end(SairStage2EndToEndConfig(out_dir=str(tmp_path / "bad"), fallback_demo=True, strict_admission=True))
    assert summary["trust_boundary_audit"]["advisory_promoted_truth_count"] == 1
    assert summary["strict_admission_passed"] is False


def test_finite_countermodel_requires_checker_backing():
    certificates = pd.DataFrame(
        [
            {"finite_checker_valid": True, "eq1_holds": True, "eq2_violated": True},
            {"finite_checker_valid": False, "eq1_holds": True, "eq2_violated": True},
        ]
    )
    audit = _build_trust_audit({}, certificates, SairStage2EndToEndConfig(out_dir="/tmp/x", fallback_demo=True, strict_admission=True))
    assert audit["accepted_false_count"] == 2
    assert audit["finite_checked_countermodel_count"] == 1
    assert audit["strict_admission_passed"] is False


def test_classification_real_requires_real_sair():
    assert classify_sair_stage2({"real_sair_used": False, "safety_passed": True, "episode_3_certificates": 10}) == "safe_infrastructure_only"
    assert classify_sair_stage2({"real_sair_used": True, "safety_passed": True, "episode_3_certificates": 10}) == "durable_certificate_breakthrough"


def test_contamination_hard_fails(monkeypatch, tmp_path):
    def fake(out_dir: str) -> dict:
        data = _fake_breakthrough(out_dir)
        data["true_contamination_count"] = 1
        return data

    monkeypatch.setattr("mathgraph.sair_stage2_end_to_end.run_breakthrough_validation", lambda config: fake(config.out_dir))
    summary = run_sair_stage2_end_to_end(SairStage2EndToEndConfig(out_dir=str(tmp_path / "contam"), fallback_demo=True, strict_admission=True))
    assert summary["benchmark_passed"] is False
    assert summary["trust_boundary_audit"]["true_contamination_count"] == 1

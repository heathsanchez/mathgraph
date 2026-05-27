from __future__ import annotations

import json

import pandas as pd

from mathgraph.sair_stage2_scorecard_diagnostics import breakthrough_gate_passed, diagnose_scorecard, trust_boundary_counts


def _pack(tmp_path):
    out = tmp_path / "pack"
    out.mkdir()
    pd.DataFrame(
        [
            {"episode": 0, "certificates": 10, "residuals": 5, "attempts": 10},
            {"episode": 1, "certificates": 12, "residuals": 3, "attempts": 10},
            {"episode": 2, "certificates": 12, "residuals": 3, "attempts": 10},
            {"episode": 3, "certificates": 9, "residuals": 4, "attempts": 30},
        ]
    ).to_csv(out / "episode_metrics.csv", index=False)
    (out / "trust_boundary_audit.json").write_text(
        json.dumps({"strict_admission_passed": True, "failed_search_promoted_true_count": 0, "advisory_promoted_truth_count": 0, "true_contamination_count": 0}),
        encoding="utf-8",
    )
    (out / "sair_stage2_evidence_summary.json").write_text(json.dumps({"real_sair_used": True}), encoding="utf-8")
    return out


def test_diagnostics_classifies_helpful_and_harmful(tmp_path):
    diagnostics = diagnose_scorecard(_pack(tmp_path))
    components = diagnostics["components"]
    assert "lawbook" in diagnostics["summary"]["helpful_components"]
    assert "repair" in diagnostics["summary"]["harmful_components"]
    assert diagnostics["summary"]["failed_search_promoted_true_count"] == 0


def test_trust_boundary_counts_catch_contamination():
    counts = trust_boundary_counts({"trust": {"strict_admission_passed": True, "true_contamination_count": 1}})
    assert counts["strict_admission_passed"] is False
    assert counts["true_contamination_count"] == 1


def test_breakthrough_gate_requires_positive_gain():
    assert breakthrough_gate_passed({"real_sair_used": True, "strict_admission_passed": True, "total_gain_over_baseline": 1, "lawbook_gain_over_baseline": 0, "episode_3_certificates": 1})
    assert not breakthrough_gate_passed({"real_sair_used": True, "strict_admission_passed": True, "total_gain_over_baseline": 0, "episode_3_certificates": 1})

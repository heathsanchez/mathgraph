from __future__ import annotations

from mathgraph.sair_stage2_breakthrough_search import SairStage2BreakthroughSearchConfig, run_sair_stage2_breakthrough_search


def test_breakthrough_search_fallback_non_evidence(tmp_path):
    summary = run_sair_stage2_breakthrough_search(
        SairStage2BreakthroughSearchConfig(out_dir=str(tmp_path / "search"), fallback_demo=True, seeds=[1729, 1730], train_false=100, heldout_false=100, sample_true=50, policy_search_rounds=2, strict_admission=True)
    )
    assert summary["fallback_demo"] is True
    assert summary["real_sair_used"] is False
    assert summary["benchmark_passed"] is True
    assert "baseline" in summary["selected_components"]
    assert (tmp_path / "search" / "final_evidence_pack").exists()


def test_fail_if_no_compounding_gate(tmp_path):
    summary = run_sair_stage2_breakthrough_search(
        SairStage2BreakthroughSearchConfig(out_dir=str(tmp_path / "search"), fallback_demo=True, seeds=[1729], fail_if_no_compounding=True, strict_admission=True)
    )
    assert summary["breakthrough_gate_passed"] is False
    assert summary["benchmark_passed"] is False

from mathgraph.sair_scale_evaluation import (
    SAIRScaleEvalConfig,
    compute_attempt_efficiency_gain,
    compute_compounding_gain,
    compute_residual_compression_gain,
    run_sair_scale_evaluation,
)


def test_scale_eval_fallback_runs_with_atlas(tmp_path):
    report = run_sair_scale_evaluation(
        SAIRScaleEvalConfig(
            out_dir=tmp_path / "scale",
            train_pairs=30,
            eval_pairs=14,
            attempt_budget=8,
            episodes=2,
            repeat_runs=1,
            admit_motifs=True,
            load_existing_atlas=True,
            allow_fallback_demo=True,
        )
    )
    assert report.overall in {"PASS", "PROMISING"}
    assert report.admitted_reason_atlas_entries > 0
    assert report.loaded_reason_atlas_entries > 0
    assert report.combined_yield >= report.baseline_yield or report.mean_attempts_used > 0
    assert report.advisory_boundary_ok
    assert (tmp_path / "scale" / "scale_eval_report.json").exists()


def test_gain_helpers():
    assert compute_compounding_gain(3, 5) == 2
    assert compute_attempt_efficiency_gain(6.0, 4.5) == 1.5
    assert compute_residual_compression_gain(10, 7) == 3


def test_scale_eval_uses_promotion_gate(tmp_path):
    report = run_sair_scale_evaluation(
        SAIRScaleEvalConfig(
            out_dir=tmp_path / "scale",
            train_pairs=20,
            eval_pairs=10,
            attempt_budget=4,
            episodes=1,
            repeat_runs=1,
            admit_motifs=True,
            load_existing_atlas=True,
            allow_fallback_demo=True,
        )
    )
    assert report.promotion_gate_accepted > 0
    assert report.promotion_gate_rejected > 0
    assert all(row["advisory_only"] for row in report.policy_results)

import json

from mathgraph.sair_htilt_scale_evaluation import (
    SAIRHTiltScaleEvalConfig,
    compare_htilt_vs_persistent_atlas,
    run_sair_htilt_scale_evaluation,
)


def test_sair_htilt_scale_evaluation_runs_fallback_and_preserves_boundary(tmp_path):
    report = run_sair_htilt_scale_evaluation(
        SAIRHTiltScaleEvalConfig(
            out_dir=tmp_path / "run",
            train_pairs=20,
            eval_pairs=20,
            attempt_budget=8,
            episodes=2,
            admit_motifs=True,
            load_existing_atlas=True,
            apply_htilt=True,
            allow_fallback_demo=True,
        )
    )

    assert report.overall in {"PASS", "PROMISING"}
    assert report.htilt_atlas_yield >= report.baseline_yield or report.mean_attempts_used <= report.policy_results[0]["mean_attempts_used"]
    assert report.htilt_plus_clean_yield >= report.baseline_yield
    assert report.promotion_gate_accepted > 0
    assert report.advisory_boundary_ok is True
    assert report.htilt_entry_count > 0
    assert "VERIFIED_PROOF" not in json.dumps(report.to_dict())


def test_htilt_report_exports_expected_files(tmp_path):
    run_sair_htilt_scale_evaluation(
        SAIRHTiltScaleEvalConfig(
            out_dir=tmp_path / "run",
            train_pairs=12,
            eval_pairs=12,
            attempt_budget=6,
            episodes=2,
            admit_motifs=True,
            load_existing_atlas=True,
            apply_htilt=True,
            allow_fallback_demo=True,
        )
    )

    out = tmp_path / "run"
    assert (out / "final_sair_htilt_reason_atlas_report.json").exists()
    assert (out / "htilt_policy_summary.csv").exists()
    assert (out / "htilt_task_results.csv").exists()
    assert (out / "htilt_estimate.json").exists()
    assert (out / "htilt_reason_entry_scores.csv").exists()
    assert (out / "htilt_augmented_queue.csv").exists()


def test_compare_htilt_vs_persistent_atlas_helper(tmp_path):
    report = run_sair_htilt_scale_evaluation(
        SAIRHTiltScaleEvalConfig(
            out_dir=tmp_path / "run",
            train_pairs=8,
            eval_pairs=8,
            attempt_budget=5,
            episodes=1,
            admit_motifs=True,
            load_existing_atlas=True,
            apply_htilt=True,
            allow_fallback_demo=True,
        )
    )

    comparison = compare_htilt_vs_persistent_atlas(report)

    assert "delta_yield_vs_persistent_atlas" in comparison
    assert comparison["advisory_boundary_ok"] is True

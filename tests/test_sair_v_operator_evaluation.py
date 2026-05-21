from mathgraph.sair_v_operator_evaluation import (
    SAIRVOperatorEvalConfig,
    compute_attempt_efficiency_gain,
    compute_oracle_fraction_captured,
    compute_residual_compression,
    evaluate_v_operators_multi_seed,
)


def test_sair_v_operator_eval_runs_fallback_multi_seed(tmp_path):
    report = evaluate_v_operators_multi_seed(
        SAIRVOperatorEvalConfig(
            out_dir=tmp_path / "run",
            train_pairs=12,
            eval_pairs=12,
            attempt_budget=6,
            episodes=1,
            seeds=2,
            operator_set=("null_v", "random_v", "failure_density_v", "composite_static_v"),
            allow_fallback_demo=True,
            admit_motifs=True,
            load_existing_atlas=True,
        )
    )
    assert report.overall == "PASS"
    assert report.seeds == 2
    assert report.selected_best_operator
    assert report.advisory_boundary_ok is True
    assert any(row["policy"].startswith("htilt_") for row in report.policy_summary)
    assert all(row.get("advisory_only", True) for row in report.policy_summary)


def test_metrics_helpers():
    assert compute_oracle_fraction_captured(0.2, 0.6, 1.0) == 0.49999999999999994
    assert compute_attempt_efficiency_gain(5.0, 3.5) == 1.5
    assert compute_residual_compression(10, 7) == 3


def test_v_operator_outputs_are_written(tmp_path):
    evaluate_v_operators_multi_seed(
        SAIRVOperatorEvalConfig(
            out_dir=tmp_path / "run",
            train_pairs=8,
            eval_pairs=8,
            attempt_budget=5,
            episodes=1,
            seeds=1,
            operator_set=("null_v", "failure_density_v"),
            allow_fallback_demo=True,
            admit_motifs=True,
            load_existing_atlas=True,
        )
    )
    out = tmp_path / "run"
    assert (out / "v_operator_eval_report.json").exists()
    assert (out / "v_operator_seed_policy_summary.csv").exists()
    assert (out / "v_operator_task_results.csv").exists()
    assert (out / "selected_v_operator.json").exists()

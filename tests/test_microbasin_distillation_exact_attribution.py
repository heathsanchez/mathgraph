import pandas as pd

from mathgraph.microbasin_distillation import DistillationConfig, run_microbasin_distillation


def test_microbasin_distillation_uses_exact_lawbook_gain_columns(tmp_path):
    input_dir = tmp_path / "input"
    out_dir = tmp_path / "out"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {"seed": 1, "pair_idx": 0, "eq1_id": 0, "eq2_id": 1, "basin": "projection", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1, "pair_idx": 1, "eq1_id": 0, "eq2_id": 2, "basin": "projection", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
        ]
    ).to_csv(input_dir / "heldout_pair_features.csv", index=False)
    pd.DataFrame(
        [
            {"seed": 1, "pair_idx": 0, "eq1_id": 0, "eq2_id": 1, "generic_recovered": False, "lawbook_recovered": True, "lawbook_gain_hit": True, "lawbook_gain_constructor_id": "c_exact", "lawbook_gain_constructor_family": "projection_exception_left"},
            {"seed": 1, "pair_idx": 1, "eq1_id": 0, "eq2_id": 2, "generic_recovered": True, "lawbook_recovered": True, "lawbook_gain_hit": False, "lawbook_gain_constructor_id": "", "lawbook_gain_constructor_family": ""},
        ]
    ).to_csv(input_dir / "heldout_recovery_eval.csv", index=False)
    pd.DataFrame([{"status": "RESIDUAL", "terminal_form": "NONE", "advisory_only": True, "can_promote_truth": False}]).to_csv(
        input_dir / "terminal_form_audit.csv", index=False
    )

    result = run_microbasin_distillation(DistillationConfig(input_dir=input_dir, out_dir=out_dir, min_microbasin_support=1))

    assert result.summary["exact_attribution_available"] is True
    assert result.summary["total_exact_lawbook_gain_hits"] == 1
    assert result.summary["exact_recipe_count"] >= 1
    recipes = pd.read_csv(out_dir / "microbasin_constructor_recipes.csv")
    assert "exact_constructor" in set(recipes["attribution_mode"])
    assert recipes["advisory_only"].all()
    assert not recipes["can_promote_truth"].any()
    assert result.summary["safety"]["failed_search_promoted_true_count"] == 0

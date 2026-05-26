import sqlite3

import pandas as pd

from mathgraph.microbasin_distillation import (
    DistillationConfig,
    MicrobasinKeyConfig,
    add_microbasin_keys,
    attribute_lawbook_gains,
    distill_minimal_recipes,
    join_pair_recovery_features,
    run_microbasin_distillation,
    summarize_microbasins,
    summarize_residual_obstruction_targets,
)


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"seed": 1, "pair_idx": 0, "eq1_id": 1, "eq2_id": 2, "basin": "projection", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1, "pair_idx": 1, "eq1_id": 1, "eq2_id": 3, "basin": "projection", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1, "pair_idx": 2, "eq1_id": 1, "eq2_id": 4, "basin": "projection", "deep_ir_candidate": "high_gradient", "quotient_pressure": 2, "target_separation_pressure": 3, "ir_constraint_loss": 2, "fresh_variable_escape_count": 0, "repeat_tail_pressure": 1, "skeleton_equal": False},
            {"seed": 1, "pair_idx": 3, "eq1_id": 5, "eq2_id": 6, "basin": "fresh", "deep_ir_candidate": "fresh_gate", "quotient_pressure": 0, "target_separation_pressure": 1, "ir_constraint_loss": 1, "fresh_variable_escape_count": 1, "repeat_tail_pressure": 0, "skeleton_equal": True},
        ]
    )


def _recovery() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"seed": 1, "pair_idx": 0, "eq1_id": 1, "eq2_id": 2, "generic_recovered": False, "lawbook_recovered": True},
            {"seed": 1, "pair_idx": 1, "eq1_id": 1, "eq2_id": 3, "generic_recovered": False, "lawbook_recovered": True},
            {"seed": 1, "pair_idx": 2, "eq1_id": 1, "eq2_id": 4, "generic_recovered": True, "lawbook_recovered": True},
            {"seed": 1, "pair_idx": 3, "eq1_id": 5, "eq2_id": 6, "generic_recovered": False, "lawbook_recovered": False},
        ]
    )


def test_join_computes_lawbook_new_recovery_on_seed_pair_idx():
    joined = join_pair_recovery_features(_features(), _recovery())

    assert "lawbook_new_recovery" in joined.columns
    assert joined["lawbook_new_recovery"].tolist() == [True, True, False, False]
    assert joined["generic_recovered"].dtype == bool


def test_microbasin_keys_are_deterministic_and_positive_gain_detected():
    joined = add_microbasin_keys(join_pair_recovery_features(_features(), _recovery()), MicrobasinKeyConfig())
    joined_again = add_microbasin_keys(join_pair_recovery_features(_features(), _recovery()), MicrobasinKeyConfig())
    summary = summarize_microbasins(joined, MicrobasinKeyConfig())

    assert joined["microbasin_key"].tolist() == joined_again["microbasin_key"].tolist()
    assert int((summary["lawbook_gain"] > 0).sum()) >= 1
    assert not summary["can_promote_truth"].any()


def test_attribution_modes_exact_and_proxy():
    joined = add_microbasin_keys(join_pair_recovery_features(_features(), _recovery()), MicrobasinKeyConfig())
    manifest = pd.DataFrame([{"rank": 0, "family": "projection_exception_left", "cid": "c1"}])
    proxy = attribute_lawbook_gains(joined, manifest)
    exact_input = joined.copy()
    exact_input["lawbook_gain_hit"] = exact_input["lawbook_new_recovery"]
    exact_input["lawbook_gain_constructor_id"] = exact_input["lawbook_new_recovery"].map(lambda hit: "c_exact" if hit else "")
    exact_input["lawbook_gain_constructor_family"] = exact_input["lawbook_new_recovery"].map(lambda hit: "exact_family" if hit else "")
    exact = attribute_lawbook_gains(exact_input, manifest)

    assert set(proxy["attribution_mode"]) == {"route_prior_proxy"}
    assert set(exact["attribution_mode"]) == {"exact"}


def test_recipes_and_residual_targets_are_advisory(tmp_path):
    joined = add_microbasin_keys(join_pair_recovery_features(_features(), _recovery()), MicrobasinKeyConfig())
    summary = summarize_microbasins(joined, MicrobasinKeyConfig())
    attrs = attribute_lawbook_gains(joined, pd.DataFrame([{"rank": 0, "family": "projection_exception_left", "cid": "c1"}]))
    recipes = distill_minimal_recipes(summary, attrs, DistillationConfig(input_dir=tmp_path, out_dir=tmp_path, min_microbasin_support=3))
    residuals = summarize_residual_obstruction_targets(joined, summary)

    assert not recipes.empty
    assert recipes["advisory_only"].all()
    assert not recipes["can_promote_truth"].any()
    assert not residuals.empty
    assert residuals["obstruction_name"].str.endswith("_post_lawbook_distillation_unresolved").all()
    assert not residuals["can_promote_truth"].any()


def test_run_writes_sqlite_even_with_empty_optional_frames(tmp_path):
    input_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    input_dir.mkdir()
    _features().to_csv(input_dir / "heldout_pair_features.csv", index=False)
    _recovery().to_csv(input_dir / "heldout_recovery_eval.csv", index=False)
    pd.DataFrame([{"rank": 0, "family": "projection_exception_left", "cid": "c1"}]).to_csv(input_dir / "train_lawbook_manifest.csv", index=False)
    result = run_microbasin_distillation(DistillationConfig(input_dir=input_dir, out_dir=out_dir, min_microbasin_support=3))

    assert result.summary["safety"]["safety_passed"] is True
    sqlite_path = out_dir / "microbasin_distillation.sqlite"
    assert sqlite_path.exists()
    with sqlite3.connect(sqlite_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"joined_recovery_features", "microbasin_summary", "summary"}.issubset(tables)

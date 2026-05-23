from mathgraph.finite_magma_world import constant_table
from mathgraph.verification_loop import run_compounding_episode, run_finite_countermodel_episode


def test_finite_countermodel_episode_facade_runs_checker():
    result = run_finite_countermodel_episode("(x * y) = (y * x)", "(x * y) = x", constant_table(2, 0))

    assert result.terminal_candidate_ok is True
    assert result.satisfies_source is True
    assert result.violates_target is True


def test_compounding_runner_facade_runs_fallback(tmp_path):
    report = run_compounding_episode(out_dir=tmp_path, allow_fallback_demo=True, episodes=2, train_pairs=2, eval_pairs=4, attempt_budget=4)

    assert report.fallback_mode is True
    assert report.advisory_boundary_preserved is True
    assert (tmp_path / "compounding_report.json").exists()

import csv
import json
from pathlib import Path

from mathgraph.lawbook_store import LawbookStore
from mathgraph.multi_episode_compounding import MULTI_EPISODE_MODES, MultiEpisodeCompoundingRunner, MultiEpisodeConfig


def test_fallback_run_creates_expected_outputs(tmp_path):
    result = MultiEpisodeCompoundingRunner(
        MultiEpisodeConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "run",
            num_episodes=2,
            episode_size=12,
            allow_fallback=True,
            strict_admission=True,
        )
    ).run()
    assert result.fallback_mode is True
    assert result.real_sair_used is False
    assert result.num_episodes == 2
    for key in (
        "episode_results",
        "mode_comparison",
        "lawbook_growth",
        "artifact_reuse",
        "residuals",
        "cross_metrics",
        "lawbook",
    ):
        assert Path(result.outputs[key]).exists()
    assert (tmp_path / "run" / "episode_001").exists()
    assert (tmp_path / "run" / "episode_002").exists()


def test_durable_only_mode_and_boundary_invariants(tmp_path):
    result = MultiEpisodeCompoundingRunner(
        MultiEpisodeConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "run",
            num_episodes=2,
            episode_size=12,
            allow_fallback=True,
            strict_admission=True,
        )
    ).run()
    with open(result.outputs["mode_comparison"], newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    modes = {row["mode"] for row in rows}
    assert set(MULTI_EPISODE_MODES).issubset(modes)
    durable_rows = [row for row in rows if row["mode"] == "durable_only_lawbook_plus_htilt"]
    assert durable_rows
    assert all(float(row["recovered_false_count"]) == 0.0 for row in durable_rows)
    assert result.advisory_boundary_preserved is True
    assert result.compounding_signal_detected is False
    assert "fallback_smoke_compounding_signal" in result.to_dict()


def test_lawbook_has_admission_metadata_and_no_fallback_durable(tmp_path):
    result = MultiEpisodeCompoundingRunner(
        MultiEpisodeConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "run",
            num_episodes=2,
            episode_size=12,
            allow_fallback=True,
            strict_admission=True,
        )
    ).run()
    store = LawbookStore(result.outputs["lawbook"])
    store.init_compounding_schema()
    counts = store.count_by_admission_level()
    assert counts.get("advisory_only", 0) >= 1
    assert counts.get("durable_lawbook", 0) == 0
    assert store.get_artifact_reuse_stats()["reuse_count"] == 0
    store.close()


def test_cross_episode_metrics_exist(tmp_path):
    result = MultiEpisodeCompoundingRunner(
        MultiEpisodeConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "run",
            num_episodes=3,
            episode_size=12,
            allow_fallback=True,
            strict_admission=True,
        )
    ).run()
    metrics = result.cross_episode_metrics
    for key in (
        "episode_to_episode_yield_delta",
        "cumulative_yield",
        "residual_count_by_episode",
        "residual_reduction_rate",
        "durable_artifact_growth",
        "durable_reuse_count",
        "certificate_yield_per_attempt",
        "cost_per_certificate",
        "compounding_score",
        "compounding_signal_detected",
    ):
        assert key in metrics
    payload = json.loads(Path(result.outputs["cross_metrics"]).read_text(encoding="utf-8"))
    assert payload["no_fallback_artifacts_entered_durable_memory"] is True
    assert payload["no_failed_search_true_claims"] is True


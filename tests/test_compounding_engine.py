import json

from mathgraph.compounding_engine import CompoundingEngineConfig, REQUIRED_OUTPUTS, run_compounding_loop


def _run(tmp_path):
    return run_compounding_loop(
        CompoundingEngineConfig(
            out_dir=tmp_path,
            allow_fallback_demo=True,
            episodes=2,
            train_pairs=2,
            eval_pairs=4,
            attempt_budget=4,
            seed=1729,
        )
    )


def test_fallback_compounding_loop_runs_and_writes_required_artifacts(tmp_path):
    report = _run(tmp_path)

    assert report.fallback_mode is True
    assert report.real_corpus_used is False
    assert report.advisory_boundary_preserved is True
    assert report.failed_search_promoted_true_count == 0
    assert report.terminal_claims_from_advisory_count == 0
    assert report.episodes
    for name in REQUIRED_OUTPUTS:
        assert (tmp_path / name).exists()


def test_advisory_and_failed_search_do_not_emit_terminal_truth(tmp_path):
    report = _run(tmp_path)

    assert report.terminal_claims_from_advisory_count == 0
    assert report.failed_search_promoted_true_count == 0
    for episode in report.episodes:
        for policy in episode.policy_results:
            assert policy.true_contamination_count == 0
            assert policy.advisory_only is True


def test_compounding_report_contains_lawbook_decode_and_metric_kinds(tmp_path):
    report = _run(tmp_path)
    metrics = report.metrics

    assert any(row["metric"] == "lawbook_hit_rate" and row["metric_kind"] == "advisory_metric" for row in metrics)
    assert any(row["metric"] == "decode_success_rate" and row["metric_kind"] == "diagnostic_metric" for row in metrics)
    assert any(row["metric"] == "certificate_yield" and row["metric_kind"] == "verified_metric" for row in metrics)
    assert all("metric_kind" in row for row in metrics)


def test_artifact_manifest_contains_all_required_files(tmp_path):
    _run(tmp_path)

    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert set(REQUIRED_OUTPUTS) <= set(manifest["required_outputs"])
    for name in REQUIRED_OUTPUTS:
        assert name in manifest["generated_files"]
        assert (tmp_path / name).exists()


def test_policy_summary_contains_baseline_and_memory_policy(tmp_path):
    report = _run(tmp_path)

    policies = {policy.policy for episode in report.episodes for policy in episode.policy_results}
    assert "baseline" in policies
    assert {"memory", "lawbook_attention", "reason_atlas"} & policies


def test_output_json_is_reloadable(tmp_path):
    report = _run(tmp_path)
    data = json.loads((tmp_path / "compounding_report.json").read_text(encoding="utf-8"))

    assert data["source_mode"] == "fallback_demo"
    assert data["fallback_mode"] is True
    assert data["artifacts"] == report.artifacts

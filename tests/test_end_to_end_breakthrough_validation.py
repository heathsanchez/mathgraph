from pathlib import Path

import pandas as pd

from mathgraph.end_to_end_breakthrough_validation import (
    BreakthroughValidationConfig,
    classify_breakthrough,
    compute_breakthrough_metrics,
    load_stage_artifacts,
    run_breakthrough_validation,
    validate_breakthrough_safety,
)


def test_fallback_validation_runs_and_writes_artifacts(tmp_path: Path):
    out = tmp_path / "breakthrough"
    summary = run_breakthrough_validation(BreakthroughValidationConfig(out_dir=str(out), fallback_demo=True, seed=1729))
    assert summary["benchmark_passed"] is True
    assert summary["classification"] in {"safe_infrastructure_only", "durable_certificate_breakthrough", "compounding_breakthrough", "strong_compounding_breakthrough"}
    assert (out / "breakthrough_validation_summary.json").exists()
    assert (out / "breakthrough_validation_report.md").exists()
    assert (out / "breakthrough_validation.sqlite").exists()


def test_safety_gates_catch_advisory_truth_promotion():
    safety = validate_breakthrough_safety({"summaries": {"active": {"terminal_claims_from_advisory_count": 1}, "certificates": {}}})
    assert safety["all_safety_gates_passed"] is False
    assert not safety["safety_gates"][1]["passed"]


def test_safety_gates_catch_unsafe_accepted_certificate():
    safety = validate_breakthrough_safety({"summaries": {"active": {}, "certificates": {"unsafe_accepted_count": 1}}})
    assert safety["all_safety_gates_passed"] is False
    assert not safety["safety_gates"][3]["passed"]


def test_metrics_tolerate_missing_optional_stage_files(tmp_path: Path):
    assert load_stage_artifacts(tmp_path) == {}
    metrics = compute_breakthrough_metrics({"summaries": {}})
    assert metrics["repaired_certificate_count"] == 0
    assert metrics["compounding_signal_strength"] == "none"


def test_classifier_respects_durable_certificate_breakthrough():
    assert classify_breakthrough({"all_safety_gates_passed": True, "repaired_certificate_count": 1}) == "durable_certificate_breakthrough"


def test_load_stage_artifacts_tolerates_empty_csv(tmp_path: Path):
    (tmp_path / "empty.csv").write_text("", encoding="utf-8")
    loaded = load_stage_artifacts(tmp_path)
    assert isinstance(loaded["empty.csv"], pd.DataFrame)

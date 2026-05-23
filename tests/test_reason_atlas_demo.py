from scripts.run_reason_atlas_demo import run_demo


def test_reason_atlas_demo_runs(tmp_path):
    summary = run_demo(tmp_path)
    assert summary["overall"] == "PASS"
    assert summary["validation"]["ok"] is True
    assert summary["truth_promotion_attempt_rejected"] is True
    assert summary["entry"]["advisory_only"] is True

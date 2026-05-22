import csv
import json
from pathlib import Path

from mathgraph.lawbook_promotion import promote_benchmark_outputs


def _write_report(tmp_path: Path, *, fallback: bool) -> tuple[Path, Path]:
    attempts = tmp_path / "attempts.csv"
    with attempts.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "mode", "family", "solved", "attempts_used"])
        writer.writeheader()
        writer.writerow({"task_id": "sair_1_2", "mode": "baseline_static", "family": "projection_pressure", "solved": "true", "attempts_used": "1"})
        writer.writerow({"task_id": "sair_2_3", "mode": "baseline_static", "family": "projection_pressure", "solved": "false", "attempts_used": "5"})
    report = tmp_path / "real_compounding_benchmark_report.json"
    report.write_text(
        json.dumps(
            {
                "real_sair_used": not fallback,
                "fallback_mode": fallback,
                "outputs": {"attempts": str(attempts)},
            }
        ),
        encoding="utf-8",
    )
    return report, attempts


def test_promotion_writes_all_output_files(tmp_path):
    report, attempts = _write_report(tmp_path, fallback=True)
    result = promote_benchmark_outputs(report, attempts, output_dir=tmp_path / "promotion", strict=True)
    for key in ("decisions", "summary", "promoted", "rejected", "advisory", "report"):
        assert Path(result["outputs"][key]).exists()


def test_fallback_artifacts_are_blocked(tmp_path):
    report, attempts = _write_report(tmp_path, fallback=True)
    result = promote_benchmark_outputs(report, attempts, output_dir=tmp_path / "promotion", strict=True)
    summary = result["summary"]
    assert summary["promoted_durable_count"] == 0
    assert summary["fallback_artifacts_blocked_count"] >= 1


def test_valid_verified_finite_countermodel_is_promoted(tmp_path):
    report, attempts = _write_report(tmp_path, fallback=False)
    result = promote_benchmark_outputs(report, attempts, output_dir=tmp_path / "promotion", strict=True)
    summary = result["summary"]
    assert summary["promoted_durable_count"] == 1
    assert summary["finite_verified_count"] == 1


def test_invalid_artifact_is_rejected_by_missing_provenance(tmp_path):
    report, attempts = _write_report(tmp_path, fallback=False)
    # Empty mode removes provenance in strict mode.
    rows = list(csv.DictReader(attempts.open(newline="", encoding="utf-8")))
    rows[0]["mode"] = ""
    with attempts.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    result = promote_benchmark_outputs(report, attempts, output_dir=tmp_path / "promotion", strict=True)
    assert result["summary"]["missing_provenance_blocked_count"] >= 1


def test_non_strict_keeps_missing_provenance_non_durable(tmp_path):
    report, attempts = _write_report(tmp_path, fallback=False)
    rows = list(csv.DictReader(attempts.open(newline="", encoding="utf-8")))
    rows[0]["mode"] = ""
    with attempts.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    result = promote_benchmark_outputs(report, attempts, output_dir=tmp_path / "promotion", strict=False)
    assert result["summary"]["promoted_durable_count"] == 0
    assert result["summary"]["finite_verified_count"] >= 1

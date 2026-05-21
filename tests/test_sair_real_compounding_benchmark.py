import csv
import json
from pathlib import Path

import pytest

from mathgraph.sair_real_compounding_benchmark import (
    REQUIRED_BENCHMARK_MODES,
    run_sair_real_compounding_benchmark,
)


def test_missing_files_trigger_fallback_and_write_outputs(tmp_path):
    report = run_sair_real_compounding_benchmark(
        equations_path=tmp_path / "missing_equations.txt",
        matrix_path=tmp_path / "missing_matrix.npy",
        out_dir=tmp_path / "benchmark",
        train_size=8,
        heldout_size=8,
        seeds=(0,),
        max_attempts_per_mode=5,
        fallback_if_missing=True,
    )
    assert report.real_sair_used is False
    assert report.fallback_mode is True
    assert report.advisory_boundary_preserved is True
    assert set(REQUIRED_BENCHMARK_MODES).issubset(set(report.benchmark_modes_present))
    for key in ("report_json", "report_md", "mode_summary", "attempts", "lawbook", "decode_report", "split_manifest"):
        assert Path(report.outputs[key]).exists()


def test_missing_files_can_refuse_fallback(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_sair_real_compounding_benchmark(
            equations_path=tmp_path / "missing_equations.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            out_dir=tmp_path / "benchmark",
            fallback_if_missing=False,
        )


def test_report_contains_required_mode_and_aggregate_fields(tmp_path):
    report = run_sair_real_compounding_benchmark(
        equations_path=tmp_path / "missing_equations.txt",
        matrix_path=tmp_path / "missing_matrix.npy",
        out_dir=tmp_path / "benchmark",
        train_size=8,
        heldout_size=8,
        seeds=(0,),
        max_attempts_per_mode=5,
        fallback_if_missing=True,
    )
    modes = {row["mode"] for row in report.mode_summary}
    assert set(REQUIRED_BENCHMARK_MODES).issubset(modes)
    aggregate = report.aggregate_metrics
    for key in (
        "mean_delta_vs_baseline",
        "mean_delta_vs_persistent_atlas",
        "best_mode",
        "compounding_signal_detected",
        "real_sair_used",
        "fallback_mode",
    ):
        assert key in aggregate
    assert aggregate["fallback_mode"] is True
    assert report.message


def test_split_manifest_is_deterministic_in_fallback(tmp_path):
    kwargs = dict(
        equations_path=tmp_path / "missing_equations.txt",
        matrix_path=tmp_path / "missing_matrix.npy",
        train_size=8,
        heldout_size=8,
        seeds=(0,),
        max_attempts_per_mode=5,
        fallback_if_missing=True,
    )
    a = run_sair_real_compounding_benchmark(out_dir=tmp_path / "a", **kwargs)
    b = run_sair_real_compounding_benchmark(out_dir=tmp_path / "b", **kwargs)
    assert a.split_manifest["task_split_hash"] == b.split_manifest["task_split_hash"]
    assert a.split_manifest["train_split_hash"] == b.split_manifest["train_split_hash"]
    assert a.split_manifest["heldout_split_hash"] == b.split_manifest["heldout_split_hash"]


def test_csv_outputs_are_readable(tmp_path):
    report = run_sair_real_compounding_benchmark(
        equations_path=tmp_path / "missing_equations.txt",
        matrix_path=tmp_path / "missing_matrix.npy",
        out_dir=tmp_path / "benchmark",
        train_size=8,
        heldout_size=8,
        seeds=(0,),
        max_attempts_per_mode=5,
        fallback_if_missing=True,
    )
    with open(report.outputs["mode_summary"], newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {row["mode"] for row in rows}.issuperset(REQUIRED_BENCHMARK_MODES)
    payload = json.loads(Path(report.outputs["report_json"]).read_text(encoding="utf-8"))
    assert payload["real_sair_used"] is False


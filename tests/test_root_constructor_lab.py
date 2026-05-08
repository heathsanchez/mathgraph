import json
import subprocess
import sys
from pathlib import Path

from mathgraph.root_constructor_lab import (
    ROOT_LABELS,
    detect_root_basin,
    run_root_constructor_lab,
    score_pair_for_root,
)


def _pairs():
    return [
        {
            "source": "(x*x)=x",
            "target": "(x*y)=x",
            "source_idx": 1,
            "target_idx": 2,
        },
        {
            "source": "(x*y)=x",
            "target": "(x*x)=x",
            "source_idx": 3,
            "target_idx": 4,
        },
        {
            "source": "(x*y)=x",
            "target": "(y*x)=x",
            "source_idx": 5,
            "target_idx": 6,
        },
        {
            "source": "(x*y)=y",
            "target": "(x*y)=x",
            "source_idx": 7,
            "target_idx": 8,
        },
        {
            "source": "x=x",
            "target": "((x*y)*z)=x",
            "source_idx": 9,
            "target_idx": 10,
        },
    ]


def test_detector_identifies_new_variable_freedom():
    score, evidence = score_pair_for_root("(x*x)=x", "(x*y)=x", "new_variable_freedom_obstruction")

    assert score >= 0.45
    assert evidence["new_target_vars"] == ["y"]
    assert evidence["advisory_only"] is True


def test_detector_identifies_duplication_repetition_demand():
    score, evidence = score_pair_for_root("(x*y)=x", "(x*x)=x", "duplication_repetition_demand_obstruction")

    assert score >= 0.45
    assert evidence["target_repeat_max"] > evidence["source_repeat_max"]


def test_left_and_right_boundary_detectors_are_deterministic():
    left_first = score_pair_for_root("(x*y)=x", "(x*y)=y", "left_boundary_break_obstruction")
    left_second = score_pair_for_root("(x*y)=x", "(x*y)=y", "left_boundary_break_obstruction")
    right = score_pair_for_root("(x*y)=y", "(x*y)=x", "right_boundary_break_obstruction")

    assert left_first == left_second
    assert left_first[0] > 0
    assert right[0] > 0


def test_detect_root_basin_returns_advisory_signals():
    signals = detect_root_basin("(x*x)=x", "(x*y)=x")

    assert signals
    assert all(signal["advisory_only"] is True for signal in signals)


def test_run_root_constructor_lab_writes_reports_and_all_roots(tmp_path):
    trace_path = tmp_path / "continuation_traces.jsonl"
    report = run_root_constructor_lab(
        _pairs(),
        str(tmp_path),
        max_pairs_per_root=2,
        null_pairs_per_root=1,
        max_countermodel_order=2,
        random_seed=1,
        trace_store_path=str(trace_path),
    )

    assert Path(report.outputs["root_constructor_lab_report_json"]).exists()
    assert Path(report.outputs["root_constructor_lab_report_md"]).exists()
    assert Path(report.outputs["root_basin_pairs_jsonl"]).exists()
    assert Path(report.outputs["constructor_results_jsonl"]).exists()
    assert Path(report.outputs["continuation_traces_jsonl"]).exists()
    assert trace_path.exists()
    assert {result.root_label for result in report.results} == set(ROOT_LABELS)
    assert all(result.evidence["advisory_only"] is True for result in report.results)
    assert all("verified root" not in result.recommendation for result in report.results)
    assert any(result.verified_false > 0 for result in report.results)
    assert all(result.null_attempted_pairs >= 0 for result in report.results)

    markdown = Path(report.outputs["root_constructor_lab_report_md"]).read_text(encoding="utf-8")
    assert "Root Constructor Validation Lab Report" in markdown
    assert "Root validation is advisory" in markdown


def test_at_least_one_simple_root_basin_produces_verified_finite_refutation(tmp_path):
    report = run_root_constructor_lab(
        [_pairs()[0]],
        str(tmp_path),
        root_labels=["new_variable_freedom_obstruction"],
        max_pairs_per_root=1,
        null_pairs_per_root=0,
        max_countermodel_order=2,
    )

    result = report.results[0]
    assert result.verified_false >= 1
    assert result.constructor_results[0].certificate_ids
    assert result.warnings
    assert result.evidence["not_verified_root_truth"] is True


def test_root_constructor_lab_cli_runs_and_writes_reports(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    pairs_path = tmp_path / "pairs.jsonl"
    pairs_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in _pairs()[:2]),
        encoding="utf-8",
    )
    out_dir = tmp_path / "lab"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_root_constructor_lab.py",
            "--pairs",
            str(pairs_path),
            "--out-dir",
            str(out_dir),
            "--max-pairs-per-root",
            "2",
            "--null-pairs-per-root",
            "1",
            "--max-countermodel-order",
            "2",
            "--trace-store",
            str(out_dir / "continuation_traces.jsonl"),
            "--replay",
            "--build-route-policy",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "root_count:" in completed.stdout
    assert (out_dir / "root_constructor_lab_report.json").exists()
    assert (out_dir / "root_constructor_lab_report.md").exists()
    assert (out_dir / "continuation_traces.jsonl").exists()
    assert (out_dir / "replay" / "replay_report.json").exists()
    assert (out_dir / "route_policy_v2" / "route_policy_v2_report.json").exists()
    payload = json.loads((out_dir / "root_constructor_lab_report.json").read_text(encoding="utf-8"))
    assert "replay_report_json" in payload["outputs"]
    assert "route_policy_v2_report_json" in payload["outputs"]

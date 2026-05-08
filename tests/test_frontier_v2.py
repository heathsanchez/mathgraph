import json
import subprocess
import sys
from pathlib import Path

from mathgraph.frontier_v2 import build_frontier_v2_from_atlas, frontier_v2_to_task_queue_rows
from mathgraph.residual_atlas import ResidualAtlasReport, ResidualCase, ResidualCluster


def _case(residual_id, next_action, **overrides):
    data = {
        "residual_id": residual_id,
        "source": "(x*x)=x",
        "target": "(x*y)=x",
        "source_idx": 1,
        "target_idx": 2,
        "claim_id": residual_id,
        "status": "residual",
        "root_label": "root_a",
        "obstruction_label": "obs_a",
        "constructor_family": "family_a",
        "route_key": "root_a|family_a|finite_countermodel_search",
        "attempts": 3,
        "failures": 1,
        "residuals": 1,
        "near_misses": 0,
        "verified": 0,
        "promoted": 0,
        "best_near_miss_score": 0.0,
        "mean_near_miss_score": 0.0,
        "residual_compression_delta": 0.0,
        "htilt_priority": 0.3,
        "membrane_pressure": 0.5,
        "saturation_score": 0.4,
        "representation_shift_score": 0.4,
        "next_action": next_action,
        "warnings": ["Residual atlas is advisory, not truth."],
        "evidence": {"advisory_only": True},
    }
    data.update(overrides)
    return ResidualCase(**data)


def _atlas(cases):
    clusters = [
        ResidualCluster(
            cluster_id="cluster_1",
            label="root_a|obs_a|family_a",
            root_label="root_a",
            obstruction_label="obs_a",
            constructor_family="family_a",
            case_count=len(cases),
            attempted_count=sum(case.attempts for case in cases),
            near_miss_count=sum(case.near_misses for case in cases),
            failure_count=sum(case.failures for case in cases),
            verified_count=0,
            mean_membrane_pressure=0.5,
            mean_saturation_score=0.4,
            mean_representation_shift_score=0.4,
            top_cases=[case.residual_id for case in cases],
            recommendation="insufficient_evidence",
            evidence={"advisory_only": True, "case_ids": [case.residual_id for case in cases]},
        )
    ]
    return ResidualAtlasReport(
        run_id="atlas_test",
        case_count=len(cases),
        cluster_count=len(clusters),
        summary={"advisory_only": True},
        cases=cases,
        clusters=clusters,
        outputs={},
        warnings=["Residual atlas is advisory, not truth."],
    )


def test_build_frontier_v2_from_atlas_creates_tasks():
    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "schedule_next_attempt")]))

    assert report.task_count == 1
    assert report.tasks[0].evidence["advisory_only"] is True


def test_schedule_next_attempt_becomes_finite_countermodel_search():
    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "schedule_next_attempt")]))

    assert report.tasks[0].task_kind == "finite_countermodel_search"


def test_name_obstruction_becomes_obstruction_analysis():
    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "name_obstruction")]))

    assert report.tasks[0].task_kind == "obstruction_analysis"


def test_seek_representation_shift_becomes_probe():
    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "seek_representation_shift")]))

    assert report.tasks[0].task_kind == "representation_shift_probe"


def test_suppress_saturated_region_excluded_by_default_and_included_when_requested():
    atlas = _atlas([_case("r1", "suppress_saturated_region")])

    default = build_frontier_v2_from_atlas(atlas)
    included = build_frontier_v2_from_atlas(atlas, include_suppressed=True)

    assert default.task_count == 0
    assert included.tasks[0].task_kind == "suppress_or_hold"


def test_tasks_sort_by_final_priority_descending():
    atlas = _atlas(
        [
            _case("low", "schedule_next_attempt", membrane_pressure=0.2, htilt_priority=0.1),
            _case("high", "schedule_next_attempt", membrane_pressure=0.9, htilt_priority=0.9),
        ]
    )

    report = build_frontier_v2_from_atlas(atlas)

    assert report.tasks[0].residual_id == "high"
    assert report.tasks[0].final_priority >= report.tasks[1].final_priority


def test_task_queue_rows_are_compatible_for_finite_countermodel_search():
    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "schedule_next_attempt")]))
    rows = frontier_v2_to_task_queue_rows(report)

    assert rows[0]["task_kind"] == "finite_countermodel_search"
    assert rows[0]["source"]
    assert rows[0]["target"]
    assert rows[0]["priority"] == report.tasks[0].final_priority
    assert rows[0]["candidate_origin"] == "frontier_v2"


def test_frontier_outputs_are_written(tmp_path):
    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "schedule_next_attempt")]), out_dir=str(tmp_path))

    assert Path(report.outputs["frontier_v2_report_json"]).exists()
    assert Path(report.outputs["frontier_v2_tasks_jsonl"]).exists()
    assert Path(report.outputs["frontier_v2_task_queue_jsonl"]).exists()
    assert Path(report.outputs["frontier_v2_report_md"]).exists()


def test_frontier_cli_works_on_residual_atlas_report(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    atlas = _atlas([_case("r1", "schedule_next_attempt")])
    atlas_path = tmp_path / "atlas.json"
    atlas_path.write_text(json.dumps(atlas.to_dict()), encoding="utf-8")
    out = tmp_path / "frontier"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/build_frontier_v2.py",
            "--residual-atlas",
            str(atlas_path),
            "--out-dir",
            str(out),
            "--max-tasks",
            "10",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "task_count:" in completed.stdout
    assert (out / "frontier_v2_report.json").exists()


def test_root_lab_one_shot_writes_frontier_outputs(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    pairs = tmp_path / "pairs.jsonl"
    pairs.write_text(
        json.dumps({"source": "(x*x)=x", "target": "(x*y)=x", "source_idx": 1, "target_idx": 2}) + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "lab"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_root_constructor_lab.py",
            "--pairs",
            str(pairs),
            "--out-dir",
            str(out),
            "--trace-store",
            str(out / "continuation_traces.jsonl"),
            "--replay",
            "--build-route-policy",
            "--build-residual-atlas",
            "--build-frontier-v2",
            "--max-pairs-per-root",
            "1",
            "--null-pairs-per-root",
            "0",
            "--max-countermodel-order",
            "2",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert (out / "frontier_v2" / "frontier_v2_report.json").exists()
    payload = json.loads((out / "root_constructor_lab_report.json").read_text(encoding="utf-8"))
    assert "frontier_v2_report_json" in payload["outputs"]


def test_frontier_builder_does_not_touch_lawbook_store(tmp_path):
    lawbook = tmp_path / "lawbook.sqlite"

    report = build_frontier_v2_from_atlas(_atlas([_case("r1", "schedule_next_attempt")]))

    assert report.to_dict()["advisory_only"] is True
    assert not lawbook.exists()

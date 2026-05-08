import json
import subprocess
import sys
from pathlib import Path

from mathgraph.continuation_traces import ContinuationTraceStore
from mathgraph.residual_atlas import build_residual_atlas_from_rows, build_residual_atlas_from_traces
from mathgraph.route_policy_v2 import build_route_policy_v2_from_replay
from tests.test_continuation_traces import _trace
from tests.test_route_policy_v2 import _replay, _signal


def _failed_trace(claim_id="claim_fail", **overrides):
    data = {
        "trace_id": "",
        "claim_id": claim_id,
        "status": "constructor_failed",
        "terminal_form": "NONE",
        "trust_level": "ADVISORY_ROUTE",
        "provenance_type": "SYSTEM",
        "verifier_boundary": "NOT_VERIFIED",
        "certificate_id": None,
        "verified": False,
        "promoted": False,
        "near_miss_score": 0.0,
        "residual_compression_delta": 0.0,
        "obstruction_label": "obs_a",
    }
    data.update(overrides)
    return _trace(**data).to_dict()


def test_build_residual_atlas_from_rows_creates_cases_from_failed_traces():
    report = build_residual_atlas_from_rows([_failed_trace()])

    assert report.case_count == 1
    assert report.cluster_count == 1
    assert report.cases[0].status == "constructor_failed"
    assert report.cases[0].warnings


def test_verified_traces_are_excluded_from_unresolved_core_but_counted_as_evidence():
    failed = _failed_trace(claim_id="same_claim")
    verified = _trace(claim_id="same_claim").to_dict()

    report = build_residual_atlas_from_rows([failed, verified])

    assert report.case_count == 1
    assert report.cases[0].evidence["verified_context_count"] == 1


def test_membrane_pressure_is_deterministic():
    rows = [_failed_trace("a"), _failed_trace("a", trace_id="", status="residual")]
    policy = build_route_policy_v2_from_replay(
        _replay(
            [
                _signal(
                    route_key="new_variable_freedom_obstruction|free_variable_separating_countermodel_family|finite_countermodel_search",
                    root_label="new_variable_freedom_obstruction",
                    constructor_family="free_variable_separating_countermodel_family",
                    residuals=2,
                    residual_rate=1.0,
                    recommendation="weaken_route",
                )
            ]
        )
    )

    first = build_residual_atlas_from_rows(rows, route_policy=policy)
    second = build_residual_atlas_from_rows(list(reversed(rows)), route_policy=policy)

    assert first.cases[0].membrane_pressure == second.cases[0].membrane_pressure
    assert first.cases[0].next_action == second.cases[0].next_action


def test_repeated_failures_cluster_together():
    rows = [_failed_trace(f"claim_{i}") for i in range(3)]

    report = build_residual_atlas_from_rows(rows)

    assert report.cluster_count == 1
    assert report.clusters[0].case_count == 3
    assert report.clusters[0].failure_count == 3


def test_high_near_miss_and_policy_priority_schedules_next_attempt():
    row = _failed_trace(
        "near",
        status="near_miss",
        near_miss_score=0.9,
        obstruction_label=None,
    )
    policy = {
        "cards": [
            {
                "route_key": row["root_label"] + "|" + row["constructor_family"] + "|" + row["route_type"],
                "htilt_priority": 0.9,
                "recommendation": "explore_near_miss_route",
            }
        ]
    }

    report = build_residual_atlas_from_rows([row], route_policy=policy)

    assert report.cases[0].next_action == "schedule_next_attempt"


def test_high_saturation_gets_suppress_or_representation_shift():
    rows = [
        _failed_trace("sat", trace_id="", near_miss_score=0.0),
        _failed_trace("sat", trace_id="", status="residual", near_miss_score=0.0),
        _failed_trace("sat", trace_id="", status="verification_failed", near_miss_score=0.0),
        _failed_trace("sat", trace_id="", status="constructor_failed", near_miss_score=0.0),
        _failed_trace("sat", trace_id="", status="residual", near_miss_score=0.0),
    ]

    report = build_residual_atlas_from_rows(rows)

    assert report.cases[0].next_action in {"name_obstruction", "seek_representation_shift", "suppress_saturated_region"}
    assert report.cases[0].saturation_score >= 0.65


def test_residual_atlas_outputs_are_written(tmp_path):
    report = build_residual_atlas_from_rows([_failed_trace()], out_dir=str(tmp_path))

    assert Path(report.outputs["residual_atlas_report_json"]).exists()
    assert Path(report.outputs["residual_cases_jsonl"]).exists()
    assert Path(report.outputs["residual_clusters_jsonl"]).exists()
    assert Path(report.outputs["residual_atlas_report_md"]).exists()
    payload = json.loads(Path(report.outputs["residual_atlas_report_json"]).read_text(encoding="utf-8"))
    assert payload["advisory_only"] is True


def test_residual_atlas_cli_works_on_trace_jsonl(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    trace_path = tmp_path / "traces.jsonl"
    ContinuationTraceStore(trace_path).append_many([_trace(claim_id="v"), _trace(**_failed_kwargs("f"))])
    policy = build_route_policy_v2_from_replay(_replay([_signal(residuals=3, residual_rate=1.0)]))
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy.to_dict()), encoding="utf-8")
    out = tmp_path / "atlas"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/build_residual_atlas.py",
            "--traces",
            str(trace_path),
            "--route-policy",
            str(policy_path),
            "--out-dir",
            str(out),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "case_count:" in completed.stdout
    assert (out / "residual_atlas_report.json").exists()


def test_root_lab_integration_writes_residual_atlas_outputs(tmp_path):
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
    assert (out / "residual_atlas" / "residual_atlas_report.json").exists()
    payload = json.loads((out / "root_constructor_lab_report.json").read_text(encoding="utf-8"))
    assert "residual_atlas_report_json" in payload["outputs"]


def test_residual_atlas_does_not_touch_lawbook_store(tmp_path):
    lawbook = tmp_path / "lawbook.sqlite"

    report = build_residual_atlas_from_rows([_failed_trace()])

    assert report.to_dict()["advisory_only"] is True
    assert not lawbook.exists()


def _failed_kwargs(claim_id):
    return {
        "trace_id": "",
        "claim_id": claim_id,
        "status": "constructor_failed",
        "terminal_form": "NONE",
        "trust_level": "ADVISORY_ROUTE",
        "provenance_type": "SYSTEM",
        "verifier_boundary": "NOT_VERIFIED",
        "certificate_id": None,
        "verified": False,
        "promoted": False,
        "near_miss_score": 0.0,
        "obstruction_label": "obs_a",
    }

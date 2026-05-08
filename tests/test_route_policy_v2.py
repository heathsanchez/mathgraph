import json
import subprocess
import sys
from pathlib import Path

from mathgraph.continuation_traces import ContinuationTraceStore
from mathgraph.replay_engine import ReplayReport, RouteReplaySignal
from mathgraph.route_policy_v2 import (
    build_route_policy_v2_from_replay,
    build_route_policy_v2_from_trace_store,
    write_route_policy_v2,
)
from tests.test_continuation_traces import _trace


def _signal(**overrides):
    data = {
        "route_key": "root|family|finite_countermodel_search",
        "root_label": "root",
        "constructor_family": "family",
        "attempts": 3,
        "verified": 0,
        "promoted": 0,
        "failures": 0,
        "residuals": 0,
        "near_misses": 0,
        "certificate_yield": 0.0,
        "near_miss_rate": 0.0,
        "residual_rate": 0.0,
        "mean_near_miss_score": 0.0,
        "mean_residual_compression_delta": 0.0,
        "route_strength_delta": 0.0,
        "recommendation": "insufficient_data",
        "evidence": {"advisory_only": True},
    }
    data.update(overrides)
    return RouteReplaySignal(**data)


def _replay(signals):
    return ReplayReport(
        run_id="replay_test",
        trace_count=sum(signal.attempts for signal in signals),
        route_signals=signals,
        root_summary={},
        constructor_summary={},
        obstruction_pressure=[],
        warnings=["Replay is advisory."],
        outputs={},
    )


def test_build_route_policy_v2_from_replay_creates_cards():
    report = build_route_policy_v2_from_replay(_replay([_signal()]))

    assert report.card_count == 1
    assert report.cards[0].route_key == "root|family|finite_countermodel_search"
    assert report.cards[0].evidence["advisory_only"] is True


def test_verified_route_gets_exploit_recommendation_and_high_priority():
    report = build_route_policy_v2_from_replay(
        _replay(
            [
                _signal(
                    verified=3,
                    promoted=2,
                    certificate_yield=1.0,
                    route_strength_delta=2.0,
                    recommendation="strengthen_route",
                )
            ]
        )
    )

    card = report.cards[0]
    assert card.recommendation == "exploit_verified_route"
    assert card.htilt_priority > 0.8


def test_high_near_miss_route_gets_explore_recommendation():
    report = build_route_policy_v2_from_replay(
        _replay(
            [
                _signal(
                    near_misses=3,
                    near_miss_rate=1.0,
                    mean_near_miss_score=0.9,
                    route_strength_delta=0.6,
                    recommendation="preserve_for_replay",
                )
            ]
        )
    )

    assert report.cards[0].recommendation == "explore_near_miss_route"


def test_repeated_structured_failure_gets_obstruction_recommendation():
    report = build_route_policy_v2_from_replay(
        _replay(
            [
                _signal(
                    failures=3,
                    residuals=0,
                    near_misses=2,
                    residual_rate=0.0,
                    near_miss_rate=0.667,
                    mean_near_miss_score=0.7,
                    recommendation="convert_to_obstruction_pressure",
                )
            ]
        )
    )

    assert report.cards[0].recommendation == "investigate_obstruction_route"
    assert report.cards[0].obstruction_pressure > 0


def test_low_value_repeated_residual_gets_suppressed():
    report = build_route_policy_v2_from_replay(
        _replay(
            [
                _signal(
                    residuals=3,
                    residual_rate=1.0,
                    route_strength_delta=-1.0,
                    recommendation="weaken_route",
                )
            ]
        )
    )

    assert report.cards[0].recommendation == "suppress_low_value_route"


def test_policy_outputs_are_written(tmp_path):
    report = build_route_policy_v2_from_replay(_replay([_signal(verified=1, certificate_yield=0.333)]))
    outputs = write_route_policy_v2(report, str(tmp_path))

    assert Path(outputs["route_policy_v2_report_json"]).exists()
    assert Path(outputs["route_policy_v2_cards_jsonl"]).exists()
    assert Path(outputs["route_policy_v2_report_md"]).exists()
    payload = json.loads(Path(outputs["route_policy_v2_report_json"]).read_text(encoding="utf-8"))
    assert payload["advisory_only"] is True


def test_cli_builds_policy_from_trace_store(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    trace_path = tmp_path / "traces.jsonl"
    ContinuationTraceStore(trace_path).append_many(
        [_trace(claim_id="a"), _trace(claim_id="b"), _trace(claim_id="c")]
    )
    out = tmp_path / "policy"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/build_route_policy_v2.py",
            "--traces",
            str(trace_path),
            "--out-dir",
            str(out),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "card_count:" in completed.stdout
    assert (out / "route_policy_v2_report.json").exists()
    assert (out / "route_policy_v2_cards.jsonl").exists()
    assert (out / "route_policy_v2_report.md").exists()


def test_build_from_trace_store_returns_json_serializable_report(tmp_path):
    trace_path = tmp_path / "traces.jsonl"
    ContinuationTraceStore(trace_path).append_many(
        [_trace(claim_id="a"), _trace(claim_id="b"), _trace(claim_id="c")]
    )

    report = build_route_policy_v2_from_trace_store(str(trace_path), out_dir=str(tmp_path / "policy"))

    json.dumps(report.to_dict())
    assert report.outputs["route_policy_v2_report_json"]

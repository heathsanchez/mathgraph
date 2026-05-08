import json
import subprocess
import sys
from pathlib import Path

from mathgraph.continuation_traces import ContinuationTraceStore
from mathgraph.replay_engine import replay_continuation_traces
from tests.test_continuation_traces import _trace


def test_replay_strengthens_route_with_verified_promoted_traces(tmp_path):
    path = tmp_path / "traces.jsonl"
    ContinuationTraceStore(path).append_many([_trace(claim_id="a"), _trace(claim_id="b")])

    report = replay_continuation_traces(str(path), str(tmp_path / "replay"))

    assert report.route_signals[0].recommendation == "strengthen_route"
    assert report.route_signals[0].verified == 2
    assert report.outputs["replay_report_json"]


def test_replay_converts_structured_failures_to_obstruction_pressure(tmp_path):
    path = tmp_path / "traces.jsonl"
    traces = [
        _trace(
            trace_id="",
            claim_id=f"fail{i}",
            status="constructor_failed",
            terminal_form="NONE",
            trust_level="ADVISORY_ROUTE",
            provenance_type="SYSTEM",
            verifier_boundary="NOT_VERIFIED",
            certificate_id=None,
            verified=False,
            promoted=False,
            near_miss_score=0.7,
            residual_compression_delta=0.0,
        )
        for i in range(2)
    ]
    ContinuationTraceStore(path).append_many(traces)

    report = replay_continuation_traces(str(path))

    assert report.route_signals[0].recommendation == "convert_to_obstruction_pressure"
    assert report.obstruction_pressure
    assert report.obstruction_pressure[0]["advisory_only"] is True


def test_replay_preserves_high_near_miss_route(tmp_path):
    path = tmp_path / "traces.jsonl"
    traces = [
        _trace(
            trace_id="",
            claim_id=f"near{i}",
            status="near_miss",
            terminal_form="NONE",
            trust_level="ADVISORY_ROUTE",
            provenance_type="SYSTEM",
            verifier_boundary="NOT_VERIFIED",
            certificate_id=None,
            verified=False,
            promoted=False,
            near_miss_score=0.9,
        )
        for i in range(2)
    ]
    ContinuationTraceStore(path).append_many(traces)

    report = replay_continuation_traces(str(path))

    assert report.route_signals[0].recommendation == "preserve_for_replay"


def test_replay_weakens_low_value_repeated_residual_route(tmp_path):
    path = tmp_path / "traces.jsonl"
    traces = [
        _trace(
            trace_id="",
            claim_id=f"res{i}",
            status="residual",
            terminal_form="NONE",
            trust_level="ADVISORY_ROUTE",
            provenance_type="SYSTEM",
            verifier_boundary="NOT_VERIFIED",
            certificate_id=None,
            verified=False,
            promoted=False,
            near_miss_score=0.0,
        )
        for i in range(2)
    ]
    ContinuationTraceStore(path).append_many(traces)

    report = replay_continuation_traces(str(path))

    assert report.route_signals[0].recommendation == "weaken_route"


def test_replay_cli_writes_outputs(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    path = tmp_path / "traces.jsonl"
    ContinuationTraceStore(path).append_many([_trace(claim_id="a"), _trace(claim_id="b")])
    out = tmp_path / "replay"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/replay_continuation_traces.py",
            "--traces",
            str(path),
            "--out-dir",
            str(out),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert (out / "replay_report.json").exists()
    assert (out / "replay_report.md").exists()
    assert (out / "route_signals.jsonl").exists()
    assert (out / "obstruction_pressure.jsonl").exists()
    payload = json.loads((out / "replay_report.json").read_text(encoding="utf-8"))
    assert payload["advisory_only"] is True


def test_replay_output_is_advisory_and_does_not_mutate_lawbook(tmp_path):
    trace_path = tmp_path / "traces.jsonl"
    lawbook_path = tmp_path / "lawbook.sqlite"
    ContinuationTraceStore(trace_path).append(_trace())

    report = replay_continuation_traces(str(trace_path))

    assert report.to_dict()["advisory_only"] is True
    assert not lawbook_path.exists()

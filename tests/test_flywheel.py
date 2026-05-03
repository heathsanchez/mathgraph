import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    Certificate,
    FlywheelConfig,
    FlywheelResult,
    FlywheelStageResult,
    TerminalForm,
    Trace,
    VerificationStatus,
    run_mathgraph_flywheel,
)


ROOT = Path(__file__).resolve().parents[1]


def _trace(source: str, target: str) -> Trace:
    return Trace(
        claim=f"{source}=>{target}",
        source=source,
        target=target,
        routes_tried=["variable_identification"],
        terminal_form=TerminalForm.VERIFIED_PROOF,
        verification_status=VerificationStatus.VERIFIED,
        certificate=Certificate(
            TerminalForm.VERIFIED_PROOF,
            f"{source}=>{target}",
            payload={
                "source_idx": source,
                "target_idx": target,
                "compiled_route": "variable_identification",
                "claim_hash": f"{source}->{target}",
                "lean_status": "lean_verified",
            },
        ),
        metadata={
            "source_idx": source,
            "target_idx": target,
            "compiled_route": "variable_identification",
            "claim_hash": f"{source}->{target}",
            "lean_status": "lean_verified",
        },
    )


def _write_traces(path: Path, traces: list[Trace] | None = None) -> None:
    traces = traces or [_trace("A", "B"), _trace("B", "C")]
    path.write_text(json.dumps([trace.to_dict() for trace in traces]), encoding="utf-8")


def test_dataclass_roundtrip() -> None:
    config = FlywheelConfig(traces_json="traces.json", out_dir="out")
    assert FlywheelConfig.from_dict(config.to_dict()) == config
    stage = FlywheelStageResult("stage", "completed", {"x": 1}, {"out": "path"}, ["warn"])
    assert FlywheelStageResult.from_dict(stage.to_dict()) == stage
    result = FlywheelResult(config.to_dict(), [stage.to_dict()], {"report": "r"}, ["warn"])
    assert FlywheelResult.from_dict(result.to_dict()) == result


def test_pipeline_runs_end_to_end_and_writes_expected_files(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    out = tmp_path / "flywheel"
    _write_traces(traces)
    result = run_mathgraph_flywheel(FlywheelConfig(str(traces), str(out)))
    expected = [
        "lawbook_store.sqlite",
        "derived_certificates.jsonl",
        "derived_certificates_summary.json",
        "pair_outcomes.jsonl",
        "pair_outcome_diagnostics.json",
        "route_policy.json",
        "route_policy_stats.json",
        "scheduled_tasks.jsonl",
        "scheduled_tasks_summary.json",
        "flywheel_report.json",
        "flywheel_report.md",
    ]
    for name in expected:
        assert (out / name).exists(), name
    stages = {stage["name"]: stage for stage in result.stages}
    assert stages["lawbook_store"]["summary"]["trace_count"] == 2
    assert stages["derived_certificates"]["summary"]["total_derived_count"] >= 1
    assert stages["outcome_dataset"]["summary"]["row_count"] >= 2
    assert set(stages) == {
        "lawbook_store",
        "derived_certificates",
        "outcome_dataset",
        "route_policy",
        "htilt_schedule",
    }


def test_derived_stage_can_run_with_zero_derived(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    out = tmp_path / "flywheel"
    _write_traces(traces, [_trace("A", "B")])
    result = run_mathgraph_flywheel(FlywheelConfig(str(traces), str(out)))
    stages = {stage["name"]: stage for stage in result.stages}
    assert stages["lawbook_store"]["summary"]["trace_count"] == 1
    assert stages["derived_certificates"]["summary"]["total_derived_count"] == 0


def test_scheduler_handles_no_unknown_pairs(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    out = tmp_path / "flywheel"
    _write_traces(traces)
    result = run_mathgraph_flywheel(FlywheelConfig(str(traces), str(out)))
    stages = {stage["name"]: stage for stage in result.stages}
    assert stages["htilt_schedule"]["summary"]["scheduled_count"] == 0
    assert "No candidate pair file supplied" in stages["htilt_schedule"]["warnings"][0]


def test_unknown_rows_are_not_promoted(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    unknown = tmp_path / "unknown.jsonl"
    out = tmp_path / "flywheel"
    _write_traces(traces)
    unknown.write_text(json.dumps({"source": "X", "target": "Y"}) + "\n", encoding="utf-8")
    run_mathgraph_flywheel(
        FlywheelConfig(str(traces), str(out), unknown_pairs_jsonl=str(unknown))
    )
    rows = [
        json.loads(line)
        for line in (out / "pair_outcomes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    unknown_rows = [row for row in rows if row["origin"] == "oracle_unknown"]
    assert unknown_rows
    assert all(row["terminal_form"] == "NAMED_OBSTRUCTION" for row in unknown_rows)
    assert all(row["verification_status"] == "UNKNOWN" for row in unknown_rows)


def test_cli_smoke(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    out = tmp_path / "flywheel"
    _write_traces(traces)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_mathgraph_flywheel.py"),
            "--traces-json",
            str(traces),
            "--out",
            str(out),
            "--schedule-top-k",
            "10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["final_report"]).exists()
    assert payload["primitive_count"] == 2
    assert payload["schedule_count"] == 0
    report = json.loads((out / "flywheel_report.json").read_text(encoding="utf-8"))
    assert len(report["stages"]) == 5

import json
import subprocess
import sys
from pathlib import Path

from mathgraph.continuation_traces import ContinuationTraceStore
from mathgraph.episode_runner_v2 import EpisodeRunnerV2Config, run_episode_v2
from mathgraph.terminal_contract import TerminalForm, TrustLevel, VerifierBoundary


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _finite_task(**overrides):
    row = {
        "task_id": "finite_false_1",
        "task_kind": "finite_countermodel_search",
        "source": "(x*x)=x",
        "target": "(x*y)=x",
        "source_idx": 1,
        "target_idx": 2,
        "route": "root_a|family_a|finite_countermodel_search",
        "constructor_family": "family_a",
        "root_label": "root_a",
        "priority": 0.9,
        "reason": "High membrane pressure / near-miss / route-policy priority.",
        "evidence": {"advisory_only": True, "residual_compression_delta": 0.25},
    }
    row.update(overrides)
    return row


def _advisory_task(**overrides):
    row = {
        "task_id": "advisory_1",
        "task_kind": "representation_shift_probe",
        "source": "(x*x)=x",
        "target": "(x*y)=x",
        "source_idx": 1,
        "target_idx": 2,
        "route": "root_a|family_a|representation_shift_probe",
        "constructor_family": "family_a",
        "root_label": "root_a",
        "priority": 0.7,
        "reason": "Saturated high-pressure membrane suggests representation shift.",
        "evidence": {"advisory_only": True},
    }
    row.update(overrides)
    return row


def test_episode_runner_loads_frontier_task_queue(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task(), _advisory_task()])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_load",
            "build_replay": False,
            "build_route_policy": False,
            "build_residual_atlas": False,
            "build_next_frontier": False,
        }
    )

    assert report.attempted_tasks == 2
    assert report.executable_tasks == 1
    assert report.advisory_tasks == 1
    assert Path(report.outputs["input_frontier_tasks_jsonl"]).exists()


def test_finite_countermodel_task_is_executable_and_can_promote(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task()])

    report = run_episode_v2(
        EpisodeRunnerV2Config(
            frontier_task_queue_jsonl=str(queue),
            out_dir=str(tmp_path / "episode"),
            store_path=str(tmp_path / "store.sqlite"),
            episode_id="episode_verified_false",
            build_replay=False,
            build_route_policy=False,
            build_residual_atlas=False,
            build_next_frontier=False,
        )
    )

    result = report.task_results[0]
    assert result.executable is True
    assert result.status == "verified_false"
    assert result.promoted is True
    assert result.certificate_id
    assert result.terminal_form == TerminalForm.REFUTATION_CERTIFICATE
    assert result.trust_level == TrustLevel.FINITE_VERIFIED
    assert result.verifier_boundary == VerifierBoundary.IMPORTER_REVALIDATED


def test_advisory_task_kinds_are_skipped_and_never_promoted(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_advisory_task(task_kind="obstruction_analysis")])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_advisory",
            "build_replay": False,
            "build_route_policy": False,
            "build_residual_atlas": False,
            "build_next_frontier": False,
        }
    )

    result = report.task_results[0]
    assert result.executable is False
    assert result.status == "skipped"
    assert result.promoted is False
    assert result.certificate_id is None
    assert result.evidence["not_executed_by_episode_runner_v2"] is True
    assert result.trust_level == TrustLevel.ADVISORY_ROUTE
    assert result.verifier_boundary == VerifierBoundary.NOT_VERIFIED


def test_finite_miss_is_not_proof(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task(task_id="finite_miss", source="(x*x)=x", target="(x*x)=x")])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_miss",
            "max_countermodel_order": 1,
            "exhaustive_order_limit": 1,
            "build_replay": False,
            "build_route_policy": False,
            "build_residual_atlas": False,
            "build_next_frontier": False,
        }
    )

    result = report.task_results[0]
    assert result.status in {"constructor_failed", "residual"}
    assert result.promoted is False
    assert result.terminal_form == TerminalForm.NONE
    assert result.trust_level == TrustLevel.ADVISORY_ROUTE


def test_traces_are_emitted_for_executable_and_advisory_tasks(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task(), _advisory_task()])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_traces",
            "build_replay": False,
            "build_route_policy": False,
            "build_residual_atlas": False,
            "build_next_frontier": False,
        }
    )
    traces = ContinuationTraceStore(report.outputs["continuation_traces_jsonl"]).load_all()

    assert len(traces) == 2
    assert {trace.status for trace in traces} == {"verified_false", "skipped"}
    assert any(trace.promoted for trace in traces)
    assert any(trace.evidence["task_result"]["evidence"].get("not_executed_by_episode_runner_v2") for trace in traces)


def test_audit_report_is_written_when_enabled(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task()])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_audit",
            "build_replay": False,
            "build_route_policy": False,
            "build_residual_atlas": False,
            "build_next_frontier": False,
        }
    )

    audit_path = Path(report.outputs["audit_report_json"])
    assert audit_path.exists()
    assert json.loads(audit_path.read_text(encoding="utf-8"))["passed"] is True


def test_learning_outputs_are_written_when_enabled(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task(), _advisory_task()])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_full_chain",
            "max_countermodel_order": 3,
        }
    )

    assert Path(report.outputs["replay_report_json"]).exists()
    assert Path(report.outputs["route_policy_v2_report_json"]).exists()
    assert Path(report.outputs["residual_atlas_report_json"]).exists()
    assert Path(report.outputs["frontier_v2_report_json"]).exists()
    assert Path(report.outputs["frontier_v2_task_queue_jsonl"]).exists()


def test_episode_runner_cli_smoke(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    queue = tmp_path / "frontier.jsonl"
    out = tmp_path / "episode"
    _write_jsonl(queue, [_finite_task(), _advisory_task()])

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_episode_v2.py",
            "--frontier-task-queue",
            str(queue),
            "--store",
            str(tmp_path / "store.sqlite"),
            "--out-dir",
            str(out),
            "--episode-id",
            "episode_cli",
            "--max-countermodel-order",
            "3",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "episode_id: episode_cli" in completed.stdout
    assert (out / "episode_v2_report.json").exists()
    assert (out / "episode_v2_report.md").exists()


def test_report_json_and_markdown_are_written(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_advisory_task()])

    report = run_episode_v2(
        {
            "frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "episode"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episode_id": "episode_reports",
            "build_replay": False,
            "build_route_policy": False,
            "build_residual_atlas": False,
            "build_next_frontier": False,
        }
    )

    report_json = Path(report.outputs["episode_v2_report_json"])
    report_md = Path(report.outputs["episode_v2_report_md"])
    assert report_json.exists()
    assert report_md.exists()
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["advisory_outputs"] is True
    assert "Trust Boundary" in report_md.read_text(encoding="utf-8")


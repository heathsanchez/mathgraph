import json
import subprocess
import sys
from pathlib import Path

from mathgraph.multi_episode_harness import (
    EpisodeSummaryRow,
    MultiEpisodeConfig,
    MultiEpisodeReport,
    run_multi_episode_harness,
)
from mathgraph.terminal_contract import TerminalForm, TrustLevel, VerifierBoundary


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _finite_task(**overrides):
    row = {
        "task_id": "multi_finite_false_1",
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
        "task_id": "multi_advisory_1",
        "task_kind": "obstruction_analysis",
        "source": "(x*x)=x",
        "target": "(x*y)=x",
        "source_idx": 1,
        "target_idx": 2,
        "route": "root_a|family_a|obstruction_analysis",
        "constructor_family": "family_a",
        "root_label": "root_a",
        "priority": 0.7,
        "reason": "Repeated structured failure should be named.",
        "evidence": {"advisory_only": True},
    }
    row.update(overrides)
    return row


def test_harness_runs_at_least_two_episodes_on_small_frontier(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task(), _advisory_task()])

    report = run_multi_episode_harness(
        MultiEpisodeConfig(
            initial_frontier_task_queue_jsonl=str(queue),
            out_dir=str(tmp_path / "multi"),
            store_path=str(tmp_path / "store.sqlite"),
            episodes=2,
            max_tasks_per_episode=10,
            stop_if_no_frontier=False,
            run_id="multi_two",
        )
    )

    assert report.episode_count == 2
    assert report.summaries[0].frontier_task_count == 2
    assert report.summaries[1].episode_index == 1


def test_report_json_markdown_and_jsonl_are_written(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task()])

    report = run_multi_episode_harness(
        {
            "initial_frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "multi"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episodes": 1,
            "run_id": "multi_outputs",
        }
    )

    assert Path(report.outputs["multi_episode_report_json"]).exists()
    assert Path(report.outputs["multi_episode_report_md"]).exists()
    assert Path(report.outputs["episode_summaries_jsonl"]).exists()


def test_episode_summary_row_contains_expected_fields(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task()])

    report = run_multi_episode_harness(
        {
            "initial_frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "multi"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episodes": 1,
        }
    )
    row = EpisodeSummaryRow.from_dict(report.summaries[0].to_dict())

    assert row.episode_index == 0
    assert row.episode_id
    assert isinstance(row.outputs, dict)
    assert row.better_shaped_unknown_score >= 0.0


def test_compounding_metrics_are_diagnostic_not_truth(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task(), _advisory_task()])

    report = run_multi_episode_harness(
        {
            "initial_frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "multi"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episodes": 2,
            "stop_if_no_frontier": False,
        }
    )
    payload = MultiEpisodeReport.from_dict(report.to_dict()).to_dict()

    assert payload["diagnostic_only"] is True
    assert "Compounding score does not verify or refute any claim." in payload["warnings"]
    assert isinstance(payload["compounding_score"], float)


def test_harness_stops_if_no_next_frontier(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task()])

    report = run_multi_episode_harness(
        {
            "initial_frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "multi"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episodes": 3,
            "stop_if_no_frontier": True,
        }
    )

    assert report.episode_count == 1
    assert any("next frontier is empty" in warning for warning in report.warnings)


def test_multi_episode_cli_runs(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    queue = tmp_path / "frontier.jsonl"
    out = tmp_path / "multi"
    _write_jsonl(queue, [_finite_task()])

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_multi_episode_harness.py",
            "--initial-frontier-task-queue",
            str(queue),
            "--store",
            str(tmp_path / "store.sqlite"),
            "--out-dir",
            str(out),
            "--episodes",
            "1",
            "--max-countermodel-order",
            "3",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "run_id:" in completed.stdout
    assert (out / "multi_episode_report.json").exists()


def test_promoted_certificates_come_from_episode_runner_v2_path(tmp_path):
    queue = tmp_path / "frontier.jsonl"
    _write_jsonl(queue, [_finite_task()])

    report = run_multi_episode_harness(
        {
            "initial_frontier_task_queue_jsonl": str(queue),
            "out_dir": str(tmp_path / "multi"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episodes": 1,
        }
    )
    episode_report = json.loads(
        Path(report.summaries[0].outputs["episode_v2_report_json"]).read_text(encoding="utf-8")
    )
    result = episode_report["task_results"][0]

    assert result["status"] == "verified_false"
    assert result["terminal_form"] == TerminalForm.REFUTATION_CERTIFICATE
    assert result["trust_level"] == TrustLevel.FINITE_VERIFIED
    assert result["verifier_boundary"] == VerifierBoundary.IMPORTER_REVALIDATED
    assert result["evidence"]["importer"]["imported"] is True


def test_missing_frontier_creates_warning_not_crash(tmp_path):
    report = run_multi_episode_harness(
        {
            "initial_frontier_task_queue_jsonl": str(tmp_path / "missing.jsonl"),
            "out_dir": str(tmp_path / "multi"),
            "store_path": str(tmp_path / "store.sqlite"),
            "episodes": 1,
        }
    )

    assert report.episode_count == 0
    assert report.status == "completed"
    assert report.warnings


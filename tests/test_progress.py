import json
import subprocess
import sys
from pathlib import Path

import pytest

from mathgraph import Kernel
from mathgraph.progress import ProgressLogger, iter_with_progress


ROOT = Path(__file__).resolve().parents[1]


def test_progress_logger_writes_jsonl_events(tmp_path: Path) -> None:
    log = tmp_path / "progress.jsonl"
    logger = ProgressLogger("test", log_jsonl=log, heartbeat_sec=0, enabled=False)
    with logger.stage("work", total=3) as stage:
        for _i, _item in stage.iter([1, 2, 3], every=1):
            pass
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert events[0]["event"] == "stage_start"
    assert events[-1]["event"] == "stage_done"
    assert events[-1]["count"] == 3


def test_stage_context_manager_records_failed(tmp_path: Path) -> None:
    log = tmp_path / "progress.jsonl"
    logger = ProgressLogger("test", log_jsonl=log)
    with pytest.raises(RuntimeError):
        with logger.stage("boom"):
            raise RuntimeError("nope")
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event"] == "stage_failed"
    assert events[-1]["error"] == "nope"


def test_iter_with_progress_counts(tmp_path: Path) -> None:
    log = tmp_path / "progress.jsonl"
    logger = ProgressLogger("test", log_jsonl=log, heartbeat_sec=0)
    seen = list(iter_with_progress(["a", "b"], logger, "letters", total=2, every=1))
    assert seen == [(1, "a"), (2, "b")]
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["count"] == 2


def test_build_lawbook_store_cli_progress_jsonl(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    trace = Kernel().prove("x = x", "x = x")
    traces.write_text(json.dumps([trace.to_dict()]), encoding="utf-8")
    progress = tmp_path / "progress.jsonl"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_store.py"),
            "--traces-json",
            str(traces),
            "--out",
            str(tmp_path / "lawbook.sqlite"),
            "--replace",
            "--progress-jsonl",
            str(progress),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    events = [json.loads(line) for line in progress.read_text(encoding="utf-8").splitlines()]
    assert any(event["event"] == "stage_start" for event in events)
    assert any(event["event"] == "stage_done" for event in events)

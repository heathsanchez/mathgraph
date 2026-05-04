"""Small stdout/JSONL progress helpers for long-running MathGraph commands."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


class ProgressLogger:
    def __init__(
        self,
        name: str,
        log_jsonl: str | Path | None = None,
        heartbeat_sec: float = 10.0,
        enabled: bool = False,
        quiet: bool = False,
    ) -> None:
        self.name = name
        self.log_jsonl = Path(log_jsonl) if log_jsonl else None
        self.heartbeat_sec = float(heartbeat_sec)
        self.enabled = bool(enabled)
        self.quiet = bool(quiet)
        if self.log_jsonl:
            self.log_jsonl.parent.mkdir(parents=True, exist_ok=True)

    def stage(self, name: str, total: int | None = None, **metadata: Any) -> "StageTimer":
        return StageTimer(self, name=name, total=total, metadata=metadata)

    def event(self, event: str, stage: str | None = None, **payload: Any) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "logger": self.name,
            "event": event,
            "stage": stage,
            **payload,
        }
        if self.log_jsonl:
            with self.log_jsonl.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        if self.enabled and not self.quiet:
            print(_format_event(record), flush=True)


@dataclass
class StageTimer:
    logger: ProgressLogger
    name: str
    total: int | None = None
    metadata: dict[str, Any] | None = None
    count: int = 0
    _started: float = 0.0
    _last_emit: float = 0.0

    def __enter__(self) -> "StageTimer":
        self._started = time.perf_counter()
        self._last_emit = self._started
        self.logger.event("stage_start", self.name, total=self.total, **(self.metadata or {}))
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, tb: Any) -> bool:
        elapsed = time.perf_counter() - self._started
        if exc is None:
            self.logger.event("stage_done", self.name, count=self.count, elapsed_sec=elapsed, rate=_rate(self.count, elapsed))
        else:
            self.logger.event(
                "stage_failed",
                self.name,
                count=self.count,
                elapsed_sec=elapsed,
                error=str(exc),
                error_type=getattr(exc_type, "__name__", str(exc_type)),
            )
        return False

    def update(self, count: int | None = None, every: int | None = None, **payload: Any) -> None:
        self.count = self.count + 1 if count is None else int(count)
        now = time.perf_counter()
        should_emit = (now - self._last_emit) >= self.logger.heartbeat_sec
        if every and self.count % int(every) == 0:
            should_emit = True
        if should_emit:
            elapsed = now - self._started
            self.logger.event(
                "stage_progress",
                self.name,
                count=self.count,
                total=self.total,
                elapsed_sec=elapsed,
                rate=_rate(self.count, elapsed),
                **payload,
            )
            self._last_emit = now

    def iter(self, items: Iterable[Any], every: int | None = None) -> Iterator[tuple[int, Any]]:
        for index, item in enumerate(items, start=1):
            self.update(index, every=every)
            yield index, item


def iter_with_progress(
    items: Iterable[Any],
    logger: ProgressLogger,
    stage_name: str,
    total: int | None = None,
    every: int | None = None,
) -> Iterator[tuple[int, Any]]:
    with logger.stage(stage_name, total=total) as stage:
        yield from stage.iter(items, every=every)


def stream_subprocess(
    cmd: list[str],
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
    timeout_sec: float | None = None,
    heartbeat_sec: float = 10.0,
    logger: ProgressLogger | None = None,
    stage: str = "subprocess",
) -> dict[str, Any]:
    started = time.perf_counter()
    output = Path(log_path) if log_path else None
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    last_output = time.perf_counter()
    timed_out = False
    assert proc.stdout is not None
    with (output.open("w", encoding="utf-8") if output else _NullWriter()) as handle:
        while True:
            line = proc.stdout.readline()
            now = time.perf_counter()
            if line:
                lines.append(line)
                handle.write(line)
                handle.flush()
                print(line, end="", flush=True)
                last_output = now
            elif proc.poll() is not None:
                break
            else:
                if timeout_sec is not None and now - started > timeout_sec:
                    timed_out = True
                    proc.kill()
                    break
                if now - last_output >= heartbeat_sec:
                    if logger:
                        logger.event("heartbeat", stage, elapsed_sec=now - started, command=" ".join(cmd))
                    else:
                        print(f"[{stage}] heartbeat elapsed={now - started:.1f}s", flush=True)
                    last_output = now
                time.sleep(0.1)
    return {
        "cmd": cmd,
        "returncode": proc.wait(),
        "timed_out": timed_out,
        "elapsed_sec": time.perf_counter() - started,
        "log_path": str(output) if output else None,
        "line_count": len(lines),
    }


class _NullWriter:
    def __enter__(self) -> "_NullWriter":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def write(self, _text: str) -> None:
        return None

    def flush(self) -> None:
        return None


def _rate(count: int, elapsed: float) -> float | None:
    return (count / elapsed) if elapsed > 0 else None


def _format_event(record: dict[str, Any]) -> str:
    stage = record.get("stage") or record["logger"]
    event = record["event"]
    if event == "stage_start":
        suffix = f" total={record.get('total')}" if record.get("total") is not None else ""
        return f"[{stage}] start{suffix}"
    if event == "stage_progress":
        total = record.get("total")
        progress = f"{record.get('count')}/{total}" if total is not None else str(record.get("count"))
        return f"[{stage}] progress {progress} elapsed={record.get('elapsed_sec', 0):.1f}s rate={record.get('rate') or 0:.1f}/s"
    if event == "stage_done":
        return f"[{stage}] done count={record.get('count')} elapsed={record.get('elapsed_sec', 0):.1f}s"
    if event == "stage_failed":
        return f"[{stage}] failed count={record.get('count')} elapsed={record.get('elapsed_sec', 0):.1f}s error={record.get('error')}"
    if event == "heartbeat":
        return f"[{stage}] heartbeat elapsed={record.get('elapsed_sec', 0):.1f}s"
    return f"[{stage}] {event}"

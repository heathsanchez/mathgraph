"""Append-only continuation trace memory for advisory replay.

Continuation traces remember how a claim became reachable, failed, or remained
residual. They are memory records, not proof objects, and replay over them is
route pressure only.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from mathgraph.hashing import content_id

TRACE_STATUSES = {
    "known_certificate_found",
    "verified_false",
    "verified_true",
    "constructor_failed",
    "parse_failed",
    "verification_failed",
    "residual",
    "near_miss",
    "obstruction_recorded",
    "skipped",
    "error",
}


@dataclass(frozen=True)
class ContinuationTrace:
    trace_id: str
    episode_id: str
    claim_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    root_label: str | None
    root_score: float | None
    basin_label: str | None
    detector_evidence: dict[str, Any]
    route_type: str
    constructor_family: str | None
    constructor_config: dict[str, Any]
    status: str
    terminal_form: str | None
    trust_level: str | None
    provenance_type: str | None
    verifier_boundary: str | None
    certificate_id: str | None
    obstruction_label: str | None
    attempted: bool
    verified: bool
    promoted: bool
    known_skipped: bool
    near_miss_score: float
    residual_compression_delta: float
    novelty_score: float
    elapsed_sec: float
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.status not in TRACE_STATUSES:
            raise ValueError(f"unknown continuation trace status: {self.status}")
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContinuationTrace":
        payload = dict(data)
        return cls(
            trace_id=str(payload.get("trace_id") or make_trace_id(payload)),
            episode_id=str(payload.get("episode_id") or ""),
            claim_id=str(payload.get("claim_id") or ""),
            source=str(payload.get("source") or ""),
            target=str(payload.get("target") or ""),
            source_idx=_optional_int(payload.get("source_idx")),
            target_idx=_optional_int(payload.get("target_idx")),
            root_label=_optional_str(payload.get("root_label")),
            root_score=_optional_float(payload.get("root_score")),
            basin_label=_optional_str(payload.get("basin_label")),
            detector_evidence=dict(payload.get("detector_evidence") or {}),
            route_type=str(payload.get("route_type") or "unknown_route"),
            constructor_family=_optional_str(payload.get("constructor_family")),
            constructor_config=dict(payload.get("constructor_config") or {}),
            status=str(payload.get("status") or "residual"),
            terminal_form=_optional_str(payload.get("terminal_form")),
            trust_level=_optional_str(payload.get("trust_level")),
            provenance_type=_optional_str(payload.get("provenance_type")),
            verifier_boundary=_optional_str(payload.get("verifier_boundary")),
            certificate_id=_optional_str(payload.get("certificate_id")),
            obstruction_label=_optional_str(payload.get("obstruction_label")),
            attempted=bool(payload.get("attempted", False)),
            verified=bool(payload.get("verified", False)),
            promoted=bool(payload.get("promoted", False)),
            known_skipped=bool(payload.get("known_skipped", False)),
            near_miss_score=float(payload.get("near_miss_score") or 0.0),
            residual_compression_delta=float(payload.get("residual_compression_delta") or 0.0),
            novelty_score=float(payload.get("novelty_score") or 0.0),
            elapsed_sec=float(payload.get("elapsed_sec") or 0.0),
            warnings=list(payload.get("warnings") or []),
            evidence=dict(payload.get("evidence") or {}),
            created_at=str(payload.get("created_at") or ""),
        )


def make_trace_id(payload: dict[str, Any]) -> str:
    stable = dict(payload)
    stable.pop("trace_id", None)
    stable.pop("created_at", None)
    return content_id("trace", stable, n=24)


class ContinuationTraceStore:
    def __init__(self, path: str | Path, *, strict: bool = True) -> None:
        self.path = Path(path)
        self.strict = strict

    def append(self, trace: ContinuationTrace) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace.to_dict(), sort_keys=True) + "\n")

    def append_many(self, traces: Iterable[ContinuationTrace]) -> int:
        rows = list(traces)
        if not rows:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for trace in rows:
                handle.write(json.dumps(trace.to_dict(), sort_keys=True) + "\n")
        return len(rows)

    def load_all(self) -> list[ContinuationTrace]:
        if not self.path.exists():
            return []
        traces: list[ContinuationTrace] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    traces.append(ContinuationTrace.from_dict(json.loads(line)))
                except Exception:
                    if self.strict:
                        raise ValueError(f"malformed continuation trace at {self.path}:{lineno}")
        return traces

    def filter_by_episode(self, episode_id: str) -> list[ContinuationTrace]:
        return [trace for trace in self.load_all() if trace.episode_id == episode_id]

    def filter_by_root(self, root_label: str) -> list[ContinuationTrace]:
        return [trace for trace in self.load_all() if trace.root_label == root_label]

    def filter_by_constructor(self, constructor_family: str) -> list[ContinuationTrace]:
        return [trace for trace in self.load_all() if trace.constructor_family == constructor_family]

    def filter_by_status(self, status: str) -> list[ContinuationTrace]:
        return [trace for trace in self.load_all() if trace.status == status]

    def summary(self) -> dict[str, Any]:
        traces = self.load_all()
        by_status = Counter(trace.status for trace in traces)
        by_root = Counter(trace.root_label or "none" for trace in traces)
        by_constructor = Counter(trace.constructor_family or "none" for trace in traces)
        return {
            "trace_count": len(traces),
            "by_status": dict(sorted(by_status.items())),
            "by_root": dict(sorted(by_root.items())),
            "by_constructor_family": dict(sorted(by_constructor.items())),
            "verified_count": sum(1 for trace in traces if trace.verified),
            "promoted_count": sum(1 for trace in traces if trace.promoted),
            "near_miss_count": sum(1 for trace in traces if trace.status == "near_miss" or trace.near_miss_score > 0),
            "obstruction_count": sum(1 for trace in traces if trace.status == "obstruction_recorded"),
            "residual_count": sum(1 for trace in traces if trace.status == "residual"),
        }


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)

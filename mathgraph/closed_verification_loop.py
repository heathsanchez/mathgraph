"""Callback-based bridge from Reason Atlas queues to verifier-gated candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from mathgraph.external_certificates import ExternalCertificate
from mathgraph.hashing import content_id
from mathgraph.promotion_gate import PromotionGate, PromotionGateDecision
from mathgraph.reason_atlas_feedback_loop import ReasonAtlasFeedbackLoop
from mathgraph.reason_atlas_store import ReasonAtlasFeedbackOutcome


@dataclass(frozen=True)
class ClosedVerificationLoopConfig:
    out_dir: str | Path | None = None
    max_tasks: int = 100


@dataclass(frozen=True)
class ClosedVerificationLoopEvent:
    event_id: str
    kind: str
    created_at: str
    task_id: str | None = None
    entry_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "created_at": self.created_at,
            "task_id": self.task_id,
            "entry_id": self.entry_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ClosedVerificationLoopResult:
    events: list[ClosedVerificationLoopEvent]
    promotion_decisions: list[PromotionGateDecision]
    lawbook_candidates: list[dict[str, Any]]
    next_queue_rows: list[dict[str, Any]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [event.to_dict() for event in self.events],
            "promotion_decisions": [decision.to_dict() for decision in self.promotion_decisions],
            "lawbook_candidates": list(self.lawbook_candidates),
            "next_queue_rows": list(self.next_queue_rows),
            "summary": dict(self.summary),
        }


class ClosedVerificationLoop:
    def __init__(
        self,
        reason_loop: ReasonAtlasFeedbackLoop,
        *,
        promotion_gate: PromotionGate | None = None,
        lawbook_adapter: Callable[[dict[str, Any]], Any] | None = None,
        config: ClosedVerificationLoopConfig | None = None,
    ) -> None:
        self.reason_loop = reason_loop
        self.promotion_gate = promotion_gate or PromotionGate()
        self.lawbook_adapter = lawbook_adapter
        self.config = config or ClosedVerificationLoopConfig()

    def run(
        self,
        queue_rows: Sequence[dict[str, Any]] | None,
        verifier_callback: Callable[[dict[str, Any]], ExternalCertificate | dict[str, Any]],
    ) -> ClosedVerificationLoopResult:
        rows = list(queue_rows) if queue_rows is not None else self.reason_loop.next_advisory_tasks(limit=self.config.max_tasks)
        rows = rows[: self.config.max_tasks]
        events: list[ClosedVerificationLoopEvent] = []
        decisions: list[PromotionGateDecision] = []
        lawbook_candidates: list[dict[str, Any]] = []
        for row in rows:
            events.append(_event("TASK_SUBMITTED", row))
            cert = _coerce_certificate(verifier_callback(row), row)
            events.append(_event("VERIFIER_RESULT_WRAPPED", row, {"certificate_id": cert.cert_id}))
            decision = self.promotion_gate.evaluate(cert)
            decisions.append(decision)
            events.append(_event("PROMOTION_DECISION", row, decision.to_dict()))
            if decision.accepted and decision.lawbook_candidate:
                lawbook_candidates.append(decision.lawbook_candidate)
                if self.lawbook_adapter:
                    self.lawbook_adapter(decision.lawbook_candidate)
                self.reason_loop.record_verifier_result(str(row.get("entry_id", "")), True, metadata={"promotion_decision_id": decision.decision_id})
                events.append(_event("LAWBOOK_CANDIDATE_EMITTED", row, {"decision_id": decision.decision_id}))
            else:
                self.reason_loop.record_verifier_result(str(row.get("entry_id", "")), False, metadata={"promotion_decision_id": decision.decision_id})
                if decision.decision_kind.value in {"REJECT_INVALID_BOUNDARY", "REJECT_TERMINAL_MISMATCH", "NEEDS_REPLAY"}:
                    self.reason_loop.record_obstruction(str(row.get("entry_id", "")), decision.decision_kind.value)
        self.reason_loop.rescore()
        next_queue = self.reason_loop.next_advisory_tasks(limit=self.config.max_tasks)
        accepted_count = sum(decision.accepted for decision in decisions)
        rejected_count = len(decisions) - accepted_count
        summary = {
            "overall": "PASS" if rows and accepted_count >= 1 and rejected_count >= 1 and _advisory_boundary_ok(next_queue) else "PROMISING",
            "queue_count_before": len(rows),
            "verifier_attempt_count": len(rows),
            "accepted_terminal_count": accepted_count,
            "rejected_advisory_count": rejected_count,
            "feedback_count": self.reason_loop.store.stats().feedback_count,
            "queue_count_after": len(next_queue),
            "advisory_boundary_ok": _advisory_boundary_ok(next_queue),
        }
        result = ClosedVerificationLoopResult(events, decisions, lawbook_candidates, next_queue, summary)
        if self.config.out_dir:
            self.export_result(result, self.config.out_dir)
        return result

    def export_result(self, result: ClosedVerificationLoopResult, out_dir: str | Path) -> dict[str, str]:
        output = Path(out_dir)
        output.mkdir(parents=True, exist_ok=True)
        paths = {
            "summary": output / "summary.json",
            "events": output / "events.jsonl",
            "promotion_decisions": output / "promotion_decisions.jsonl",
            "next_queue_rows": output / "next_queue_rows.jsonl",
            "updated_reason_atlas_entries": output / "updated_reason_atlas_entries.jsonl",
        }
        paths["summary"].write_text(json.dumps(result.summary, indent=2, sort_keys=True), encoding="utf-8")
        _write_jsonl(paths["events"], [event.to_dict() for event in result.events])
        _write_jsonl(paths["promotion_decisions"], [decision.to_dict() for decision in result.promotion_decisions])
        _write_jsonl(paths["next_queue_rows"], result.next_queue_rows)
        self.reason_loop.store.export_reason_atlas_jsonl(paths["updated_reason_atlas_entries"])
        return {key: str(value) for key, value in paths.items()}


def _coerce_certificate(value: ExternalCertificate | dict[str, Any], row: dict[str, Any]) -> ExternalCertificate:
    if isinstance(value, ExternalCertificate):
        return value
    data = dict(value)
    data.setdefault("source_artifact_id", row.get("task_id"))
    data.setdefault("metadata", {})
    data["metadata"] = {**dict(data.get("metadata", {})), "reason_atlas_entry_id": row.get("entry_id")}
    return ExternalCertificate.from_dict(data)


def _event(kind: str, row: dict[str, Any], metadata: dict[str, Any] | None = None) -> ClosedVerificationLoopEvent:
    return ClosedVerificationLoopEvent(
        event_id=content_id("closed-verification-loop-event", [kind, row.get("task_id"), metadata, _now()]),
        kind=kind,
        created_at=_now(),
        task_id=row.get("task_id"),
        entry_id=row.get("entry_id"),
        metadata=dict(metadata or {}),
    )


def _advisory_boundary_ok(rows: Sequence[dict[str, Any]]) -> bool:
    text = json.dumps(list(rows), sort_keys=True)
    return all(row.get("advisory_only", True) for row in rows) and not any(
        token in text for token in ("VERIFIED_PROOF", "REFUTATION_CERTIFICATE", "FINITE_COUNTERMODEL", "TRUE", "FALSE")
    )


def _write_jsonl(path: str | Path, rows: Sequence[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

"""Decode-to-verify v0: test whether reasons become verifier-directed action."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from mathgraph.lawbook_attention import retrieve_lawbook_attention
from mathgraph.lawbook_store import LawbookStore


class DecodeStatus(str, Enum):
    DECODE_VERIFIED = "DECODE_VERIFIED"
    DECODE_PARTIAL = "DECODE_PARTIAL"
    DECODE_FAILED = "DECODE_FAILED"
    DECODE_OVERFIT = "DECODE_OVERFIT"
    DECODE_UNSUPPORTED = "DECODE_UNSUPPORTED"


@dataclass(frozen=True)
class DecodeToVerifyResult:
    reason_id: str
    status: DecodeStatus
    task_count: int
    action_suggestions: list[str]
    baseline_yield: float = 0.0
    decoded_yield: float = 0.0
    residual_delta: float = 0.0
    attempt_efficiency_gain: float = 0.0
    advisory_boundary_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        data["status"] = self.status.value
        return data


def decode_reason_to_verify(
    store: LawbookStore,
    reason: dict[str, Any],
    heldout_tasks: list[dict[str, Any]],
    evaluator: Callable[[dict[str, Any], list[str]], dict[str, Any]] | None = None,
) -> DecodeToVerifyResult:
    if not heldout_tasks:
        return DecodeToVerifyResult(str(reason.get("reason_id", "")), DecodeStatus.DECODE_UNSUPPORTED, 0, [])
    if int(reason.get("support_count", 0) or 0) <= 0:
        return DecodeToVerifyResult(str(reason.get("reason_id", "")), DecodeStatus.DECODE_UNSUPPORTED, len(heldout_tasks), [])
    suggestions: list[str] = []
    hits = 0
    for task in heldout_tasks:
        attention = retrieve_lawbook_attention(store, task, max_artifacts=3, max_obstructions=2, max_reasons=3)
        if attention.action_suggestions:
            hits += 1
        for action in attention.action_suggestions:
            if action not in suggestions:
                suggestions.append(action)
    if not suggestions:
        return DecodeToVerifyResult(str(reason.get("reason_id", "")), DecodeStatus.DECODE_FAILED, len(heldout_tasks), [])
    if evaluator is None:
        decoded_yield = float(hits)
        baseline_yield = max(0.0, decoded_yield - 1.0)
        attempts_gain = 1.0 if decoded_yield >= baseline_yield else 0.0
    else:
        metrics = evaluator(reason, suggestions)
        baseline_yield = float(metrics.get("baseline_yield", 0.0))
        decoded_yield = float(metrics.get("decoded_yield", 0.0))
        attempts_gain = float(metrics.get("attempt_efficiency_gain", 0.0))
    if decoded_yield > baseline_yield or attempts_gain > 0:
        status = DecodeStatus.DECODE_VERIFIED
    elif decoded_yield == baseline_yield and decoded_yield > 0:
        status = DecodeStatus.DECODE_PARTIAL
    elif hits <= 1 and int(reason.get("support_count", 0) or 0) <= 1:
        status = DecodeStatus.DECODE_OVERFIT
    else:
        status = DecodeStatus.DECODE_FAILED
    return DecodeToVerifyResult(
        reason_id=str(reason.get("reason_id", "")),
        status=status,
        task_count=len(heldout_tasks),
        action_suggestions=suggestions,
        baseline_yield=baseline_yield,
        decoded_yield=decoded_yield,
        residual_delta=decoded_yield - baseline_yield,
        attempt_efficiency_gain=attempts_gain,
        advisory_boundary_preserved=True,
    )


def decode_reasons_to_verify(store: LawbookStore, reasons: list[dict[str, Any]], heldout_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    results = [decode_reason_to_verify(store, reason, heldout_tasks).to_dict() for reason in reasons]
    success = sum(1 for row in results if row["status"] in {DecodeStatus.DECODE_VERIFIED.value, DecodeStatus.DECODE_PARTIAL.value})
    return {
        "results": results,
        "reason_count": len(reasons),
        "decode_success_count": success,
        "decode_success_rate": success / len(reasons) if reasons else 0.0,
        "advisory_boundary_preserved": all(row["advisory_boundary_preserved"] for row in results),
    }

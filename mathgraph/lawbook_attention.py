"""Sparse Lawbook attention for compounding verifier-directed search."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.lawbook_store import LawbookStore


@dataclass(frozen=True)
class LawbookAttentionTraceItem:
    item_id: str
    item_type: str
    score: float
    why_retrieved: list[str]
    action_suggestion: str
    verified: bool
    cannot_prove: str = "Retrieved context is not a verifier result for the current task."

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class LawbookAttentionResult:
    artifacts: list[dict[str, Any]]
    obstructions: list[dict[str, Any]]
    reasons: list[dict[str, Any]]
    attention_trace: list[dict[str, Any]]
    action_suggestions: list[str]
    advisory_boundary_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def retrieve_lawbook_attention(
    store: LawbookStore,
    task: dict[str, Any],
    *,
    max_artifacts: int = 5,
    max_obstructions: int = 5,
    max_reasons: int = 5,
) -> LawbookAttentionResult:
    context = store.retrieve_candidate_context(task, max_artifacts=max_artifacts * 4, max_obstructions=max_obstructions * 4, max_reasons=max_reasons * 4)
    artifacts = _rank(context["artifacts"], task, "artifact")[:max_artifacts]
    obstructions = _rank(context["obstructions"], task, "obstruction")[:max_obstructions]
    reasons = _rank(context["reasons"], task, "reason")[:max_reasons]
    trace = [_trace(row, task, "artifact") for row in artifacts] + [_trace(row, task, "obstruction") for row in obstructions] + [_trace(row, task, "reason") for row in reasons]
    suggestions = []
    for item in trace:
        if item.action_suggestion not in suggestions:
            suggestions.append(item.action_suggestion)
    return LawbookAttentionResult(
        artifacts=artifacts,
        obstructions=obstructions,
        reasons=reasons,
        attention_trace=[item.to_dict() for item in trace],
        action_suggestions=suggestions,
        advisory_boundary_preserved=True,
        metadata={"task_id": task.get("task_id") or task.get("claim_id")},
    )


def _rank(rows: list[dict[str, Any]], task: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    scored = []
    for row in rows:
        score, why = _score(row, task, kind)
        scored.append((score, why, row))
    scored.sort(key=lambda item: (-item[0], str(item[2].get("created_at", ""))))
    out = []
    for score, why, row in scored:
        item = dict(row)
        item["_attention_score"] = score
        item["_why"] = why
        out.append(item)
    return out


def _score(row: dict[str, Any], task: dict[str, Any], kind: str) -> tuple[float, list[str]]:
    score = 0.0
    why = []
    comparisons = [
        ("domain", 4.0),
        ("source_id", 5.0),
        ("target_id", 5.0),
        ("basin", 6.0),
        ("micro_basin", 3.0),
    ]
    task_basin = task.get("basin") or task.get("family")
    task_values = {**task, "basin": task_basin}
    for field, weight in comparisons:
        if row.get(field) and task_values.get(field) and str(row.get(field)) == str(task_values.get(field)):
            score += weight
            why.append(f"same {field}")
    if kind == "artifact":
        if row.get("terminal_form") in {"VERIFIED_PROOF", "FINITE_COUNTERMODEL", "NAMED_OBSTRUCTION"}:
            score += 8.0
            why.append("verified terminal memory")
        elif any(r.get("terminal_form") in {"VERIFIED_PROOF", "FINITE_COUNTERMODEL", "NAMED_OBSTRUCTION"} for r in [row]):
            pass
        else:
            score -= 1.0
            why.append("advisory-only penalty")
    if kind == "reason":
        score += float(row.get("decode_success_count", 0) or 0) * 2.0
        score -= float(row.get("decode_failure_count", 0) or 0) * 2.0
        if row.get("promotion_status") in {"DECODE_TESTED_REASON", "PROJECTABLE_REASON", "LAWBOOK_REASON"}:
            score += 3.0
            why.append("decode-tested reason")
    if kind == "obstruction" and row.get("obstruction_type"):
        score += 2.0
        why.append("same obstruction family candidate")
    return score, why or ["fallback sparse retrieval"]


def _trace(row: dict[str, Any], task: dict[str, Any], kind: str) -> LawbookAttentionTraceItem:
    if kind == "artifact":
        suggestion = "try_route:" + str(row.get("payload", {}).get("constructor", row.get("provenance_type", "lawbook_memory")))
        verified = row.get("terminal_form") in {"VERIFIED_PROOF", "FINITE_COUNTERMODEL", "NAMED_OBSTRUCTION"}
        item_id = row.get("artifact_id", "")
    elif kind == "reason":
        suggestion = "decode_reason:" + str(row.get("reason_type", "routing_rule"))
        verified = False
        item_id = row.get("reason_id", "")
    else:
        suggestion = "avoid_or_repair:" + str(row.get("route_killed", row.get("obstruction_type", "unknown")))
        verified = False
        item_id = row.get("obstruction_id", "")
    return LawbookAttentionTraceItem(
        item_id=str(item_id),
        item_type=kind,
        score=float(row.get("_attention_score", 0.0)),
        why_retrieved=list(row.get("_why", [])),
        action_suggestion=suggestion,
        verified=verified,
    )

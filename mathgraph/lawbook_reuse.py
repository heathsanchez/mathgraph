"""Lightweight Lawbook reuse signals for compounding runs."""

from __future__ import annotations

from typing import Any, Sequence


def compute_lawbook_hit_rate(rows: Sequence[dict[str, Any]]) -> float:
    return _ratio(sum(1 for row in rows if row.get("hit") or row.get("lawbook_hit")), len(rows))


def compute_action_change_rate(rows: Sequence[dict[str, Any]]) -> float:
    return _ratio(sum(1 for row in rows if row.get("changed_action") or row.get("action_changed")), len(rows))


def retrieve_reuse_candidates(store: Any, task: dict[str, Any], *, limit: int = 10, durable_only: bool = False) -> list[dict[str, Any]]:
    if store is None or not hasattr(store, "query_artifacts"):
        return []
    rows = store.query_artifacts(domain=task.get("domain", ""), basin=task.get("basin", task.get("family", "")), limit=limit)
    if durable_only:
        rows = [row for row in rows if bool(row.get("durable")) or int(row.get("trust_level", 0) or 0) >= 100]
    return rows[:limit]


def classify_reuse_kind(row: dict[str, Any]) -> str:
    if bool(row.get("durable")) or int(row.get("trust_level", 0) or 0) >= 100:
        return "durable_verified_reuse"
    if str(row.get("terminal_form", "")).upper() in {"ADVISORY", "", "NONE"}:
        return "advisory_reuse"
    return "candidate_reuse"


def _ratio(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0

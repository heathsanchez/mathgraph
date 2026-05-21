"""Reason coagulation v0 from Lawbook attempts and artifacts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from mathgraph.hashing import content_id


PROMOTION_STATUSES = {
    "CANDIDATE_REASON",
    "SUPPORTED_REASON",
    "DECODE_TESTED_REASON",
    "PROJECTABLE_REASON",
    "LAWBOOK_REASON",
    "RETIRED_REASON",
}


@dataclass(frozen=True)
class CoagulatedReason:
    reason_id: str
    domain: str
    reason_type: str
    basin: str
    support_count: int
    verified_support_count: int
    conditions: dict[str, Any]
    payload: dict[str, Any]
    promotion_status: str = "CANDIDATE_REASON"
    decode_success_count: int = 0
    decode_failure_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def coagulate_reasons(attempts: list[dict[str, Any]], artifacts: list[dict[str, Any]], obstructions: list[dict[str, Any]] | None = None) -> list[CoagulatedReason]:
    reasons: list[CoagulatedReason] = []
    reasons.extend(_coagulate_attempts(attempts, artifacts))
    reasons.extend(_coagulate_obstructions(obstructions or []))
    return reasons


def _coagulate_attempts(attempts: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> list[CoagulatedReason]:
    artifact_by_id = {row.get("artifact_id"): row for row in artifacts}
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for attempt in attempts:
        artifact = artifact_by_id.get(attempt.get("artifact_id"), {})
        terminal = artifact.get("terminal_form", attempt.get("result_type", ""))
        key = (
            str(attempt.get("domain", artifact.get("domain", ""))),
            str(artifact.get("basin", attempt.get("basin", ""))),
            str(artifact.get("micro_basin", "")),
            str(attempt.get("route", "")),
            str(terminal),
        )
        grouped[key].append(attempt)
    out = []
    for key, rows in grouped.items():
        domain, basin, micro_basin, route, terminal = key
        success = sum(1 for row in rows if row.get("success"))
        status = "SUPPORTED_REASON" if success >= 2 else "CANDIDATE_REASON"
        reason_type = "constructor_family" if route else "routing_rule"
        payload = {"route": route, "terminal_form": terminal, "micro_basin": micro_basin, "attempt_ids": [r.get("attempt_id") for r in rows]}
        out.append(
            CoagulatedReason(
                reason_id=content_id("coagulated-reason", [key, payload]),
                domain=domain,
                reason_type=reason_type,
                basin=basin,
                support_count=len(rows),
                verified_support_count=success,
                conditions={"route": route, "terminal_form": terminal, "micro_basin": micro_basin},
                payload=payload,
                promotion_status=status,
            )
        )
    return out


def _coagulate_obstructions(obstructions: list[dict[str, Any]]) -> list[CoagulatedReason]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for obs in obstructions:
        key = (str(obs.get("domain", "")), str(obs.get("basin", "")), str(obs.get("obstruction_type", "")), str(obs.get("route_killed", "")))
        grouped[key].append(obs)
    out = []
    for key, rows in grouped.items():
        domain, basin, obstruction_type, route = key
        out.append(
            CoagulatedReason(
                reason_id=content_id("obstruction-reason", [key, [r.get("obstruction_id") for r in rows]]),
                domain=domain,
                reason_type="obstruction_family",
                basin=basin,
                support_count=len(rows),
                verified_support_count=0,
                conditions={"obstruction_type": obstruction_type, "route_killed": route},
                payload={"obstruction_ids": [r.get("obstruction_id") for r in rows]},
                promotion_status="SUPPORTED_REASON" if len(rows) >= 2 else "CANDIDATE_REASON",
            )
        )
    return out

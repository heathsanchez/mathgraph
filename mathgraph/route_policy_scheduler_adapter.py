"""Adapters from Route Policy v2 cards to scheduler priority hints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from mathgraph.route_policy_v2 import RoutePolicyV2Report


@dataclass(frozen=True)
class RoutePriorityHint:
    route_key: str
    root_label: str | None
    constructor_family: str | None
    htilt_priority: float
    recommendation: str
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def route_policy_to_priority_hints(policy: RoutePolicyV2Report | dict[str, Any]) -> list[RoutePriorityHint]:
    cards = policy.cards if isinstance(policy, RoutePolicyV2Report) else policy.get("cards", [])
    hints = []
    for card in cards:
        data = card.to_dict() if hasattr(card, "to_dict") else dict(card)
        hints.append(
            RoutePriorityHint(
                route_key=str(data.get("route_key")),
                root_label=data.get("root_label"),
                constructor_family=data.get("constructor_family"),
                htilt_priority=float(data.get("htilt_priority") or 0.0),
                recommendation=str(data.get("recommendation") or "insufficient_data"),
                reason=_reason(data),
                evidence={
                    "advisory_only": True,
                    "policy_id": data.get("policy_id"),
                    "trust_boundary": data.get("trust_boundary"),
                },
            )
        )
    return sorted(hints, key=lambda item: (-item.htilt_priority, item.route_key))


def match_priority_hint(
    source: str,
    target: str,
    root_label: str | None,
    constructor_family: str | None,
    hints: list[RoutePriorityHint],
) -> RoutePriorityHint | None:
    del source, target
    for hint in hints:
        if hint.root_label == root_label and hint.constructor_family == constructor_family:
            return hint
    for hint in hints:
        if hint.root_label == root_label and constructor_family is None:
            return hint
    return None


def _reason(data: dict[str, Any]) -> str:
    return (
        f"{data.get('recommendation')} from H-tilt priority {data.get('htilt_priority')} "
        f"over route {data.get('route_key')}; advisory scheduling pressure only."
    )

"""Explicit interpretation choice points for theory objectification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChoicePointStatus(str, Enum):
    OPEN = "OPEN"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    AMBIGUOUS = "AMBIGUOUS"
    RESOLVED_BY_VERIFIER = "RESOLVED_BY_VERIFIER"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class InterpretationChoicePoint:
    choice_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    ambiguous_symbol: str
    context: str = ""
    candidate_readings: list[dict[str, Any]] = field(default_factory=list)
    selected_reading_id: str | None = None
    rejected_reading_ids: list[str] = field(default_factory=list)
    downstream_effects: list[str] = field(default_factory=list)
    status: ChoicePointStatus = ChoicePointStatus.OPEN
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "IMPORTED"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def has_selected_reading(self) -> bool:
        return bool(self.selected_reading_id)

    def is_resolved(self) -> bool:
        return self.status in {
            ChoicePointStatus.SELECTED,
            ChoicePointStatus.REJECTED,
            ChoicePointStatus.SUPERSEDED,
            ChoicePointStatus.RESOLVED_BY_VERIFIER,
        } and (self.has_selected_reading() or self.status is not ChoicePointStatus.SELECTED)

    def summary(self) -> dict[str, Any]:
        return {
            "choice_id": self.choice_id,
            "ambiguous_symbol": self.ambiguous_symbol,
            "status": self.status.value,
            "candidate_count": len(self.candidate_readings),
            "selected_reading_id": self.selected_reading_id,
            "resolved": self.is_resolved(),
            "truth_boundary": "Interpretation choices are visible metadata, not verification.",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice_id": self.choice_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "ambiguous_symbol": self.ambiguous_symbol,
            "context": self.context,
            "candidate_readings": list(self.candidate_readings),
            "selected_reading_id": self.selected_reading_id,
            "rejected_reading_ids": list(self.rejected_reading_ids),
            "downstream_effects": list(self.downstream_effects),
            "status": self.status.value,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InterpretationChoicePoint":
        return cls(
            choice_id=str(data["choice_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            ambiguous_symbol=str(data["ambiguous_symbol"]),
            context=str(data.get("context", "")),
            candidate_readings=[dict(item) for item in data.get("candidate_readings", [])],
            selected_reading_id=data.get("selected_reading_id"),
            rejected_reading_ids=[str(item) for item in data.get("rejected_reading_ids", [])],
            downstream_effects=[str(item) for item in data.get("downstream_effects", [])],
            status=_enum(ChoicePointStatus, data.get("status"), ChoicePointStatus.OPEN),
            trust_level=str(data.get("trust_level", "ADVISORY_ROUTE")),
            provenance_type=str(data.get("provenance_type", "IMPORTED")),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )

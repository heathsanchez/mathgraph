"""Denotation status and free-logic promotion guards."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


class DenotationStatus(str, Enum):
    DENOTES = "DENOTES"
    NON_DENOTING = "NON_DENOTING"
    UNKNOWN = "UNKNOWN"
    BLOCKED_BY_FREE_LOGIC = "BLOCKED_BY_FREE_LOGIC"


def _denotation(value: Any) -> DenotationStatus:
    if isinstance(value, DenotationStatus):
        return value
    for status in DenotationStatus:
        if str(value) == status.value:
            return status
    return DenotationStatus.UNKNOWN


def can_promote_denotation(status: Any) -> bool:
    return _denotation(status) is DenotationStatus.DENOTES


def require_denotes(record_or_status: Any) -> None:
    status = record_or_status.denotation_status if hasattr(record_or_status, "denotation_status") else record_or_status
    if not can_promote_denotation(status):
        raise ValueError(f"Cannot promote non-denoting or unknown-denoting object: {_denotation(status).value}")


@dataclass(frozen=True)
class DenotationRecord:
    denotation_id: str
    object_id: str
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    reason: str = ""
    checked_by: str = ""
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "denotation_id": self.denotation_id,
            "object_id": self.object_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "denotation_status": self.denotation_status.value,
            "reason": self.reason,
            "checked_by": self.checked_by,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DenotationRecord":
        return cls(
            denotation_id=str(data["denotation_id"]),
            object_id=str(data["object_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            denotation_status=_denotation(data.get("denotation_status")),
            reason=str(data.get("reason", "")),
            checked_by=str(data.get("checked_by", "")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            payload=dict(data.get("payload", {})),
        )

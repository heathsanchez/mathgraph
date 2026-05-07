"""Reason-containment scaffolding for future reason promotion."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.denotation import DenotationStatus, can_promote_denotation
from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


class ContainmentMode(str, Enum):
    SOURCE_CONTAINS_TARGET = "SOURCE_CONTAINS_TARGET"
    TARGET_NOT_CONTAINED = "TARGET_NOT_CONTAINED"
    COUNTERMODEL_SEPARATES = "COUNTERMODEL_SEPARATES"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReasonContainmentRecord:
    containment_id: str
    reason_node_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    source_id: str
    target_id: str
    containment_mode: ContainmentMode = ContainmentMode.UNKNOWN
    source_constraints: list[str] = field(default_factory=list)
    target_demand: list[str] = field(default_factory=list)
    separator_certificate_id: str | None = None
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        return (
            can_promote_denotation(self.denotation_status)
            and bool(self.separator_certificate_id)
            and self.trust_level in {TrustLevel.FINITE_VERIFIED, TrustLevel.LEAN_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}
        )

    def advisory_warning(self) -> str:
        return "Reason containment is advisory unless backed by proof/refutation and denoting objects."

    def to_dict(self) -> dict[str, Any]:
        return {
            "containment_id": self.containment_id,
            "reason_node_id": self.reason_node_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "containment_mode": self.containment_mode.value,
            "source_constraints": list(self.source_constraints),
            "target_demand": list(self.target_demand),
            "separator_certificate_id": self.separator_certificate_id,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "denotation_status": self.denotation_status.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasonContainmentRecord":
        return cls(
            containment_id=str(data["containment_id"]),
            reason_node_id=str(data["reason_node_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            containment_mode=ContainmentMode(str(data.get("containment_mode", "UNKNOWN"))),
            source_constraints=[str(item) for item in data.get("source_constraints", [])],
            target_demand=[str(item) for item in data.get("target_demand", [])],
            separator_certificate_id=data.get("separator_certificate_id"),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            denotation_status=DenotationStatus(str(data.get("denotation_status", "UNKNOWN"))),
            payload=dict(data.get("payload", {})),
        )

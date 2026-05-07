"""Correspondence claims between semantic conditions and syntactic laws."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.trust import TrustLevel, trust_level


class CorrespondenceDirection(str, Enum):
    CONDITION_IMPLIES_AXIOM = "CONDITION_IMPLIES_AXIOM"
    AXIOM_IMPLIES_CONDITION = "AXIOM_IMPLIES_CONDITION"
    EQUIVALENCE = "EQUIVALENCE"
    MOTIF_IMPLIES_CERTIFICATE_FAMILY = "MOTIF_IMPLIES_CERTIFICATE_FAMILY"
    ROOT_EXPLAINS_REASON = "ROOT_EXPLAINS_REASON"
    UNKNOWN = "UNKNOWN"


class CorrespondenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    OPEN = "OPEN"
    BENCHMARK_SUPPORTED = "BENCHMARK_SUPPORTED"
    ADVISORY = "ADVISORY"
    UNKNOWN = "UNKNOWN"


SAFE_TRUST = {TrustLevel.LEAN_VERIFIED, TrustLevel.FINITE_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class CorrespondenceClaim:
    correspondence_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    semantic_condition_id: str | None
    syntactic_axiom_id: str | None
    source_object_id: str | None = None
    target_object_id: str | None = None
    direction: CorrespondenceDirection = CorrespondenceDirection.UNKNOWN
    status: CorrespondenceStatus = CorrespondenceStatus.UNKNOWN
    proof_artifact_id: str | None = None
    countermodel_artifact_id: str | None = None
    benchmark_suite_id: str | None = None
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "IMPORTED"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        if trust_level(self.trust_level) not in SAFE_TRUST:
            return False
        if self.status is CorrespondenceStatus.VERIFIED:
            return bool(self.proof_artifact_id)
        if self.status is CorrespondenceStatus.REFUTED:
            return bool(self.countermodel_artifact_id)
        return False

    def advisory_warning(self) -> str:
        return "Correspondence claims are advisory unless backed by proof/refutation artifacts."

    def to_dict(self) -> dict[str, Any]:
        return {
            "correspondence_id": self.correspondence_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "semantic_condition_id": self.semantic_condition_id,
            "syntactic_axiom_id": self.syntactic_axiom_id,
            "source_object_id": self.source_object_id,
            "target_object_id": self.target_object_id,
            "direction": self.direction.value,
            "status": self.status.value,
            "proof_artifact_id": self.proof_artifact_id,
            "countermodel_artifact_id": self.countermodel_artifact_id,
            "benchmark_suite_id": self.benchmark_suite_id,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorrespondenceClaim":
        return cls(
            correspondence_id=str(data["correspondence_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            semantic_condition_id=data.get("semantic_condition_id"),
            syntactic_axiom_id=data.get("syntactic_axiom_id"),
            source_object_id=data.get("source_object_id"),
            target_object_id=data.get("target_object_id"),
            direction=_enum(CorrespondenceDirection, data.get("direction"), CorrespondenceDirection.UNKNOWN),
            status=_enum(CorrespondenceStatus, data.get("status"), CorrespondenceStatus.UNKNOWN),
            proof_artifact_id=data.get("proof_artifact_id"),
            countermodel_artifact_id=data.get("countermodel_artifact_id"),
            benchmark_suite_id=data.get("benchmark_suite_id"),
            trust_level=str(data.get("trust_level", "ADVISORY_ROUTE")),
            provenance_type=str(data.get("provenance_type", "IMPORTED")),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )

"""Theory-relative objectification maps and analytic readings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.denotation import DenotationStatus, can_promote_denotation
from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


class TheoryObjectKind(str, Enum):
    INDIVIDUAL_TERM = "INDIVIDUAL_TERM"
    PROPERTY_TERM = "PROPERTY_TERM"
    RELATION_TERM = "RELATION_TERM"
    PROPOSITION = "PROPOSITION"
    THEOREM = "THEOREM"
    AXIOM = "AXIOM"
    DEFINITION = "DEFINITION"
    CLAIM = "CLAIM"
    OPERATION_SYMBOL = "OPERATION_SYMBOL"
    WITNESS_ASSIGNMENT = "WITNESS_ASSIGNMENT"
    FINITE_STRUCTURE = "FINITE_STRUCTURE"
    FORMAL_WORLD = "FORMAL_WORLD"
    PROOF_METHOD = "PROOF_METHOD"
    INFERENCE_RULE = "INFERENCE_RULE"


def _denotation(value: Any) -> DenotationStatus:
    if isinstance(value, DenotationStatus):
        return value
    for status in DenotationStatus:
        if str(value) == status.value:
            return status
    return DenotationStatus.UNKNOWN


@dataclass(frozen=True)
class TheoryObjectificationMap:
    map_id: str
    domain_kernel_id: str
    formal_world_id: str | None
    theory_id: str
    description: str = ""
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {**self.__dict__, "trust_level": self.trust_level.value, "provenance_type": self.provenance_type.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TheoryObjectificationMap":
        return cls(
            map_id=str(data["map_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data["theory_id"]),
            description=str(data.get("description", "")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class TheoryDenotation:
    denotation_id: str
    domain_kernel_id: str
    formal_world_id: str | None
    theory_id: str
    source_symbol: str
    source_kind: TheoryObjectKind
    target_object_id: str
    target_type_expr: str
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "source_kind": self.source_kind.value,
            "denotation_status": self.denotation_status.value,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TheoryDenotation":
        return cls(
            denotation_id=str(data["denotation_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data["theory_id"]),
            source_symbol=str(data["source_symbol"]),
            source_kind=TheoryObjectKind(str(data.get("source_kind", "CLAIM"))),
            target_object_id=str(data["target_object_id"]),
            target_type_expr=str(data["target_type_expr"]),
            denotation_status=_denotation(data.get("denotation_status")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class TheoryReading:
    reading_id: str
    domain_kernel_id: str
    formal_world_id: str | None
    theory_id: str
    source_statement: str
    reading_statement: str
    reading_type_expr: str
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "denotation_status": self.denotation_status.value,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TheoryReading":
        return cls(
            reading_id=str(data["reading_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data["theory_id"]),
            source_statement=str(data["source_statement"]),
            reading_statement=str(data["reading_statement"]),
            reading_type_expr=str(data["reading_type_expr"]),
            denotation_status=_denotation(data.get("denotation_status")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class AnalyticTruth:
    analytic_truth_id: str
    domain_kernel_id: str
    formal_world_id: str | None
    theory_id: str
    statement: str
    reading_id: str
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    verifier_id: str | None = None
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        return (
            can_promote_denotation(self.denotation_status)
            and self.trust_level in {TrustLevel.LEAN_VERIFIED, TrustLevel.FINITE_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}
            and bool(self.verifier_id)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "denotation_status": self.denotation_status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalyticTruth":
        return cls(
            analytic_truth_id=str(data["analytic_truth_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data["theory_id"]),
            statement=str(data["statement"]),
            reading_id=str(data["reading_id"]),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            verifier_id=data.get("verifier_id"),
            denotation_status=_denotation(data.get("denotation_status")),
            payload=dict(data.get("payload", {})),
        )

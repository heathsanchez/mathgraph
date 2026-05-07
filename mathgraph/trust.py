"""Trust and provenance labels kept separate from terminal truth."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar


class TrustLevel(str, Enum):
    ADVISORY_ROUTE = "ADVISORY_ROUTE"
    CANDIDATE_CERTIFICATE = "CANDIDATE_CERTIFICATE"
    BOUNDED_CERT = "BOUNDED_CERT"
    FINITE_VERIFIED = "FINITE_VERIFIED"
    DERIVED_CHAIN_VERIFIED = "DERIVED_CHAIN_VERIFIED"
    LEAN_VERIFIED = "LEAN_VERIFIED"


class ProvenanceType(str, Enum):
    PRIMITIVE = "PRIMITIVE"
    DERIVED = "DERIVED"
    IMPORTED = "IMPORTED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"


EnumT = TypeVar("EnumT", bound=Enum)


def enum_value(value: str | Enum | None, enum_type: type[EnumT], default: EnumT) -> EnumT:
    """Return an enum member without treating unknown strings as truth."""

    if isinstance(value, enum_type):
        return value
    if value in (None, ""):
        return default
    text = str(value)
    for member in enum_type:
        if text == member.name or text == str(member.value):
            return member
    return default


def trust_level(value: str | TrustLevel | None, default: TrustLevel = TrustLevel.ADVISORY_ROUTE) -> TrustLevel:
    return enum_value(value, TrustLevel, default)


def provenance_type(
    value: str | ProvenanceType | None,
    default: ProvenanceType = ProvenanceType.IMPORTED,
) -> ProvenanceType:
    return enum_value(value, ProvenanceType, default)


@dataclass(frozen=True)
class TrustProvenance:
    """Small JSON-safe pair used by importers and middleware."""

    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrustProvenance":
        return cls(
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
        )

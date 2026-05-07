"""Encoding and exemplification predication facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.denotation import DenotationStatus, can_promote_denotation
from mathgraph.hashing import content_id
from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


class PredicationMode(str, Enum):
    EXEMPLIFIES = "EXEMPLIFIES"
    ENCODES = "ENCODES"


class PredicateKind(str, Enum):
    PROPERTY = "PROPERTY"
    RELATION = "RELATION"
    META_PROPERTY = "META_PROPERTY"
    STRUCTURAL_FEATURE = "STRUCTURAL_FEATURE"
    TERMINAL_FEATURE = "TERMINAL_FEATURE"
    ADVISORY_FEATURE = "ADVISORY_FEATURE"
    FORMAL_PRIMITIVE = "FORMAL_PRIMITIVE"
    OBJECTIFICATION_FEATURE = "OBJECTIFICATION_FEATURE"
    CONTAINMENT_FEATURE = "CONTAINMENT_FEATURE"


def _mode(value: Any) -> PredicationMode:
    return value if isinstance(value, PredicationMode) else PredicationMode(str(value))


def _kind(value: Any) -> PredicateKind:
    if isinstance(value, PredicateKind):
        return value
    for kind in PredicateKind:
        if str(value) == kind.value:
            return kind
    return PredicateKind.ADVISORY_FEATURE


def _denotation(value: Any) -> DenotationStatus:
    if isinstance(value, DenotationStatus):
        return value
    for status in DenotationStatus:
        if str(value) in {status.value, status.name}:
            return status
    return DenotationStatus.UNKNOWN


@dataclass(frozen=True)
class PredicationFact:
    predication_id: str
    subject_id: str
    predicate_id: str
    mode: PredicationMode
    predicate_kind: PredicateKind
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        return (
            self.mode is PredicationMode.EXEMPLIFIES
            and self.trust_level in {TrustLevel.FINITE_VERIFIED, TrustLevel.LEAN_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}
            and can_promote_denotation(self.denotation_status)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "predication_id": self.predication_id,
            "subject_id": self.subject_id,
            "predicate_id": self.predicate_id,
            "mode": self.mode.value,
            "predicate_kind": self.predicate_kind.value,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "denotation_status": self.denotation_status.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PredicationFact":
        return cls(
            predication_id=str(data["predication_id"]),
            subject_id=str(data["subject_id"]),
            predicate_id=str(data["predicate_id"]),
            mode=_mode(data.get("mode")),
            predicate_kind=_kind(data.get("predicate_kind")),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            denotation_status=_denotation(data.get("denotation_status")),
            payload=dict(data.get("payload", {})),
        )


def encodes(subject_id: str, predicate_id: str, **kwargs: Any) -> PredicationFact:
    return _make_predication(subject_id, predicate_id, PredicationMode.ENCODES, **kwargs)


def exemplifies(subject_id: str, predicate_id: str, **kwargs: Any) -> PredicationFact:
    return _make_predication(subject_id, predicate_id, PredicationMode.EXEMPLIFIES, **kwargs)


def _make_predication(
    subject_id: str, predicate_id: str, mode: PredicationMode, **kwargs: Any
) -> PredicationFact:
    payload = dict(kwargs.pop("payload", {}))
    predicate_kind = _kind(kwargs.pop("predicate_kind", PredicateKind.ADVISORY_FEATURE))
    data = {"subject_id": subject_id, "predicate_id": predicate_id, "mode": mode.value, "payload": payload}
    return PredicationFact(
        predication_id=str(kwargs.pop("predication_id", content_id("predication", data))),
        subject_id=subject_id,
        predicate_id=predicate_id,
        mode=mode,
        predicate_kind=predicate_kind,
        domain_kernel_id=kwargs.pop("domain_kernel_id", None),
        formal_world_id=kwargs.pop("formal_world_id", None),
        trust_level=trust_level(kwargs.pop("trust_level", None)),
        provenance_type=provenance_type(kwargs.pop("provenance_type", None)),
        denotation_status=_denotation(kwargs.pop("denotation_status", "UNKNOWN")),
        payload=payload,
    )

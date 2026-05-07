"""Lightweight paradox guard metadata and pattern checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParadoxGuardKind(str, Enum):
    DENOTATION_GUARD = "DENOTATION_GUARD"
    COMPREHENSION_GUARD = "COMPREHENSION_GUARD"
    LAMBDA_ABSTRACTION_GUARD = "LAMBDA_ABSTRACTION_GUARD"
    ENCODING_BLEED_GUARD = "ENCODING_BLEED_GUARD"
    HOST_ARTIFACT_GUARD = "HOST_ARTIFACT_GUARD"
    SET_COLLAPSE_GUARD = "SET_COLLAPSE_GUARD"


class GuardSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


@dataclass(frozen=True)
class ParadoxGuardResult:
    guard_id: str
    status: str
    message: str
    matched_patterns: list[str] = field(default_factory=list)
    severity: GuardSeverity = GuardSeverity.INFO
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "guard_id": self.guard_id,
            "status": self.status,
            "message": self.message,
            "matched_patterns": list(self.matched_patterns),
            "severity": self.severity.value,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class ParadoxGuard:
    guard_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    guard_kind: ParadoxGuardKind
    name: str
    description: str = ""
    severity: GuardSeverity = GuardSeverity.WARNING
    blocked_patterns: list[str] = field(default_factory=list)
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def check_text(self, text: str) -> ParadoxGuardResult:
        matched = [pattern for pattern in self.blocked_patterns if pattern and pattern in text]
        if not matched:
            return ParadoxGuardResult(self.guard_id, "PASS", "No guard pattern matched.", [], GuardSeverity.INFO)
        status = "BLOCK" if self.severity is GuardSeverity.BLOCKING else "WARN"
        return ParadoxGuardResult(
            self.guard_id,
            status,
            f"{self.name} matched blocked patterns.",
            matched,
            self.severity,
            {"text_preview": text[:120]},
        )

    def is_blocking_result(self, result: ParadoxGuardResult) -> bool:
        return result.status == "BLOCK" or result.severity is GuardSeverity.BLOCKING

    def to_dict(self) -> dict[str, Any]:
        return {
            "guard_id": self.guard_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "guard_kind": self.guard_kind.value,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "blocked_patterns": list(self.blocked_patterns),
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParadoxGuard":
        return cls(
            guard_id=str(data["guard_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            guard_kind=ParadoxGuardKind(str(data["guard_kind"])),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            severity=GuardSeverity(str(data.get("severity", "WARNING"))),
            blocked_patterns=[str(item) for item in data.get("blocked_patterns", [])],
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )


def aot_complex_term_guard() -> ParadoxGuard:
    return ParadoxGuard(
        guard_id="guard_aot_complex_terms",
        domain_kernel_id="aot",
        formal_world_id="formal_world_aot_precedent",
        guard_kind=ParadoxGuardKind.DENOTATION_GUARD,
        name="AOT complex term denotation guard",
        description="Blocks unguarded complex terms until denotation is checked.",
        severity=GuardSeverity.BLOCKING,
        blocked_patterns=["ι", "definite_description", "unsafe_comprehension", "unrestricted_lambda"],
    )


def semantic_embedding_artifact_guard() -> ParadoxGuard:
    return ParadoxGuard(
        guard_id="guard_semantic_embedding_artifact_risk",
        domain_kernel_id=None,
        formal_world_id=None,
        guard_kind=ParadoxGuardKind.HOST_ARTIFACT_GUARD,
        name="Semantic embedding artifact-risk guard",
        severity=GuardSeverity.WARNING,
        blocked_patterns=["HOST_ONLY", "UNKNOWN_RISK", "TRANSPORT_FAILED"],
        notes="Host proof is not automatically target proof.",
    )


def set_collapse_guard() -> ParadoxGuard:
    return ParadoxGuard(
        guard_id="guard_set_collapse",
        domain_kernel_id=None,
        formal_world_id=None,
        guard_kind=ParadoxGuardKind.SET_COLLAPSE_GUARD,
        name="Set-collapse guard",
        severity=GuardSeverity.WARNING,
        blocked_patterns=["root_is_evidence_set", "reason_is_coverage_only"],
        notes="Same extension is not same law.",
    )

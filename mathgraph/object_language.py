"""Lightweight formal object-language IR containers.

This module intentionally does not parse Isabelle, AOT, Lean, or ETP syntax.
It records normalized text and enough metadata for later verifier-specific
importers to connect object-language material to certificates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.denotation import DenotationStatus


class ObjectLanguageKind(str, Enum):
    TERM = "TERM"
    FORMULA = "FORMULA"
    PREDICATE = "PREDICATE"
    RELATION = "RELATION"
    THEOREM_STATEMENT = "THEOREM_STATEMENT"
    AXIOM_STATEMENT = "AXIOM_STATEMENT"
    DEFINITION_STATEMENT = "DEFINITION_STATEMENT"
    PROOF_METHOD_STATEMENT = "PROOF_METHOD_STATEMENT"
    UNKNOWN = "UNKNOWN"


class FormulaRole(str, Enum):
    PREMISE = "PREMISE"
    CONCLUSION = "CONCLUSION"
    CLAIM = "CLAIM"
    AXIOM = "AXIOM"
    THEOREM = "THEOREM"
    DEFINITION = "DEFINITION"
    WORLD_CONDITION = "WORLD_CONDITION"
    DENOTATION_CONDITION = "DENOTATION_CONDITION"
    UNKNOWN = "UNKNOWN"


def normalize_object_language_text(text: str) -> str:
    return " ".join(str(text).strip().split())


def _status(value: Any) -> DenotationStatus:
    if isinstance(value, DenotationStatus):
        return value
    for status in DenotationStatus:
        if str(value) in {status.value, status.name}:
            return status
    return DenotationStatus.UNKNOWN


def _role(value: Any) -> FormulaRole:
    if isinstance(value, FormulaRole):
        return value
    for role in FormulaRole:
        if str(value) in {role.value, role.name}:
            return role
    return FormulaRole.UNKNOWN


@dataclass(frozen=True)
class ObjectLanguageTerm:
    term_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    raw_text: str
    normalized_text: str | None = None
    type_expr: str = "i"
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    role: str = ObjectLanguageKind.TERM.value
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.normalized_text is None:
            object.__setattr__(self, "normalized_text", normalize_object_language_text(self.raw_text))

    def to_dict(self) -> dict[str, Any]:
        return {
            "term_id": self.term_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "type_expr": self.type_expr,
            "denotation_status": self.denotation_status.value,
            "role": self.role,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObjectLanguageTerm":
        return cls(
            term_id=str(data["term_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            raw_text=str(data.get("raw_text", "")),
            normalized_text=data.get("normalized_text"),
            type_expr=str(data.get("type_expr", "i")),
            denotation_status=_status(data.get("denotation_status")),
            role=str(data.get("role", ObjectLanguageKind.TERM.value)),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class ObjectLanguageFormula:
    formula_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    raw_text: str
    normalized_text: str | None = None
    type_expr: str = "<>"
    formula_role: FormulaRole = FormulaRole.UNKNOWN
    denotation_status: DenotationStatus = DenotationStatus.UNKNOWN
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.normalized_text is None:
            object.__setattr__(self, "normalized_text", normalize_object_language_text(self.raw_text))

    def to_dict(self) -> dict[str, Any]:
        return {
            "formula_id": self.formula_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "type_expr": self.type_expr,
            "formula_role": self.formula_role.value,
            "denotation_status": self.denotation_status.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObjectLanguageFormula":
        return cls(
            formula_id=str(data["formula_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            raw_text=str(data.get("raw_text", "")),
            normalized_text=data.get("normalized_text"),
            type_expr=str(data.get("type_expr", "<>")),
            formula_role=_role(data.get("formula_role")),
            denotation_status=_status(data.get("denotation_status")),
            payload=dict(data.get("payload", {})),
        )

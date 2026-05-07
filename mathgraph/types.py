"""Typed formal objects and hyperintensional identity metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.hashing import content_id


class TypeParseError(ValueError):
    pass


class ObjectIdentityMode(str, Enum):
    HASH_EXACT = "HASH_EXACT"
    ALIAS_EQUIVALENT = "ALIAS_EQUIVALENT"
    COVERAGE_EQUIVALENT = "COVERAGE_EQUIVALENT"
    ENCODED_PROPERTY_EQUIVALENT = "ENCODED_PROPERTY_EQUIVALENT"
    THEORY_RELATIVE_DENOTATION = "THEORY_RELATIVE_DENOTATION"
    UNKNOWN = "UNKNOWN"


class UniquenessStatus(str, Enum):
    UNIQUE_VERIFIED = "UNIQUE_VERIFIED"
    UNIQUE_BY_HASH = "UNIQUE_BY_HASH"
    UNIQUE_BY_DOMAIN_AXIOM = "UNIQUE_BY_DOMAIN_AXIOM"
    AMBIGUOUS_ALIAS = "AMBIGUOUS_ALIAS"
    FAMILY_NAME_ONLY = "FAMILY_NAME_ONLY"
    UNKNOWN = "UNKNOWN"


class HyperintensionalIdentityMode(str, Enum):
    SURFACE_SYNTAX = "SURFACE_SYNTAX"
    NORMALIZED_SYNTAX = "NORMALIZED_SYNTAX"
    ENCODED_PROPERTIES = "ENCODED_PROPERTIES"
    THEORY_RELATIVE_ROLE = "THEORY_RELATIVE_ROLE"
    CERTIFICATE_COVERAGE = "CERTIFICATE_COVERAGE"
    CONTINUATION_BEHAVIOR = "CONTINUATION_BEHAVIOR"
    VERIFIED_EQUIVALENCE = "VERIFIED_EQUIVALENCE"
    UNKNOWN = "UNKNOWN"


class ExtensionalCollapsePolicy(str, Enum):
    NEVER_BY_DEFAULT = "NEVER_BY_DEFAULT"
    ALLOW_IF_VERIFIED_EQUIVALENCE = "ALLOW_IF_VERIFIED_EQUIVALENCE"
    ALLOW_IF_DOMAIN_KERNEL_DECLARES_EXTENSIONAL = "ALLOW_IF_DOMAIN_KERNEL_DECLARES_EXTENSIONAL"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass(frozen=True)
class MathGraphType:
    raw: str
    normalized: str
    children: tuple["MathGraphType", ...] = ()

    @property
    def arity(self) -> int:
        if self.is_individual or self.is_proposition:
            return 0
        return len(self.children)

    @property
    def is_individual(self) -> bool:
        return self.normalized == "i"

    @property
    def is_proposition(self) -> bool:
        return self.normalized == "<>"

    @property
    def is_relation(self) -> bool:
        return self.normalized.startswith("<") and self.normalized.endswith(">")

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "normalized": self.normalized,
            "children": [child.to_dict() for child in self.children],
        }


def normalize_type_expr(expr: str) -> str:
    return parse_type_expr(expr).normalized


def parse_type_expr(expr: str) -> MathGraphType:
    text = "".join(str(expr).split())
    if not text:
        raise TypeParseError("empty type expression")
    node, index = _parse_at(text, 0)
    if index != len(text):
        raise TypeParseError(f"trailing type text at {index}: {text[index:]}")
    return node


def _parse_at(text: str, index: int) -> tuple[MathGraphType, int]:
    if index >= len(text):
        raise TypeParseError("unexpected end of type expression")
    if text[index] == "i":
        return MathGraphType(raw="i", normalized="i"), index + 1
    if text[index] != "<":
        raise TypeParseError(f"expected 'i' or '<' at {index}")
    index += 1
    children: list[MathGraphType] = []
    if index < len(text) and text[index] == ">":
        return MathGraphType(raw="<>", normalized="<>"), index + 1
    while True:
        child, index = _parse_at(text, index)
        children.append(child)
        if index >= len(text):
            raise TypeParseError("unterminated relational type")
        if text[index] == ",":
            index += 1
            continue
        if text[index] == ">":
            index += 1
            normalized = "<" + ",".join(child.normalized for child in children) + ">"
            return MathGraphType(raw=normalized, normalized=normalized, children=tuple(children)), index
        raise TypeParseError(f"unexpected character {text[index]!r} at {index}")


@dataclass(frozen=True)
class TypedObject:
    object_id: str
    type_expr: str
    object_kind: str
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    ordinary_or_abstract: str = "UNKNOWN"
    identity_mode: str = ObjectIdentityMode.UNKNOWN.value
    uniqueness_status: str = UniquenessStatus.UNKNOWN.value
    hyperintensional_identity_mode: str = HyperintensionalIdentityMode.UNKNOWN.value
    label: str | None = None
    encoded_properties: dict[str, Any] = field(default_factory=dict)
    exemplified_properties: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        parse_type_expr(self.type_expr)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "type_expr": normalize_type_expr(self.type_expr),
            "object_kind": self.object_kind,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "ordinary_or_abstract": self.ordinary_or_abstract,
            "identity_mode": self.identity_mode,
            "uniqueness_status": self.uniqueness_status,
            "hyperintensional_identity_mode": self.hyperintensional_identity_mode,
            "label": self.label,
            "encoded_properties": dict(self.encoded_properties),
            "exemplified_properties": dict(self.exemplified_properties),
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TypedObject":
        return cls(
            object_id=str(data["object_id"]),
            type_expr=str(data["type_expr"]),
            object_kind=str(data["object_kind"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            ordinary_or_abstract=str(data.get("ordinary_or_abstract", "UNKNOWN")),
            identity_mode=str(data.get("identity_mode", ObjectIdentityMode.UNKNOWN.value)),
            uniqueness_status=str(data.get("uniqueness_status", UniquenessStatus.UNKNOWN.value)),
            hyperintensional_identity_mode=str(
                data.get("hyperintensional_identity_mode", HyperintensionalIdentityMode.UNKNOWN.value)
            ),
            label=data.get("label"),
            encoded_properties=dict(data.get("encoded_properties", {})),
            exemplified_properties=dict(data.get("exemplified_properties", {})),
            payload=dict(data.get("payload", {})),
        )


def canonical_encoded_object_id(
    domain_kernel_id: str | None,
    formal_world_id: str | None,
    type_expr: str,
    encoded_properties: dict[str, Any],
) -> str:
    return content_id(
        "encoded_object",
        {
            "domain_kernel_id": domain_kernel_id,
            "formal_world_id": formal_world_id,
            "type_expr": normalize_type_expr(type_expr),
            "encoded_properties": encoded_properties,
        },
    )


def should_merge_objects(a: Any, b: Any, policy: str | ExtensionalCollapsePolicy) -> bool:
    policy_value = policy.value if isinstance(policy, ExtensionalCollapsePolicy) else str(policy)
    left = a.to_dict() if hasattr(a, "to_dict") else dict(a)
    right = b.to_dict() if hasattr(b, "to_dict") else dict(b)
    if left.get("object_id") and left.get("object_id") == right.get("object_id"):
        return True
    if policy_value == ExtensionalCollapsePolicy.NEVER_BY_DEFAULT.value:
        return False
    if policy_value == ExtensionalCollapsePolicy.ADVISORY_ONLY.value:
        return False
    if policy_value == ExtensionalCollapsePolicy.ALLOW_IF_VERIFIED_EQUIVALENCE.value:
        return (
            left.get("hyperintensional_identity_mode") == HyperintensionalIdentityMode.VERIFIED_EQUIVALENCE.value
            and right.get("hyperintensional_identity_mode") == HyperintensionalIdentityMode.VERIFIED_EQUIVALENCE.value
            and left.get("encoded_properties") == right.get("encoded_properties")
        )
    if policy_value == ExtensionalCollapsePolicy.ALLOW_IF_DOMAIN_KERNEL_DECLARES_EXTENSIONAL.value:
        return bool(left.get("payload", {}).get("domain_kernel_declares_extensional")) and (
            left.get("encoded_properties") == right.get("encoded_properties")
        )
    return False

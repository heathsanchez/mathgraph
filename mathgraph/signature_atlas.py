"""Signature atlas records for Lean declaration contact promotion."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class SignatureRole(str, Enum):
    THEOREM = "THEOREM"
    DEFINITION = "DEFINITION"
    PREDICATE = "PREDICATE"
    TYPE = "TYPE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SignatureAtlasRecord:
    decl_name: str
    namespace: str
    shape: str
    role: SignatureRole
    raw_check_output: str
    normalized_signature: str
    returns_prop: bool
    returns_type: bool
    explicit_binder_count: int
    implicit_binder_count: int
    typeclass_binder_count: int
    hypothesis_count: int
    arity_estimate: int
    has_universe_params: bool
    has_typeclass_requirements: bool
    can_be_exact_term_candidate: bool
    needs_hypotheses: bool
    known_successful_contact_terms: tuple[str, ...] = ()
    known_failed_contact_terms: tuple[str, ...] = ()
    last_failure_class: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _parse_role(self.role))

    def to_dict(self) -> dict[str, Any]:
        return {
            "decl_name": self.decl_name,
            "namespace": self.namespace,
            "shape": self.shape,
            "role": self.role.value,
            "raw_check_output": self.raw_check_output,
            "normalized_signature": self.normalized_signature,
            "returns_prop": self.returns_prop,
            "returns_type": self.returns_type,
            "explicit_binder_count": self.explicit_binder_count,
            "implicit_binder_count": self.implicit_binder_count,
            "typeclass_binder_count": self.typeclass_binder_count,
            "hypothesis_count": self.hypothesis_count,
            "arity_estimate": self.arity_estimate,
            "has_universe_params": self.has_universe_params,
            "has_typeclass_requirements": self.has_typeclass_requirements,
            "can_be_exact_term_candidate": self.can_be_exact_term_candidate,
            "needs_hypotheses": self.needs_hypotheses,
            "known_successful_contact_terms": list(self.known_successful_contact_terms),
            "known_failed_contact_terms": list(self.known_failed_contact_terms),
            "last_failure_class": self.last_failure_class,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignatureAtlasRecord":
        return cls(
            decl_name=str(data.get("decl_name", "")),
            namespace=str(data.get("namespace", "")),
            shape=str(data.get("shape", "")),
            role=_parse_role(data.get("role")),
            raw_check_output=str(data.get("raw_check_output", "")),
            normalized_signature=str(data.get("normalized_signature", "")),
            returns_prop=_truthy(data.get("returns_prop")),
            returns_type=_truthy(data.get("returns_type")),
            explicit_binder_count=int(data.get("explicit_binder_count", 0) or 0),
            implicit_binder_count=int(data.get("implicit_binder_count", 0) or 0),
            typeclass_binder_count=int(data.get("typeclass_binder_count", 0) or 0),
            hypothesis_count=int(data.get("hypothesis_count", 0) or 0),
            arity_estimate=int(data.get("arity_estimate", 0) or 0),
            has_universe_params=_truthy(data.get("has_universe_params")),
            has_typeclass_requirements=_truthy(data.get("has_typeclass_requirements")),
            can_be_exact_term_candidate=_truthy(data.get("can_be_exact_term_candidate")),
            needs_hypotheses=_truthy(data.get("needs_hypotheses")),
            known_successful_contact_terms=tuple(data.get("known_successful_contact_terms", []) or ()),
            known_failed_contact_terms=tuple(data.get("known_failed_contact_terms", []) or ()),
            last_failure_class=str(data.get("last_failure_class", "")),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class SignatureParseResult:
    record: SignatureAtlasRecord
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"record": self.record.to_dict(), "warnings": list(self.warnings)}


class SignatureAtlas:
    def __init__(self, records: Iterable[SignatureAtlasRecord] | None = None) -> None:
        self.records: dict[str, SignatureAtlasRecord] = {}
        for record in records or ():
            self.add(record)

    def add(self, record: SignatureAtlasRecord) -> None:
        self.records[record.decl_name] = record

    def get(self, decl_name: str) -> SignatureAtlasRecord | None:
        return self.records.get(decl_name)

    def to_rows(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in sorted(self.records.values(), key=lambda item: item.decl_name)]

    @classmethod
    def from_rows(cls, rows: Iterable[dict[str, Any]]) -> "SignatureAtlas":
        return cls(SignatureAtlasRecord.from_dict(row) for row in rows)

    def to_jsonable(self) -> dict[str, Any]:
        return {"records": self.to_rows(), "count": len(self.records)}


def parse_check_output(raw: str, decl_name: str, shape: str = "", source: str = "") -> SignatureAtlasRecord:
    normalized = normalize_signature(raw)
    features = estimate_signature_features(normalized)
    namespace = decl_name.split(".", 1)[0] if "." in decl_name else ""
    role = _estimate_role(normalized, features)
    return SignatureAtlasRecord(
        decl_name=decl_name,
        namespace=namespace,
        shape=shape,
        role=role,
        raw_check_output=raw or "",
        normalized_signature=normalized,
        returns_prop=bool(features["returns_prop"]),
        returns_type=bool(features["returns_type"]),
        explicit_binder_count=int(features["explicit_binder_count"]),
        implicit_binder_count=int(features["implicit_binder_count"]),
        typeclass_binder_count=int(features["typeclass_binder_count"]),
        hypothesis_count=int(features["hypothesis_count"]),
        arity_estimate=int(features["arity_estimate"]),
        has_universe_params=bool(features["has_universe_params"]),
        has_typeclass_requirements=bool(features["has_typeclass_requirements"]),
        can_be_exact_term_candidate=bool(features["can_be_exact_term_candidate"]),
        needs_hypotheses=bool(features["needs_hypotheses"]),
        source=source,
        metadata={"parser": "heuristic_signature_atlas_v0"},
    )


def normalize_signature(raw: str) -> str:
    text = (raw or "").strip()
    text = re.sub(r"^\s*#check\s+", "", text)
    text = re.sub(r"^\S+:\d+:\d+:\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def estimate_signature_features(raw: str) -> dict[str, Any]:
    text = normalize_signature(raw)
    body = _signature_body(text)
    explicit_blocks = re.findall(r"\([^)]*\)", text)
    implicit_blocks = re.findall(r"\{[^}]*\}", text)
    typeclass_blocks = re.findall(r"\[[^\]]*\]", text)
    explicit_count = _binder_count(explicit_blocks)
    implicit_count = _binder_count(implicit_blocks)
    typeclass_count = len([block for block in typeclass_blocks if block.strip("[] ").strip()])
    returns_prop = _looks_prop(body)
    returns_type = _looks_type(body)
    arrow_count = body.count("→") + len(re.findall(r"\s->\s", body))
    hypothesis_count = sum(1 for block in explicit_blocks if ":" in block and _looks_prop(block))
    has_universe = bool(re.search(r"\.\{[^}]+\}|Type\s+[uv]\b|Sort\s+[uv]\b", text))
    arity = explicit_count + implicit_count + typeclass_count + arrow_count
    needs_hypotheses = hypothesis_count > 0 or arrow_count > 0
    role = _estimate_role(text, {"returns_prop": returns_prop, "returns_type": returns_type})
    return {
        "returns_prop": returns_prop,
        "returns_type": returns_type,
        "explicit_binder_count": explicit_count,
        "implicit_binder_count": implicit_count,
        "typeclass_binder_count": typeclass_count,
        "hypothesis_count": hypothesis_count,
        "arity_estimate": arity,
        "has_universe_params": has_universe,
        "has_typeclass_requirements": typeclass_count > 0,
        "can_be_exact_term_candidate": role in {SignatureRole.THEOREM, SignatureRole.PREDICATE} and returns_prop,
        "needs_hypotheses": needs_hypotheses,
    }


def _signature_body(text: str) -> str:
    if ":" not in text:
        return text
    return text.split(":", 1)[1].strip()


def _binder_count(blocks: list[str]) -> int:
    total = 0
    for block in blocks:
        inside = block[1:-1].strip()
        if not inside:
            continue
        if ":" in inside:
            total += max(1, len(inside.split(":", 1)[0].split()))
        else:
            total += max(1, len(inside.split()))
    return total


def _looks_prop(text: str) -> bool:
    proposition_tokens = ("∣", "=", "≤", "<", "↔", "→", "->", "Prop", "∈", "⊆", "¬", "∃", "∀")
    return any(token in text for token in proposition_tokens)


def _looks_type(text: str) -> bool:
    return bool(re.search(r"\b(Type|Sort|Prop)\b", text))


def _estimate_role(text: str, features: dict[str, Any]) -> SignatureRole:
    body = _signature_body(text)
    if features.get("returns_prop"):
        return SignatureRole.THEOREM
    if features.get("returns_type") or "Type" in body or "Sort" in body:
        return SignatureRole.TYPE
    if "Bool" in body or "Prop" in body:
        return SignatureRole.PREDICATE
    if ":" in text:
        return SignatureRole.DEFINITION
    return SignatureRole.UNKNOWN


def _parse_role(value: Any) -> SignatureRole:
    if isinstance(value, SignatureRole):
        return value
    text = str(value or "").strip().upper()
    for role in SignatureRole:
        if text == role.value:
            return role
    return SignatureRole.UNKNOWN


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)

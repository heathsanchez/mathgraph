"""Bounded language fragments for formal worlds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.types import normalize_type_expr


@dataclass(frozen=True)
class LanguageFragment:
    fragment_id: str
    domain_kernel_id: str
    formal_world_id: str | None
    language_name: str
    width_bound: int | None = None
    height_bound: int | None = None
    supported_type_exprs: list[str] = field(default_factory=list)
    supported_term_constructors: list[str] = field(default_factory=list)
    supported_claim_types: list[str] = field(default_factory=list)
    supported_verifiers: list[str] = field(default_factory=list)
    blocked_term_patterns: list[str] = field(default_factory=list)
    paradox_guard_policy: str | None = None
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def supports_type(self, type_expr: str) -> bool:
        normalized = normalize_type_expr(type_expr)
        return normalized in {normalize_type_expr(item) for item in self.supported_type_exprs}

    def summary(self) -> dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "language_name": self.language_name,
            "type_count": len(self.supported_type_exprs),
            "constructor_count": len(self.supported_term_constructors),
            "blocked_pattern_count": len(self.blocked_term_patterns),
            "paradox_guard_policy": self.paradox_guard_policy,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "language_name": self.language_name,
            "width_bound": self.width_bound,
            "height_bound": self.height_bound,
            "supported_type_exprs": [normalize_type_expr(item) for item in self.supported_type_exprs],
            "supported_term_constructors": list(self.supported_term_constructors),
            "supported_claim_types": list(self.supported_claim_types),
            "supported_verifiers": list(self.supported_verifiers),
            "blocked_term_patterns": list(self.blocked_term_patterns),
            "paradox_guard_policy": self.paradox_guard_policy,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LanguageFragment":
        return cls(
            fragment_id=str(data["fragment_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            language_name=str(data["language_name"]),
            width_bound=data.get("width_bound"),
            height_bound=data.get("height_bound"),
            supported_type_exprs=[str(item) for item in data.get("supported_type_exprs", [])],
            supported_term_constructors=[str(item) for item in data.get("supported_term_constructors", [])],
            supported_claim_types=[str(item) for item in data.get("supported_claim_types", [])],
            supported_verifiers=[str(item) for item in data.get("supported_verifiers", [])],
            blocked_term_patterns=[str(item) for item in data.get("blocked_term_patterns", [])],
            paradox_guard_policy=data.get("paradox_guard_policy"),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )


def etp_magma_equations_fragment() -> LanguageFragment:
    return LanguageFragment(
        fragment_id="fragment_etp_magma_equations",
        domain_kernel_id="etp_magma",
        formal_world_id="formal_world_etp_magma",
        language_name="ETP magma equations",
        width_bound=2,
        height_bound=None,
        supported_type_exprs=["i", "<>", "<i,i>"],
        supported_term_constructors=["variable", "binary_magma_operation", "equation", "implication_claim"],
        supported_claim_types=["equational_implication"],
        supported_verifiers=["python_finite_table_checker", "external_lean_optional"],
        paradox_guard_policy="parser_denotation_guard",
        notes="One binary operation, universal equations, implication between equations.",
    )


def external_theory_precedent_fragment() -> LanguageFragment:
    return LanguageFragment(
        fragment_id="fragment_aot_l23_precedent",
        domain_kernel_id="aot",
        formal_world_id="formal_world_aot_precedent",
        language_name="External theory precedent fragment",
        supported_type_exprs=["i", "<>", "<i>", "<i,i>", "<<i>>", "<<i,i>>"],
        supported_term_constructors=[
            "exemplification",
            "encoding",
            "definite_description",
            "lambda_relation",
            "theory_objectification",
        ],
        supported_claim_types=["object_theory_theorem_metadata"],
        supported_verifiers=["Isabelle/HOL precedent metadata only for now"],
        blocked_term_patterns=["unsafe_comprehension", "unguarded_definite_description", "unrestricted_lambda"],
        paradox_guard_policy="negative_free_logic_guarded_complex_terms",
        notes="Metadata-only external theory precedent; no Isabelle import yet.",
    )


def aot_l23_precedent_fragment() -> LanguageFragment:
    """Legacy internal alias; use ``external_theory_precedent_fragment`` publicly."""

    return external_theory_precedent_fragment()

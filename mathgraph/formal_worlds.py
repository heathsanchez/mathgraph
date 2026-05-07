"""Formal-world metadata boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FormalWorldKind(str, Enum):
    EQUATIONAL_THEORY_WORLD = "EQUATIONAL_THEORY_WORLD"
    OBJECT_THEORY_WORLD = "OBJECT_THEORY_WORLD"
    MODAL_WORLD_THEORY = "MODAL_WORLD_THEORY"
    LEIBNIZ_CONCEPT_WORLD = "LEIBNIZ_CONCEPT_WORLD"
    FINITE_MODEL_WORLD = "FINITE_MODEL_WORLD"
    ADVISORY_METADATA_WORLD = "ADVISORY_METADATA_WORLD"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FormalWorld:
    formal_world_id: str
    domain_kernel_id: str
    name: str
    world_kind: FormalWorldKind
    object_logic: str = ""
    identity_policy: str = ""
    denotation_policy: str = ""
    verifier_policy: str = ""
    language_fragment_ids: list[str] = field(default_factory=list)
    semantic_embedding_ids: list[str] = field(default_factory=list)
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "formal_world_id": self.formal_world_id,
            "domain_kernel_id": self.domain_kernel_id,
            "name": self.name,
            "world_kind": self.world_kind.value,
            "language_fragment_count": len(self.language_fragment_ids),
            "semantic_embedding_count": len(self.semantic_embedding_ids),
            "truth_boundary": "Formal worlds are context boundaries, not proof objects.",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "formal_world_id": self.formal_world_id,
            "domain_kernel_id": self.domain_kernel_id,
            "name": self.name,
            "world_kind": self.world_kind.value,
            "object_logic": self.object_logic,
            "identity_policy": self.identity_policy,
            "denotation_policy": self.denotation_policy,
            "verifier_policy": self.verifier_policy,
            "language_fragment_ids": list(self.language_fragment_ids),
            "semantic_embedding_ids": list(self.semantic_embedding_ids),
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormalWorld":
        return cls(
            formal_world_id=str(data["formal_world_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            name=str(data["name"]),
            world_kind=FormalWorldKind(str(data.get("world_kind", "UNKNOWN"))),
            object_logic=str(data.get("object_logic", "")),
            identity_policy=str(data.get("identity_policy", "")),
            denotation_policy=str(data.get("denotation_policy", "")),
            verifier_policy=str(data.get("verifier_policy", "")),
            language_fragment_ids=[str(item) for item in data.get("language_fragment_ids", [])],
            semantic_embedding_ids=[str(item) for item in data.get("semantic_embedding_ids", [])],
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )


def etp_magma_formal_world() -> FormalWorld:
    return FormalWorld(
        formal_world_id="formal_world_etp_magma",
        domain_kernel_id="etp_magma",
        name="ETP magma equational implication world",
        world_kind=FormalWorldKind.EQUATIONAL_THEORY_WORLD,
        object_logic="universal equational logic over magmas",
        identity_policy="equation_id_and_normalized_syntax",
        denotation_policy="all parsed core equations denote unless parser fails",
        verifier_policy="finite table countermodel checker; Lean optional",
        language_fragment_ids=["fragment_etp_magma_equations"],
        semantic_embedding_ids=["embedding_etp_native_finite_checker"],
        notes="Metadata boundary for SAIR/ETP magma nursery.",
    )


def aot_formal_world_precedent() -> FormalWorld:
    return FormalWorld(
        formal_world_id="formal_world_aot_precedent",
        domain_kernel_id="aot",
        name="AOT computational metaphysics precedent world",
        world_kind=FormalWorldKind.OBJECT_THEORY_WORLD,
        object_logic="AOT / second-order modal object theory",
        identity_policy="abstract_identity_by_encoded_properties",
        denotation_policy="negative_free_logic_guarded",
        verifier_policy="Isabelle/HOL metadata only until proof artifacts imported",
        language_fragment_ids=["fragment_aot_l23_precedent"],
        semantic_embedding_ids=["embedding_aot_isabelle_shallow"],
        notes="Formal-world metadata only; no Isabelle session import yet.",
    )

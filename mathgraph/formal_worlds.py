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
    workbench_id: str | None = None
    lifecycle_status: str = "DECLARED"
    embedding_strategy_profile_ids: list[str] = field(default_factory=list)
    faithfulness_assessment_ids: list[str] = field(default_factory=list)
    benchmark_suite_ids: list[str] = field(default_factory=list)
    verifier_backend_ids: list[str] = field(default_factory=list)
    logic_combination_ids: list[str] = field(default_factory=list)
    interpretation_choice_ids: list[str] = field(default_factory=list)
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
            "lifecycle_status": self.lifecycle_status,
            "benchmark_suite_count": len(self.benchmark_suite_ids),
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
            "workbench_id": self.workbench_id,
            "lifecycle_status": self.lifecycle_status,
            "embedding_strategy_profile_ids": list(self.embedding_strategy_profile_ids),
            "faithfulness_assessment_ids": list(self.faithfulness_assessment_ids),
            "benchmark_suite_ids": list(self.benchmark_suite_ids),
            "verifier_backend_ids": list(self.verifier_backend_ids),
            "logic_combination_ids": list(self.logic_combination_ids),
            "interpretation_choice_ids": list(self.interpretation_choice_ids),
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
            workbench_id=data.get("workbench_id"),
            lifecycle_status=str(data.get("lifecycle_status", "DECLARED")),
            embedding_strategy_profile_ids=[str(item) for item in data.get("embedding_strategy_profile_ids", [])],
            faithfulness_assessment_ids=[str(item) for item in data.get("faithfulness_assessment_ids", [])],
            benchmark_suite_ids=[str(item) for item in data.get("benchmark_suite_ids", [])],
            verifier_backend_ids=[str(item) for item in data.get("verifier_backend_ids", [])],
            logic_combination_ids=[str(item) for item in data.get("logic_combination_ids", [])],
            interpretation_choice_ids=[str(item) for item in data.get("interpretation_choice_ids", [])],
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
        workbench_id="workbench_mathgraph_default",
        lifecycle_status="BENCHMARKED",
        embedding_strategy_profile_ids=["strategy_etp_native_finite_checker"],
        faithfulness_assessment_ids=["faithfulness_etp_native_not_applicable"],
        benchmark_suite_ids=["benchmark_etp_matrix_metadata"],
        verifier_backend_ids=["backend_python_finite_table_checker", "backend_lean_placeholder"],
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
        workbench_id="workbench_logikey_style",
        lifecycle_status="SEMANTICS_SELECTED",
        embedding_strategy_profile_ids=["strategy_logikey_shallow_hol"],
        faithfulness_assessment_ids=["faithfulness_logikey_style_placeholder"],
        benchmark_suite_ids=["benchmark_logikey_methodology"],
        verifier_backend_ids=[
            "backend_isabelle_sledgehammer_placeholder",
            "backend_isabelle_nitpick_placeholder",
            "backend_isabelle_nunchaku_placeholder",
        ],
        notes="Formal-world metadata only; no Isabelle session import yet.",
    )

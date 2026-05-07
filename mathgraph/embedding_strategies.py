"""Embedding strategy profiles for plural formal-world workbenches."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EmbeddingStrategy(str, Enum):
    NATIVE_KERNEL = "NATIVE_KERNEL"
    SHALLOW_SEMANTIC_EMBEDDING = "SHALLOW_SEMANTIC_EMBEDDING"
    DEEP_SYNTAX_EMBEDDING = "DEEP_SYNTAX_EMBEDDING"
    HYBRID_SHALLOW_DEEP = "HYBRID_SHALLOW_DEEP"
    EXTERNAL_VERIFIER_BRIDGE = "EXTERNAL_VERIFIER_BRIDGE"
    ADVISORY_METADATA_ONLY = "ADVISORY_METADATA_ONLY"


class SyntaxRepresentation(str, Enum):
    NATIVE_OBJECTS = "NATIVE_OBJECTS"
    SHALLOW_HOST_TERMS = "SHALLOW_HOST_TERMS"
    DEEP_AST = "DEEP_AST"
    HYBRID = "HYBRID"
    EXTERNAL_TEXT = "EXTERNAL_TEXT"
    UNKNOWN = "UNKNOWN"


class SemanticsRepresentation(str, Enum):
    NATIVE_EVALUATOR = "NATIVE_EVALUATOR"
    HOST_LAMBDA_SEMANTICS = "HOST_LAMBDA_SEMANTICS"
    RECURSIVE_INTERPRETER = "RECURSIVE_INTERPRETER"
    AXIOMATIC_PROOF_RULES = "AXIOMATIC_PROOF_RULES"
    FINITE_CHECKER = "FINITE_CHECKER"
    EXTERNAL_VERIFIER = "EXTERNAL_VERIFIER"
    UNKNOWN = "UNKNOWN"


class AutomationBias(str, Enum):
    PROVER_FRIENDLY = "PROVER_FRIENDLY"
    MODEL_FINDER_FRIENDLY = "MODEL_FINDER_FRIENDLY"
    EXPLANATION_FRIENDLY = "EXPLANATION_FRIENDLY"
    CERTIFICATE_FRIENDLY = "CERTIFICATE_FRIENDLY"
    BENCHMARK_FRIENDLY = "BENCHMARK_FRIENDLY"
    UNKNOWN = "UNKNOWN"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class EmbeddingStrategyProfile:
    profile_id: str
    embedding_id: str | None = None
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    strategy: EmbeddingStrategy = EmbeddingStrategy.ADVISORY_METADATA_ONLY
    syntax_representation: SyntaxRepresentation = SyntaxRepresentation.UNKNOWN
    semantics_representation: SemanticsRepresentation = SemanticsRepresentation.UNKNOWN
    automation_bias: AutomationBias = AutomationBias.UNKNOWN
    expected_strengths: list[str] = field(default_factory=list)
    expected_risks: list[str] = field(default_factory=list)
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_shallow(self) -> bool:
        return self.strategy in {
            EmbeddingStrategy.SHALLOW_SEMANTIC_EMBEDDING,
            EmbeddingStrategy.HYBRID_SHALLOW_DEEP,
        }

    def is_deep(self) -> bool:
        return self.strategy in {
            EmbeddingStrategy.DEEP_SYNTAX_EMBEDDING,
            EmbeddingStrategy.HYBRID_SHALLOW_DEEP,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "embedding_id": self.embedding_id,
            "domain_kernel_id": self.domain_kernel_id,
            "strategy": self.strategy.value,
            "syntax_representation": self.syntax_representation.value,
            "semantics_representation": self.semantics_representation.value,
            "automation_bias": self.automation_bias.value,
            "is_shallow": self.is_shallow(),
            "is_deep": self.is_deep(),
            "truth_boundary": "Embedding strategy metadata does not prove object-theory claims.",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "embedding_id": self.embedding_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "strategy": self.strategy.value,
            "syntax_representation": self.syntax_representation.value,
            "semantics_representation": self.semantics_representation.value,
            "automation_bias": self.automation_bias.value,
            "expected_strengths": list(self.expected_strengths),
            "expected_risks": list(self.expected_risks),
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingStrategyProfile":
        return cls(
            profile_id=str(data["profile_id"]),
            embedding_id=data.get("embedding_id"),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            strategy=_enum(EmbeddingStrategy, data.get("strategy"), EmbeddingStrategy.ADVISORY_METADATA_ONLY),
            syntax_representation=_enum(
                SyntaxRepresentation, data.get("syntax_representation"), SyntaxRepresentation.UNKNOWN
            ),
            semantics_representation=_enum(
                SemanticsRepresentation, data.get("semantics_representation"), SemanticsRepresentation.UNKNOWN
            ),
            automation_bias=_enum(AutomationBias, data.get("automation_bias"), AutomationBias.UNKNOWN),
            expected_strengths=[str(item) for item in data.get("expected_strengths", [])],
            expected_risks=[str(item) for item in data.get("expected_risks", [])],
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )

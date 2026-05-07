"""Advisory registry records for formal theories and proof infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.semantic_embeddings import ArtifactRisk
from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


class TheoryDeclarationKind(str, Enum):
    AXIOM = "AXIOM"
    DEFINITION = "DEFINITION"
    THEOREM = "THEOREM"
    LEMMA = "LEMMA"
    COROLLARY = "COROLLARY"
    WORLD_DECLARATION = "WORLD_DECLARATION"
    SYNTAX_DECLARATION = "SYNTAX_DECLARATION"
    UNKNOWN = "UNKNOWN"


class ProofMethodKind(str, Enum):
    INTRO_RULE = "INTRO_RULE"
    ELIM_RULE = "ELIM_RULE"
    REWRITE_RULE = "REWRITE_RULE"
    INSTANTIATION_RULE = "INSTANTIATION_RULE"
    RULIFICATION = "RULIFICATION"
    SMT_BRIDGE = "SMT_BRIDGE"
    SLEDGEHAMMER_BRIDGE = "SLEDGEHAMMER_BRIDGE"
    CUSTOM_METHOD = "CUSTOM_METHOD"
    UNKNOWN = "UNKNOWN"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) in {member.name, member.value}:
            return member
    return default


@dataclass(frozen=True)
class TheoryDeclaration:
    declaration_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    theory_id: str
    declaration_kind: TheoryDeclarationKind
    name: str
    statement: str = ""
    source_file: str = ""
    source_line: int | None = None
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    host_logic: str = ""
    object_logic: str = ""
    object_theory_verified: bool = False
    host_embedding_verified: bool = False
    artifact_risk: ArtifactRisk = ArtifactRisk.UNKNOWN
    payload: dict[str, Any] = field(default_factory=dict)

    def is_verified_inside_mathgraph(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "theory_id": self.theory_id,
            "declaration_kind": self.declaration_kind.value,
            "name": self.name,
            "statement": self.statement,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "host_logic": self.host_logic,
            "object_logic": self.object_logic,
            "object_theory_verified": self.object_theory_verified,
            "host_embedding_verified": self.host_embedding_verified,
            "artifact_risk": self.artifact_risk.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TheoryDeclaration":
        return cls(
            declaration_id=str(data["declaration_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data.get("theory_id", "")),
            declaration_kind=_enum(
                TheoryDeclarationKind,
                data.get("declaration_kind"),
                TheoryDeclarationKind.UNKNOWN,
            ),
            name=str(data.get("name", "")),
            statement=str(data.get("statement", "")),
            source_file=str(data.get("source_file", "")),
            source_line=_optional_int(data.get("source_line")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            host_logic=str(data.get("host_logic", "")),
            object_logic=str(data.get("object_logic", "")),
            object_theory_verified=bool(data.get("object_theory_verified", False)),
            host_embedding_verified=bool(data.get("host_embedding_verified", False)),
            artifact_risk=_enum(ArtifactRisk, data.get("artifact_risk"), ArtifactRisk.UNKNOWN),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class ProofMethod:
    proof_method_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    theory_id: str
    name: str
    method_kind: ProofMethodKind = ProofMethodKind.UNKNOWN
    source_file: str = ""
    source_line: int | None = None
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_method_id": self.proof_method_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "theory_id": self.theory_id,
            "name": self.name,
            "method_kind": self.method_kind.value,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProofMethod":
        return cls(
            proof_method_id=str(data["proof_method_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data.get("theory_id", "")),
            name=str(data.get("name", "")),
            method_kind=_enum(ProofMethodKind, data.get("method_kind"), ProofMethodKind.UNKNOWN),
            source_file=str(data.get("source_file", "")),
            source_line=_optional_int(data.get("source_line")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class InferenceRule:
    inference_rule_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    theory_id: str
    name: str
    rule_kind: ProofMethodKind = ProofMethodKind.UNKNOWN
    statement: str = ""
    source_file: str = ""
    source_line: int | None = None
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inference_rule_id": self.inference_rule_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "theory_id": self.theory_id,
            "name": self.name,
            "rule_kind": self.rule_kind.value,
            "statement": self.statement,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InferenceRule":
        return cls(
            inference_rule_id=str(data["inference_rule_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data.get("theory_id", "")),
            name=str(data.get("name", "")),
            rule_kind=_enum(ProofMethodKind, data.get("rule_kind"), ProofMethodKind.UNKNOWN),
            statement=str(data.get("statement", "")),
            source_file=str(data.get("source_file", "")),
            source_line=_optional_int(data.get("source_line")),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
            payload=dict(data.get("payload", {})),
        )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

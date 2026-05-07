"""Semantic embedding risk metadata and proof transport guards."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EmbeddingKind(str, Enum):
    NATIVE_KERNEL = "NATIVE_KERNEL"
    SHALLOW_SEMANTIC_EMBEDDING = "SHALLOW_SEMANTIC_EMBEDDING"
    DEEP_SYNTAX_IMPORT = "DEEP_SYNTAX_IMPORT"
    EXTERNAL_VERIFIER_BRIDGE = "EXTERNAL_VERIFIER_BRIDGE"
    ADVISORY_METADATA_ONLY = "ADVISORY_METADATA_ONLY"


class ArtifactRisk(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class ProofTransportStatus(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    HOST_ONLY = "HOST_ONLY"
    TRANSPORT_PENDING = "TRANSPORT_PENDING"
    TRANSPORT_VALIDATED = "TRANSPORT_VALIDATED"
    TRANSPORT_FAILED = "TRANSPORT_FAILED"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class SemanticEmbedding:
    embedding_id: str
    domain_kernel_id: str
    formal_world_id: str | None = None
    embedding_kind: EmbeddingKind = EmbeddingKind.ADVISORY_METADATA_ONLY
    host_logic: str = ""
    object_logic: str = ""
    host_verifier: str = ""
    object_theory: str = ""
    artifact_risk: ArtifactRisk = ArtifactRisk.UNKNOWN
    object_theory_verified: bool = False
    host_embedding_verified: bool = False
    proof_transport_status: ProofTransportStatus = ProofTransportStatus.NOT_ATTEMPTED
    embedding_strategy_profile_id: str | None = None
    faithfulness_assessment_id: str | None = None
    syntax_representation: str | None = None
    semantics_representation: str | None = None
    automation_bias: str | None = None
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_promotion_safe(self) -> bool:
        low_risk = self.artifact_risk in {ArtifactRisk.NONE, ArtifactRisk.LOW}
        if self.embedding_kind is EmbeddingKind.NATIVE_KERNEL:
            return low_risk and self.object_theory_verified
        faithfulness_validated = bool(self.faithfulness_assessment_id) or bool(
            self.payload.get("faithfulness_validated")
        )
        return (
            low_risk
            and self.object_theory_verified
            and self.proof_transport_status is ProofTransportStatus.TRANSPORT_VALIDATED
            and faithfulness_validated
        )

    def advisory_warning(self) -> str:
        return (
            f"Semantic embedding {self.embedding_id} has artifact risk "
            f"{self.artifact_risk.value} and proof transport "
            f"{self.proof_transport_status.value}; host proof is not automatically target proof."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "embedding_id": self.embedding_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "embedding_kind": self.embedding_kind.value,
            "host_logic": self.host_logic,
            "object_logic": self.object_logic,
            "host_verifier": self.host_verifier,
            "object_theory": self.object_theory,
            "artifact_risk": self.artifact_risk.value,
            "object_theory_verified": self.object_theory_verified,
            "host_embedding_verified": self.host_embedding_verified,
            "proof_transport_status": self.proof_transport_status.value,
            "embedding_strategy_profile_id": self.embedding_strategy_profile_id,
            "faithfulness_assessment_id": self.faithfulness_assessment_id,
            "syntax_representation": self.syntax_representation,
            "semantics_representation": self.semantics_representation,
            "automation_bias": self.automation_bias,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SemanticEmbedding":
        return cls(
            embedding_id=str(data["embedding_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            embedding_kind=_enum(EmbeddingKind, data.get("embedding_kind"), EmbeddingKind.ADVISORY_METADATA_ONLY),
            host_logic=str(data.get("host_logic", "")),
            object_logic=str(data.get("object_logic", "")),
            host_verifier=str(data.get("host_verifier", "")),
            object_theory=str(data.get("object_theory", "")),
            artifact_risk=_enum(ArtifactRisk, data.get("artifact_risk"), ArtifactRisk.UNKNOWN),
            object_theory_verified=bool(data.get("object_theory_verified", False)),
            host_embedding_verified=bool(data.get("host_embedding_verified", False)),
            proof_transport_status=_enum(
                ProofTransportStatus,
                data.get("proof_transport_status"),
                ProofTransportStatus.NOT_ATTEMPTED,
            ),
            embedding_strategy_profile_id=data.get("embedding_strategy_profile_id"),
            faithfulness_assessment_id=data.get("faithfulness_assessment_id"),
            syntax_representation=data.get("syntax_representation"),
            semantics_representation=data.get("semantics_representation"),
            automation_bias=data.get("automation_bias"),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )

"""Proof-finder and model-finder result records."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.trust import TrustLevel, trust_level


class ProofFinderStatus(str, Enum):
    PROOF_FOUND = "PROOF_FOUND"
    NO_PROOF_FOUND = "NO_PROOF_FOUND"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class ModelFinderStatus(str, Enum):
    MODEL_FOUND = "MODEL_FOUND"
    NO_MODEL_FOUND = "NO_MODEL_FOUND"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


SAFE_TRUST = {TrustLevel.LEAN_VERIFIED, TrustLevel.FINITE_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}
SAFE_RISK = {"NONE", "LOW"}


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class ProofFinderResult:
    result_id: str
    claim_id: str | None
    backend_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    status: ProofFinderStatus
    proof_artifact_id: str | None = None
    proof_text: str | None = None
    runtime_sec: float | None = None
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "IMPORTED"
    artifact_risk: str = "UNKNOWN"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        return (
            self.status is ProofFinderStatus.PROOF_FOUND
            and trust_level(self.trust_level) in SAFE_TRUST
            and self.artifact_risk in SAFE_RISK
            and bool(self.proof_artifact_id)
        )

    def advisory_warning(self) -> str:
        if self.status is ProofFinderStatus.NO_PROOF_FOUND:
            return "No proof found is not refutation."
        return "Proof-finder output is advisory until a replayable proof artifact is verified."

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "claim_id": self.claim_id,
            "backend_id": self.backend_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "status": self.status.value,
            "proof_artifact_id": self.proof_artifact_id,
            "proof_text": self.proof_text,
            "runtime_sec": self.runtime_sec,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "artifact_risk": self.artifact_risk,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProofFinderResult":
        return cls(
            result_id=str(data["result_id"]),
            claim_id=data.get("claim_id"),
            backend_id=str(data["backend_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            status=_enum(ProofFinderStatus, data.get("status"), ProofFinderStatus.UNKNOWN),
            proof_artifact_id=data.get("proof_artifact_id"),
            proof_text=data.get("proof_text"),
            runtime_sec=data.get("runtime_sec"),
            trust_level=str(data.get("trust_level", "ADVISORY_ROUTE")),
            provenance_type=str(data.get("provenance_type", "IMPORTED")),
            artifact_risk=str(data.get("artifact_risk", "UNKNOWN")),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class ModelFinderResult:
    result_id: str
    claim_id: str | None
    backend_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    status: ModelFinderStatus
    model_artifact_id: str | None = None
    model_payload: dict[str, Any] = field(default_factory=dict)
    scope_bounds: dict[str, Any] = field(default_factory=dict)
    runtime_sec: float | None = None
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "IMPORTED"
    artifact_risk: str = "UNKNOWN"
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_refutation_candidate(self) -> bool:
        return self.status is ModelFinderStatus.MODEL_FOUND and bool(self.model_artifact_id or self.model_payload)

    def is_authoritative(self) -> bool:
        return (
            self.status is ModelFinderStatus.MODEL_FOUND
            and trust_level(self.trust_level) in SAFE_TRUST
            and self.artifact_risk in SAFE_RISK
            and bool(self.model_artifact_id)
        )

    def advisory_warning(self) -> str:
        if self.status is ModelFinderStatus.NO_MODEL_FOUND:
            return "No model found is not proof."
        return "Model-finder output is advisory until a replayable countermodel artifact is verified."

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "claim_id": self.claim_id,
            "backend_id": self.backend_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "status": self.status.value,
            "model_artifact_id": self.model_artifact_id,
            "model_payload": dict(self.model_payload),
            "scope_bounds": dict(self.scope_bounds),
            "runtime_sec": self.runtime_sec,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "artifact_risk": self.artifact_risk,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelFinderResult":
        return cls(
            result_id=str(data["result_id"]),
            claim_id=data.get("claim_id"),
            backend_id=str(data["backend_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            status=_enum(ModelFinderStatus, data.get("status"), ModelFinderStatus.UNKNOWN),
            model_artifact_id=data.get("model_artifact_id"),
            model_payload=dict(data.get("model_payload", {})),
            scope_bounds=dict(data.get("scope_bounds", {})),
            runtime_sec=data.get("runtime_sec"),
            trust_level=str(data.get("trust_level", "ADVISORY_ROUTE")),
            provenance_type=str(data.get("provenance_type", "IMPORTED")),
            artifact_risk=str(data.get("artifact_risk", "UNKNOWN")),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )

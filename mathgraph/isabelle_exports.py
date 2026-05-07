"""Metadata boundary for future Isabelle export ingestion.

No Isabelle execution or proof checking happens here. These records only make
host/object theorem transport status explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IsabelleExportStatus(str, Enum):
    NOT_IMPORTED = "NOT_IMPORTED"
    IMPORTED_METADATA_ONLY = "IMPORTED_METADATA_ONLY"
    HOST_VERIFIED = "HOST_VERIFIED"
    OBJECT_TRANSPORT_VALIDATED = "OBJECT_TRANSPORT_VALIDATED"
    TRANSPORT_FAILED = "TRANSPORT_FAILED"


def _status(value: Any) -> IsabelleExportStatus:
    if isinstance(value, IsabelleExportStatus):
        return value
    for status in IsabelleExportStatus:
        if str(value) in {status.name, status.value}:
            return status
    return IsabelleExportStatus.NOT_IMPORTED


@dataclass(frozen=True)
class IsabelleExportRecord:
    export_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    theory_id: str
    name: str
    source_file: str = ""
    host_logic: str = "Isabelle/HOL"
    object_logic: str = ""
    export_status: IsabelleExportStatus = IsabelleExportStatus.IMPORTED_METADATA_ONLY
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "export_id": self.export_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "theory_id": self.theory_id,
            "name": self.name,
            "source_file": self.source_file,
            "host_logic": self.host_logic,
            "object_logic": self.object_logic,
            "export_status": self.export_status.value,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IsabelleExportRecord":
        return cls(
            export_id=str(data["export_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data.get("theory_id", "")),
            name=str(data.get("name", "")),
            source_file=str(data.get("source_file", "")),
            host_logic=str(data.get("host_logic", "Isabelle/HOL")),
            object_logic=str(data.get("object_logic", "")),
            export_status=_status(data.get("export_status")),
            payload=dict(data.get("payload", {})),
        )


@dataclass(frozen=True)
class HostObjectTheoremLink:
    link_id: str
    domain_kernel_id: str | None
    formal_world_id: str | None
    theory_id: str
    host_theorem_id: str
    object_theorem_id: str
    export_status: IsabelleExportStatus = IsabelleExportStatus.IMPORTED_METADATA_ONLY
    proof_transport_status: str = "NOT_ATTEMPTED"
    artifact_risk: str = "UNKNOWN"
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "theory_id": self.theory_id,
            "host_theorem_id": self.host_theorem_id,
            "object_theorem_id": self.object_theorem_id,
            "export_status": self.export_status.value,
            "proof_transport_status": self.proof_transport_status,
            "artifact_risk": self.artifact_risk,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HostObjectTheoremLink":
        return cls(
            link_id=str(data["link_id"]),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            theory_id=str(data.get("theory_id", "")),
            host_theorem_id=str(data.get("host_theorem_id", "")),
            object_theorem_id=str(data.get("object_theorem_id", "")),
            export_status=_status(data.get("export_status")),
            proof_transport_status=str(data.get("proof_transport_status", "NOT_ATTEMPTED")),
            artifact_risk=str(data.get("artifact_risk", "UNKNOWN")),
            payload=dict(data.get("payload", {})),
        )

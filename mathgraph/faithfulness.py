"""Faithfulness assessment metadata for semantic embeddings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FaithfulnessStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    EMPIRICALLY_SUPPORTED = "EMPIRICALLY_SUPPORTED"
    PROVED_ON_PAPER = "PROVED_ON_PAPER"
    MECHANIZED = "MECHANIZED"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SoundnessStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    SOUND = "SOUND"
    UNSOUND = "UNSOUND"
    RELATIVE_SOUNDNESS = "RELATIVE_SOUNDNESS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CompletenessStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    RELATIVE_COMPLETE = "RELATIVE_COMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value:
            return member
    return default


@dataclass(frozen=True)
class FaithfulnessAssessment:
    assessment_id: str
    domain_kernel_id: str
    formal_world_id: str | None
    embedding_id: str
    object_logic: str
    host_logic: str
    status: FaithfulnessStatus = FaithfulnessStatus.UNKNOWN
    soundness_status: SoundnessStatus = SoundnessStatus.UNKNOWN
    completeness_status: CompletenessStatus = CompletenessStatus.UNKNOWN
    benchmark_suite_id: str | None = None
    proof_artifact_id: str | None = None
    counterexamples_found: int = 0
    assessed_by: str | None = None
    notes: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def is_promotion_supporting(self) -> bool:
        return (
            self.status in {
                FaithfulnessStatus.MECHANIZED,
                FaithfulnessStatus.PROVED_ON_PAPER,
                FaithfulnessStatus.EMPIRICALLY_SUPPORTED,
            }
            and self.soundness_status in {SoundnessStatus.SOUND, SoundnessStatus.RELATIVE_SOUNDNESS}
            and int(self.counterexamples_found) == 0
        )

    def risk_note(self) -> str:
        if self.status in {FaithfulnessStatus.UNKNOWN, FaithfulnessStatus.FAILED}:
            return f"Faithfulness assessment {self.assessment_id} is {self.status.value}; embedding risk remains."
        if self.soundness_status not in {SoundnessStatus.SOUND, SoundnessStatus.RELATIVE_SOUNDNESS}:
            return f"Faithfulness assessment {self.assessment_id} lacks soundness support."
        if self.counterexamples_found:
            return f"Faithfulness assessment {self.assessment_id} found counterexamples."
        return "Faithfulness assessment supports lower bridge risk but does not prove arbitrary claims."

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "embedding_id": self.embedding_id,
            "object_logic": self.object_logic,
            "host_logic": self.host_logic,
            "status": self.status.value,
            "soundness_status": self.soundness_status.value,
            "completeness_status": self.completeness_status.value,
            "benchmark_suite_id": self.benchmark_suite_id,
            "proof_artifact_id": self.proof_artifact_id,
            "counterexamples_found": self.counterexamples_found,
            "assessed_by": self.assessed_by,
            "notes": self.notes,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FaithfulnessAssessment":
        return cls(
            assessment_id=str(data["assessment_id"]),
            domain_kernel_id=str(data["domain_kernel_id"]),
            formal_world_id=data.get("formal_world_id"),
            embedding_id=str(data["embedding_id"]),
            object_logic=str(data.get("object_logic", "")),
            host_logic=str(data.get("host_logic", "")),
            status=_enum(FaithfulnessStatus, data.get("status"), FaithfulnessStatus.UNKNOWN),
            soundness_status=_enum(SoundnessStatus, data.get("soundness_status"), SoundnessStatus.UNKNOWN),
            completeness_status=_enum(
                CompletenessStatus, data.get("completeness_status"), CompletenessStatus.UNKNOWN
            ),
            benchmark_suite_id=data.get("benchmark_suite_id"),
            proof_artifact_id=data.get("proof_artifact_id"),
            counterexamples_found=int(data.get("counterexamples_found", 0) or 0),
            assessed_by=data.get("assessed_by"),
            notes=str(data.get("notes", "")),
            payload=dict(data.get("payload", {})),
        )

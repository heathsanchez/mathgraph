"""Domain-agnostic claim identity for MathGraph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.trust import ProvenanceType, TrustLevel, provenance_type, trust_level


def normalize_claim_text(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


@dataclass(frozen=True)
class GeneralClaim:
    claim_id: str
    domain: str
    source: str
    target: str
    normalized_source: str
    normalized_target: str
    source_idx: int | None = None
    target_idx: int | None = None
    claim_type: str = "implication"
    metadata: dict[str, Any] = field(default_factory=dict)
    trust_level: TrustLevel = TrustLevel.ADVISORY_ROUTE
    provenance_type: ProvenanceType = ProvenanceType.IMPORTED

    @classmethod
    def create(
        cls,
        source: str,
        target: str,
        *,
        domain: str = "magma_equation",
        source_idx: int | None = None,
        target_idx: int | None = None,
        claim_type: str = "implication",
        metadata: dict[str, Any] | None = None,
        trust_level_value: str | TrustLevel | None = None,
        provenance_type_value: str | ProvenanceType | None = None,
    ) -> "GeneralClaim":
        normalized_source = normalize_claim_text(source)
        normalized_target = normalize_claim_text(target)
        payload = {
            "domain": domain,
            "source": normalized_source,
            "target": normalized_target,
            "source_idx": source_idx,
            "target_idx": target_idx,
            "claim_type": claim_type,
        }
        return cls(
            claim_id=content_id("claim", payload),
            domain=domain,
            source=source,
            target=target,
            normalized_source=normalized_source,
            normalized_target=normalized_target,
            source_idx=source_idx,
            target_idx=target_idx,
            claim_type=claim_type,
            metadata=dict(metadata or {}),
            trust_level=trust_level(trust_level_value),
            provenance_type=provenance_type(provenance_type_value),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "domain": self.domain,
            "source": self.source,
            "target": self.target,
            "normalized_source": self.normalized_source,
            "normalized_target": self.normalized_target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "claim_type": self.claim_type,
            "metadata": dict(self.metadata),
            "trust_level": self.trust_level.value,
            "provenance_type": self.provenance_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneralClaim":
        return cls(
            claim_id=str(data.get("claim_id") or content_id("claim", data)),
            domain=str(data.get("domain", "magma_equation")),
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            normalized_source=str(
                data.get("normalized_source") or normalize_claim_text(data.get("source"))
            ),
            normalized_target=str(
                data.get("normalized_target") or normalize_claim_text(data.get("target"))
            ),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            claim_type=str(data.get("claim_type", "implication")),
            metadata=dict(data.get("metadata", {})),
            trust_level=trust_level(data.get("trust_level")),
            provenance_type=provenance_type(data.get("provenance_type")),
        )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

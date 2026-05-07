"""TRUE-side proof motif records and lightweight inference helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.trust import TrustLevel, trust_level


class ProofMotifKind(str, Enum):
    VARIABLE_IDENTIFICATION = "VARIABLE_IDENTIFICATION"
    TERM_REWRITE = "TERM_REWRITE"
    SOURCE_COLLAPSE = "SOURCE_COLLAPSE"
    TARGET_SUBSTITUTION = "TARGET_SUBSTITUTION"
    PROJECTION_FORCED = "PROJECTION_FORCED"
    TRIVIALIZATION = "TRIVIALIZATION"
    TRANSITIVITY_CHAIN = "TRANSITIVITY_CHAIN"
    EQUIVALENCE_CLASS_CANONICALIZATION = "EQUIVALENCE_CLASS_CANONICALIZATION"
    DIAGONALIZATION = "DIAGONALIZATION"
    ASSOCIATIVE_RESHAPE = "ASSOCIATIVE_RESHAPE"
    COMMUTATIVE_RESHAPE = "COMMUTATIVE_RESHAPE"
    IDEMPOTENT_COLLAPSE = "IDEMPOTENT_COLLAPSE"
    ABSORPTION = "ABSORPTION"
    ROUTE_COMPOSITION = "ROUTE_COMPOSITION"
    UNKNOWN = "UNKNOWN"


class ProofRouteStatus(str, Enum):
    OBSERVED = "OBSERVED"
    IMPORTED = "IMPORTED"
    GENERATED = "GENERATED"
    SKETCHED = "SKETCHED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    ADVISORY = "ADVISORY"


SAFE_TRUST = {TrustLevel.LEAN_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}
SAFE_STATUS = {"LEAN_VERIFIED", "VERIFIED_PROOF", "DERIVED_CHAIN_VERIFIED", "VERIFIED"}


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if str(value) == member.value or str(value) == member.name:
            return member
    return default


def make_proof_motif_id(
    motif_kind: str,
    source_basin: str | None = None,
    target_basin: str | None = None,
    route_signature: str | None = None,
    normalized_pattern: str | None = None,
) -> str:
    return content_id(
        "proof_motif",
        {
            "motif_kind": motif_kind,
            "source_basin": source_basin or "",
            "target_basin": target_basin or "",
            "route_signature": route_signature or "",
            "normalized_pattern": normalized_pattern or "",
        },
    )


def infer_proof_motif_kind(row_or_features: dict[str, Any]) -> str:
    text = " ".join(
        str(row_or_features.get(key, ""))
        for key in ("proof_motif", "proof_route", "route_name", "route_signature", "theorem_name")
    ).lower()
    if "variable" in text or "rename" in text or "identification" in text:
        return ProofMotifKind.VARIABLE_IDENTIFICATION.value
    if "transitiv" in text or "chain" in text:
        return ProofMotifKind.TRANSITIVITY_CHAIN.value
    if "projection" in text or "project" in text:
        return ProofMotifKind.PROJECTION_FORCED.value
    if "collapse" in text:
        return ProofMotifKind.SOURCE_COLLAPSE.value
    if "substitut" in text:
        return ProofMotifKind.TARGET_SUBSTITUTION.value
    if "rewrite" in text:
        return ProofMotifKind.TERM_REWRITE.value
    if "trivial" in text:
        return ProofMotifKind.TRIVIALIZATION.value
    if "assoc" in text:
        return ProofMotifKind.ASSOCIATIVE_RESHAPE.value
    if "commut" in text:
        return ProofMotifKind.COMMUTATIVE_RESHAPE.value
    if "idempot" in text:
        return ProofMotifKind.IDEMPOTENT_COLLAPSE.value
    if "absorp" in text:
        return ProofMotifKind.ABSORPTION.value
    return ProofMotifKind.UNKNOWN.value


@dataclass(frozen=True)
class ProofMotif:
    proof_motif_id: str
    motif_kind: ProofMotifKind | str
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    source_basin: str | None = None
    target_basin: str | None = None
    source_shape: str | None = None
    target_shape: str | None = None
    route_signature: str | None = None
    normalized_pattern: str | None = None
    support_count: int = 0
    unique_sources: int = 0
    unique_targets: int = 0
    unique_claims: int = 0
    example_claim_ids: list[str] = field(default_factory=list)
    example_source_idxs: list[int] = field(default_factory=list)
    example_target_idxs: list[int] = field(default_factory=list)
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "IMPORTED"
    verification_status: str = "UNKNOWN"
    status: ProofRouteStatus | str = ProofRouteStatus.ADVISORY
    payload: dict[str, Any] = field(default_factory=dict)

    def is_authoritative(self) -> bool:
        return trust_level(self.trust_level) in SAFE_TRUST or self.verification_status in SAFE_STATUS

    def advisory_warning(self) -> str:
        return "Proof motifs are advisory unless backed by verified proof artifacts or certificate chains."

    def summary(self) -> dict[str, Any]:
        return {
            "proof_motif_id": self.proof_motif_id,
            "motif_kind": _value(self.motif_kind),
            "support_count": self.support_count,
            "unique_claims": self.unique_claims,
            "verification_status": self.verification_status,
            "authoritative": self.is_authoritative(),
            "truth_boundary": self.advisory_warning(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_motif_id": self.proof_motif_id,
            "motif_kind": _value(self.motif_kind),
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "source_basin": self.source_basin,
            "target_basin": self.target_basin,
            "source_shape": self.source_shape,
            "target_shape": self.target_shape,
            "route_signature": self.route_signature,
            "normalized_pattern": self.normalized_pattern,
            "support_count": self.support_count,
            "unique_sources": self.unique_sources,
            "unique_targets": self.unique_targets,
            "unique_claims": self.unique_claims,
            "example_claim_ids": list(self.example_claim_ids),
            "example_source_idxs": list(self.example_source_idxs),
            "example_target_idxs": list(self.example_target_idxs),
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "verification_status": self.verification_status,
            "status": _value(self.status),
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProofMotif":
        return cls(
            proof_motif_id=str(data["proof_motif_id"]),
            motif_kind=_enum(ProofMotifKind, data.get("motif_kind"), ProofMotifKind.UNKNOWN),
            domain_kernel_id=data.get("domain_kernel_id"),
            formal_world_id=data.get("formal_world_id"),
            source_basin=data.get("source_basin"),
            target_basin=data.get("target_basin"),
            source_shape=data.get("source_shape"),
            target_shape=data.get("target_shape"),
            route_signature=data.get("route_signature"),
            normalized_pattern=data.get("normalized_pattern"),
            support_count=int(data.get("support_count", 0) or 0),
            unique_sources=int(data.get("unique_sources", 0) or 0),
            unique_targets=int(data.get("unique_targets", 0) or 0),
            unique_claims=int(data.get("unique_claims", 0) or 0),
            example_claim_ids=[str(item) for item in data.get("example_claim_ids", [])],
            example_source_idxs=[int(item) for item in data.get("example_source_idxs", [])],
            example_target_idxs=[int(item) for item in data.get("example_target_idxs", [])],
            trust_level=str(data.get("trust_level", "ADVISORY_ROUTE")),
            provenance_type=str(data.get("provenance_type", "IMPORTED")),
            verification_status=str(data.get("verification_status", "UNKNOWN")),
            status=_enum(ProofRouteStatus, data.get("status"), ProofRouteStatus.ADVISORY),
            payload=dict(data.get("payload", {})),
        )


def proof_motif_from_group(
    rows: list[dict[str, Any]],
    *,
    motif_kind: str,
    source_basin: str | None = None,
    target_basin: str | None = None,
    route_signature: str | None = None,
    domain_kernel_id: str | None = "etp_magma",
    formal_world_id: str | None = None,
) -> ProofMotif:
    claim_ids = [str(row.get("claim_id") or f"{row.get('source_idx')}->{row.get('target_idx')}") for row in rows]
    sources = [_optional_int(row.get("source_idx")) for row in rows]
    targets = [_optional_int(row.get("target_idx")) for row in rows]
    sources = [item for item in sources if item is not None]
    targets = [item for item in targets if item is not None]
    motif_id = make_proof_motif_id(motif_kind, source_basin, target_basin, route_signature)
    return ProofMotif(
        proof_motif_id=motif_id,
        motif_kind=motif_kind,
        domain_kernel_id=domain_kernel_id,
        formal_world_id=formal_world_id,
        source_basin=source_basin,
        target_basin=target_basin,
        route_signature=route_signature,
        normalized_pattern="::".join(part or "" for part in (motif_kind, source_basin, target_basin, route_signature)),
        support_count=len(rows),
        unique_sources=len(set(sources)),
        unique_targets=len(set(targets)),
        unique_claims=len(set(claim_ids)),
        example_claim_ids=claim_ids[:10],
        example_source_idxs=sources[:10],
        example_target_idxs=targets[:10],
        trust_level="ADVISORY_ROUTE",
        provenance_type="IMPORTED",
        verification_status="UNKNOWN",
        status=ProofRouteStatus.OBSERVED,
        payload={"truth_boundary": "motif_group_is_not_proof"},
    )


def _optional_int(value: Any) -> int | None:
    try:
        return None if value in (None, "") else int(value)
    except (TypeError, ValueError):
        return None


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)

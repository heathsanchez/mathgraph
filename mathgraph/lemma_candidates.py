"""Lemma and cut-introduction candidate records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.proof_motifs import ProofMotif
from mathgraph.trust import TrustLevel, trust_level


class LemmaCandidateStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    SKETCH_GENERATED = "SKETCH_GENERATED"
    LEAN_ARTIFACT_GENERATED = "LEAN_ARTIFACT_GENERATED"
    LEAN_VERIFIED = "LEAN_VERIFIED"
    LEAN_FAILED = "LEAN_FAILED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class CutIntroductionKind(str, Enum):
    NAMED_INTERMEDIATE_PROPERTY = "NAMED_INTERMEDIATE_PROPERTY"
    NORMAL_FORM_LEMMA = "NORMAL_FORM_LEMMA"
    SOURCE_COLLAPSE_LEMMA = "SOURCE_COLLAPSE_LEMMA"
    TARGET_DEMAND_LEMMA = "TARGET_DEMAND_LEMMA"
    PROJECTION_LEMMA = "PROJECTION_LEMMA"
    TRIVIALIZATION_LEMMA = "TRIVIALIZATION_LEMMA"
    TRANSITIVITY_COMPRESSOR = "TRANSITIVITY_COMPRESSOR"
    EQUIVALENCE_REPRESENTATIVE = "EQUIVALENCE_REPRESENTATIVE"
    HIGHER_ORDER_SCHEMA = "HIGHER_ORDER_SCHEMA"
    UNKNOWN = "UNKNOWN"


SAFE_TRUST = {TrustLevel.LEAN_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}


def canonical_lemma_name(*parts: str | None) -> str:
    text = "_".join(part or "" for part in parts if part)
    text = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_").lower()
    text = re.sub(r"_+", "_", text)
    return f"mg_{text or 'lemma_candidate'}"


def make_lemma_candidate_id(candidate_name: str, statement_text: str = "", proof_motif_id: str | None = None) -> str:
    return content_id(
        "lemma_candidate",
        {"candidate_name": candidate_name, "statement_text": statement_text, "proof_motif_id": proof_motif_id or ""},
    )


@dataclass(frozen=True)
class LemmaCandidate:
    lemma_candidate_id: str
    candidate_name: str
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    proof_motif_id: str | None = None
    reason_node_id: str | None = None
    root_node_id: str | None = None
    cut_kind: CutIntroductionKind | str = CutIntroductionKind.UNKNOWN
    statement_text: str = ""
    normalized_statement: str | None = None
    lean_statement: str | None = None
    lean_sketch: str | None = None
    expected_covered_claims: int = 0
    example_claim_ids: list[str] = field(default_factory=list)
    example_source_idxs: list[int] = field(default_factory=list)
    example_target_idxs: list[int] = field(default_factory=list)
    status: LemmaCandidateStatus | str = LemmaCandidateStatus.CANDIDATE
    trust_level: str = "ADVISORY_ROUTE"
    provenance_type: str = "GENERATED"
    verification_status: str = "UNKNOWN"
    verifier_id: str | None = None
    proof_artifact_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def is_verified(self) -> bool:
        return _value(self.status) == LemmaCandidateStatus.LEAN_VERIFIED.value or self.verification_status == "LEAN_VERIFIED"

    def is_authoritative(self) -> bool:
        return self.is_verified() and trust_level(self.trust_level) in SAFE_TRUST and bool(self.proof_artifact_id or self.verifier_id)

    def advisory_warning(self) -> str:
        return "Lemma candidates are proposed cuts, not theorems, until Lean verifies them."

    def summary(self) -> dict[str, Any]:
        return {
            "lemma_candidate_id": self.lemma_candidate_id,
            "candidate_name": self.candidate_name,
            "cut_kind": _value(self.cut_kind),
            "expected_covered_claims": self.expected_covered_claims,
            "status": _value(self.status),
            "verification_status": self.verification_status,
            "authoritative": self.is_authoritative(),
            "truth_boundary": self.advisory_warning(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "lemma_candidate_id": self.lemma_candidate_id,
            "candidate_name": self.candidate_name,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "proof_motif_id": self.proof_motif_id,
            "reason_node_id": self.reason_node_id,
            "root_node_id": self.root_node_id,
            "cut_kind": _value(self.cut_kind),
            "statement_text": self.statement_text,
            "normalized_statement": self.normalized_statement,
            "lean_statement": self.lean_statement,
            "lean_sketch": self.lean_sketch,
            "expected_covered_claims": self.expected_covered_claims,
            "example_claim_ids": list(self.example_claim_ids),
            "example_source_idxs": list(self.example_source_idxs),
            "example_target_idxs": list(self.example_target_idxs),
            "status": _value(self.status),
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "verification_status": self.verification_status,
            "verifier_id": self.verifier_id,
            "proof_artifact_id": self.proof_artifact_id,
            "payload": dict(self.payload),
        }


def lemma_candidate_from_motif(motif: ProofMotif, index: int = 0) -> LemmaCandidate:
    cut_kind = _cut_kind_for_motif(str(motif.motif_kind.value if hasattr(motif.motif_kind, "value") else motif.motif_kind))
    name = canonical_lemma_name(str(cut_kind).lower(), motif.source_basin, motif.target_basin, str(index))
    statement = (
        f"Candidate cut for {motif.motif_kind}: "
        f"{motif.source_basin or 'unknown_source'} -> {motif.target_basin or 'unknown_target'}"
    )
    return LemmaCandidate(
        lemma_candidate_id=make_lemma_candidate_id(name, statement, motif.proof_motif_id),
        candidate_name=name,
        domain_kernel_id=motif.domain_kernel_id,
        formal_world_id=motif.formal_world_id,
        proof_motif_id=motif.proof_motif_id,
        cut_kind=cut_kind,
        statement_text=statement,
        normalized_statement=" ".join(statement.split()),
        lean_statement="True",
        expected_covered_claims=motif.unique_claims or motif.support_count,
        example_claim_ids=list(motif.example_claim_ids),
        example_source_idxs=list(motif.example_source_idxs),
        example_target_idxs=list(motif.example_target_idxs),
        payload={"truth_boundary": "candidate_cut_requires_lean_verification"},
    )


def _cut_kind_for_motif(motif_kind: str) -> CutIntroductionKind:
    if "PROJECTION" in motif_kind:
        return CutIntroductionKind.PROJECTION_LEMMA
    if "COLLAPSE" in motif_kind:
        return CutIntroductionKind.SOURCE_COLLAPSE_LEMMA
    if "TRANSITIVITY" in motif_kind or "CHAIN" in motif_kind:
        return CutIntroductionKind.TRANSITIVITY_COMPRESSOR
    if "EQUIVALENCE" in motif_kind:
        return CutIntroductionKind.EQUIVALENCE_REPRESENTATIVE
    if "TRIVIAL" in motif_kind:
        return CutIntroductionKind.TRIVIALIZATION_LEMMA
    return CutIntroductionKind.NAMED_INTERMEDIATE_PROPERTY


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)

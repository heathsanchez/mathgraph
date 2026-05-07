"""Proof motif atlas aggregation for TRUE-side rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.lean_artifacts import LeanArtifact
from mathgraph.lemma_candidates import LemmaCandidate, lemma_candidate_from_motif
from mathgraph.proof_motifs import ProofMotif, infer_proof_motif_kind, proof_motif_from_group


@dataclass(frozen=True)
class ProofAtlas:
    atlas_id: str
    domain_kernel_id: str | None = None
    formal_world_id: str | None = None
    proof_motifs: list[ProofMotif] = field(default_factory=list)
    lemma_candidates: list[LemmaCandidate] = field(default_factory=list)
    lean_artifacts: list[LeanArtifact] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)

    def top_motifs(self, n: int = 20) -> list[ProofMotif]:
        return sorted(self.proof_motifs, key=lambda motif: (motif.support_count, motif.unique_claims), reverse=True)[:n]

    def top_lemma_candidates(self, n: int = 20) -> list[LemmaCandidate]:
        return sorted(self.lemma_candidates, key=lambda item: item.expected_covered_claims, reverse=True)[:n]

    def verified_lemmas(self) -> list[LemmaCandidate]:
        return [candidate for candidate in self.lemma_candidates if candidate.is_verified()]

    def advisory_summary(self) -> dict[str, Any]:
        return {
            "proof_motif_count": len(self.proof_motifs),
            "lemma_candidate_count": len(self.lemma_candidates),
            "lean_artifact_count": len(self.lean_artifacts),
            "truth_boundary": "Proof atlas rows shape proof search; Lean/verifiers decide truth.",
        }

    def summary(self) -> dict[str, Any]:
        return {
            "atlas_id": self.atlas_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            **self.advisory_summary(),
            "verified_lemma_count": len(self.verified_lemmas()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "atlas_id": self.atlas_id,
            "domain_kernel_id": self.domain_kernel_id,
            "formal_world_id": self.formal_world_id,
            "proof_motifs": [motif.to_dict() for motif in self.proof_motifs],
            "lemma_candidates": [candidate.to_dict() for candidate in self.lemma_candidates],
            "lean_artifacts": [artifact.to_dict() for artifact in self.lean_artifacts],
            "payload": dict(self.payload),
        }


def build_proof_atlas_from_true_rows(
    rows: list[dict[str, Any]],
    limit: int | None = None,
    *,
    domain_kernel_id: str | None = "etp_magma",
    formal_world_id: str | None = None,
    max_lemma_candidates: int = 50,
) -> ProofAtlas:
    selected = rows[:limit] if limit is not None else list(rows)
    grouped: dict[tuple[str, str | None, str | None, str | None], list[dict[str, Any]]] = {}
    for row in selected:
        motif_kind = row.get("proof_motif") or infer_proof_motif_kind(row)
        route = row.get("proof_route") or row.get("route_name") or row.get("route_signature")
        key = (str(motif_kind), row.get("source_basin"), row.get("target_basin"), route)
        grouped.setdefault(key, []).append(row)
    motifs = [
        proof_motif_from_group(
            group,
            motif_kind=key[0],
            source_basin=key[1],
            target_basin=key[2],
            route_signature=key[3],
            domain_kernel_id=domain_kernel_id,
            formal_world_id=formal_world_id,
        )
        for key, group in grouped.items()
    ]
    motifs = sorted(motifs, key=lambda motif: (motif.support_count, motif.unique_claims), reverse=True)
    candidates = [lemma_candidate_from_motif(motif, index=i) for i, motif in enumerate(motifs[:max_lemma_candidates])]
    atlas_id = content_id(
        "proof_atlas",
        {
            "domain_kernel_id": domain_kernel_id or "",
            "formal_world_id": formal_world_id or "",
            "motif_ids": [motif.proof_motif_id for motif in motifs],
        },
    )
    return ProofAtlas(
        atlas_id=atlas_id,
        domain_kernel_id=domain_kernel_id,
        formal_world_id=formal_world_id,
        proof_motifs=motifs,
        lemma_candidates=candidates,
        payload={"row_count": len(selected), "truth_boundary": "atlas_is_advisory"},
    )

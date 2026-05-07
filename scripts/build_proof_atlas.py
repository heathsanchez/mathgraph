#!/usr/bin/env python
"""Build a proof motif atlas and optional Lean sketches from TRUE-side rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore  # noqa: E402
from mathgraph.lean_artifacts import (  # noqa: E402
    LeanArtifact,
    LeanArtifactKind,
    LeanVerificationStatus,
    make_lean_artifact_id,
    render_lean_skeleton,
)
from mathgraph.proof_atlas import build_proof_atlas_from_true_rows  # noqa: E402
from mathgraph.proof_importers import load_true_proof_rows  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-db")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--emit-lean-sketches", action="store_true")
    parser.add_argument("--max-lemma-candidates", type=int, default=50)
    parser.add_argument("--domain-kernel-id", default="etp_magma")
    parser.add_argument("--formal-world-id")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = load_true_proof_rows(args.input, limit=args.limit)
    atlas = build_proof_atlas_from_true_rows(
        rows,
        domain_kernel_id=args.domain_kernel_id,
        formal_world_id=args.formal_world_id,
        max_lemma_candidates=args.max_lemma_candidates,
    )
    lean_artifacts = []
    if args.emit_lean_sketches:
        sketches_dir = out_dir / "lean_sketches"
        sketches_dir.mkdir(parents=True, exist_ok=True)
        for candidate in atlas.lemma_candidates:
            sketch = render_lean_skeleton(candidate)
            path = sketches_dir / f"{candidate.candidate_name}.lean"
            path.write_text(sketch, encoding="utf-8")
            lean_artifacts.append(
                LeanArtifact(
                    lean_artifact_id=make_lean_artifact_id(
                        candidate.candidate_name, LeanArtifactKind.PROOF_SKETCH.value, candidate.lean_statement
                    ),
                    artifact_kind=LeanArtifactKind.PROOF_SKETCH,
                    name=candidate.candidate_name,
                    domain_kernel_id=candidate.domain_kernel_id,
                    formal_world_id=candidate.formal_world_id,
                    theorem_name=candidate.candidate_name,
                    statement=candidate.lean_statement,
                    proof_text=sketch,
                    imports=["Mathlib"],
                    verification_status=LeanVerificationStatus.GENERATED,
                    trust_level="ADVISORY_ROUTE",
                    provenance_type="GENERATED",
                    source_file=str(path),
                    payload={"lemma_candidate_id": candidate.lemma_candidate_id},
                )
            )
    atlas = type(atlas)(
        atlas_id=atlas.atlas_id,
        domain_kernel_id=atlas.domain_kernel_id,
        formal_world_id=atlas.formal_world_id,
        proof_motifs=atlas.proof_motifs,
        lemma_candidates=atlas.lemma_candidates,
        lean_artifacts=lean_artifacts,
        payload=atlas.payload,
    )

    _write_json(out_dir / "proof_motifs.json", [motif.to_dict() for motif in atlas.proof_motifs])
    _write_json(out_dir / "lemma_candidates.json", [candidate.to_dict() for candidate in atlas.lemma_candidates])
    if lean_artifacts:
        _write_json(out_dir / "lean_artifacts.json", [artifact.to_dict() for artifact in lean_artifacts])
    _write_json(out_dir / "proof_atlas_summary.json", atlas.summary())

    if args.out_db:
        store = LawbookStore(args.out_db)
        try:
            store.init_schema()
            for motif in atlas.proof_motifs:
                store.add_proof_motif(motif)
            for candidate in atlas.lemma_candidates:
                store.add_lemma_candidate(candidate)
            for artifact in lean_artifacts:
                store.add_lean_artifact(artifact)
            store.add_proof_atlas(atlas)
        finally:
            store.close()

    print(json.dumps(atlas.summary(), indent=2, sort_keys=True))
    return 0


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

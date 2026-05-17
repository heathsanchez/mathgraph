#!/usr/bin/env python
"""Build a persistent SQLite LawbookStore from traces or artifact directories."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
import sys
from pathlib import Path

from mathgraph import LawbookStore
from mathgraph.artifact_warehouse import (
    import_v16_6_2_elevated_false_dir,
    import_v16_7_root_atlas_dir,
)
from mathgraph.progress import ProgressLogger
from mathgraph.lean_artifacts import LeanArtifact, LeanArtifactKind, LeanVerificationStatus, make_lean_artifact_id, render_lean_skeleton
from mathgraph.proof_atlas import build_proof_atlas_from_true_rows
from mathgraph.proof_importers import import_true_proof_artifacts_to_store, load_true_proof_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json")
    parser.add_argument("--out")
    parser.add_argument("--out-db")
    parser.add_argument("--v1662-dir")
    parser.add_argument("--v167-dir")
    parser.add_argument("--true-proofs")
    parser.add_argument("--proof-atlas", action="store_true")
    parser.add_argument("--emit-lean-sketches")
    parser.add_argument("--max-lemma-candidates", type=int, default=50)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--heartbeat-sec", type=float, default=10.0)
    parser.add_argument("--progress-jsonl", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    progress = ProgressLogger(
        "build_lawbook_store",
        log_jsonl=args.progress_jsonl,
        heartbeat_sec=args.heartbeat_sec,
        enabled=args.progress,
        quiet=args.quiet,
    )

    db_path = args.out_db or args.out
    if not db_path:
        parser.error("--out-db or --out is required")
    if not args.traces_json and not args.v1662_dir and not args.v167_dir and not args.true_proofs:
        parser.error("provide --traces-json and/or --v1662-dir/--v167-dir/--true-proofs")

    store = LawbookStore(db_path)
    try:
        with progress.stage("init_schema", output=db_path):
            store.init_schema()
        imports: dict[str, object] = {}
        if args.traces_json:
            with progress.stage("import_traces_json", input=args.traces_json, replace=args.replace):
                imports["traces"] = store.import_traces_json(args.traces_json, replace=args.replace).to_dict()
        if args.v1662_dir:
            with progress.stage("import_v16_6_2", input=args.v1662_dir):
                imports["v16_6_2"] = import_v16_6_2_elevated_false_dir(
                    args.v1662_dir, store, limit=args.limit
                )
        if args.v167_dir:
            with progress.stage("import_v16_7", input=args.v167_dir):
                imports["v16_7"] = import_v16_7_root_atlas_dir(args.v167_dir, store, limit=args.limit)
        true_rows = []
        if args.true_proofs:
            with progress.stage("import_true_proofs", input=args.true_proofs):
                imports["true_proofs"] = import_true_proof_artifacts_to_store(store, args.true_proofs, limit=args.limit)
                true_rows = load_true_proof_rows(args.true_proofs, limit=args.limit)
        if args.proof_atlas and true_rows:
            with progress.stage("build_proof_atlas", row_count=len(true_rows)):
                atlas = build_proof_atlas_from_true_rows(
                    true_rows,
                    max_lemma_candidates=args.max_lemma_candidates,
                )
                lean_artifacts = []
                if args.emit_lean_sketches:
                    sketches_dir = Path(args.emit_lean_sketches)
                    sketches_dir.mkdir(parents=True, exist_ok=True)
                    for candidate in atlas.lemma_candidates[: args.max_lemma_candidates]:
                        sketch = render_lean_skeleton(candidate)
                        path = sketches_dir / f"{candidate.candidate_name}.lean"
                        path.write_text(sketch, encoding="utf-8")
                        artifact = LeanArtifact(
                            lean_artifact_id=make_lean_artifact_id(
                                candidate.candidate_name,
                                LeanArtifactKind.PROOF_SKETCH.value,
                                candidate.lean_statement,
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
                            source_file=str(path),
                            payload={"lemma_candidate_id": candidate.lemma_candidate_id},
                        )
                        lean_artifacts.append(artifact)
                        store.add_lean_artifact(artifact)
                for motif in atlas.proof_motifs:
                    store.add_proof_motif(motif)
                for candidate in atlas.lemma_candidates[: args.max_lemma_candidates]:
                    store.add_lemma_candidate(candidate)
                atlas = type(atlas)(
                    atlas_id=atlas.atlas_id,
                    domain_kernel_id=atlas.domain_kernel_id,
                    formal_world_id=atlas.formal_world_id,
                    proof_motifs=atlas.proof_motifs,
                    lemma_candidates=atlas.lemma_candidates[: args.max_lemma_candidates],
                    lean_artifacts=lean_artifacts,
                    payload=atlas.payload,
                )
                store.add_proof_atlas(atlas)
                imports["proof_atlas"] = atlas.summary()
        payload = {"store_path": str(db_path), "imports": imports, "summary": store.summary()}
        if "traces" in imports and isinstance(imports["traces"], dict):
            payload = {**imports["traces"], **payload}
        if not args.summary_json and args.out_db:
            args.summary_json = str(Path(args.out_db).with_suffix(".summary.json"))
        if args.summary_json:
            with progress.stage("write_summary", output=args.summary_json):
                target = Path(args.summary_json)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.quiet:
            print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

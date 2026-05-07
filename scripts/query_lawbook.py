#!/usr/bin/env python
"""Query the v16.8 persistent MathGraph LawbookStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph import LawbookStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--claim", nargs=2, metavar=("SOURCE_IDX", "TARGET_IDX"))
    parser.add_argument("--refutation", nargs=2, metavar=("SOURCE_IDX", "TARGET_IDX"))
    parser.add_argument("--source-idx")
    parser.add_argument("--target-idx")
    parser.add_argument("--top-roots", type=int)
    parser.add_argument("--top-reasons", type=int)
    parser.add_argument("--top-obstructions", type=int)
    parser.add_argument("--root")
    parser.add_argument("--reason")
    parser.add_argument("--obstruction")
    parser.add_argument("--domain-kernels", action="store_true")
    parser.add_argument("--domain-kernel")
    parser.add_argument("--typed-objects", action="store_true")
    parser.add_argument("--predications", nargs="?", const="", default=None, metavar="SUBJECT_ID")
    parser.add_argument("--denotations", action="store_true")
    parser.add_argument("--semantic-embeddings", action="store_true")
    parser.add_argument("--language-fragments", action="store_true")
    parser.add_argument("--formal-worlds", action="store_true")
    parser.add_argument("--paradox-guards", action="store_true")
    parser.add_argument("--theory-objectification-maps", action="store_true")
    parser.add_argument("--theory-denotations", action="store_true")
    parser.add_argument("--theory-readings", action="store_true")
    parser.add_argument("--analytic-truths", action="store_true")
    parser.add_argument("--reason-containment", action="store_true")
    parser.add_argument("--object-language-terms", action="store_true")
    parser.add_argument("--object-language-formulas", action="store_true")
    parser.add_argument("--theory-declarations", action="store_true")
    parser.add_argument("--proof-methods", action="store_true")
    parser.add_argument("--inference-rules", action="store_true")
    parser.add_argument("--isabelle-exports", action="store_true")
    parser.add_argument("--host-object-links", action="store_true")
    parser.add_argument("--logical-workbenches", action="store_true")
    parser.add_argument("--embedding-strategies", action="store_true")
    parser.add_argument("--faithfulness", action="store_true")
    parser.add_argument("--logic-combinations", action="store_true")
    parser.add_argument("--verifier-backends", action="store_true")
    parser.add_argument("--proof-results", action="store_true")
    parser.add_argument("--model-results", action="store_true")
    parser.add_argument("--benchmark-suites", action="store_true")
    parser.add_argument("--benchmark-runs", action="store_true")
    parser.add_argument("--benchmark-results", action="store_true")
    parser.add_argument("--correspondences", action="store_true")
    parser.add_argument("--interpretation-choices", action="store_true")
    parser.add_argument("--proof-motifs", action="store_true")
    parser.add_argument("--lemma-candidates", action="store_true")
    parser.add_argument("--lean-artifacts", action="store_true")
    parser.add_argument("--proof-atlases", action="store_true")
    parser.add_argument("--proof-motif")
    parser.add_argument("--lemma-candidate")
    parser.add_argument("--lean-artifact")
    parser.add_argument("--top-proof-motifs", type=int)
    parser.add_argument("--top-lemma-candidates", type=int)
    parser.add_argument("--verified-lean-artifacts", action="store_true")
    parser.add_argument("--cycle-summary")
    parser.add_argument("--recent-certificates", type=int)
    parser.add_argument("--recent-obstructions", type=int)
    parser.add_argument("--route-yields", action="store_true")
    parser.add_argument("--next-frontier")
    args = parser.parse_args(argv)
    store = LawbookStore(args.db)
    try:
        store.init_schema()
        if args.summary:
            payload = store.summary()
        elif args.claim:
            payload = store.query_claim(args.claim[0], args.claim[1])
        elif args.refutation:
            payload = store.query_refutation(args.refutation[0], args.refutation[1])
        elif args.source_idx is not None and args.target_idx is not None:
            payload = _query_explicit_pair(store, args.source_idx, args.target_idx)
        elif args.top_roots:
            payload = store.top_roots(args.top_roots)
        elif args.top_reasons:
            payload = store.top_reasons(args.top_reasons)
        elif args.top_obstructions:
            payload = store.top_obstructions(args.top_obstructions)
        elif args.root:
            payload = store.explain_root(args.root)
        elif args.reason:
            payload = store.explain_reason(args.reason)
        elif args.obstruction:
            payload = store.explain_obstruction(args.obstruction)
        elif args.domain_kernels:
            payload = store.list_domain_kernels()
        elif args.domain_kernel:
            payload = store.get_domain_kernel(args.domain_kernel)
        elif args.typed_objects:
            payload = store.list_typed_objects()
        elif args.predications is not None:
            payload = store.list_predication_facts(subject_id=args.predications or None)
        elif args.denotations:
            payload = store.list_denotation_records()
        elif args.semantic_embeddings:
            payload = store.list_semantic_embeddings()
        elif args.language_fragments:
            payload = store.list_language_fragments()
        elif args.formal_worlds:
            payload = store.list_formal_worlds()
        elif args.paradox_guards:
            payload = store.list_paradox_guards()
        elif args.theory_objectification_maps:
            payload = store.list_theory_objectification_maps()
        elif args.theory_denotations:
            payload = store.list_theory_denotations()
        elif args.theory_readings:
            payload = store.list_theory_readings()
        elif args.analytic_truths:
            payload = store.list_analytic_truths()
        elif args.reason_containment:
            payload = store.list_reason_containment_records()
        elif args.object_language_terms:
            payload = store.list_object_language_terms()
        elif args.object_language_formulas:
            payload = store.list_object_language_formulas()
        elif args.theory_declarations:
            payload = store.list_theory_declarations()
        elif args.proof_methods:
            payload = store.list_proof_methods()
        elif args.inference_rules:
            payload = store.list_inference_rules()
        elif args.isabelle_exports:
            payload = store.list_isabelle_export_records()
        elif args.host_object_links:
            payload = store.list_host_object_theorem_links()
        elif args.logical_workbenches:
            payload = store.list_logical_workbenches()
        elif args.embedding_strategies:
            payload = store.list_embedding_strategy_profiles()
        elif args.faithfulness:
            payload = store.list_faithfulness_assessments()
        elif args.logic_combinations:
            payload = store.list_logic_combinations()
        elif args.verifier_backends:
            payload = store.list_verifier_backend_profiles()
        elif args.proof_results:
            payload = store.list_proof_finder_results()
        elif args.model_results:
            payload = store.list_model_finder_results()
        elif args.benchmark_suites:
            payload = store.list_benchmark_suites()
        elif args.benchmark_runs:
            payload = store.list_benchmark_runs()
        elif args.benchmark_results:
            payload = store.list_benchmark_results()
        elif args.correspondences:
            payload = store.list_correspondence_claims()
        elif args.interpretation_choices:
            payload = store.list_interpretation_choice_points()
        elif args.proof_motifs:
            payload = store.list_proof_motifs()
        elif args.lemma_candidates:
            payload = store.list_lemma_candidates()
        elif args.lean_artifacts:
            payload = store.list_lean_artifacts()
        elif args.proof_atlases:
            payload = store.list_proof_atlases()
        elif args.proof_motif:
            payload = store.get_proof_motif(args.proof_motif)
        elif args.lemma_candidate:
            payload = store.get_lemma_candidate(args.lemma_candidate)
        elif args.lean_artifact:
            payload = store.get_lean_artifact(args.lean_artifact)
        elif args.top_proof_motifs:
            payload = store.list_proof_motifs(limit=args.top_proof_motifs)
        elif args.top_lemma_candidates:
            payload = store.list_lemma_candidates(limit=args.top_lemma_candidates)
        elif args.verified_lean_artifacts:
            payload = [
                *store.list_lean_artifacts(verification_status="LEAN_VERIFIED"),
                *store.list_lean_artifacts(verification_status="IMPORTED_VERIFIED"),
            ]
        elif args.cycle_summary:
            payload = json.loads(Path(args.cycle_summary).read_text(encoding="utf-8"))
        elif args.recent_certificates:
            primitive = list(store.iter_primitive_traces(limit=args.recent_certificates))
            derived = list(store.iter_derived_certificates(limit=args.recent_certificates))
            payload = {
                "primitive": primitive[-args.recent_certificates :],
                "derived": derived[-args.recent_certificates :],
                "truth_boundary": "Only verified proof and finite countermodel traces are authoritative terminal artifacts.",
            }
        elif args.recent_obstructions:
            payload = {
                "primitive_obstructions": store.find_by_terminal_form(
                    "NAMED_OBSTRUCTION", limit=args.recent_obstructions
                ),
                "truth_boundary": "Named obstructions record residual pressure; they are not proofs or refutations.",
            }
        elif args.route_yields:
            payload = {
                "route_counts": store.stats().route_counts,
                "truth_boundary": "Route yields are advisory search pressure, not truth.",
            }
        elif args.next_frontier:
            payload = _read_jsonl(Path(args.next_frontier))
        else:
            parser.error("provide a query option")
        print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        store.close()
    return 0


def _query_explicit_pair(store: LawbookStore, source_idx: str, target_idx: str) -> dict:
    refutation = store.query_refutation(source_idx, target_idx)
    claim = store.query_claim(source_idx, target_idx)
    refutation_hit = refutation is not None
    claim_hit = claim.get("status") == "hit"
    terminal = None
    trust = None
    provenance = None
    explanation = "No exact claim or refutation found."
    if refutation_hit:
        terminal = refutation.get("terminal_form")
        trust = refutation.get("trust_level")
        provenance = refutation.get("provenance_type")
        explanation = "Exact finite refutation found."
    elif claim_hit:
        terminal = claim.get("terminal_form")
        trust = claim.get("trust_level")
        provenance = claim.get("provenance_type")
        explanation = "Exact claim found."
    return {
        "status": "hit" if (refutation_hit or claim_hit) else "missing",
        "source_idx": str(source_idx),
        "target_idx": str(target_idx),
        "claim_hit": claim_hit,
        "refutation_hit": refutation_hit,
        "terminal_form": terminal or "NAMED_OBSTRUCTION",
        "trust_level": trust,
        "provenance_type": provenance,
        "explanation": explanation,
        "refutation": refutation,
    }


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())

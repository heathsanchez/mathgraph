#!/usr/bin/env python3
"""Run the canonical finite-countermodel trust-boundary demo."""

from __future__ import annotations

import json
from pathlib import Path

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.finite_magma_world import check_finite_countermodel, constant_table
from mathgraph.hashing import sha256_hex
from mathgraph.evidence_replay import replay_evidence_manifest
from mathgraph.invariants import TrustBoundaryEvidence, check_all_core_invariants
from mathgraph.lawbook_acceptance import accept_lawbook_entry, lawbook_entry_from_evidence_manifest, validate_lawbook_acceptance
from mathgraph.lawbook_store import LawbookStore
from mathgraph.semantic_validation import (
    FormalClaim,
    InformalClaim,
    SemanticValidationEvidence,
    TranslationAssumption,
    validate_claim_translation,
)


def run_demo(out_dir: str | Path = "examples/canonical_finite_countermodel_demo/out") -> dict:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    claim_id = "canonical_commutativity_not_left_zero"
    informal = InformalClaim(
        claim_id="informal_commutativity_not_left_zero",
        text="Commutativity does not imply left-zero behavior for all binary operations.",
        source_ref="canonical_demo",
    )
    formal = FormalClaim(
        claim_id=claim_id,
        statement="(x * y) = (y * x) does not imply (x * y) = x",
    )
    source = "(x * y) = (y * x)"
    target = "(x * y) = x"
    table = constant_table(2, 0)
    result = check_finite_countermodel(source, target, table)
    if not result.terminal_candidate_ok:
        raise RuntimeError(result.diagnostic)
    artifact = {
        "claim_id": claim_id,
        "informal_claim": informal.to_dict(),
        "formal_claim": formal.to_dict(),
        "source_equation": source,
        "target_equation": target,
        "countermodel": result.to_dict(),
    }
    artifact_hash = sha256_hex(artifact)
    artifact_path = output / "countermodel_artifact.json"
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    semantic_report = validate_claim_translation(
        informal,
        formal,
        evidence=(
            SemanticValidationEvidence(
                "canonical_statement_match",
                "theorem_statement_match",
                "Informal 'commutativity' maps to x*y=y*x and 'left-zero behavior' maps to x*y=x.",
                reviewer="mathgraph.canonical_demo",
            ),
            SemanticValidationEvidence(
                "canonical_example_alignment",
                "examples_or_test_cases",
                "The constant-zero operation is commutative and violates left-zero at x=1,y=0.",
                reviewer="mathgraph.canonical_demo",
            ),
        ),
        assumptions=(TranslationAssumption("binary_total_operation", "The informal phrase 'binary operations' is interpreted as total finite magma operations."),),
    )
    manifest = EvidenceManifest(
        claim_id=claim_id,
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        evidence_type="finite_magma_countermodel",
        verifier_boundary="finite_model_checker",
        artifact_hashes=(artifact_hash,),
        artifact_paths=("countermodel_artifact.json",),
        claim_data={"source_equation": source, "target_equation": target, "table": [list(row) for row in table]},
        witness=result.witness_env,
        provenance=("canonical_finite_countermodel_demo",),
        informal_claim_id=informal.claim_id,
        formal_claim_id=formal.claim_id,
        semantic_validation_status=semantic_report.status,
        semantic_validation_evidence_refs=semantic_report.evidence_refs,
        translation_assumptions=tuple(a.to_dict() for a in semantic_report.assumptions),
        validation_report_hash=semantic_report.stable_hash(),
        replay_instructions=("python scripts/run_canonical_finite_countermodel_demo.py",),
    )
    evidence = TrustBoundaryEvidence(
        evidence_id="canonical_finite_countermodel_boundary",
        verifier_boundary="finite_model_checker",
        evidence_type="finite_magma_countermodel",
        replayable=True,
        advisory=False,
        artifact_hashes=(artifact_hash,),
        witness_checked=True,
        source_satisfied=result.satisfies_source,
        target_violated=result.violates_target,
        provenance=("canonical_finite_countermodel_demo",),
        trust_level=100,
    )
    manifest_path = output / "evidence_manifest.json"
    manifest_path.write_text(manifest.to_json(), encoding="utf-8")
    replay_result = replay_evidence_manifest(manifest_path, expected_terminal_form=TerminalForm.FINITE_COUNTERMODEL)
    if not replay_result.ok:
        raise RuntimeError(json.dumps(replay_result.to_dict(), indent=2))
    entry = {
        "claim_id": claim_id,
        "status": "ACCEPTED",
        "terminal_form": "FINITE_COUNTERMODEL",
        "advisory": False,
        "provenance": ("canonical_finite_countermodel_demo",),
        "replay_manifest": manifest.to_dict(),
    }
    invariant_report = check_all_core_invariants(entry, evidence, manifest)
    if not invariant_report.ok:
        raise RuntimeError(json.dumps(invariant_report.to_dict(), indent=2))
    candidate_entry = lawbook_entry_from_evidence_manifest(
        manifest,
        evidence=evidence,
        source=source,
        target=target,
        metadata={"advisory_route": "canonical_constant_n2_0", "informal_claim_id": informal.claim_id, "claims_informal_solution": True},
    )
    acceptance_result = validate_lawbook_acceptance(candidate_entry, manifest=manifest, evidence=evidence, manifest_path=str(manifest_path))
    if not acceptance_result.ok:
        raise RuntimeError(json.dumps(acceptance_result.to_dict(), indent=2))
    accepted_entry = accept_lawbook_entry(candidate_entry, manifest=manifest, evidence=evidence, manifest_path=str(manifest_path))
    store = LawbookStore(output / "canonical_lawbook.sqlite")
    store.init_compounding_schema()
    lawbook_artifact = store.insert_artifact(
        {
            "artifact_id": claim_id,
            "domain": "canonical_demo",
            "claim_id": claim_id,
            "source_id": "x_eq_x",
            "target_id": "left_zero",
            "basin": "finite_countermodel_demo",
            "terminal_form": "FINITE_COUNTERMODEL",
            "trust_level": 100,
            "provenance_type": "canonical_demo",
            "boundary_type": "finite_model_checker",
            "payload": {**artifact, "manifest": manifest.to_dict()},
            "artifact_kind": "finite_countermodel_verified",
            "admission_level": "durable_lawbook",
            "durable": True,
            "replay_status": "replayable",
            "provenance_hash": artifact_hash,
        }
    )
    store.close()
    paths = {
        "artifact": artifact_path,
        "manifest": manifest_path,
        "invariants": output / "invariant_report.json",
        "lawbook_entry": output / "lawbook_entry.json",
        "acceptance": output / "lawbook_acceptance.json",
        "replay": output / "replay_summary.json",
        "summary": output / "demo_summary.json",
    }
    paths["invariants"].write_text(json.dumps(invariant_report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    paths["lawbook_entry"].write_text(json.dumps(accepted_entry.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    paths["acceptance"].write_text(json.dumps(acceptance_result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    paths["replay"].write_text(json.dumps(replay_result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "claim_id": claim_id,
        "terminal_form": "FINITE_COUNTERMODEL",
        "informal_claim": informal.to_dict(),
        "formal_claim": formal.to_dict(),
        "semantic_validation_status": semantic_report.status.value,
        "semantic_validation_report_hash": semantic_report.stable_hash(),
        "source_equation": source,
        "target_equation": target,
        "witness": result.witness_env,
        "artifact_hash": artifact_hash,
        "manifest_hash": manifest.stable_hash(),
        "lawbook_artifact_id": lawbook_artifact["artifact_id"],
        "lawbook_entry_id": accepted_entry.entry_id,
        "lawbook_acceptance_ok": acceptance_result.ok,
        "replay_ok": replay_result.ok,
        "advisory_boundary_preserved": True,
        "outputs": {key: str(value) for key, value in paths.items()},
    }
    paths["summary"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="examples/canonical_finite_countermodel_demo/out")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.out_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

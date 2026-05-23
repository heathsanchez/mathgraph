#!/usr/bin/env python3
"""Run a tiny verifier-backed Reason Atlas routing-memory demo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.reason_atlas import (
    ReasonAtlasEvidenceRef,
    build_reason_atlas_entry_from_outcomes,
    check_reason_atlas_no_truth_promotion,
    reason_atlas_report,
    summarize_constructor_family_performance,
    validate_reason_atlas_entry,
)
from scripts.run_canonical_finite_countermodel_demo import run_demo as run_canonical_demo


def run_demo(out_dir: str | Path = "/tmp/mathgraph_reason_atlas_demo") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    canonical_summary = run_canonical_demo(out / "canonical")
    manifest_path = Path(canonical_summary["outputs"]["manifest"])
    manifest = EvidenceManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    outcomes = [
        ReasonAtlasEvidenceRef(
            evidence_id="canonical_finite_countermodel",
            claim_id=manifest.claim_id,
            terminal_form=TerminalForm.FINITE_COUNTERMODEL.value,
            manifest_path=str(manifest_path),
            manifest_hash=manifest.stable_hash(),
            lawbook_entry_id=canonical_summary["lawbook_entry_id"],
            verifier_backed=True,
            advisory_only=False,
            replay_status="replayable",
            semantic_validation_status=manifest.semantic_validation_status.value,
            outcome="success",
        ),
        ReasonAtlasEvidenceRef(
            evidence_id="advisory_route_observation",
            claim_id="advisory-route",
            verifier_backed=False,
            advisory_only=True,
            outcome="observation",
        ),
        ReasonAtlasEvidenceRef(
            evidence_id="rejected_route_observation",
            claim_id="failed-route",
            verifier_backed=False,
            advisory_only=True,
            outcome="rejected",
        ),
    ]
    entry = build_reason_atlas_entry_from_outcomes(
        basin_id="finite_magma_countermodel_basin",
        signature="commutativity_to_left_zero_countermodel",
        basin_name="finite magma countermodel routing",
        constructor_family="constant_table",
        route_priority=0.75,
        outcomes=outcomes,
        heldout_gain=1.0,
        known_limits=("routing_memory_not_truth",),
    )
    validation = validate_reason_atlas_entry(entry)
    report = reason_atlas_report(entry)
    family_summary = summarize_constructor_family_performance([entry])
    truth_attempt = check_reason_atlas_no_truth_promotion({**entry.to_dict(), "terminal_form": "FINITE_COUNTERMODEL", "claims_truth": True})
    summary = {
        "overall": "PASS" if validation.ok and not truth_attempt.ok else "FAIL",
        "entry": entry.to_dict(),
        "validation": validation.to_dict(),
        "family_summary": family_summary,
        "truth_promotion_attempt_rejected": not truth_attempt.ok,
        "canonical_manifest": str(manifest_path),
        "advisory_boundary_preserved": True,
    }
    (out / "reason_atlas_entry.json").write_text(json.dumps(entry.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    (out / "reason_atlas_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (out / "reason_atlas_demo_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_reason_atlas_demo")
    args = parser.parse_args()
    summary = run_demo(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

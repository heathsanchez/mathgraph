import csv
import json

from mathgraph.discovery_candidate_sources import (
    CANONICAL_EVIDENCE_PACKS,
    candidates_from_lean_digest_dir,
    collect_discovery_candidates_from_sources,
    split_valid_candidates,
)
from mathgraph.discovery_scheduler import DiscoveryCandidate, validate_candidate
from mathgraph.lean_project_digest import run_lean_project_digest
from scripts.run_discovery_scheduler_from_evidence import run_from_evidence
from scripts.run_repo_architecture_audit import ROOT, run_audit


EXPECTED_OUTPUTS = {
    "evidence_candidate_inventory.csv",
    "valid_candidates.csv",
    "rejected_candidates.csv",
    "taste_policy_ledger.csv",
    "attention_allocation.csv",
    "discovery_from_evidence_summary.json",
    "discovery_from_evidence_report.md",
}


def test_evidence_root_run_creates_outputs(tmp_path) -> None:
    out_dir = tmp_path / "run"
    summary = run_from_evidence(
        evidence_root=ROOT / "examples" / "evidence_packs",
        out_dir=out_dir,
        mode="balanced",
        top_k=5,
        beta=1.0,
    )
    assert EXPECTED_OUTPUTS <= {path.name for path in out_dir.iterdir()}
    assert summary["candidate_count"] >= len(CANONICAL_EVIDENCE_PACKS)
    assert summary["valid_count"] >= len(CANONICAL_EVIDENCE_PACKS)
    assert summary["advisory_boundary_ok"] is True


def test_canonical_evidence_packs_generate_one_candidate_each() -> None:
    result = collect_discovery_candidates_from_sources(evidence_root=ROOT / "examples" / "evidence_packs")
    valid, rejected = split_valid_candidates(result.candidates)
    assert not rejected
    refs = {candidate.source_ref for candidate in valid}
    assert set(CANONICAL_EVIDENCE_PACKS) <= refs
    assert all(candidate.advisory_only and not candidate.can_promote_truth for candidate in valid)


def test_crossworld_and_collatz_boundary_notes_preserved() -> None:
    result = collect_discovery_candidates_from_sources(evidence_root=ROOT / "examples" / "evidence_packs")
    by_id = {candidate.candidate_id: candidate for candidate in result.candidates}
    crossworld = by_id["crossworld_projection_test_candidate"]
    collatz = by_id["collatz_obstruction_naming_candidate"]
    assert "not a formal theorem" in crossworld.notes
    assert "not a truth oracle" in crossworld.notes
    assert "not_a_proof" in collatz.notes
    assert collatz.expected_certificate_value < collatz.expected_obstruction_value


def test_lean_digest_fixture_generates_sorry_axiom_unsafe_candidates(tmp_path) -> None:
    digest_dir = tmp_path / "lean_digest"
    run_lean_project_digest(digest_dir, fallback_demo=True)
    candidates = candidates_from_lean_digest_dir(digest_dir)
    types = {candidate.candidate_type for candidate in candidates}
    assert "lean_sorry_repair_candidate" in types
    assert "lean_axiom_boundary_candidate" in types
    assert "lean_unsafe_audit_candidate" in types
    assert all(candidate.advisory_only and not candidate.can_promote_truth for candidate in candidates)
    assert any("cannot become VERIFIED_PROOF" in candidate.notes for candidate in candidates)


def test_invalid_no_descension_candidate_is_rejected() -> None:
    candidate = DiscoveryCandidate(
        candidate_id="missing_descension",
        candidate_type="demo",
        source="test",
        source_kind="unit",
        source_ref="unit",
        advisory_only=True,
        can_promote_truth=False,
    )
    ok, violations = validate_candidate(candidate)
    assert ok is False
    assert "invalid_or_missing_descension_target" in violations


def test_rejected_candidates_are_not_allocated_attention(tmp_path) -> None:
    summary = run_from_evidence(
        evidence_root=ROOT / "examples" / "evidence_packs",
        out_dir=tmp_path / "run",
        mode="frontier",
        top_k=4,
    )
    allocation = list(csv.DictReader(open(tmp_path / "run" / "attention_allocation.csv", encoding="utf-8")))
    rejected = list(csv.DictReader(open(tmp_path / "run" / "rejected_candidates.csv", encoding="utf-8")))
    allocated_ids = {row["candidate_id"] for row in allocation}
    rejected_ids = {row["candidate_id"] for row in rejected if row.get("candidate_id")}
    assert not (allocated_ids & rejected_ids)
    assert abs(sum(float(row["attention_probability"]) for row in allocation) - 1.0) < 1e-9
    assert summary["advisory_boundary_ok"] is True


def test_malformed_source_records_warning_without_crashing(tmp_path) -> None:
    root = tmp_path / "evidence"
    (root / "sair_stage2_breakthrough_20260526").mkdir(parents=True)
    (root / "sair_stage2_breakthrough_20260526" / "metrics.json").write_text("{bad json", encoding="utf-8")
    result = collect_discovery_candidates_from_sources(evidence_root=root)
    assert result.warnings
    assert result.rejected_rows


def test_architecture_audit_recognizes_candidate_sources() -> None:
    report = run_audit(ROOT)
    assert report["canonical_module_presence"]["mathgraph/discovery_candidate_sources.py"] is True
    assert report["canonical_script_presence"]["scripts/run_discovery_scheduler_from_evidence.py"] is True
    assert report["canonical_doc_presence"]["docs/discovery_candidate_sources.md"] is True
    assert report["status"] == "PASS"


def test_cli_summary_json_preserves_trust_boundary(tmp_path) -> None:
    run_from_evidence(evidence_root=ROOT / "examples" / "evidence_packs", out_dir=tmp_path / "run")
    summary = json.loads((tmp_path / "run" / "discovery_from_evidence_summary.json").read_text(encoding="utf-8"))
    assert summary["can_promote_truth_count"] == 0
    assert summary["advisory_boundary_ok"] is True

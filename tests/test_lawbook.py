import json
import subprocess
import sys
from pathlib import Path

import pytest

from mathgraph import CertificateLawbook, JsonlLedger, Kernel, TerminalForm, VerificationStatus
from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase
from mathgraph.discovery_value import DiscoveryValueDecision, DiscoveryValueObjectKind, DiscoveryValueScore
from mathgraph.lawbook import (
    LawbookAcceptanceBoundary,
    LawbookEntry,
    LawbookEntryKind,
    LawbookEntryStatus,
    LawbookReview,
    LawbookReviewDecision,
    LawbookStore as AcceptedLawbookStore,
    accept_lawbook_entry,
    audit_lawbook_entry,
    audit_lawbook_store,
    build_lawbook_store,
    lawbook_entry_from_assimilation_candidate,
    lawbook_entry_from_certificate_like,
    lawbook_entry_from_discovery_value_score,
    lawbook_entry_from_projection_candidate,
    lawbook_entry_from_proof_digestion,
    lawbook_store_to_agent_experiences,
    lawbook_store_to_alchemical_trace,
    lawbook_store_to_continuation_outputs,
    lawbook_store_to_projection_candidates,
    review_lawbook_candidate,
)
from mathgraph.proof_digestion import LawbookAssimilationCandidate, digest_proof_artifact, proof_artifact_from_content
from mathgraph.projection import ProjectionCandidate
from mathgraph.roadmap_alignment import check_roadmap_alignment


ROOT = Path(__file__).resolve().parents[1]


def _traces():
    proof = Kernel().prove("x = x", "x = x")
    proof.metadata.update(
        {
            "source_idx": "1",
            "target_idx": "2",
            "source_equation": "x = x",
            "target_equation": "x = x",
            "compiled_route": "variable_identification",
            "claim_hash": "claim-proof",
            "lean_status": "lean_verified_true",
            "promotion_status": "lean_verified_true_promotable",
        }
    )
    proof.certificate.payload.update({"proof": {"route": "variable_identification"}})

    counter = Kernel().prove("x = x", "x * x = x")
    counter.metadata.update(
        {
            "source_idx": "1",
            "target_idx": "3",
            "source_equation": "x = x",
            "target_equation": "x * x = x",
            "compiled_route": "finite_countermodel",
            "claim_hash": "claim-counter",
        }
    )
    counter.certificate.payload["model"]["countermodel"] = {"table": [[0, 1], [1, 0]]}

    obstruction = Kernel(finite_magmas=[]).prove("x * y = x", "x * y = y")
    obstruction.metadata.update(
        {
            "source_idx": "4",
            "target_idx": "5",
            "compiled_route": "unknown_route",
            "claim_hash": "claim-obstruction",
        }
    )
    return [proof, counter, obstruction]


def test_lawbook_from_trace_list_summary_counts() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    summary = lawbook.summary()

    assert summary["trace_count"] == 3
    assert summary["terminal_form_counts"]["VERIFIED_PROOF"] == 1
    assert summary["terminal_form_counts"]["FINITE_COUNTERMODEL"] == 1
    assert summary["terminal_form_counts"]["NAMED_OBSTRUCTION"] == 1
    assert summary["verification_status_counts"]["VERIFIED"] == 1
    assert summary["route_counts"]["finite_countermodel"] == 1
    assert summary["source_count"] == 2
    assert summary["target_count"] == 3
    assert summary["pair_count"] == 3
    assert summary["promotable_count"] == 2
    assert summary["obstruction_count"] == 1


def test_lawbook_route_and_endpoint_summaries() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    routes = lawbook.route_summary()
    source = lawbook.source_summary("1")
    target = lawbook.target_summary("3")

    assert routes["variable_identification"]["count"] == 1
    assert routes["finite_countermodel"]["terminal_form_counts"]["FINITE_COUNTERMODEL"] == 1
    assert source["trace_count"] == 2
    assert source["target_indices"] == ["2", "3"]
    assert target["trace_count"] == 1
    assert target["source_indices"] == ["1"]


def test_lawbook_lookup_and_query() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())

    assert lawbook.get_by_claim("claim-proof").terminal_form == TerminalForm.VERIFIED_PROOF
    assert lawbook.get_by_pair(1, 3).terminal_form == TerminalForm.FINITE_COUNTERMODEL
    assert lawbook.query(terminal_form="FINITE_COUNTERMODEL")[0].verification_status == VerificationStatus.REFUTED
    assert lawbook.query(route="variable_identification")[0].claim == "x = x => x = x"
    assert len(lawbook.query(limit=2)) == 2
    assert lawbook.find_by_source(1, limit=1)[0].metadata["source_idx"] == "1"
    assert lawbook.find_by_target(3)[0].metadata["target_idx"] == "3"
    assert lawbook.find_by_route("finite_countermodel")[0].terminal_form == TerminalForm.FINITE_COUNTERMODEL


def test_lawbook_extraction_helpers() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    counter = lawbook.countermodels()[0]
    proof = lawbook.verified_proofs()[0]

    assert lawbook.extract_countermodel(counter) == {"table": [[0, 1], [1, 0]]}
    assert lawbook.extract_proof_payload(proof) == {"route": "variable_identification"}
    assert lawbook.obstructions()[0].terminal_form == TerminalForm.NAMED_OBSTRUCTION


def test_lawbook_missing_fields_do_not_crash() -> None:
    trace = Kernel().prove("x = x")
    lawbook = CertificateLawbook([trace.to_dict()])

    assert lawbook.summary()["trace_count"] == 1
    assert lawbook.source_summary("missing")["trace_count"] == 0
    assert lawbook.explain_trace(trace)["source_idx"] is None


def test_lawbook_explain_trace_and_claim_pair() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    explanation = lawbook.explain_pair("1", "3")

    assert explanation["terminal_form"] == "FINITE_COUNTERMODEL"
    assert explanation["route"] == "finite_countermodel"
    assert explanation["has_certificate"] is True
    assert explanation["has_countermodel"] is True
    assert explanation["proof_countermodel_obstruction_kind"] == "countermodel"
    assert lawbook.explain_claim("claim-counter")["target_idx"] == "3"


def test_lawbook_top_level_import_and_missing_pair_response() -> None:
    from mathgraph import CertificateLawbook as ImportedLawbook

    lawbook = ImportedLawbook.from_traces(_traces())
    explanation = lawbook.explain_pair("missing", "pair")

    assert explanation["terminal_form"] == "NAMED_OBSTRUCTION"
    assert explanation["verification_status"] == "OBSTRUCTED"
    assert explanation["proof_countermodel_obstruction_kind"] == "not_in_lawbook"
    assert explanation["has_certificate"] is False


def test_lawbook_route_cards_and_filters() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    card = lawbook.route_card("finite_countermodel")
    cards = lawbook.all_route_cards()

    assert card["route"] == "finite_countermodel"
    assert card["count"] == 1
    assert card["source_count"] == 1
    assert card["target_count"] == 1
    assert card["sample_pairs"] == [{"source_idx": "1", "target_idx": "3"}]
    assert "variable_identification" in cards
    assert len(lawbook.countermodels()) == 1
    assert len(lawbook.verified_proofs()) == 1
    assert len(lawbook.obstructions()) == 1


def test_lawbook_explain_trace_omits_full_payload() -> None:
    lawbook = CertificateLawbook.from_traces(_traces())
    explanation = lawbook.explain_trace("claim-counter")

    assert "certificate_payload" not in explanation
    assert "model" in explanation["certificate_payload_keys"]
    assert explanation["artifact_counts"] == {"total": 0, "json": 0, "lean": 0}


def test_lawbook_save_summary(tmp_path: Path) -> None:
    path = tmp_path / "summary.json"
    route_path = tmp_path / "routes.json"
    lawbook = CertificateLawbook.from_traces(_traces())

    lawbook.save_summary(path)
    lawbook.save_route_summary(route_path)

    assert json.loads(path.read_text(encoding="utf-8"))["summary"]["trace_count"] == 3
    assert "finite_countermodel" in json.loads(route_path.read_text(encoding="utf-8"))


def test_lawbook_cli_traces_json(tmp_path: Path) -> None:
    traces_path = tmp_path / "traces.json"
    out_path = tmp_path / "lawbook_summary.json"
    traces_path.write_text(
        json.dumps([trace.to_dict() for trace in _traces()]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_summary.py"),
            "--traces-json",
            str(traces_path),
            "--out",
            str(out_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert '"trace_count": 3' in result.stdout
    assert out_path.exists()


def test_lawbook_cli_traces_jsonl(tmp_path: Path) -> None:
    ledger_path = tmp_path / "traces.jsonl"
    route_path = tmp_path / "route_summary.json"
    ledger = JsonlLedger(ledger_path)
    for trace in _traces():
        ledger.append_trace(trace)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_lawbook_summary.py"),
            "--traces-jsonl",
            str(ledger_path),
            "--route-summary",
            str(route_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert route_path.exists()
    assert "variable_identification" in json.loads(route_path.read_text(encoding="utf-8"))


def _valid_proof_entry() -> LawbookEntry:
    return lawbook_entry_from_certificate_like(
        claim_id="claim-proof",
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id="cert-proof",
        verifier_boundary_crossed=True,
        provenance={"verifier": "lean"},
    )


def test_accepted_lawbook_entry_review_store_serialization() -> None:
    entry = _valid_proof_entry()
    review = review_lawbook_candidate(entry, reviewer="alice")
    store = build_lawbook_store(entries=[entry], reviews=[review])

    assert LawbookEntry.from_json(entry.to_json()).entry_id == entry.entry_id
    assert LawbookReview.from_json(review.to_json()).decision == LawbookReviewDecision.ACCEPT
    assert AcceptedLawbookStore.from_json(store.to_json()).entry_count() == 1


def test_empty_accepted_lawbook_store_is_valid() -> None:
    store = build_lawbook_store()
    assert store.entry_count() == 0
    assert store.summary["entry_total"] == 0


def test_truth_candidates_require_valid_boundary_before_acceptance() -> None:
    valid = _valid_proof_entry()
    invalid = lawbook_entry_from_certificate_like(terminal_form=TerminalForm.VERIFIED_PROOF)
    counter = lawbook_entry_from_certificate_like(
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="cert-false",
        verifier_boundary_crossed=True,
        provenance={"validator": "finite"},
    )
    assert valid.status == LawbookEntryStatus.CANDIDATE
    assert review_lawbook_candidate(valid).decision == LawbookReviewDecision.ACCEPT
    assert review_lawbook_candidate(invalid).decision == LawbookReviewDecision.NEEDS_VERIFIER
    assert accept_lawbook_entry(valid, review_lawbook_candidate(valid)).is_accepted()
    assert accept_lawbook_entry(counter, review_lawbook_candidate(counter)).is_accepted()
    with pytest.raises(ValueError):
        accept_lawbook_entry(invalid, LawbookReview("r", invalid.entry_id, LawbookReviewDecision.ACCEPT))


def test_named_obstruction_requires_evidence() -> None:
    entry = lawbook_entry_from_certificate_like(terminal_form=TerminalForm.NAMED_OBSTRUCTION)
    entry.acceptance_boundary = LawbookAcceptanceBoundary.NAMED_OBSTRUCTION
    assert review_lawbook_candidate(entry).decision == LawbookReviewDecision.NEEDS_MORE_EVIDENCE
    entry.metadata["obstruction"] = "named"
    assert review_lawbook_candidate(entry).decision == LawbookReviewDecision.ACCEPT


def test_candidate_converters_preserve_non_truth_boundary() -> None:
    digest = digest_proof_artifact(proof_artifact_from_content("theorem t : True := by trivial"))
    digestion_entry = lawbook_entry_from_proof_digestion(digest)
    assimilation_entry = lawbook_entry_from_assimilation_candidate(
        LawbookAssimilationCandidate("assim-1", digest.trace_id)
    )
    projection_entry = lawbook_entry_from_projection_candidate(
        ProjectionCandidate("proj-1", None, None, source="a", target="b")
    )
    score_entry = lawbook_entry_from_discovery_value_score(
        DiscoveryValueScore("score-1", "obj", DiscoveryValueObjectKind.RAW_TASK, decision=DiscoveryValueDecision.QUEUE_SOON)
    )
    assert digestion_entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY
    assert not digestion_entry.is_truth_entry()
    assert assimilation_entry.status == LawbookEntryStatus.CANDIDATE
    assert projection_entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY
    assert projection_entry.terminal_form is None
    assert score_entry.metadata["value_score_not_truth"] is True


def test_digested_proof_needs_certificate_link() -> None:
    digest = digest_proof_artifact(proof_artifact_from_content("theorem t : True := by trivial"))
    entry = lawbook_entry_from_proof_digestion(digest)
    assert review_lawbook_candidate(entry).decision == LawbookReviewDecision.NEEDS_VERIFIER
    linked = lawbook_entry_from_proof_digestion(digest, existing_certificate_id="cert")
    assert review_lawbook_candidate(linked).decision == LawbookReviewDecision.ACCEPT


def test_audit_catches_boundary_drift() -> None:
    bad = lawbook_entry_from_certificate_like(terminal_form=TerminalForm.VERIFIED_PROOF, certificate_id="cert")
    bad.status = LawbookEntryStatus.ACCEPTED
    projection = LawbookEntry(
        "projection-bad",
        LawbookEntryKind.PROJECTION_RULE_ENTRY,
        metadata={"projection_is_certificate": True},
    )
    assert any(item["code"] == "ACCEPTED_TRUTH_WITHOUT_BOUNDARY" for item in audit_lawbook_entry(bad))
    assert any(item["code"] == "PROJECTION_AS_CERTIFICATE" for item in audit_lawbook_entry(projection))
    assert audit_lawbook_store(build_lawbook_store(entries=[bad]))


def test_build_store_auto_review_and_auto_accept() -> None:
    store = build_lawbook_store(entries=[_valid_proof_entry()], auto_review=True, auto_accept=True, reviewer="alice")
    assert store.reviews
    assert store.accepted_entries()


def test_lawbook_bridges_preserve_boundary() -> None:
    accepted = accept_lawbook_entry(_valid_proof_entry(), review_lawbook_candidate(_valid_proof_entry()))
    projection = lawbook_entry_from_projection_candidate(ProjectionCandidate("proj-2", None, None, source="a", target="b", metadata={"conditions": ["known"]}))
    projection = accept_lawbook_entry(projection, review_lawbook_candidate(projection))
    candidate = lawbook_entry_from_discovery_value_score(DiscoveryValueScore("score-2", "obj", DiscoveryValueObjectKind.RAW_TASK))
    store = build_lawbook_store(entries=[accepted, projection, candidate])

    assert lawbook_store_to_projection_candidates(store)
    assert all(not output.is_terminal() for output in lawbook_store_to_continuation_outputs(store))
    assert lawbook_store_to_alchemical_trace(store).has_phase(AlchemicalPhase.FIXATION)
    experiences = lawbook_store_to_agent_experiences(store)
    assert any(item.outcome == AgentExperienceOutcome.VERIFIED_PROOF for item in experiences)
    assert any(item.outcome == AgentExperienceOutcome.ADVISORY_ONLY for item in experiences)


def test_roadmap_alignment_catches_lawbook_drift() -> None:
    bad = lawbook_entry_from_certificate_like(terminal_form=TerminalForm.VERIFIED_PROOF, certificate_id="cert")
    bad.status = LawbookEntryStatus.ACCEPTED
    bad.metadata["value_score_as_truth"] = True
    bad.metadata["digestion_creates_proof"] = True
    report = check_roadmap_alignment(lawbook_entries=[bad])
    codes = {finding.code for finding in report.findings}
    assert "LAWBOOK_ACCEPTED_TRUTH_WITHOUT_BOUNDARY" in codes
    assert "LAWBOOK_VALUE_AS_TRUTH" in codes
    assert "LAWBOOK_DIGESTION_AS_PROOF" in codes


def test_run_lawbook_cli_empty_and_certificate_like(tmp_path: Path) -> None:
    out_store = tmp_path / "store.json"
    cert = tmp_path / "cert.json"
    cert.write_text(
        json.dumps(
            {
                "claim_id": "claim",
                "terminal_form": "VERIFIED_PROOF",
                "certificate_id": "cert",
                "verifier_boundary_crossed": True,
                "provenance": {"verifier": "lean"},
            }
        ),
        encoding="utf-8",
    )
    empty = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_lawbook.py")], capture_output=True, text=True)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_lawbook.py"),
            "--certificate-like-json",
            str(cert),
            "--auto-review",
            "--auto-accept",
            "--out-store-json",
            str(out_store),
        ],
        capture_output=True,
        text=True,
    )
    assert empty.returncode == 0
    assert result.returncode == 0, result.stderr
    assert json.loads(out_store.read_text(encoding="utf-8"))["summary"]["accepted_count"] == 1

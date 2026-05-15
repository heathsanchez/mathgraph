import json
import subprocess
import sys
from pathlib import Path

from mathgraph.agent_biography import AgentExperienceOutcome
from mathgraph.alchemy import AlchemicalPhase
from mathgraph.certificates import TerminalForm
from mathgraph.lawbook import (
    LawbookAcceptanceBoundary,
    LawbookEntry,
    LawbookEntryKind,
    LawbookEntryStatus,
    LawbookStore,
    accept_lawbook_entry,
    lawbook_entry_from_certificate_like,
    lawbook_entry_from_projection_candidate,
    review_lawbook_candidate,
)
from mathgraph.lawbook_query import (
    KnownSkipDecision,
    LawbookQuery,
    LawbookQueryAnswer,
    LawbookQueryKind,
    LawbookQueryReport,
    LawbookQueryStatus,
    LawbookTrustLevel,
    build_lawbook_trust_summary,
    explain_lawbook_answer,
    lawbook_query_answer_to_continuation_outputs,
    lawbook_query_answer_to_projection_candidates,
    lawbook_query_report_to_agent_experiences,
    lawbook_query_report_to_alchemical_trace,
    lawbook_query_report_to_route_telemetry_events,
    make_certificate_query,
    make_claim_query,
    make_entry_query,
    make_known_skip_query,
    query_lawbook_store,
    query_lawbook_store_many,
)
from mathgraph.projection import ProjectionCandidate
from mathgraph.roadmap_alignment import check_roadmap_alignment

ROOT = Path(__file__).resolve().parents[1]


def _accepted_proof() -> LawbookEntry:
    candidate = lawbook_entry_from_certificate_like(
        claim_id="claim",
        source="x=x",
        target="x=x",
        raw="proof raw",
        terminal_form=TerminalForm.VERIFIED_PROOF,
        certificate_id="cert-proof",
        verifier_boundary_crossed=True,
        provenance={"verifier": "lean"},
    )
    return accept_lawbook_entry(candidate, review_lawbook_candidate(candidate))


def _accepted_counter() -> LawbookEntry:
    candidate = lawbook_entry_from_certificate_like(
        claim_id="false-claim",
        terminal_form=TerminalForm.FINITE_COUNTERMODEL,
        certificate_id="cert-false",
        verifier_boundary_crossed=True,
        provenance={"validator": "finite"},
    )
    return accept_lawbook_entry(candidate, review_lawbook_candidate(candidate))


def _accepted_obstruction() -> LawbookEntry:
    entry = lawbook_entry_from_certificate_like(claim_id="blocked", terminal_form=TerminalForm.NAMED_OBSTRUCTION)
    entry.acceptance_boundary = LawbookAcceptanceBoundary.NAMED_OBSTRUCTION
    entry.metadata["obstruction"] = "named"
    return accept_lawbook_entry(entry, review_lawbook_candidate(entry))


def test_query_records_roundtrip() -> None:
    query = make_claim_query(claim_id="claim")
    answer = LawbookQueryAnswer("a", query.query_id, LawbookQueryStatus.NOT_FOUND, LawbookTrustLevel.NONE)
    report = LawbookQueryReport("r", [query], [answer])
    assert LawbookQuery.from_json(query.to_json()).claim_id == "claim"
    assert LawbookQueryAnswer.from_json(answer.to_json()).status == LawbookQueryStatus.NOT_FOUND
    assert LawbookQueryReport.from_json(report.to_json()).answer_count() == 1


def test_empty_and_invalid_queries() -> None:
    store = LawbookStore("empty")
    assert query_lawbook_store_many(store, []).answer_count() == 0
    answer = query_lawbook_store(store, LawbookQuery("q", LawbookQueryKind.CLAIM))
    assert answer.status == LawbookQueryStatus.INVALID_QUERY


def test_accepted_truth_obstruction_and_skip_classification() -> None:
    store = LawbookStore("s", [_accepted_proof(), _accepted_counter(), _accepted_obstruction()])
    proof = query_lawbook_store(store, make_claim_query(claim_id="claim"))
    counter = query_lawbook_store(store, make_claim_query(claim_id="false-claim"))
    obstruction = query_lawbook_store(store, make_claim_query(claim_id="blocked"))
    assert proof.status == LawbookQueryStatus.FOUND_ACCEPTED_TRUTH
    assert proof.trust_level == LawbookTrustLevel.VERIFIED_TRUTH
    assert proof.known_skip_decision == KnownSkipDecision.SKIP_VERIFIED_PROOF
    assert counter.trust_level == LawbookTrustLevel.FINITE_REFUTATION
    assert counter.known_skip_decision == KnownSkipDecision.SKIP_FINITE_COUNTERMODEL
    assert obstruction.status == LawbookQueryStatus.FOUND_ACCEPTED_OBSTRUCTION
    assert obstruction.known_skip_decision == KnownSkipDecision.SKIP_ACCEPTED_OBSTRUCTION


def test_candidate_digest_projection_and_not_found_refuse_skip() -> None:
    candidate = lawbook_entry_from_certificate_like(claim_id="candidate", terminal_form=TerminalForm.VERIFIED_PROOF)
    digest = LawbookEntry("digest", LawbookEntryKind.DIGESTED_PROOF_ENTRY, LawbookEntryStatus.ACCEPTED, claim_id="digest", certificate_id="cert", digestion_trace_ids=("d",), metadata={"digestion_not_verification": True})
    projection = lawbook_entry_from_projection_candidate(ProjectionCandidate("p", "proj", "proj", source="a", target="b", metadata={"conditions": ["c"]}))
    projection = accept_lawbook_entry(projection, review_lawbook_candidate(projection))
    store = LawbookStore("s", [candidate, digest, projection])
    candidate_answer = query_lawbook_store(store, make_known_skip_query(claim_id="candidate"))
    digest_answer = query_lawbook_store(store, make_known_skip_query(claim_id="digest"))
    projection_answer = query_lawbook_store(store, make_known_skip_query(claim_id="proj"))
    missing = query_lawbook_store(store, make_known_skip_query(claim_id="missing"))
    assert candidate_answer.known_skip_decision == KnownSkipDecision.DO_NOT_SKIP_CANDIDATE_ONLY
    assert digest_answer.status == LawbookQueryStatus.FOUND_DIGESTION_ONLY
    assert digest_answer.known_skip_decision == KnownSkipDecision.DO_NOT_SKIP_ADVISORY_ONLY
    assert projection_answer.trust_level == LawbookTrustLevel.ADVISORY_PROJECTION
    assert projection_answer.known_skip_decision == KnownSkipDecision.DO_NOT_SKIP_ADVISORY_ONLY
    assert missing.known_skip_decision == KnownSkipDecision.DO_NOT_SKIP_NOT_FOUND


def test_conflict_certificate_entry_pair_raw_and_summary() -> None:
    proof = _accepted_proof()
    counter = _accepted_counter()
    counter.claim_id = "claim"
    store = LawbookStore("s", [proof, counter])
    ambiguous = query_lawbook_store(store, make_known_skip_query(claim_id="claim"))
    assert ambiguous.status == LawbookQueryStatus.AMBIGUOUS
    assert ambiguous.known_skip_decision == KnownSkipDecision.DO_NOT_SKIP_AMBIGUOUS
    assert query_lawbook_store(LawbookStore("p", [proof]), make_certificate_query("cert-proof")).matched_entry_ids
    assert query_lawbook_store(LawbookStore("p", [proof]), make_entry_query(proof.entry_id)).matched_entry_ids
    assert query_lawbook_store(LawbookStore("p", [proof]), make_claim_query(source="x=x", target="x=x")).matched_entry_ids
    assert query_lawbook_store(LawbookStore("p", [proof]), make_claim_query(raw="proof raw")).matched_entry_ids
    assert build_lawbook_trust_summary(LawbookStore("p", [proof]))["accepted_proof_count"] == 1


def test_explanations_and_bridges() -> None:
    proof = query_lawbook_store(LawbookStore("p", [_accepted_proof()]), make_claim_query(claim_id="claim"))
    candidate = query_lawbook_store(LawbookStore("c", [lawbook_entry_from_certificate_like(claim_id="c")]), make_claim_query(claim_id="c"))
    projection_entry = lawbook_entry_from_projection_candidate(ProjectionCandidate("p", "proj", "proj", metadata={"conditions": ["c"]}))
    projection_entry = accept_lawbook_entry(projection_entry, review_lawbook_candidate(projection_entry))
    projection = query_lawbook_store(LawbookStore("proj", [projection_entry]), make_claim_query(claim_id="proj"))
    assert "verifier boundary" in explain_lawbook_answer(proof)
    assert "candidate only" in explain_lawbook_answer(candidate)
    assert "not a certificate" in explain_lawbook_answer(projection)
    assert lawbook_query_answer_to_projection_candidates(proof)
    assert not lawbook_query_answer_to_projection_candidates(candidate)
    conflicting = LawbookQueryAnswer("a", "q", LawbookQueryStatus.AMBIGUOUS, LawbookTrustLevel.UNKNOWN, KnownSkipDecision.DO_NOT_SKIP_AMBIGUOUS)
    assert lawbook_query_answer_to_continuation_outputs(conflicting)[0].task_payload["task"] == "audit_conflict"
    report = query_lawbook_store_many(LawbookStore("p", [_accepted_proof()]), [make_claim_query(claim_id="claim")])
    assert lawbook_query_report_to_alchemical_trace(report).has_phase(AlchemicalPhase.FIXATION)
    advisory_report = query_lawbook_store_many(LawbookStore("c", [lawbook_entry_from_certificate_like(claim_id="c")]), [make_claim_query(claim_id="c")])
    assert all(exp.outcome == AgentExperienceOutcome.ADVISORY_ONLY for exp in lawbook_query_report_to_agent_experiences(advisory_report))
    assert isinstance(lawbook_query_report_to_route_telemetry_events(report)[0], dict)


def test_alignment_catches_query_drift() -> None:
    bad = LawbookQueryAnswer("a", "q", LawbookQueryStatus.FOUND_ACCEPTED_TRUTH, LawbookTrustLevel.VERIFIED_TRUTH, terminal_form=TerminalForm.VERIFIED_PROOF)
    candidate_skip = LawbookQueryAnswer("b", "q", LawbookQueryStatus.FOUND_CANDIDATE_ONLY, LawbookTrustLevel.CANDIDATE_MEMORY, KnownSkipDecision.SKIP_VERIFIED_PROOF)
    ambiguous_skip = LawbookQueryAnswer("c", "q", LawbookQueryStatus.AMBIGUOUS, LawbookTrustLevel.UNKNOWN, KnownSkipDecision.SKIP_VERIFIED_PROOF)
    codes = {finding.code for finding in check_roadmap_alignment(lawbook_query_answers=[bad, candidate_skip, ambiguous_skip]).findings}
    assert "LAWBOOK_QUERY_TERMINAL_WITHOUT_CERTIFICATE" in codes
    assert "LAWBOOK_QUERY_TERMINAL_WITHOUT_BOUNDARY" in codes
    assert "LAWBOOK_CANDIDATE_SKIP_DRIFT" in codes
    assert "LAWBOOK_AMBIGUOUS_SKIP_DRIFT" in codes


def test_cli_empty_and_query_modes(tmp_path: Path) -> None:
    store = LawbookStore("s", [_accepted_proof()])
    store_path = tmp_path / "store.json"
    report_path = tmp_path / "report.json"
    answers_path = tmp_path / "answers.jsonl"
    projections_path = tmp_path / "projections.jsonl"
    store.write_json(store_path)
    empty = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_lawbook_query.py")], capture_output=True, text=True)
    result = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts" / "run_lawbook_query.py"),
            "--store-json", str(store_path), "--claim-id", "claim",
            "--out-report-json", str(report_path), "--out-answers-jsonl", str(answers_path),
            "--out-projection-candidates-jsonl", str(projections_path),
        ],
        capture_output=True, text=True,
    )
    known = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_lawbook_query.py"), "--store-json", str(store_path), "--claim-id", "claim", "--known-skip"], capture_output=True, text=True)
    summary = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_lawbook_query.py"), "--store-json", str(store_path), "--trust-summary"], capture_output=True, text=True)
    assert empty.returncode == 0
    assert result.returncode == 0, result.stderr
    assert report_path.exists() and answers_path.exists() and projections_path.exists()
    assert "SKIP_VERIFIED_PROOF" in known.stdout
    assert "trust_summary" in summary.stdout

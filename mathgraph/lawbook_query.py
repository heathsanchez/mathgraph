"""Read-only accepted-memory queries and known-skip decisions for MathGraph."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.certificates import TerminalForm
from mathgraph.hashing import content_id
from mathgraph.lawbook import (
    LawbookAcceptanceBoundary,
    LawbookEntry,
    LawbookEntryKind,
    LawbookEntryStatus,
    LawbookStore,
    audit_lawbook_store,
)


class LawbookQueryKind(str, Enum):
    CLAIM = "CLAIM"
    PAIR = "PAIR"
    CERTIFICATE = "CERTIFICATE"
    ENTRY = "ENTRY"
    PROOF = "PROOF"
    COUNTERMODEL = "COUNTERMODEL"
    OBSTRUCTION = "OBSTRUCTION"
    DIGESTION = "DIGESTION"
    PROJECTION = "PROJECTION"
    KNOWN_SKIP = "KNOWN_SKIP"
    TRUST_SUMMARY = "TRUST_SUMMARY"
    AUDIT = "AUDIT"
    UNKNOWN = "UNKNOWN"


class LawbookQueryStatus(str, Enum):
    FOUND_ACCEPTED_TRUTH = "FOUND_ACCEPTED_TRUTH"
    FOUND_ACCEPTED_OBSTRUCTION = "FOUND_ACCEPTED_OBSTRUCTION"
    FOUND_ACCEPTED_ADVISORY = "FOUND_ACCEPTED_ADVISORY"
    FOUND_CANDIDATE_ONLY = "FOUND_CANDIDATE_ONLY"
    FOUND_PROJECTION_ONLY = "FOUND_PROJECTION_ONLY"
    FOUND_DIGESTION_ONLY = "FOUND_DIGESTION_ONLY"
    FOUND_VALUE_ONLY = "FOUND_VALUE_ONLY"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID_QUERY = "INVALID_QUERY"
    ADVISORY_ONLY = "ADVISORY_ONLY"


class LawbookTrustLevel(str, Enum):
    VERIFIED_TRUTH = "VERIFIED_TRUTH"
    FINITE_REFUTATION = "FINITE_REFUTATION"
    ACCEPTED_OBSTRUCTION = "ACCEPTED_OBSTRUCTION"
    ACCEPTED_PUBLIC_MEMORY = "ACCEPTED_PUBLIC_MEMORY"
    CANDIDATE_MEMORY = "CANDIDATE_MEMORY"
    ADVISORY_PROJECTION = "ADVISORY_PROJECTION"
    ADVISORY_DIGESTION = "ADVISORY_DIGESTION"
    ADVISORY_VALUE = "ADVISORY_VALUE"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class KnownSkipDecision(str, Enum):
    SKIP_VERIFIED_PROOF = "SKIP_VERIFIED_PROOF"
    SKIP_FINITE_COUNTERMODEL = "SKIP_FINITE_COUNTERMODEL"
    SKIP_ACCEPTED_OBSTRUCTION = "SKIP_ACCEPTED_OBSTRUCTION"
    DO_NOT_SKIP_CANDIDATE_ONLY = "DO_NOT_SKIP_CANDIDATE_ONLY"
    DO_NOT_SKIP_ADVISORY_ONLY = "DO_NOT_SKIP_ADVISORY_ONLY"
    DO_NOT_SKIP_AMBIGUOUS = "DO_NOT_SKIP_AMBIGUOUS"
    DO_NOT_SKIP_NOT_FOUND = "DO_NOT_SKIP_NOT_FOUND"
    UNKNOWN = "UNKNOWN"


class LawbookQueryReportStatus(str, Enum):
    EMPTY = "EMPTY"
    ANSWERED = "ANSWERED"
    PARTIAL = "PARTIAL"
    NOT_FOUND = "NOT_FOUND"
    INVALID = "INVALID"
    HAS_WARNINGS = "HAS_WARNINGS"
    HAS_CRITICALS = "HAS_CRITICALS"


@dataclass
class LawbookQuery:
    query_id: str
    kind: LawbookQueryKind
    claim_id: str | None = None
    source: str | None = None
    target: str | None = None
    raw: str | None = None
    certificate_id: str | None = None
    entry_id: str | None = None
    include_candidates: bool = True
    include_advisory: bool = True
    include_projection_candidates: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "kind": self.kind.value,
            "claim_id": self.claim_id,
            "source": self.source,
            "target": self.target,
            "raw": self.raw,
            "certificate_id": self.certificate_id,
            "entry_id": self.entry_id,
            "include_candidates": self.include_candidates,
            "include_advisory": self.include_advisory,
            "include_projection_candidates": self.include_projection_candidates,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookQuery":
        return cls(
            query_id=str(data["query_id"]),
            kind=LawbookQueryKind(str(data.get("kind", LawbookQueryKind.UNKNOWN.value))),
            claim_id=_optional_str(data.get("claim_id")),
            source=_optional_str(data.get("source")),
            target=_optional_str(data.get("target")),
            raw=_optional_str(data.get("raw")),
            certificate_id=_optional_str(data.get("certificate_id")),
            entry_id=_optional_str(data.get("entry_id")),
            include_candidates=bool(data.get("include_candidates", True)),
            include_advisory=bool(data.get("include_advisory", True)),
            include_projection_candidates=bool(data.get("include_projection_candidates", True)),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookQuery":
        return cls.from_dict(json.loads(text))


@dataclass
class LawbookQueryAnswer:
    answer_id: str
    query_id: str
    status: LawbookQueryStatus
    trust_level: LawbookTrustLevel
    known_skip_decision: KnownSkipDecision = KnownSkipDecision.UNKNOWN
    terminal_form: TerminalForm | None = None
    certificate_id: str | None = None
    verifier_boundary_crossed: bool = False
    acceptance_boundary: LawbookAcceptanceBoundary | None = None
    matched_entry_ids: tuple[str, ...] = ()
    candidate_entry_ids: tuple[str, ...] = ()
    projection_candidate_ids: tuple[str, ...] = ()
    digestion_trace_ids: tuple[str, ...] = ()
    advisory_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    criticals: tuple[str, ...] = ()
    explanation: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = False

    def is_terminal_answer(self) -> bool:
        return (
            self.terminal_form is not None
            and bool(self.certificate_id)
            and self.verifier_boundary_crossed
            and self.trust_level in {LawbookTrustLevel.VERIFIED_TRUTH, LawbookTrustLevel.FINITE_REFUTATION}
        )

    def is_known_skip(self) -> bool:
        return self.known_skip_decision in {
            KnownSkipDecision.SKIP_VERIFIED_PROOF,
            KnownSkipDecision.SKIP_FINITE_COUNTERMODEL,
            KnownSkipDecision.SKIP_ACCEPTED_OBSTRUCTION,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer_id": self.answer_id,
            "query_id": self.query_id,
            "status": self.status.value,
            "trust_level": self.trust_level.value,
            "known_skip_decision": self.known_skip_decision.value,
            "terminal_form": self.terminal_form.value if self.terminal_form else None,
            "certificate_id": self.certificate_id,
            "verifier_boundary_crossed": self.verifier_boundary_crossed,
            "acceptance_boundary": self.acceptance_boundary.value if self.acceptance_boundary else None,
            "matched_entry_ids": list(self.matched_entry_ids),
            "candidate_entry_ids": list(self.candidate_entry_ids),
            "projection_candidate_ids": list(self.projection_candidate_ids),
            "digestion_trace_ids": list(self.digestion_trace_ids),
            "advisory_reasons": list(self.advisory_reasons),
            "warnings": list(self.warnings),
            "criticals": list(self.criticals),
            "explanation": self.explanation,
            "evidence": dict(self.evidence),
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookQueryAnswer":
        terminal = data.get("terminal_form")
        boundary = data.get("acceptance_boundary")
        return cls(
            answer_id=str(data["answer_id"]),
            query_id=str(data["query_id"]),
            status=LawbookQueryStatus(str(data.get("status", LawbookQueryStatus.ADVISORY_ONLY.value))),
            trust_level=LawbookTrustLevel(str(data.get("trust_level", LawbookTrustLevel.UNKNOWN.value))),
            known_skip_decision=KnownSkipDecision(str(data.get("known_skip_decision", KnownSkipDecision.UNKNOWN.value))),
            terminal_form=TerminalForm(str(terminal)) if terminal else None,
            certificate_id=_optional_str(data.get("certificate_id")),
            verifier_boundary_crossed=bool(data.get("verifier_boundary_crossed", False)),
            acceptance_boundary=LawbookAcceptanceBoundary(str(boundary)) if boundary else None,
            matched_entry_ids=tuple(str(x) for x in data.get("matched_entry_ids", ())),
            candidate_entry_ids=tuple(str(x) for x in data.get("candidate_entry_ids", ())),
            projection_candidate_ids=tuple(str(x) for x in data.get("projection_candidate_ids", ())),
            digestion_trace_ids=tuple(str(x) for x in data.get("digestion_trace_ids", ())),
            advisory_reasons=tuple(str(x) for x in data.get("advisory_reasons", ())),
            warnings=tuple(str(x) for x in data.get("warnings", ())),
            criticals=tuple(str(x) for x in data.get("criticals", ())),
            explanation=_optional_str(data.get("explanation")),
            evidence=dict(data.get("evidence", {})),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", False)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookQueryAnswer":
        return cls.from_dict(json.loads(text))


@dataclass
class LawbookQueryReport:
    report_id: str
    queries: list[LawbookQuery] = field(default_factory=list)
    answers: list[LawbookQueryAnswer] = field(default_factory=list)
    status: LawbookQueryReportStatus = LawbookQueryReportStatus.EMPTY
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def answer_count(self) -> int:
        return len(self.answers)

    def known_skip_count(self) -> int:
        return sum(answer.is_known_skip() for answer in self.answers)

    def terminal_answer_count(self) -> int:
        return sum(answer.is_terminal_answer() for answer in self.answers)

    def critical_count(self) -> int:
        return sum(len(answer.criticals) for answer in self.answers)

    def summarize(self) -> dict[str, Any]:
        self.summary = {
            "query_total": len(self.queries),
            "answer_total": len(self.answers),
            "known_skip_count": self.known_skip_count(),
            "terminal_answer_count": self.terminal_answer_count(),
            "critical_count": self.critical_count(),
            "warning_count": sum(len(answer.warnings) for answer in self.answers),
            "status_counts": _counts(answer.status.value for answer in self.answers),
            "trust_counts": _counts(answer.trust_level.value for answer in self.answers),
        }
        return dict(self.summary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "queries": [query.to_dict() for query in self.queries],
            "answers": [answer.to_dict() for answer in self.answers],
            "status": self.status.value,
            "created_at": self.created_at,
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LawbookQueryReport":
        return cls(
            report_id=str(data["report_id"]),
            queries=[LawbookQuery.from_dict(item) for item in data.get("queries", [])],
            answers=[LawbookQueryAnswer.from_dict(item) for item in data.get("answers", [])],
            status=LawbookQueryReportStatus(str(data.get("status", LawbookQueryReportStatus.EMPTY.value))),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            summary=dict(data.get("summary", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LawbookQueryReport":
        return cls.from_dict(json.loads(text))

    def write_json(self, path: str | Path) -> None:
        _write_text(path, json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")

    @classmethod
    def read_json(cls, path: str | Path) -> "LawbookQueryReport":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def write_jsonl(self, path: str | Path) -> None:
        _write_text(path, self.to_json() + "\n")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> list["LawbookQueryReport"]:
        return [cls.from_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def make_lawbook_query_id(*parts: Any) -> str:
    return content_id("lawbook_query", parts)


def make_lawbook_query_answer_id(*parts: Any) -> str:
    return content_id("lawbook_query_answer", parts)


def make_lawbook_query_report_id(*parts: Any) -> str:
    return content_id("lawbook_query_report", parts)


def make_claim_query(**kwargs: Any) -> LawbookQuery:
    return _make_query(LawbookQueryKind.CLAIM, **kwargs)


def make_certificate_query(certificate_id: str) -> LawbookQuery:
    return _make_query(LawbookQueryKind.CERTIFICATE, certificate_id=certificate_id)


def make_entry_query(entry_id: str) -> LawbookQuery:
    return _make_query(LawbookQueryKind.ENTRY, entry_id=entry_id)


def make_known_skip_query(**kwargs: Any) -> LawbookQuery:
    return _make_query(LawbookQueryKind.KNOWN_SKIP, **kwargs)


def make_trust_summary_query() -> LawbookQuery:
    return _make_query(LawbookQueryKind.TRUST_SUMMARY)


def query_lawbook_store(store: LawbookStore, query: LawbookQuery) -> LawbookQueryAnswer:
    if query.kind == LawbookQueryKind.TRUST_SUMMARY:
        answer = _answer(query, LawbookQueryStatus.FOUND_ACCEPTED_ADVISORY, LawbookTrustLevel.ACCEPTED_PUBLIC_MEMORY, evidence={"trust_summary": build_lawbook_trust_summary(store)})
        answer.explanation = explain_lawbook_answer(answer)
        return answer
    matches, valid = _matches(store, query)
    if not valid:
        answer = _answer(query, LawbookQueryStatus.INVALID_QUERY, LawbookTrustLevel.NONE, warnings=("query has no usable lookup key",))
        answer.explanation = explain_lawbook_answer(answer)
        return answer
    accepted = [entry for entry in matches if entry.is_accepted()]
    candidates = [entry for entry in matches if entry.status in {LawbookEntryStatus.CANDIDATE, LawbookEntryStatus.NEEDS_REVIEW}]
    proofs = [entry for entry in accepted if entry.kind == LawbookEntryKind.VERIFIED_PROOF_ENTRY and entry.has_valid_truth_boundary()]
    counters = [entry for entry in accepted if entry.kind == LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY and entry.has_valid_truth_boundary()]
    obstructions = [entry for entry in accepted if entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY]
    projections = [entry for entry in accepted if entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY]
    digests = [entry for entry in accepted if entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY]
    if proofs and counters:
        answer = _answer(query, LawbookQueryStatus.AMBIGUOUS, LawbookTrustLevel.UNKNOWN, matched=accepted, candidates=candidates, criticals=("accepted proof and finite countermodel conflict",), skip=KnownSkipDecision.DO_NOT_SKIP_AMBIGUOUS)
    elif proofs:
        entry = proofs[0]
        answer = _answer(query, LawbookQueryStatus.FOUND_ACCEPTED_TRUTH, LawbookTrustLevel.VERIFIED_TRUTH, matched=proofs, candidates=candidates, terminal=TerminalForm.VERIFIED_PROOF, certificate_id=entry.certificate_id, boundary=True, acceptance=entry.acceptance_boundary, skip=KnownSkipDecision.SKIP_VERIFIED_PROOF)
    elif counters:
        entry = counters[0]
        answer = _answer(query, LawbookQueryStatus.FOUND_ACCEPTED_TRUTH, LawbookTrustLevel.FINITE_REFUTATION, matched=counters, candidates=candidates, terminal=TerminalForm.FINITE_COUNTERMODEL, certificate_id=entry.certificate_id, boundary=True, acceptance=entry.acceptance_boundary, skip=KnownSkipDecision.SKIP_FINITE_COUNTERMODEL)
    elif obstructions:
        entry = obstructions[0]
        answer = _answer(query, LawbookQueryStatus.FOUND_ACCEPTED_OBSTRUCTION, LawbookTrustLevel.ACCEPTED_OBSTRUCTION, matched=obstructions, candidates=candidates, terminal=entry.terminal_form, acceptance=entry.acceptance_boundary, skip=KnownSkipDecision.SKIP_ACCEPTED_OBSTRUCTION)
    elif projections:
        answer = _answer(query, LawbookQueryStatus.FOUND_PROJECTION_ONLY, LawbookTrustLevel.ADVISORY_PROJECTION, matched=projections, candidates=candidates, skip=KnownSkipDecision.DO_NOT_SKIP_ADVISORY_ONLY, advisory=True)
    elif digests:
        answer = _answer(query, LawbookQueryStatus.FOUND_DIGESTION_ONLY, LawbookTrustLevel.ADVISORY_DIGESTION, matched=digests, candidates=candidates, skip=KnownSkipDecision.DO_NOT_SKIP_ADVISORY_ONLY, advisory=True)
    elif candidates and query.include_candidates:
        answer = _answer(query, LawbookQueryStatus.FOUND_CANDIDATE_ONLY, LawbookTrustLevel.CANDIDATE_MEMORY, candidates=candidates, skip=KnownSkipDecision.DO_NOT_SKIP_CANDIDATE_ONLY, advisory=True)
    else:
        answer = _answer(query, LawbookQueryStatus.NOT_FOUND, LawbookTrustLevel.NONE, skip=KnownSkipDecision.DO_NOT_SKIP_NOT_FOUND)
    answer.explanation = explain_lawbook_answer(answer)
    return answer


def query_lawbook_store_many(store: LawbookStore, queries: Sequence[LawbookQuery]) -> LawbookQueryReport:
    answers = [query_lawbook_store(store, query) for query in queries]
    if not queries:
        status = LawbookQueryReportStatus.EMPTY
    elif any(answer.criticals for answer in answers):
        status = LawbookQueryReportStatus.HAS_CRITICALS
    elif any(answer.warnings for answer in answers):
        status = LawbookQueryReportStatus.HAS_WARNINGS
    elif all(answer.status == LawbookQueryStatus.NOT_FOUND for answer in answers):
        status = LawbookQueryReportStatus.NOT_FOUND
    elif any(answer.status in {LawbookQueryStatus.NOT_FOUND, LawbookQueryStatus.INVALID_QUERY} for answer in answers):
        status = LawbookQueryReportStatus.PARTIAL
    else:
        status = LawbookQueryReportStatus.ANSWERED
    report = LawbookQueryReport(
        report_id=make_lawbook_query_report_id([query.query_id for query in queries]),
        queries=list(queries),
        answers=answers,
        status=status,
        metadata={"advisory_query_not_verification": True, "trust_summary": build_lawbook_trust_summary(store)},
    )
    report.summarize()
    return report


def query_lawbook_store_by_claim(store: LawbookStore, **kwargs: Any) -> LawbookQueryAnswer:
    return query_lawbook_store(store, make_claim_query(**kwargs))


def query_lawbook_store_by_certificate(store: LawbookStore, certificate_id: str) -> LawbookQueryAnswer:
    return query_lawbook_store(store, make_certificate_query(certificate_id))


def query_lawbook_store_by_entry(store: LawbookStore, entry_id: str) -> LawbookQueryAnswer:
    return query_lawbook_store(store, make_entry_query(entry_id))


def known_skip_for_claim(store: LawbookStore, **kwargs: Any) -> KnownSkipDecision:
    return query_lawbook_store(store, make_known_skip_query(**kwargs)).known_skip_decision


def build_lawbook_trust_summary(store: LawbookStore) -> dict[str, Any]:
    findings = audit_lawbook_store(store)
    accepted = store.accepted_entries()
    truth = [entry for entry in accepted if entry.is_truth_entry() and entry.has_valid_truth_boundary()]
    return {
        "entry_total": len(store.entries),
        "accepted_count": len(accepted),
        "candidate_count": len(store.candidate_entries()),
        "accepted_truth_count": len(truth),
        "accepted_proof_count": sum(entry.kind == LawbookEntryKind.VERIFIED_PROOF_ENTRY for entry in truth),
        "accepted_countermodel_count": sum(entry.kind == LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY for entry in truth),
        "accepted_obstruction_count": sum(entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY for entry in accepted),
        "accepted_projection_rule_count": sum(entry.kind == LawbookEntryKind.PROJECTION_RULE_ENTRY for entry in accepted),
        "accepted_digestion_count": sum(entry.kind == LawbookEntryKind.DIGESTED_PROOF_ENTRY for entry in accepted),
        "critical_count": sum(item["severity"] == "CRITICAL" for item in findings),
        "warning_count": sum(item["severity"] == "WARNING" for item in findings),
        "queryable_truth_count": len(truth),
        "known_skip_capable_count": len(truth) + sum(entry.kind == LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY for entry in accepted),
        "advisory_only_count": sum(entry.advisory for entry in store.entries),
    }


def explain_lawbook_answer(answer: LawbookQueryAnswer) -> str:
    if answer.known_skip_decision == KnownSkipDecision.SKIP_VERIFIED_PROOF:
        return "This claim can be skipped because an accepted Lawbook entry points to an existing VERIFIED_PROOF certificate that crossed a verifier boundary."
    if answer.known_skip_decision == KnownSkipDecision.SKIP_FINITE_COUNTERMODEL:
        return "This claim can be skipped because an accepted Lawbook entry points to an existing FINITE_COUNTERMODEL certificate that crossed a finite-validation boundary."
    if answer.known_skip_decision == KnownSkipDecision.SKIP_ACCEPTED_OBSTRUCTION:
        return "This claim can be skipped because an accepted Lawbook obstruction entry already records structured residual knowledge."
    if answer.status == LawbookQueryStatus.FOUND_CANDIDATE_ONLY:
        return "This is a candidate only. It cannot be skipped and does not establish truth."
    if answer.status == LawbookQueryStatus.FOUND_PROJECTION_ONLY:
        return "This projection rule may schedule work, but it is not a certificate."
    if answer.status == LawbookQueryStatus.FOUND_DIGESTION_ONLY:
        return "This digestion entry improves understanding, but digestion is not verification and cannot permit skip."
    if answer.status == LawbookQueryStatus.AMBIGUOUS:
        return "Accepted memory conflicts for this query, so it cannot be skipped until audited."
    if answer.status == LawbookQueryStatus.INVALID_QUERY:
        return "This query has no usable lookup key."
    if answer.status == LawbookQueryStatus.NOT_FOUND:
        return "No accepted Lawbook memory answered this query."
    return "This query reports accepted public memory without creating new truth."


def lawbook_query_answer_to_projection_candidates(answer: LawbookQueryAnswer) -> list[Any]:
    from mathgraph.projection import ProjectionCandidate, ProjectionRuleKind

    if answer.status == LawbookQueryStatus.AMBIGUOUS or answer.status == LawbookQueryStatus.FOUND_CANDIDATE_ONLY:
        return []
    if answer.is_known_skip():
        return [
            ProjectionCandidate(
                candidate_id=content_id("lawbook_query_projection", answer.answer_id),
                source_claim_id=None,
                target_claim_id=None,
                rule_kind=ProjectionRuleKind.EXACT_KNOWN,
                originating_lawbook_entry_id=answer.matched_entry_ids[0] if answer.matched_entry_ids else None,
                originating_certificate_id=answer.certificate_id,
                confidence=1.0,
                advisory=True,
                metadata={"known_skip_lookup": True, "query_answer_id": answer.answer_id},
            )
        ]
    if answer.status == LawbookQueryStatus.FOUND_PROJECTION_ONLY:
        return [
            ProjectionCandidate(
                candidate_id=content_id("lawbook_query_advisory_projection", answer.answer_id),
                source_claim_id=None,
                target_claim_id=None,
                rule_kind=ProjectionRuleKind.ADVISORY_SIMILARITY,
                originating_lawbook_entry_id=answer.matched_entry_ids[0] if answer.matched_entry_ids else None,
                confidence=0.5,
                advisory=True,
                metadata={"query_answer_id": answer.answer_id, "not_certificate": True},
            )
        ]
    return []


def lawbook_query_answer_to_continuation_outputs(answer: LawbookQueryAnswer) -> list[Any]:
    from mathgraph.continuation_actions import ContinuationActionOutput, ContinuationActionStatus, ContinuationOutputKind

    task = {
        LawbookQueryStatus.NOT_FOUND: "investigate_claim",
        LawbookQueryStatus.FOUND_CANDIDATE_ONLY: "review_lawbook_candidate",
        LawbookQueryStatus.FOUND_PROJECTION_ONLY: "project_lawbook_entry",
        LawbookQueryStatus.FOUND_ACCEPTED_TRUTH: "known_skip",
        LawbookQueryStatus.FOUND_ACCEPTED_OBSTRUCTION: "known_skip",
        LawbookQueryStatus.AMBIGUOUS: "audit_conflict",
    }.get(answer.status)
    if not task:
        return []
    return [
        ContinuationActionOutput(
            output_id=content_id("lawbook_query_output", answer.answer_id),
            action_id="lawbook_query",
            kind=ContinuationOutputKind.TASK,
            status=ContinuationActionStatus.PRODUCED_TASK,
            task_payload={"task": task, "answer_id": answer.answer_id},
            metadata={"advisory_only": True, "query_is_not_verification": True},
            advisory=True,
        )
    ]


def lawbook_query_report_to_alchemical_trace(report: LawbookQueryReport) -> Any:
    from mathgraph.alchemy import AlchemicalPhase, AlchemicalStatus, AlchemicalStep, AlchemicalTrace

    trace = AlchemicalTrace(trace_id=content_id("lawbook_query_alchemy", report.report_id))
    if report.queries:
        trace.add_step(AlchemicalStep(AlchemicalPhase.RAW_MATTER, AlchemicalStatus.ADVISORY_ONLY))
        trace.add_step(AlchemicalStep(AlchemicalPhase.SOLUTION, AlchemicalStatus.ADVISORY_ONLY))
        trace.add_step(AlchemicalStep(AlchemicalPhase.DISTILLATION, AlchemicalStatus.ADVISORY_ONLY))
    if any(lawbook_query_answer_to_projection_candidates(answer) for answer in report.answers):
        trace.add_step(AlchemicalStep(AlchemicalPhase.PROJECTION, AlchemicalStatus.ADVISORY_ONLY))
    if any(answer.is_terminal_answer() for answer in report.answers):
        trace.add_step(AlchemicalStep(AlchemicalPhase.FIXATION, AlchemicalStatus.PROMOTED_BY_VERIFIER, verifier_boundary="inherited"))
    return trace


def lawbook_query_report_to_agent_experiences(report: LawbookQueryReport, agent_id: str | None = None) -> list[Any]:
    from mathgraph.agent_biography import AgentExperience, AgentExperienceOutcome

    items = []
    for answer in report.answers:
        outcome = AgentExperienceOutcome.ADVISORY_ONLY
        if answer.is_terminal_answer() and answer.terminal_form == TerminalForm.VERIFIED_PROOF:
            outcome = AgentExperienceOutcome.VERIFIED_PROOF
        elif answer.is_terminal_answer() and answer.terminal_form == TerminalForm.FINITE_COUNTERMODEL:
            outcome = AgentExperienceOutcome.FINITE_COUNTERMODEL
        elif answer.status in {LawbookQueryStatus.AMBIGUOUS, LawbookQueryStatus.FOUND_ACCEPTED_OBSTRUCTION}:
            outcome = AgentExperienceOutcome.RESIDUAL
        items.append(
            AgentExperience(
                experience_id=content_id("lawbook_query_experience", answer.answer_id),
                agent_id=agent_id or "lawbook_query",
                episode_id=None,
                claim_id=None,
                route="lawbook_query",
                phase="DISTILLATION",
                outcome=outcome,
                terminal_form=answer.terminal_form if answer.is_terminal_answer() else None,
                certificate_id=answer.certificate_id if answer.is_terminal_answer() else None,
                verifier_boundary_crossed=answer.is_terminal_answer(),
                metadata={"known_skip_decision": answer.known_skip_decision.value, "lookup_not_new_verification": True},
            )
        )
    return items


def lawbook_query_report_to_route_telemetry_events(report: LawbookQueryReport) -> list[dict[str, Any]]:
    return [
        {
            "event_id": content_id("lawbook_query_telemetry", answer.answer_id),
            "route_kind": "lawbook_query",
            "outcome": answer.status.value,
            "known_skip_decision": answer.known_skip_decision.value,
            "advisory": not answer.is_terminal_answer(),
        }
        for answer in report.answers
    ]


def _make_query(kind: LawbookQueryKind, **kwargs: Any) -> LawbookQuery:
    payload = {"kind": kind.value, **kwargs}
    return LawbookQuery(query_id=make_lawbook_query_id(payload), kind=kind, **kwargs)


def _matches(store: LawbookStore, query: LawbookQuery) -> tuple[list[LawbookEntry], bool]:
    if query.kind == LawbookQueryKind.ENTRY:
        return [entry for entry in store.entries if entry.entry_id == query.entry_id], bool(query.entry_id)
    if query.kind == LawbookQueryKind.CERTIFICATE:
        return [entry for entry in store.entries if entry.certificate_id == query.certificate_id], bool(query.certificate_id)
    if query.claim_id:
        return [entry for entry in store.entries if entry.claim_id == query.claim_id], True
    if query.source is not None and query.target is not None:
        return [entry for entry in store.entries if entry.source == query.source and entry.target == query.target], True
    if query.raw:
        return [entry for entry in store.entries if entry.raw == query.raw], True
    return [], False


def _answer(
    query: LawbookQuery,
    status: LawbookQueryStatus,
    trust: LawbookTrustLevel,
    *,
    matched: Sequence[LawbookEntry] = (),
    candidates: Sequence[LawbookEntry] = (),
    terminal: TerminalForm | None = None,
    certificate_id: str | None = None,
    boundary: bool = False,
    acceptance: LawbookAcceptanceBoundary | None = None,
    skip: KnownSkipDecision = KnownSkipDecision.UNKNOWN,
    warnings: tuple[str, ...] = (),
    criticals: tuple[str, ...] = (),
    evidence: Mapping[str, Any] | None = None,
    advisory: bool = False,
) -> LawbookQueryAnswer:
    return LawbookQueryAnswer(
        answer_id=make_lawbook_query_answer_id(query.query_id, status.value, [entry.entry_id for entry in matched]),
        query_id=query.query_id,
        status=status,
        trust_level=trust,
        known_skip_decision=skip,
        terminal_form=terminal,
        certificate_id=certificate_id,
        verifier_boundary_crossed=boundary,
        acceptance_boundary=acceptance,
        matched_entry_ids=tuple(entry.entry_id for entry in matched),
        candidate_entry_ids=tuple(entry.entry_id for entry in candidates),
        projection_candidate_ids=tuple(item for entry in matched for item in entry.projection_rule_ids),
        digestion_trace_ids=tuple(item for entry in matched for item in entry.digestion_trace_ids),
        advisory_reasons=("query reports memory; it does not create truth",) if advisory else (),
        warnings=warnings,
        criticals=criticals,
        evidence=dict(evidence or {}),
        advisory=advisory,
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _counts(values: Sequence[str] | Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def _write_text(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

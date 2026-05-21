"""Central advisory-to-Lawbook promotion gate."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.external_certificates import (
    ExternalBoundaryEvidence,
    ExternalCertificate,
    ExternalCertificateKind,
    ExternalCertificateStatus,
    ExternalVerifierKind,
)
from mathgraph.hashing import content_id
from mathgraph.lawbook import (
    LawbookAcceptanceBoundary,
    LawbookEntry,
    LawbookEntryKind,
    LawbookEntryStatus,
    TerminalForm,
    make_lawbook_entry_id,
)
from mathgraph.terminal_schema import CanonicalTerminalForm, VerifierBoundaryKind


class PromotionGateDecisionKind(str, Enum):
    ACCEPT_FOR_LAWBOOK = "ACCEPT_FOR_LAWBOOK"
    REJECT_ADVISORY_ONLY = "REJECT_ADVISORY_ONLY"
    REJECT_INVALID_BOUNDARY = "REJECT_INVALID_BOUNDARY"
    REJECT_TERMINAL_MISMATCH = "REJECT_TERMINAL_MISMATCH"
    REJECT_FINITE_SEARCH_MISS = "REJECT_FINITE_SEARCH_MISS"
    NEEDS_REPLAY = "NEEDS_REPLAY"
    NAMED_OBSTRUCTION_ONLY = "NAMED_OBSTRUCTION_ONLY"


class PromotionRejectionReason(str, Enum):
    ADVISORY_OBJECT = "ADVISORY_OBJECT"
    INVALID_BOUNDARY = "INVALID_BOUNDARY"
    TERMINAL_MISMATCH = "TERMINAL_MISMATCH"
    FINITE_SEARCH_MISS = "FINITE_SEARCH_MISS"
    RAW_SUCCESS_TEXT_ONLY = "RAW_SUCCESS_TEXT_ONLY"
    REASON_ATLAS_ENTRY = "REASON_ATLAS_ENTRY"
    ROOT_OPERATOR_SCHEMA = "ROOT_OPERATOR_SCHEMA"
    ROUTE_LAW = "ROUTE_LAW"
    FEEDBACK_EVENT = "FEEDBACK_EVENT"
    ADVISORY_ONLY_CERTIFICATE = "ADVISORY_ONLY_CERTIFICATE"
    NONE = "NONE"


@dataclass(frozen=True)
class PromotionGateConfig:
    allow_named_obstruction_without_boundary: bool = True
    accepted_by: str = "promotion_gate"


@dataclass(frozen=True)
class PromotionGateDecision:
    decision_id: str
    decision_kind: PromotionGateDecisionKind
    accepted: bool
    terminal_form: str | None = None
    certificate_id: str | None = None
    rejection_reasons: tuple[PromotionRejectionReason, ...] = ()
    lawbook_candidate: dict[str, Any] | None = None
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_kind": self.decision_kind.value,
            "accepted": self.accepted,
            "terminal_form": self.terminal_form,
            "certificate_id": self.certificate_id,
            "rejection_reasons": [reason.value for reason in self.rejection_reasons],
            "lawbook_candidate": dict(self.lawbook_candidate) if self.lawbook_candidate else None,
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class PromotionGate:
    def __init__(self, config: PromotionGateConfig | None = None) -> None:
        self.config = config or PromotionGateConfig()

    def evaluate(self, candidate: Any) -> PromotionGateDecision:
        if isinstance(candidate, ExternalCertificate):
            return self._evaluate_external_certificate(candidate)
        if _looks_reason_atlas_entry(candidate):
            return _reject(candidate, PromotionGateDecisionKind.REJECT_ADVISORY_ONLY, PromotionRejectionReason.REASON_ATLAS_ENTRY)
        if _looks_root_operator_schema(candidate):
            return _reject(candidate, PromotionGateDecisionKind.REJECT_ADVISORY_ONLY, PromotionRejectionReason.ROOT_OPERATOR_SCHEMA)
        if _looks_route_law(candidate):
            return _reject(candidate, PromotionGateDecisionKind.REJECT_ADVISORY_ONLY, PromotionRejectionReason.ROUTE_LAW)
        if _looks_feedback_event(candidate):
            return _reject(candidate, PromotionGateDecisionKind.REJECT_ADVISORY_ONLY, PromotionRejectionReason.FEEDBACK_EVENT)
        if _looks_boundary_evidence(candidate):
            return self._evaluate_boundary_evidence(candidate)
        return _reject(candidate, PromotionGateDecisionKind.NEEDS_REPLAY, PromotionRejectionReason.ADVISORY_OBJECT)

    def _evaluate_external_certificate(self, cert: ExternalCertificate) -> PromotionGateDecision:
        form = cert.candidate_terminal_form()
        if cert.metadata.get("finite_search_miss") and form == CanonicalTerminalForm.VERIFIED_PROOF:
            return _reject(cert, PromotionGateDecisionKind.REJECT_FINITE_SEARCH_MISS, PromotionRejectionReason.FINITE_SEARCH_MISS)
        if cert.metadata.get("raw_success_text") and not cert.boundary_valid:
            return _reject(cert, PromotionGateDecisionKind.REJECT_INVALID_BOUNDARY, PromotionRejectionReason.RAW_SUCCESS_TEXT_ONLY)
        if cert.certificate_kind == ExternalCertificateKind.ADVISORY_ONLY or form == CanonicalTerminalForm.NONE:
            return _reject(cert, PromotionGateDecisionKind.REJECT_ADVISORY_ONLY, PromotionRejectionReason.ADVISORY_ONLY_CERTIFICATE)
        if form == CanonicalTerminalForm.NAMED_OBSTRUCTION:
            return PromotionGateDecision(
                decision_id=content_id("promotion-decision", cert.to_dict()),
                decision_kind=PromotionGateDecisionKind.NAMED_OBSTRUCTION_ONLY,
                accepted=False,
                terminal_form=form.value,
                certificate_id=cert.cert_id,
                warnings=("Named obstruction may be recorded separately; it is not proof/refutation truth.",),
                metadata={"advisory_boundary": True},
            )
        if not (cert.boundary_evidence and cert.boundary_evidence.is_valid_boundary() and cert.boundary_valid):
            return _reject(cert, PromotionGateDecisionKind.REJECT_INVALID_BOUNDARY, PromotionRejectionReason.INVALID_BOUNDARY)
        if cert.boundary_evidence.terminal_form != form:
            return _reject(cert, PromotionGateDecisionKind.REJECT_TERMINAL_MISMATCH, PromotionRejectionReason.TERMINAL_MISMATCH)
        entry = self._lawbook_candidate_from_certificate(cert, form)
        return PromotionGateDecision(
            decision_id=content_id("promotion-decision", cert.to_dict()),
            decision_kind=PromotionGateDecisionKind.ACCEPT_FOR_LAWBOOK,
            accepted=True,
            terminal_form=form.value,
            certificate_id=cert.cert_id,
            lawbook_candidate=entry.to_dict(),
            metadata={"boundary_evidence": cert.boundary_evidence.to_dict()},
        )

    def _evaluate_boundary_evidence(self, evidence: Any) -> PromotionGateDecision:
        is_valid = bool(evidence.is_valid_boundary_evidence() if hasattr(evidence, "is_valid_boundary_evidence") else evidence.is_valid_boundary())
        if not is_valid:
            return _reject(evidence, PromotionGateDecisionKind.REJECT_INVALID_BOUNDARY, PromotionRejectionReason.INVALID_BOUNDARY)
        terminal = str(getattr(evidence, "terminal_form", "") or "")
        cert_id = str(getattr(evidence, "certificate_id", "") or "")
        if terminal not in {"VERIFIED_PROOF", "REFUTATION_CERTIFICATE", "FINITE_COUNTERMODEL"}:
            return _reject(evidence, PromotionGateDecisionKind.REJECT_TERMINAL_MISMATCH, PromotionRejectionReason.TERMINAL_MISMATCH)
        mapped = CanonicalTerminalForm.VERIFIED_PROOF if terminal == "VERIFIED_PROOF" else CanonicalTerminalForm.REFUTATION_CERTIFICATE
        artifact_hash = getattr(evidence, "artifact_hash", None) or getattr(evidence, "command_contract_hash", None)
        source_artifact_id = getattr(evidence, "source_artifact_id", None) or getattr(evidence, "artifact_id", None) or getattr(evidence, "result_id", None)
        raw_output_hash = getattr(evidence, "raw_output_hash", None) or getattr(evidence, "result_id", None)
        boundary = ExternalBoundaryEvidence(
            evidence_id=str(getattr(evidence, "evidence_id", "") or content_id("external-boundary-evidence", _candidate_payload(evidence))),
            boundary_kind=_coerce_boundary_kind(getattr(evidence, "boundary_kind", None)),
            certificate_id=cert_id,
            terminal_form=mapped,
            source_artifact_id=source_artifact_id,
            artifact_hash=artifact_hash,
            raw_output_hash=raw_output_hash,
            verifier_kind=_coerce_verifier_kind(getattr(evidence, "verifier_kind", None)),
            checker_name=str(getattr(evidence, "checker_name", "") or ""),
            checker_version=str(getattr(evidence, "checker_version", "") or ""),
            metadata={"from_existing_boundary_evidence": True},
        )
        cert = ExternalCertificate(
            cert_id=cert_id,
            verifier=boundary.verifier_kind,
            status=ExternalCertificateStatus.ACCEPTED,
            claim="",
            claim_hash="",
            certificate_kind=ExternalCertificateKind.VERIFIED_PROOF
            if mapped == CanonicalTerminalForm.VERIFIED_PROOF
            else ExternalCertificateKind.REFUTATION_CERTIFICATE,
            proposed_terminal_form=mapped,
            boundary_evidence=boundary,
            boundary_valid=True,
            metadata={"from_boundary_evidence": True},
        )
        return self._evaluate_external_certificate(cert)

    def _lawbook_candidate_from_certificate(self, cert: ExternalCertificate, form: CanonicalTerminalForm) -> LawbookEntry:
        if form == CanonicalTerminalForm.VERIFIED_PROOF:
            kind = LawbookEntryKind.VERIFIED_PROOF_ENTRY
            terminal = TerminalForm.VERIFIED_PROOF
            boundary = LawbookAcceptanceBoundary.VERIFIED_PROOF
        else:
            kind = LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY
            terminal = TerminalForm.FINITE_COUNTERMODEL
            boundary = LawbookAcceptanceBoundary.FINITE_COUNTERMODEL
        return LawbookEntry(
            entry_id=make_lawbook_entry_id("promotion-gate", cert.cert_id),
            kind=kind,
            status=LawbookEntryStatus.CANDIDATE,
            raw=cert.claim,
            terminal_form=terminal,
            certificate_id=cert.cert_id,
            verifier_boundary_crossed=True,
            acceptance_boundary=boundary,
            artifact_ids=tuple(x for x in (cert.source_artifact_id, cert.artifact_hash) if x),
            metadata={
                "promotion_gate": True,
                "external_certificate_id": cert.cert_id,
                "boundary_valid": cert.boundary_valid,
                "raw_success_text_not_enough": True,
            },
        )


def _reject(candidate: Any, kind: PromotionGateDecisionKind, reason: PromotionRejectionReason) -> PromotionGateDecision:
    return PromotionGateDecision(
        decision_id=content_id("promotion-decision", _candidate_payload(candidate)),
        decision_kind=kind,
        accepted=False,
        rejection_reasons=(reason,),
        metadata={"candidate_kind": candidate.__class__.__name__},
    )


def _candidate_payload(candidate: Any) -> Any:
    return candidate.to_dict() if hasattr(candidate, "to_dict") else getattr(candidate, "__dict__", str(candidate))


def _looks_reason_atlas_entry(candidate: Any) -> bool:
    return candidate.__class__.__name__ == "ReasonAtlasEntry" or hasattr(candidate, "priority_score") and hasattr(candidate, "advisory_only")


def _looks_root_operator_schema(candidate: Any) -> bool:
    return candidate.__class__.__name__ == "RootOperatorSchema" or hasattr(candidate, "schema_id") and hasattr(candidate, "source_trace_ids")


def _looks_route_law(candidate: Any) -> bool:
    data = _candidate_payload(candidate)
    return isinstance(data, dict) and str(data.get("law_kind", "")).upper() == "PROMOTED_ROUTE_LAW"


def _looks_feedback_event(candidate: Any) -> bool:
    return candidate.__class__.__name__ == "ReasonAtlasFeedbackEvent" or hasattr(candidate, "outcome") and hasattr(candidate, "entry_id")


def _looks_boundary_evidence(candidate: Any) -> bool:
    return hasattr(candidate, "is_valid_boundary_evidence") or hasattr(candidate, "is_valid_boundary")


def _coerce_boundary_kind(value: Any) -> VerifierBoundaryKind:
    if isinstance(value, VerifierBoundaryKind):
        return value
    text = str(value or "").strip().upper()
    legacy = {
        "VERIFIER_CHECK": VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
        "LOCAL_VERIFIER_ACCEPTED": VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
        "TRUSTED_IMPORT": VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
        "FINITE_VALIDATION": VerifierBoundaryKind.FINITE_CHECKED,
        "CHAIN_AUDIT": VerifierBoundaryKind.CHAIN_AUDITED,
    }
    if text in legacy:
        return legacy[text]
    for item in VerifierBoundaryKind:
        if text in {item.name, item.value.upper()}:
            return item
    return VerifierBoundaryKind.NOT_VERIFIED


def _coerce_verifier_kind(value: Any) -> ExternalVerifierKind:
    if isinstance(value, ExternalVerifierKind):
        return value
    text = str(value or "").strip().upper()
    for item in ExternalVerifierKind:
        if text in {item.name, item.value.upper()}:
            return item
    return ExternalVerifierKind.UNKNOWN

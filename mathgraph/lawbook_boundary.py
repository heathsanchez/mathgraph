"""Canonical Lawbook boundary façade.

New code should call this module before writing terminal Lawbook entries.  It
wraps PromotionGate and rejects advisory scheduler objects, raw success text,
and failed finite searches as terminal evidence.
"""

from __future__ import annotations

from typing import Any

from mathgraph.external_certificates import ExternalCertificate
from mathgraph.lawbook_schema import BoundaryEvidenceType, LawbookAdmissionDecision, TerminalForm, normalize_terminal_form
from mathgraph.promotion_gate import PromotionGate, PromotionGateDecisionKind
from mathgraph.terminal_schema import VerifierBoundaryKind


def evaluate_lawbook_admission(candidate: Any, *, failed_finite_search: bool = False) -> LawbookAdmissionDecision:
    if failed_finite_search:
        return reject_failed_search_as_truth()
    if isinstance(candidate, str):
        return LawbookAdmissionDecision(False, "raw_success_text_is_not_boundary_evidence")
    if _looks_advisory(candidate):
        return LawbookAdmissionDecision(False, "advisory_artifact_cannot_promote", advisory_only=True)
    if isinstance(candidate, dict):
        if candidate.get("failed_finite_search") and str(candidate.get("terminal_form", "")).upper() in {"TRUE", "VERIFIED_PROOF"}:
            return reject_failed_search_as_truth()
        if candidate.get("raw_success_text") and not candidate.get("boundary_evidence"):
            return LawbookAdmissionDecision(False, "raw_success_text_is_not_boundary_evidence")
        if candidate.get("advisory_only") is True:
            return LawbookAdmissionDecision(False, "advisory_artifact_cannot_promote", advisory_only=True)
    gate_decision = PromotionGate().evaluate(candidate)
    if not gate_decision.accepted:
        reason = gate_decision.rejection_reasons[0].value if gate_decision.rejection_reasons else gate_decision.decision_kind.value
        return LawbookAdmissionDecision(False, reason, advisory_only=True, metadata=gate_decision.to_dict())
    terminal = normalize_terminal_form(gate_decision.terminal_form)
    boundary = _boundary_from_candidate(candidate)
    return LawbookAdmissionDecision(
        accepted=True,
        reason="accepted_by_promotion_gate",
        advisory_only=False,
        terminal_form=terminal,
        boundary_evidence_type=boundary,
        can_promote_truth=True,
        metadata=gate_decision.to_dict(),
    )


def assert_advisory_cannot_promote(candidate: Any) -> None:
    decision = evaluate_lawbook_admission(candidate)
    if decision.can_promote_truth:
        raise AssertionError("advisory candidate unexpectedly promoted truth")


def is_boundary_backed_terminal_candidate(candidate: Any) -> bool:
    return evaluate_lawbook_admission(candidate).can_promote_truth


def reject_failed_search_as_truth() -> LawbookAdmissionDecision:
    return LawbookAdmissionDecision(False, "failed_finite_search_cannot_be_true", advisory_only=True)


def normalize_terminal_form_value(value: Any) -> TerminalForm:
    return normalize_terminal_form(value)


def explain_admission_decision(decision: LawbookAdmissionDecision) -> str:
    if decision.accepted:
        return f"accepted {decision.terminal_form.value} via {decision.boundary_evidence_type.value}"
    return f"rejected: {decision.reason}"


def _boundary_from_candidate(candidate: Any) -> BoundaryEvidenceType:
    evidence = getattr(candidate, "boundary_evidence", None)
    kind = getattr(evidence, "boundary_kind", None)
    if kind == VerifierBoundaryKind.FINITE_CHECKED:
        return BoundaryEvidenceType.FINITE_CHECKED
    if kind == VerifierBoundaryKind.LEAN_TYPECHECKED:
        return BoundaryEvidenceType.LEAN_TYPECHECKED
    if kind == VerifierBoundaryKind.CHAIN_AUDITED:
        return BoundaryEvidenceType.CHAIN_AUDIT
    if kind == VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED:
        return BoundaryEvidenceType.TRUSTED_IMPORT
    return BoundaryEvidenceType.NONE


def _looks_advisory(candidate: Any) -> bool:
    name = candidate.__class__.__name__
    if name in {"ReasonAtlasEntry", "RootOperatorSchema", "ReasonAtlasHTiltScore"}:
        return True
    if hasattr(candidate, "priority_score") and hasattr(candidate, "advisory_only"):
        return True
    if hasattr(candidate, "new_priority_score") and getattr(candidate, "advisory_only", False):
        return True
    if isinstance(candidate, dict):
        kind = str(candidate.get("kind") or candidate.get("artifact_kind") or candidate.get("law_kind") or "").lower()
        if kind in {"reason_atlas_entry", "htilt_score", "route_law", "advisory_route"}:
            return True
    return False

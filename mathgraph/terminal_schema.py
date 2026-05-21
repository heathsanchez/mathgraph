"""Compatibility helpers for MathGraph terminal forms and truth boundaries."""

from __future__ import annotations

from enum import Enum


class CanonicalTerminalForm(str, Enum):
    VERIFIED_PROOF = "VERIFIED_PROOF"
    REFUTATION_CERTIFICATE = "REFUTATION_CERTIFICATE"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"
    NONE = "NONE"


class RefutationKind(str, Enum):
    FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"
    SMT_COUNTERMODEL = "SMT_COUNTERMODEL"
    SAT_ASSIGNMENT = "SAT_ASSIGNMENT"
    EXECUTION_COUNTEREXAMPLE = "EXECUTION_COUNTEREXAMPLE"
    EXTERNAL_COUNTERMODEL = "EXTERNAL_COUNTERMODEL"
    UNKNOWN = "UNKNOWN"


class VerifierBoundaryKind(str, Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    FINITE_CHECKED = "FINITE_CHECKED"
    LEAN_TYPECHECKED = "LEAN_TYPECHECKED"
    COQ_CHECKED = "COQ_CHECKED"
    ISABELLE_CHECKED = "ISABELLE_CHECKED"
    SMT_CHECKED = "SMT_CHECKED"
    TRUSTED_IMPORT_REVALIDATED = "TRUSTED_IMPORT_REVALIDATED"
    CHAIN_AUDITED = "CHAIN_AUDITED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    ERROR = "ERROR"


_TRUTH_PROMOTING_BOUNDARIES = {
    VerifierBoundaryKind.FINITE_CHECKED,
    VerifierBoundaryKind.LEAN_TYPECHECKED,
    VerifierBoundaryKind.COQ_CHECKED,
    VerifierBoundaryKind.ISABELLE_CHECKED,
    VerifierBoundaryKind.SMT_CHECKED,
    VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
    VerifierBoundaryKind.CHAIN_AUDITED,
}

_PROOF_BOUNDARIES = {
    VerifierBoundaryKind.LEAN_TYPECHECKED,
    VerifierBoundaryKind.COQ_CHECKED,
    VerifierBoundaryKind.ISABELLE_CHECKED,
    VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
    VerifierBoundaryKind.CHAIN_AUDITED,
}

_REFUTATION_BOUNDARIES = {
    VerifierBoundaryKind.FINITE_CHECKED,
    VerifierBoundaryKind.SMT_CHECKED,
    VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
    VerifierBoundaryKind.CHAIN_AUDITED,
}


def _enum_value(value: str | Enum | None) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value or "")


def terminal_form_from_legacy(value: str) -> CanonicalTerminalForm:
    normalized = _enum_value(value).strip().upper()
    if normalized == "VERIFIED_PROOF":
        return CanonicalTerminalForm.VERIFIED_PROOF
    if normalized in {"FINITE_COUNTERMODEL", "REFUTATION_CERTIFICATE"}:
        return CanonicalTerminalForm.REFUTATION_CERTIFICATE
    if normalized == "NAMED_OBSTRUCTION":
        return CanonicalTerminalForm.NAMED_OBSTRUCTION
    if normalized == "NONE":
        return CanonicalTerminalForm.NONE
    return CanonicalTerminalForm.NONE


def refutation_kind_from_legacy(value: str | None) -> RefutationKind:
    normalized = _enum_value(value).strip().upper()
    if normalized == "FINITE_COUNTERMODEL":
        return RefutationKind.FINITE_COUNTERMODEL
    return RefutationKind.UNKNOWN


def verifier_boundary_from_value(value: str | VerifierBoundaryKind) -> VerifierBoundaryKind:
    normalized = _enum_value(value).strip().upper()
    for boundary in VerifierBoundaryKind:
        if normalized == boundary.value:
            return boundary
    return VerifierBoundaryKind.NOT_VERIFIED


def is_truth_promoting_boundary(boundary: str) -> bool:
    return verifier_boundary_from_value(boundary) in _TRUTH_PROMOTING_BOUNDARIES


def can_promote_terminal_form(
    terminal_form: str,
    trust_level: str,
    verifier_boundary: str,
    certificate_id: str | None = None,
) -> bool:
    form = terminal_form_from_legacy(terminal_form)
    boundary = verifier_boundary_from_value(verifier_boundary)
    has_certificate = bool(certificate_id)
    if form == CanonicalTerminalForm.VERIFIED_PROOF:
        return has_certificate and boundary in _PROOF_BOUNDARIES
    if form == CanonicalTerminalForm.REFUTATION_CERTIFICATE:
        return has_certificate and boundary in _REFUTATION_BOUNDARIES
    if form == CanonicalTerminalForm.NAMED_OBSTRUCTION:
        trust = _enum_value(trust_level).upper()
        proof_or_refutation_words = (
            "VERIFIED_PROOF",
            "REFUTATION",
            "FINITE_COUNTERMODEL",
            "SMT_CHECKED",
            "LEAN_TYPECHECKED",
            "COQ_CHECKED",
            "ISABELLE_CHECKED",
        )
        return not any(word in trust for word in proof_or_refutation_words)
    return False

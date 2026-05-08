"""Stable public terminal-form contract for MathGraph boundary responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class TerminalForm:
    VERIFIED_PROOF = "VERIFIED_PROOF"
    REFUTATION_CERTIFICATE = "REFUTATION_CERTIFICATE"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"
    NONE = "NONE"


class TrustLevel:
    ADVISORY_ROUTE = "ADVISORY_ROUTE"
    CANDIDATE_CERTIFICATE = "CANDIDATE_CERTIFICATE"
    BOUNDED_CERT = "BOUNDED_CERT"
    FINITE_VERIFIED = "FINITE_VERIFIED"
    DERIVED_CHAIN_VERIFIED = "DERIVED_CHAIN_VERIFIED"
    LEAN_VERIFIED = "LEAN_VERIFIED"
    ERROR = "ERROR"


class ProvenanceType:
    PRIMITIVE = "PRIMITIVE"
    DERIVED = "DERIVED"
    IMPORTED = "IMPORTED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    ADVISORY = "ADVISORY"
    SYSTEM = "SYSTEM"


class VerifierBoundary:
    NOT_VERIFIED = "NOT_VERIFIED"
    FINITE_CHECKED = "FINITE_CHECKED"
    IMPORTER_REVALIDATED = "IMPORTER_REVALIDATED"
    CHAIN_AUDITED = "CHAIN_AUDITED"
    LEAN_TYPECHECKED = "LEAN_TYPECHECKED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    ERROR = "ERROR"


class Status:
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    OBSTRUCTED = "OBSTRUCTED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"
    KNOWN_CERTIFICATE_FOUND = "KNOWN_CERTIFICATE_FOUND"
    VERIFIED_FALSE = "VERIFIED_FALSE"
    VERIFIED_TRUE = "VERIFIED_TRUE"
    CONSTRUCTOR_FAILED = "CONSTRUCTOR_FAILED"
    PARSE_FAILED = "PARSE_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    RESIDUAL = "RESIDUAL"


_VERIFIED_STATUSES = {Status.VERIFIED, Status.VERIFIED_TRUE}
_REFUTED_STATUSES = {Status.REFUTED, Status.VERIFIED_FALSE, Status.KNOWN_CERTIFICATE_FOUND}
_FAILURE_STATUSES = {
    Status.CONSTRUCTOR_FAILED,
    Status.PARSE_FAILED,
    Status.VERIFICATION_FAILED,
    Status.RESIDUAL,
    Status.UNKNOWN,
    Status.OBSTRUCTED,
    Status.ERROR,
}


@dataclass(frozen=True)
class TerminalContractResult:
    status: str
    terminal_form: str
    trust_level: str
    provenance_type: str
    verifier_boundary: str
    certificate_id: str | None
    certificate_chain: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "terminal_form": self.terminal_form,
            "trust_level": self.trust_level,
            "provenance_type": self.provenance_type,
            "verifier_boundary": self.verifier_boundary,
            "certificate_id": self.certificate_id,
            "certificate_chain": list(self.certificate_chain),
            "warnings": list(self.warnings),
            "evidence": dict(self.evidence),
        }

    def _validate(self) -> None:
        if self.status in _VERIFIED_STATUSES and self.trust_level == TrustLevel.ADVISORY_ROUTE:
            raise ValueError("verified result cannot have advisory trust")
        if self.status in _REFUTED_STATUSES and self.trust_level == TrustLevel.CANDIDATE_CERTIFICATE:
            raise ValueError("refuted result cannot rely on candidate certificate trust")
        if self.status == Status.VERIFIED_TRUE and self.trust_level == TrustLevel.FINITE_VERIFIED:
            raise ValueError("ETP TRUE results cannot be finite-verified refutations")
        if self.status in {Status.CONSTRUCTOR_FAILED, Status.PARSE_FAILED, Status.VERIFICATION_FAILED, Status.RESIDUAL}:
            if self.trust_level in {TrustLevel.FINITE_VERIFIED, TrustLevel.LEAN_VERIFIED, TrustLevel.DERIVED_CHAIN_VERIFIED}:
                raise ValueError("failed/residual result cannot have verified trust")
        if self.status == "no_countermodel_found" and self.terminal_form == TerminalForm.VERIFIED_PROOF:
            raise ValueError("finite search miss is not a proof")
        if self.terminal_form == TerminalForm.REFUTATION_CERTIFICATE and not self.certificate_id:
            raise ValueError("refutation certificate requires certificate_id")
        if self.trust_level == TrustLevel.FINITE_VERIFIED and self.verifier_boundary not in {
            VerifierBoundary.IMPORTER_REVALIDATED,
            VerifierBoundary.FINITE_CHECKED,
        }:
            raise ValueError("finite verified trust requires finite checked or importer revalidated boundary")
        if self.terminal_form == TerminalForm.REFUTATION_CERTIFICATE and self.trust_level not in {
            TrustLevel.FINITE_VERIFIED,
            TrustLevel.DERIVED_CHAIN_VERIFIED,
        }:
            raise ValueError("refutation certificate requires verified finite/derived trust")
        if self.terminal_form == TerminalForm.VERIFIED_PROOF and self.verifier_boundary != VerifierBoundary.LEAN_TYPECHECKED:
            raise ValueError("verified proof requires Lean typechecked boundary")
        if self.status in _FAILURE_STATUSES and self.terminal_form == TerminalForm.REFUTATION_CERTIFICATE:
            raise ValueError("failure/unknown status cannot expose refutation terminal form")


"""Advisory envelopes for outputs produced by external verifier tools."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.terminal_schema import (
    CanonicalTerminalForm,
    RefutationKind,
    VerifierBoundaryKind,
)


class ExternalVerifierKind(str, Enum):
    LEAN4 = "LEAN4"
    LEAN3 = "LEAN3"
    ISABELLE = "ISABELLE"
    COQ = "COQ"
    Z3 = "Z3"
    CVC5 = "CVC5"
    MINISAT = "MINISAT"
    VAMPIRE = "VAMPIRE"
    E_PROVER = "E_PROVER"
    AGDA = "AGDA"
    PYTHON_FINITE_CHECKER = "PYTHON_FINITE_CHECKER"
    UNKNOWN = "UNKNOWN"


class ExternalCertificateStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COUNTERMODEL_FOUND = "COUNTERMODEL_FOUND"
    UNSAT = "UNSAT"
    SAT = "SAT"
    TIMEOUT = "TIMEOUT"
    PARSE_ERROR = "PARSE_ERROR"
    UNSUPPORTED = "UNSUPPORTED"
    PENDING = "PENDING"
    ERROR = "ERROR"


_PROOF_ASSISTANTS = {
    ExternalVerifierKind.LEAN4,
    ExternalVerifierKind.LEAN3,
    ExternalVerifierKind.ISABELLE,
    ExternalVerifierKind.COQ,
    ExternalVerifierKind.AGDA,
}

_SMT_SOLVERS = {ExternalVerifierKind.Z3, ExternalVerifierKind.CVC5}


def _parse_enum(enum_cls: type[Enum], value: Any, default: Enum) -> Enum:
    if isinstance(value, enum_cls):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    for item in enum_cls:
        if text == item.name or text == str(item.value).upper():
            return item
    return default


@dataclass
class ExternalCertificate:
    cert_id: str
    verifier: ExternalVerifierKind
    status: ExternalCertificateStatus
    claim: str
    claim_hash: str
    artifact_uri: str | None = None
    proof_artifact: str | None = None
    countermodel: dict[str, Any] | None = None
    verifier_version: str = ""
    elapsed_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def __post_init__(self) -> None:
        self.verifier = _parse_enum(ExternalVerifierKind, self.verifier, ExternalVerifierKind.UNKNOWN)  # type: ignore[assignment]
        self.status = _parse_enum(ExternalCertificateStatus, self.status, ExternalCertificateStatus.ERROR)  # type: ignore[assignment]
        self.advisory = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "cert_id": self.cert_id,
            "verifier": self.verifier.value,
            "status": self.status.value,
            "claim": self.claim,
            "claim_hash": self.claim_hash,
            "artifact_uri": self.artifact_uri,
            "proof_artifact": self.proof_artifact,
            "countermodel": self.countermodel,
            "verifier_version": self.verifier_version,
            "elapsed_seconds": self.elapsed_seconds,
            "metadata": dict(self.metadata),
            "advisory": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExternalCertificate":
        cert_id = str(data.get("cert_id") or content_id("external_cert", data))
        return cls(
            cert_id=cert_id,
            verifier=_parse_enum(ExternalVerifierKind, data.get("verifier"), ExternalVerifierKind.UNKNOWN),  # type: ignore[arg-type]
            status=_parse_enum(ExternalCertificateStatus, data.get("status"), ExternalCertificateStatus.ERROR),  # type: ignore[arg-type]
            claim=str(data.get("claim", "")),
            claim_hash=str(data.get("claim_hash", "")),
            artifact_uri=data.get("artifact_uri"),
            proof_artifact=data.get("proof_artifact"),
            countermodel=data.get("countermodel"),
            verifier_version=str(data.get("verifier_version", "")),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0) or 0.0),
            metadata=dict(data.get("metadata", {})),
            advisory=True,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "ExternalCertificate":
        return cls.from_dict(json.loads(text))

    def candidate_terminal_form(self) -> CanonicalTerminalForm:
        if self.status == ExternalCertificateStatus.PENDING:
            return CanonicalTerminalForm.NONE
        if self.status in {
            ExternalCertificateStatus.TIMEOUT,
            ExternalCertificateStatus.PARSE_ERROR,
            ExternalCertificateStatus.UNSUPPORTED,
            ExternalCertificateStatus.ERROR,
        }:
            return CanonicalTerminalForm.NAMED_OBSTRUCTION
        if self.status == ExternalCertificateStatus.ACCEPTED and self.verifier in _PROOF_ASSISTANTS:
            return CanonicalTerminalForm.VERIFIED_PROOF
        if self.status == ExternalCertificateStatus.UNSAT:
            if self.verifier in _PROOF_ASSISTANTS:
                return CanonicalTerminalForm.VERIFIED_PROOF
            if self.verifier in _SMT_SOLVERS and self.metadata.get("unsat_proves_claim") is True:
                return CanonicalTerminalForm.VERIFIED_PROOF
            return CanonicalTerminalForm.NAMED_OBSTRUCTION
        if self.status in {
            ExternalCertificateStatus.REJECTED,
            ExternalCertificateStatus.COUNTERMODEL_FOUND,
            ExternalCertificateStatus.SAT,
        } and self.countermodel:
            return CanonicalTerminalForm.REFUTATION_CERTIFICATE
        return CanonicalTerminalForm.NAMED_OBSTRUCTION

    def candidate_refutation_kind(self) -> RefutationKind:
        if self.candidate_terminal_form() != CanonicalTerminalForm.REFUTATION_CERTIFICATE:
            return RefutationKind.UNKNOWN
        if self.verifier == ExternalVerifierKind.PYTHON_FINITE_CHECKER:
            return RefutationKind.FINITE_COUNTERMODEL
        if self.verifier in _SMT_SOLVERS:
            return RefutationKind.SMT_COUNTERMODEL
        if self.verifier == ExternalVerifierKind.MINISAT:
            return RefutationKind.SAT_ASSIGNMENT
        return RefutationKind.EXTERNAL_COUNTERMODEL

    def to_candidate_payload(self) -> dict[str, Any]:
        return {
            "external_cert_id": self.cert_id,
            "candidate_terminal_form": self.candidate_terminal_form().value,
            "candidate_refutation_kind": self.candidate_refutation_kind().value,
            "claim": self.claim,
            "claim_hash": self.claim_hash,
            "verifier": self.verifier.value,
            "status": self.status.value,
            "advisory": True,
            "can_cross_verifier_boundary": False,
            "metadata": dict(self.metadata),
        }


@dataclass
class ExternalCertificateImportDecision:
    decision_id: str
    external_cert_id: str
    accepted_for_replay: bool
    required_boundary: VerifierBoundaryKind
    candidate_terminal_form: CanonicalTerminalForm
    warnings: tuple[str, ...]
    criticals: tuple[str, ...]
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "external_cert_id": self.external_cert_id,
            "accepted_for_replay": self.accepted_for_replay,
            "required_boundary": self.required_boundary.value,
            "candidate_terminal_form": self.candidate_terminal_form.value,
            "warnings": list(self.warnings),
            "criticals": list(self.criticals),
            "advisory": True,
        }


def plan_external_certificate_import(cert: ExternalCertificate) -> ExternalCertificateImportDecision:
    form = cert.candidate_terminal_form()
    warnings = ["External certificate is advisory until replayed, imported, or revalidated."]
    criticals: list[str] = []
    required = VerifierBoundaryKind.NOT_VERIFIED
    if form == CanonicalTerminalForm.VERIFIED_PROOF:
        if cert.verifier in {ExternalVerifierKind.LEAN4, ExternalVerifierKind.LEAN3}:
            required = VerifierBoundaryKind.LEAN_TYPECHECKED
        elif cert.verifier == ExternalVerifierKind.COQ:
            required = VerifierBoundaryKind.COQ_CHECKED
        elif cert.verifier == ExternalVerifierKind.ISABELLE:
            required = VerifierBoundaryKind.ISABELLE_CHECKED
        else:
            required = VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED
    elif form == CanonicalTerminalForm.REFUTATION_CERTIFICATE:
        if cert.verifier == ExternalVerifierKind.PYTHON_FINITE_CHECKER:
            required = VerifierBoundaryKind.FINITE_CHECKED
        elif cert.verifier in _SMT_SOLVERS or cert.verifier == ExternalVerifierKind.MINISAT:
            required = VerifierBoundaryKind.SMT_CHECKED
        else:
            required = VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED
    elif form == CanonicalTerminalForm.NAMED_OBSTRUCTION:
        required = VerifierBoundaryKind.ADVISORY_ONLY
    accepted = form != CanonicalTerminalForm.NONE
    return ExternalCertificateImportDecision(
        decision_id=content_id("external_cert_import_decision", cert.to_dict()),
        external_cert_id=cert.cert_id,
        accepted_for_replay=accepted,
        required_boundary=required,
        candidate_terminal_form=form,
        warnings=tuple(warnings),
        criticals=tuple(criticals),
        advisory=True,
    )

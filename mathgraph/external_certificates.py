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
    LEAN = "LEAN"
    LEAN4 = "LEAN4"
    LEAN3 = "LEAN3"
    ISABELLE = "ISABELLE"
    COQ = "COQ"
    FINITE_COUNTERMODEL_CHECKER = "FINITE_COUNTERMODEL_CHECKER"
    SMT = "SMT"
    SAT = "SAT"
    PYTHON_PROPERTY_CHECKER = "PYTHON_PROPERTY_CHECKER"
    TRUSTED_IMPORTER = "TRUSTED_IMPORTER"
    CHAIN_AUDIT = "CHAIN_AUDIT"
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


class ExternalCertificateKind(str, Enum):
    VERIFIED_PROOF = "VERIFIED_PROOF"
    REFUTATION_CERTIFICATE = "REFUTATION_CERTIFICATE"
    FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"
    SMT_MODEL = "SMT_MODEL"
    SAT_ASSIGNMENT = "SAT_ASSIGNMENT"
    EXECUTION_COUNTEREXAMPLE = "EXECUTION_COUNTEREXAMPLE"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"
    ADVISORY_ONLY = "ADVISORY_ONLY"


@dataclass(frozen=True)
class ExternalBoundaryEvidence:
    evidence_id: str
    boundary_kind: VerifierBoundaryKind
    certificate_id: str
    terminal_form: CanonicalTerminalForm
    source_artifact_id: str | None = None
    artifact_hash: str | None = None
    raw_output_hash: str | None = None
    verifier_kind: ExternalVerifierKind = ExternalVerifierKind.UNKNOWN
    checker_name: str = ""
    checker_version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary_kind", _parse_enum(VerifierBoundaryKind, self.boundary_kind, VerifierBoundaryKind.NOT_VERIFIED))
        object.__setattr__(self, "terminal_form", _parse_enum(CanonicalTerminalForm, self.terminal_form, CanonicalTerminalForm.NONE))
        object.__setattr__(self, "verifier_kind", _parse_enum(ExternalVerifierKind, self.verifier_kind, ExternalVerifierKind.UNKNOWN))

    def is_valid_boundary(self) -> bool:
        return bool(
            self.certificate_id
            and self.terminal_form != CanonicalTerminalForm.NONE
            and self.boundary_kind
            in {
                VerifierBoundaryKind.FINITE_CHECKED,
                VerifierBoundaryKind.LEAN_TYPECHECKED,
                VerifierBoundaryKind.COQ_CHECKED,
                VerifierBoundaryKind.ISABELLE_CHECKED,
                VerifierBoundaryKind.SMT_CHECKED,
                VerifierBoundaryKind.TRUSTED_IMPORT_REVALIDATED,
                VerifierBoundaryKind.CHAIN_AUDITED,
            }
            and (self.artifact_hash or self.raw_output_hash or self.source_artifact_id)
            and not self.advisory
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "boundary_kind": self.boundary_kind.value,
            "certificate_id": self.certificate_id,
            "terminal_form": self.terminal_form.value,
            "source_artifact_id": self.source_artifact_id,
            "artifact_hash": self.artifact_hash,
            "raw_output_hash": self.raw_output_hash,
            "verifier_kind": self.verifier_kind.value,
            "checker_name": self.checker_name,
            "checker_version": self.checker_version,
            "metadata": dict(self.metadata),
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExternalBoundaryEvidence":
        return cls(
            evidence_id=str(data.get("evidence_id") or content_id("external_boundary_evidence", data)),
            boundary_kind=_parse_enum(VerifierBoundaryKind, data.get("boundary_kind"), VerifierBoundaryKind.NOT_VERIFIED),  # type: ignore[arg-type]
            certificate_id=str(data.get("certificate_id", "")),
            terminal_form=_parse_enum(CanonicalTerminalForm, data.get("terminal_form"), CanonicalTerminalForm.NONE),  # type: ignore[arg-type]
            source_artifact_id=data.get("source_artifact_id"),
            artifact_hash=data.get("artifact_hash"),
            raw_output_hash=data.get("raw_output_hash"),
            verifier_kind=_parse_enum(ExternalVerifierKind, data.get("verifier_kind"), ExternalVerifierKind.UNKNOWN),  # type: ignore[arg-type]
            checker_name=str(data.get("checker_name", "")),
            checker_version=str(data.get("checker_version", "")),
            metadata=dict(data.get("metadata", {})),
            advisory=bool(data.get("advisory", False)),
        )


_PROOF_ASSISTANTS = {
    ExternalVerifierKind.LEAN,
    ExternalVerifierKind.LEAN4,
    ExternalVerifierKind.LEAN3,
    ExternalVerifierKind.ISABELLE,
    ExternalVerifierKind.COQ,
    ExternalVerifierKind.AGDA,
}

_SMT_SOLVERS = {ExternalVerifierKind.Z3, ExternalVerifierKind.CVC5, ExternalVerifierKind.SMT}


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
    source_artifact_id: str | None = None
    certificate_kind: ExternalCertificateKind | None = None
    proposed_terminal_form: CanonicalTerminalForm | None = None
    boundary_evidence: ExternalBoundaryEvidence | None = None
    raw_output_hash: str | None = None
    artifact_hash: str | None = None
    replay_command: tuple[str, ...] = ()
    checker_name: str = ""
    checker_version: str = ""
    artifact_uri: str | None = None
    proof_artifact: str | None = None
    countermodel: dict[str, Any] | None = None
    verifier_version: str = ""
    elapsed_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True
    advisory_only: bool = True
    boundary_valid: bool = False
    accepted: bool = False

    def __post_init__(self) -> None:
        self.verifier = _parse_enum(ExternalVerifierKind, self.verifier, ExternalVerifierKind.UNKNOWN)  # type: ignore[assignment]
        self.status = _parse_enum(ExternalCertificateStatus, self.status, ExternalCertificateStatus.ERROR)  # type: ignore[assignment]
        if self.certificate_kind is not None:
            self.certificate_kind = _parse_enum(ExternalCertificateKind, self.certificate_kind, ExternalCertificateKind.ADVISORY_ONLY)  # type: ignore[assignment]
        if self.proposed_terminal_form is not None:
            self.proposed_terminal_form = _parse_enum(CanonicalTerminalForm, self.proposed_terminal_form, CanonicalTerminalForm.NONE)  # type: ignore[assignment]
        if self.boundary_evidence is not None and not isinstance(self.boundary_evidence, ExternalBoundaryEvidence):
            self.boundary_evidence = ExternalBoundaryEvidence.from_dict(dict(self.boundary_evidence))  # type: ignore[assignment]
        self.boundary_valid = bool(self.boundary_valid and self.boundary_evidence and self.boundary_evidence.is_valid_boundary())
        self.accepted = bool(self.accepted and self.boundary_valid)
        self.advisory_only = not self.accepted
        self.advisory = True
        if self.accepted and not self.boundary_valid:
            self.accepted = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "cert_id": self.cert_id,
            "certificate_id": self.cert_id,
            "verifier": self.verifier.value,
            "status": self.status.value,
            "claim": self.claim,
            "claim_hash": self.claim_hash,
            "source_artifact_id": self.source_artifact_id,
            "certificate_kind": self.certificate_kind.value if self.certificate_kind else None,
            "proposed_terminal_form": self.proposed_terminal_form.value if self.proposed_terminal_form else None,
            "boundary_evidence": self.boundary_evidence.to_dict() if self.boundary_evidence else None,
            "raw_output_hash": self.raw_output_hash,
            "artifact_hash": self.artifact_hash,
            "replay_command": list(self.replay_command),
            "checker_name": self.checker_name,
            "checker_version": self.checker_version,
            "artifact_uri": self.artifact_uri,
            "proof_artifact": self.proof_artifact,
            "countermodel": self.countermodel,
            "verifier_version": self.verifier_version,
            "elapsed_seconds": self.elapsed_seconds,
            "metadata": dict(self.metadata),
            "advisory": True,
            "advisory_only": self.advisory_only,
            "boundary_valid": self.boundary_valid,
            "accepted": self.accepted,
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
            source_artifact_id=data.get("source_artifact_id"),
            certificate_kind=_parse_enum(ExternalCertificateKind, data.get("certificate_kind"), ExternalCertificateKind.ADVISORY_ONLY) if data.get("certificate_kind") else None,  # type: ignore[arg-type]
            proposed_terminal_form=_parse_enum(CanonicalTerminalForm, data.get("proposed_terminal_form"), CanonicalTerminalForm.NONE) if data.get("proposed_terminal_form") else None,  # type: ignore[arg-type]
            boundary_evidence=ExternalBoundaryEvidence.from_dict(data["boundary_evidence"]) if data.get("boundary_evidence") else None,
            raw_output_hash=data.get("raw_output_hash"),
            artifact_hash=data.get("artifact_hash"),
            replay_command=tuple(data.get("replay_command", ()) or ()),
            checker_name=str(data.get("checker_name", "")),
            checker_version=str(data.get("checker_version", "")),
            artifact_uri=data.get("artifact_uri"),
            proof_artifact=data.get("proof_artifact"),
            countermodel=data.get("countermodel"),
            verifier_version=str(data.get("verifier_version", "")),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0) or 0.0),
            metadata=dict(data.get("metadata", {})),
            advisory=True,
            advisory_only=bool(data.get("advisory_only", True)),
            boundary_valid=bool(data.get("boundary_valid", False)),
            accepted=bool(data.get("accepted", False)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "ExternalCertificate":
        return cls.from_dict(json.loads(text))

    def candidate_terminal_form(self) -> CanonicalTerminalForm:
        if self.proposed_terminal_form is not None:
            return self.proposed_terminal_form
        if self.certificate_kind == ExternalCertificateKind.VERIFIED_PROOF:
            return CanonicalTerminalForm.VERIFIED_PROOF
        if self.certificate_kind in {
            ExternalCertificateKind.REFUTATION_CERTIFICATE,
            ExternalCertificateKind.FINITE_COUNTERMODEL,
            ExternalCertificateKind.SMT_MODEL,
            ExternalCertificateKind.SAT_ASSIGNMENT,
            ExternalCertificateKind.EXECUTION_COUNTEREXAMPLE,
        }:
            return CanonicalTerminalForm.REFUTATION_CERTIFICATE
        if self.certificate_kind == ExternalCertificateKind.NAMED_OBSTRUCTION:
            return CanonicalTerminalForm.NAMED_OBSTRUCTION
        if self.certificate_kind == ExternalCertificateKind.ADVISORY_ONLY:
            return CanonicalTerminalForm.NONE
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
        if self.certificate_kind == ExternalCertificateKind.FINITE_COUNTERMODEL:
            return RefutationKind.FINITE_COUNTERMODEL
        if self.certificate_kind == ExternalCertificateKind.SAT_ASSIGNMENT:
            return RefutationKind.SAT_ASSIGNMENT
        if self.verifier in {ExternalVerifierKind.PYTHON_FINITE_CHECKER, ExternalVerifierKind.FINITE_COUNTERMODEL_CHECKER}:
            return RefutationKind.FINITE_COUNTERMODEL
        if self.verifier in _SMT_SOLVERS:
            return RefutationKind.SMT_COUNTERMODEL
        if self.verifier in {ExternalVerifierKind.MINISAT, ExternalVerifierKind.SAT}:
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

    @property
    def certificate_id(self) -> str:
        return self.cert_id

    def with_gate_acceptance(self) -> "ExternalCertificate":
        data = self.to_dict()
        data["accepted"] = True
        data["boundary_valid"] = bool(self.boundary_evidence and self.boundary_evidence.is_valid_boundary())
        data["advisory_only"] = not data["boundary_valid"]
        return ExternalCertificate.from_dict(data)


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
        if cert.verifier in {ExternalVerifierKind.LEAN, ExternalVerifierKind.LEAN4, ExternalVerifierKind.LEAN3}:
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

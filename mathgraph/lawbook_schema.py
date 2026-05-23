"""Canonical Lawbook schema adapters.

These dataclasses are intentionally small.  They provide a stable façade for
new Lawbook code while preserving the older LawbookStore and certificate
objects behind it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any

from mathgraph.terminal_schema import CanonicalTerminalForm, terminal_form_from_legacy


class TerminalForm(str, Enum):
    VERIFIED_PROOF = "VERIFIED_PROOF"
    FINITE_COUNTERMODEL = "FINITE_COUNTERMODEL"
    REFUTATION_CERTIFICATE = "REFUTATION_CERTIFICATE"
    NAMED_OBSTRUCTION = "NAMED_OBSTRUCTION"
    NONE = "NONE"


class TrustLevel(IntEnum):
    REJECTED = 0
    ADVISORY = 10
    CANDIDATE = 40
    BOUNDED_VERIFIED = 70
    VERIFIED = 100


class ProvenanceType(str, Enum):
    UNKNOWN = "unknown"
    FINITE_CHECKER = "finite_checker"
    PROOF_CHECKER = "proof_checker"
    TRUSTED_IMPORTER = "trusted_importer"
    CHAIN_AUDIT = "chain_audit"
    ADVISORY_TRACE = "advisory_trace"


class BoundaryEvidenceType(str, Enum):
    NONE = "none"
    FINITE_CHECKED = "finite_checked"
    LEAN_TYPECHECKED = "lean_typechecked"
    TRUSTED_IMPORT = "trusted_import"
    CHAIN_AUDIT = "chain_audit"
    OBSTRUCTION_AUDIT = "obstruction_audit"


@dataclass(frozen=True)
class LawbookArtifact:
    artifact_id: str
    claim_id: str = ""
    domain: str = ""
    source_id: str = ""
    target_id: str = ""
    terminal_form: TerminalForm = TerminalForm.NONE
    trust_level: TrustLevel = TrustLevel.ADVISORY
    provenance_type: ProvenanceType = ProvenanceType.UNKNOWN
    boundary_evidence_type: BoundaryEvidenceType = BoundaryEvidenceType.NONE
    payload: dict[str, Any] = field(default_factory=dict)
    advisory_only: bool = True

    def to_store_row(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "claim_id": self.claim_id,
            "domain": self.domain,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "terminal_form": self.terminal_form.value,
            "trust_level": int(self.trust_level),
            "provenance_type": self.provenance_type.value,
            "boundary_type": self.boundary_evidence_type.value,
            "payload": dict(self.payload),
            "durable": int(self.trust_level) >= int(TrustLevel.VERIFIED) and not self.advisory_only,
        }


@dataclass(frozen=True)
class LawbookAdmissionDecision:
    accepted: bool
    reason: str
    advisory_only: bool = True
    terminal_form: TerminalForm = TerminalForm.NONE
    boundary_evidence_type: BoundaryEvidenceType = BoundaryEvidenceType.NONE
    can_promote_truth: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "advisory_only": self.advisory_only,
            "terminal_form": self.terminal_form.value,
            "boundary_evidence_type": self.boundary_evidence_type.value,
            "can_promote_truth": self.can_promote_truth,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LawbookQuery:
    claim_id: str | None = None
    source_id: str | None = None
    target_id: str | None = None
    domain: str | None = None
    terminal_form: TerminalForm | str | None = None
    limit: int = 100


@dataclass(frozen=True)
class LawbookQueryResult:
    rows: tuple[dict[str, Any], ...]
    query: LawbookQuery

    @property
    def count(self) -> int:
        return len(self.rows)


def normalize_terminal_form(value: Any) -> TerminalForm:
    if isinstance(value, TerminalForm):
        return value
    form = terminal_form_from_legacy(str(value or ""))
    if form == CanonicalTerminalForm.VERIFIED_PROOF:
        return TerminalForm.VERIFIED_PROOF
    if form == CanonicalTerminalForm.REFUTATION_CERTIFICATE:
        text = str(value or "").upper()
        return TerminalForm.FINITE_COUNTERMODEL if text == "FINITE_COUNTERMODEL" else TerminalForm.REFUTATION_CERTIFICATE
    if form == CanonicalTerminalForm.NAMED_OBSTRUCTION:
        return TerminalForm.NAMED_OBSTRUCTION
    return TerminalForm.NONE

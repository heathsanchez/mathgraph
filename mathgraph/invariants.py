"""Executable trust-boundary invariants for MathGraph.

These checks are intentionally lightweight and conservative.  They do not
verify mathematics; they verify that accepted MathGraph claims carry exactly one
terminal form and replayable boundary evidence, and that advisory artifacts do
not promote truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, is_dataclass, asdict
from enum import Enum
from typing import Any, Iterable

from mathgraph.certificates import TerminalForm


class ClaimStatus(str, Enum):
    ADVISORY = "ADVISORY"
    CANDIDATE = "CANDIDATE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class TrustBoundaryEvidence:
    evidence_id: str = ""
    verifier_boundary: str = ""
    evidence_type: str = ""
    replayable: bool = False
    advisory: bool = True
    artifact_hashes: tuple[str, ...] = ()
    command_contract_hash: str = ""
    expected_theorem: str = ""
    witness_checked: bool = False
    source_satisfied: bool = False
    target_violated: bool = False
    obstruction_id: str = ""
    structured_obstruction: bool = False
    provenance: tuple[str, ...] = ()
    raw_returncode_only: bool = False
    artifact_text: str = ""
    derived_from: tuple[str, ...] = ()
    trust_level: int = 0

    @classmethod
    def from_any(cls, value: Any) -> "TrustBoundaryEvidence":
        if isinstance(value, cls):
            return value
        data = _asdict(value)
        return cls(
            evidence_id=str(data.get("evidence_id", "")),
            verifier_boundary=str(data.get("verifier_boundary", data.get("boundary_type", ""))),
            evidence_type=str(data.get("evidence_type", "")),
            replayable=bool(data.get("replayable", False)),
            advisory=bool(data.get("advisory", data.get("advisory_only", True))),
            artifact_hashes=tuple(str(x) for x in data.get("artifact_hashes", ()) or ()),
            command_contract_hash=str(data.get("command_contract_hash", "")),
            expected_theorem=str(data.get("expected_theorem", data.get("theorem_name", ""))),
            witness_checked=bool(data.get("witness_checked", False)),
            source_satisfied=bool(data.get("source_satisfied", data.get("source_satisfied_global", False))),
            target_violated=bool(data.get("target_violated", data.get("target_violated_at_witness", False))),
            obstruction_id=str(data.get("obstruction_id", "")),
            structured_obstruction=bool(data.get("structured_obstruction", False)),
            provenance=tuple(str(x) for x in data.get("provenance", ()) or ()),
            raw_returncode_only=bool(data.get("raw_returncode_only", False)),
            artifact_text=str(data.get("artifact_text", "")),
            derived_from=tuple(str(x) for x in data.get("derived_from", ()) or ()),
            trust_level=int(data.get("trust_level", 0) or 0),
        )


@dataclass(frozen=True)
class InvariantViolation:
    code: str
    message: str
    severity: str = "error"
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "severity": self.severity, "context": dict(self.context)}


@dataclass(frozen=True)
class LawbookEntryInvariantReport:
    ok: bool
    violations: tuple[InvariantViolation, ...] = ()
    warnings: tuple[InvariantViolation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
        }


UNSAFE_LEAN_RE = re.compile(r"(^|[^A-Za-z0-9_])(sorry|admit|axiom|unsafe)([^A-Za-z0-9_]|$)")


def check_terminal_form_contract(entry: Any) -> LawbookEntryInvariantReport:
    data = _asdict(entry)
    if _status(data) != ClaimStatus.ACCEPTED:
        return _report([])
    forms = _terminal_forms(data)
    if len(forms) != 1:
        return _report([_violation("terminal_form_count", "Accepted claim must have exactly one terminal form.", {"forms": forms})])
    if forms[0] not in {form.value for form in TerminalForm}:
        return _report([_violation("invalid_terminal_form", "Accepted claim terminal form is not allowed.", {"terminal_form": forms[0]})])
    return _report([])


def check_no_advisory_truth_promotion(entry: Any) -> LawbookEntryInvariantReport:
    data = _asdict(entry)
    if _is_truth_terminal(data) and bool(data.get("advisory", data.get("advisory_only", False))):
        return _report([_violation("advisory_truth_promotion", "Advisory artifacts may guide search but cannot promote terminal truth.")])
    source = str(data.get("source", data.get("artifact_kind", data.get("route", "")))).lower()
    if _is_truth_terminal(data) and any(word in source for word in ("route_score", "htilt", "model_output", "semantic_intake", "explanation")):
        return _report([_violation("advisory_source_truth_promotion", "Advisory scoring/explanation source attempted terminal promotion.", {"source": source})])
    return _report([])


def check_finite_failure_not_true(entry: Any) -> LawbookEntryInvariantReport:
    data = _asdict(entry)
    failed = bool(data.get("finite_search_failed", data.get("finite_search_miss", False)))
    if failed and (str(data.get("truth_value", "")).upper() == "TRUE" or str(data.get("terminal_form", "")).upper() == TerminalForm.VERIFIED_PROOF.value):
        return _report([_violation("finite_failure_as_truth", "Finite-search failure is residual evidence, not proof of truth.")])
    return _report([])


def check_boundary_evidence_required(entry: Any, evidence: Any = None) -> LawbookEntryInvariantReport:
    data = _asdict(entry)
    ev = TrustBoundaryEvidence.from_any(evidence if evidence is not None else data.get("boundary_evidence", data.get("evidence", {})))
    if not _is_truth_terminal(data):
        return _report([])
    violations: list[InvariantViolation] = []
    if ev.advisory:
        violations.append(_violation("boundary_advisory", "Boundary evidence for terminal claims cannot be advisory."))
    if not ev.replayable:
        violations.append(_violation("boundary_not_replayable", "Accepted terminal claims require replayable evidence."))
    if ev.raw_returncode_only:
        violations.append(_violation("raw_returncode_only", "Raw success text or returncode is not boundary evidence."))
    terminal = str(data.get("terminal_form", "")).upper()
    if terminal == TerminalForm.FINITE_COUNTERMODEL.value and not (ev.witness_checked and ev.source_satisfied and ev.target_violated):
        violations.append(_violation("finite_countermodel_unchecked", "Finite countermodel requires checked source, target violation, and witness."))
    if terminal == TerminalForm.VERIFIED_PROOF.value and not (ev.expected_theorem or ev.command_contract_hash):
        violations.append(_violation("proof_boundary_incomplete", "Verified proof requires expected theorem or safe command contract evidence."))
    if terminal == TerminalForm.NAMED_OBSTRUCTION.value and not (ev.obstruction_id and ev.structured_obstruction):
        violations.append(_violation("obstruction_unstructured", "Named obstruction requires structured obstruction evidence."))
    return _report(violations)


def check_unsafe_artifact_rejected(artifact: Any) -> LawbookEntryInvariantReport:
    data = _asdict(artifact)
    text = str(data.get("artifact_text", data.get("proof_text", data.get("payload", ""))))
    if UNSAFE_LEAN_RE.search(text):
        return _report([_violation("unsafe_lean_marker", "Unsafe Lean marker cannot create boundary evidence.", {"marker_text": text[:120]})])
    return _report([])


def check_lawbook_entry_replayable(entry: Any, manifest: Any = None) -> LawbookEntryInvariantReport:
    data = _asdict(entry)
    if not _is_truth_terminal(data):
        return _report([])
    manifest_data = _asdict(manifest if manifest is not None else data.get("replay_manifest", {}))
    if not manifest_data or not manifest_data.get("replay_instructions"):
        return _report([_violation("missing_replay_manifest", "Accepted Lawbook entry requires replay instructions.")])
    if not manifest_data.get("artifact_hashes"):
        return _report([_violation("missing_artifact_hashes", "Replay manifest requires artifact hashes.")])
    return _report([])


def check_provenance_preserved(entry: Any) -> LawbookEntryInvariantReport:
    data = _asdict(entry)
    if not _is_truth_terminal(data):
        return _report([])
    provenance = data.get("provenance", ())
    derived = data.get("derived", False) or str(data.get("artifact_kind", "")).lower().startswith("derived")
    if not provenance:
        return _report([_violation("missing_provenance", "Accepted terminal artifacts must preserve provenance.")])
    if derived and not data.get("derived_from"):
        return _report([_violation("derived_missing_sources", "Derived certificates must preserve source certificate provenance.")])
    return _report([])


def check_all_core_invariants(entry: Any, evidence: Any = None, manifest: Any = None) -> LawbookEntryInvariantReport:
    reports = [
        check_terminal_form_contract(entry),
        check_no_advisory_truth_promotion(entry),
        check_finite_failure_not_true(entry),
        check_boundary_evidence_required(entry, evidence),
        check_unsafe_artifact_rejected(evidence if evidence is not None else entry),
        check_lawbook_entry_replayable(entry, manifest),
        check_provenance_preserved(entry),
    ]
    violations = tuple(v for report in reports for v in report.violations)
    warnings = tuple(w for report in reports for w in report.warnings)
    return LawbookEntryInvariantReport(ok=not violations, violations=violations, warnings=warnings)


def has_terminal_form(certificate: Any) -> bool:
    """Backward-compatible helper retained for older tests."""

    try:
        from mathgraph.certificates import Certificate
        from mathgraph.verification import verify_certificate

        if isinstance(certificate, Certificate):
            verify_certificate(certificate)
            return True
    except Exception:
        pass
    return check_terminal_form_contract(certificate).ok


def _asdict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if is_dataclass(value):
        return dict(asdict(value))
    if isinstance(value, dict):
        return dict(value)
    return dict(getattr(value, "__dict__", {}))


def _terminal_forms(data: dict[str, Any]) -> list[str]:
    forms = data.get("terminal_forms")
    if forms is not None:
        return [str(x).upper() for x in forms if str(x)]
    form = data.get("terminal_form")
    return [str(form).upper()] if form else []


def _status(data: dict[str, Any]) -> ClaimStatus:
    text = str(data.get("status", data.get("claim_status", ""))).upper()
    return ClaimStatus.ACCEPTED if text == "ACCEPTED" or data.get("accepted") is True else ClaimStatus(text) if text in ClaimStatus.__members__ else ClaimStatus.CANDIDATE


def _is_truth_terminal(data: dict[str, Any]) -> bool:
    return bool(set(_terminal_forms(data)) & {form.value for form in TerminalForm})


def _violation(code: str, message: str, context: dict[str, Any] | None = None) -> InvariantViolation:
    return InvariantViolation(code=code, message=message, context=dict(context or {}))


def _report(violations: Iterable[InvariantViolation]) -> LawbookEntryInvariantReport:
    items = tuple(violations)
    return LawbookEntryInvariantReport(ok=not items, violations=items)

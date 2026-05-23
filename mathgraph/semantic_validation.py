"""Semantic validation boundary between informal claims and formal artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mathgraph.hashing import sha256_hex


class SemanticValidationStatus(str, Enum):
    MISSING = "MISSING"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    PARTIAL = "PARTIAL"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class InformalClaim:
    claim_id: str
    text: str
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"claim_id": self.claim_id, "text": self.text, "source_ref": self.source_ref, "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class FormalClaim:
    claim_id: str
    statement: str
    formal_system: str = "mathgraph.finite_magma_world"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"claim_id": self.claim_id, "statement": self.statement, "formal_system": self.formal_system, "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class TranslationAssumption:
    assumption_id: str
    description: str
    status: str = "ASSUMED"

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class SemanticValidationEvidence:
    evidence_id: str
    evidence_type: str
    description: str = ""
    reviewer: str = ""
    model_generated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "description": self.description,
            "reviewer": self.reviewer,
            "model_generated": self.model_generated,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SemanticValidationViolation:
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "context": dict(self.context)}


@dataclass(frozen=True)
class SemanticValidationReport:
    status: SemanticValidationStatus
    ok: bool
    violations: tuple[SemanticValidationViolation, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    assumptions: tuple[TranslationAssumption, ...] = ()
    informal_claim_id: str = ""
    formal_claim_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
            "evidence_refs": list(self.evidence_refs),
            "translation_assumptions": [a.to_dict() for a in self.assumptions],
            "informal_claim_id": self.informal_claim_id,
            "formal_claim_id": self.formal_claim_id,
        }

    def stable_hash(self) -> str:
        return sha256_hex(self.to_dict())


VALIDATION_EVIDENCE_TYPES = {
    "human_review",
    "roundtrip_translation",
    "examples_or_test_cases",
    "counterexample_search",
    "theorem_statement_match",
    "domain_schema_match",
    "source_document_reference",
    "formal_definition_alignment",
}


def validate_claim_translation(
    informal: InformalClaim | dict[str, Any] | None,
    formal: FormalClaim | dict[str, Any] | None,
    *,
    evidence: tuple[SemanticValidationEvidence, ...] = (),
    assumptions: tuple[TranslationAssumption, ...] = (),
    model_generated: bool = False,
) -> SemanticValidationReport:
    informal_data = _asdict(informal)
    formal_data = _asdict(formal)
    violations: list[SemanticValidationViolation] = []
    if not informal_data.get("claim_id") or not informal_data.get("text"):
        violations.append(_violation("informal_claim_missing", "Semantic validation requires an informal claim."))
    if not formal_data.get("claim_id") or not formal_data.get("statement"):
        violations.append(_violation("formal_claim_missing", "Semantic validation requires a formal claim."))
    bad_evidence = [ev.evidence_type for ev in evidence if ev.evidence_type not in VALIDATION_EVIDENCE_TYPES]
    if bad_evidence:
        violations.append(_violation("unknown_validation_evidence", "Semantic validation evidence type is not recognized.", {"types": bad_evidence}))
    if model_generated and not evidence:
        return SemanticValidationReport(
            status=SemanticValidationStatus.ADVISORY_ONLY,
            ok=False,
            violations=tuple(violations + [_violation("model_translation_advisory", "Model-generated translations are advisory until validated.")]),
            evidence_refs=(),
            assumptions=assumptions,
            informal_claim_id=str(informal_data.get("claim_id", "")),
            formal_claim_id=str(formal_data.get("claim_id", "")),
        )
    if violations:
        status = SemanticValidationStatus.REJECTED
    elif any(ev.model_generated for ev in evidence) and not any(ev.evidence_type == "human_review" for ev in evidence):
        status = SemanticValidationStatus.PARTIAL
    elif evidence:
        status = SemanticValidationStatus.VALIDATED
    else:
        status = SemanticValidationStatus.MISSING
    return SemanticValidationReport(
        status=status,
        ok=status == SemanticValidationStatus.VALIDATED,
        violations=tuple(violations),
        evidence_refs=tuple(ev.evidence_id for ev in evidence),
        assumptions=assumptions,
        informal_claim_id=str(informal_data.get("claim_id", "")),
        formal_claim_id=str(formal_data.get("claim_id", "")),
    )


def check_semantic_validation_required(entry: Any, report: SemanticValidationReport | dict[str, Any] | None = None) -> SemanticValidationReport:
    data = _asdict(entry)
    has_informal = bool(data.get("informal_claim_id") or data.get("metadata", {}).get("informal_claim_id"))
    claims_solution = bool(data.get("claims_informal_solution") or data.get("metadata", {}).get("claims_informal_solution"))
    current = _report_from_any(report)
    if not has_informal:
        return SemanticValidationReport(SemanticValidationStatus.MISSING, True)
    if current.status in {SemanticValidationStatus.MISSING, SemanticValidationStatus.ADVISORY_ONLY, SemanticValidationStatus.PARTIAL} and claims_solution:
        return SemanticValidationReport(
            status=current.status,
            ok=False,
            violations=(_violation("informal_solution_without_validation", "Informal-claim solution requires semantic validation."),),
            evidence_refs=current.evidence_refs,
            assumptions=current.assumptions,
            informal_claim_id=current.informal_claim_id,
            formal_claim_id=current.formal_claim_id,
        )
    if current.status == SemanticValidationStatus.REJECTED and claims_solution:
        return SemanticValidationReport(
            status=current.status,
            ok=False,
            violations=(_violation("semantic_validation_rejected", "Rejected semantic validation blocks claiming the informal statement was solved."),),
            evidence_refs=current.evidence_refs,
            assumptions=current.assumptions,
            informal_claim_id=current.informal_claim_id,
            formal_claim_id=current.formal_claim_id,
        )
    return current


def check_model_translation_not_truth(payload: Any) -> SemanticValidationReport:
    data = _asdict(payload)
    if data.get("model_generated_translation") and data.get("claims_truth"):
        return SemanticValidationReport(
            SemanticValidationStatus.ADVISORY_ONLY,
            False,
            (_violation("model_translation_truth", "Model-generated translations cannot promote truth."),),
        )
    return SemanticValidationReport(SemanticValidationStatus.MISSING, True)


def check_formal_verification_not_informal_solution(payload: Any) -> SemanticValidationReport:
    data = _asdict(payload)
    if data.get("formal_verified") and data.get("claims_informal_solution") and data.get("semantic_validation_status") != SemanticValidationStatus.VALIDATED.value:
        return SemanticValidationReport(
            SemanticValidationStatus(str(data.get("semantic_validation_status") or "MISSING")),
            False,
            (_violation("formal_verification_not_informal_solution", "Formal verification alone does not validate the intended informal claim."),),
        )
    return SemanticValidationReport(SemanticValidationStatus(str(data.get("semantic_validation_status") or "MISSING")), True)


def semantic_validation_report(*args: Any, **kwargs: Any) -> SemanticValidationReport:
    return validate_claim_translation(*args, **kwargs)


def attach_semantic_validation_to_manifest(manifest: Any, report: SemanticValidationReport) -> Any:
    from dataclasses import replace

    return replace(
        manifest,
        informal_claim_id=report.informal_claim_id,
        formal_claim_id=report.formal_claim_id,
        semantic_validation_status=report.status,
        semantic_validation_evidence_refs=report.evidence_refs,
        translation_assumptions=tuple(a.to_dict() for a in report.assumptions),
        validation_report_hash=report.stable_hash(),
    )


def _report_from_any(value: SemanticValidationReport | dict[str, Any] | None) -> SemanticValidationReport:
    if isinstance(value, SemanticValidationReport):
        return value
    data = _asdict(value)
    return SemanticValidationReport(
        status=SemanticValidationStatus(str(data.get("status", data.get("semantic_validation_status", "MISSING")))),
        ok=bool(data.get("ok", False)),
        evidence_refs=tuple(str(x) for x in data.get("evidence_refs", data.get("semantic_validation_evidence_refs", ())) or ()),
        assumptions=tuple(TranslationAssumption(str(x.get("assumption_id", "")), str(x.get("description", "")), str(x.get("status", "ASSUMED"))) for x in data.get("translation_assumptions", ()) if isinstance(x, dict)),
        informal_claim_id=str(data.get("informal_claim_id", "")),
        formal_claim_id=str(data.get("formal_claim_id", "")),
    )


def _asdict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if isinstance(value, dict):
        return dict(value)
    return dict(getattr(value, "__dict__", {}))


def _violation(code: str, message: str, context: dict[str, Any] | None = None) -> SemanticValidationViolation:
    return SemanticValidationViolation(code, message, dict(context or {}))

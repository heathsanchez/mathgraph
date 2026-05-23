"""Lawbook acceptance contract built on existing Lawbook and invariant types."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from mathgraph.certificates import TerminalForm
from mathgraph.evidence_manifest import EvidenceManifest
from mathgraph.evidence_replay import replay_evidence_manifest
from mathgraph.invariants import (
    InvariantViolation,
    LawbookEntryInvariantReport,
    TrustBoundaryEvidence,
    check_all_core_invariants,
)
from mathgraph.lawbook import (
    LawbookAcceptanceBoundary,
    LawbookEntry,
    LawbookEntryKind,
    LawbookEntryStatus,
    make_lawbook_entry_id,
)
from mathgraph.semantic_validation import (
    SemanticValidationReport,
    SemanticValidationStatus,
    check_semantic_validation_required,
)


@dataclass(frozen=True)
class LawbookAcceptanceResult:
    ok: bool
    entry: LawbookEntry | None = None
    invariant_report: LawbookEntryInvariantReport | None = None
    violations: tuple[InvariantViolation, ...] = ()
    accepted: bool = False
    replay_ok: bool = False
    reason_codes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "accepted": self.accepted,
            "replay_ok": self.replay_ok,
            "reason_codes": list(self.reason_codes),
            "violations": [v.to_dict() for v in self.violations],
            "entry": self.entry.to_dict() if self.entry else None,
            "metadata": dict(self.metadata),
        }


def lawbook_entry_from_evidence_manifest(
    manifest: EvidenceManifest,
    *,
    evidence: TrustBoundaryEvidence | None = None,
    entry_id: str | None = None,
    source: str | None = None,
    target: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> LawbookEntry:
    terminal = manifest.terminal_form
    return LawbookEntry(
        entry_id=entry_id or make_lawbook_entry_id("manifest", manifest.claim_id, manifest.stable_hash()),
        kind=_kind_for_terminal(terminal),
        status=LawbookEntryStatus.CANDIDATE,
        claim_id=manifest.claim_id,
        source=source,
        target=target,
        terminal_form=terminal,
        certificate_id=manifest.stable_hash(),
        verifier_boundary_crossed=evidence is not None and not evidence.advisory,
        acceptance_boundary=_boundary_for_terminal(terminal),
        artifact_ids=tuple(manifest.artifact_hashes),
        provenance={"manifest": manifest.to_dict(), "refs": list(manifest.provenance)},
        metadata=dict(metadata or {}),
        advisory=False,
    )


def validate_lawbook_acceptance(
    entry: LawbookEntry | dict[str, Any],
    *,
    manifest: EvidenceManifest | dict[str, Any] | None,
    evidence: TrustBoundaryEvidence | dict[str, Any] | None,
    require_replay: bool = True,
    manifest_path: str | None = None,
) -> LawbookAcceptanceResult:
    entry_obj = entry if isinstance(entry, LawbookEntry) else LawbookEntry.from_dict(entry)
    violations: list[InvariantViolation] = []
    reason_codes: list[str] = []
    manifest_obj: EvidenceManifest | None = None
    evidence_obj = TrustBoundaryEvidence.from_any(evidence)

    if manifest is None:
        violations.append(_violation("missing_evidence_manifest", "Lawbook acceptance requires an EvidenceManifest."))
    else:
        try:
            manifest_obj = manifest if isinstance(manifest, EvidenceManifest) else EvidenceManifest.from_dict(dict(manifest))
        except Exception as exc:
            violations.append(_violation("invalid_evidence_manifest", f"EvidenceManifest failed validation: {exc}"))

    if manifest_obj is not None:
        if entry_obj.claim_id != manifest_obj.claim_id:
            violations.append(_violation("claim_id_mismatch", "Lawbook entry claim_id must match manifest claim_id."))
        if entry_obj.terminal_form != manifest_obj.terminal_form:
            violations.append(_violation("terminal_form_mismatch", "Lawbook entry terminal_form must match manifest terminal_form."))
        semantic_report = _semantic_report_from_manifest(manifest_obj, entry_obj)
        semantic_check = check_semantic_validation_required({**entry_obj.to_dict(), "metadata": entry_obj.metadata}, semantic_report)
        violations.extend(_semantic_violations(semantic_check))
    else:
        semantic_report = SemanticValidationReport(SemanticValidationStatus.MISSING, True)

    if entry_obj.advisory:
        violations.append(_violation("advisory_lawbook_truth", "Advisory entries cannot enter the Lawbook as accepted truth."))
    if _looks_like_reason_atlas_route(entry_obj):
        violations.append(_violation("reason_atlas_truth_promotion", "Reason Atlas routing entries cannot enter the Lawbook as terminal truth."))

    invariant_report = check_all_core_invariants(
        _entry_invariant_payload(entry_obj, manifest_obj),
        evidence_obj,
        manifest_obj,
    )
    violations.extend(invariant_report.violations)
    violations.extend(_derived_guardrail_violations(entry_obj, evidence_obj))

    replay_ok = not require_replay
    replay_details: dict[str, Any] = {}
    if require_replay:
        if not manifest_path:
            violations.append(_violation("replay_path_missing", "Replay requires a manifest path."))
        else:
            replay = replay_evidence_manifest(manifest_path, expected_terminal_form=entry_obj.terminal_form)
            replay_ok = replay.ok
            replay_details = replay.to_dict()
            if not replay.ok:
                violations.append(_violation("replay_failed", "Evidence manifest replay failed.", replay.to_dict()))

    ok = not violations
    if ok:
        reason_codes.append("accepted_replayable_terminal_evidence")
        if semantic_report.status == SemanticValidationStatus.VALIDATED:
            reason_codes.append("semantic_validation_validated")
        else:
            reason_codes.append("formal_only_or_semantic_validation_not_claimed")
    return LawbookAcceptanceResult(
        ok=ok,
        entry=entry_obj,
        invariant_report=invariant_report,
        violations=tuple(violations),
        accepted=ok,
        replay_ok=replay_ok,
        reason_codes=tuple(reason_codes),
        metadata={"replay": replay_details, "semantic_validation": semantic_report.to_dict()},
    )


def check_lawbook_entry_replay_contract(
    entry: LawbookEntry | dict[str, Any],
    *,
    manifest_path: str,
    evidence: TrustBoundaryEvidence | dict[str, Any],
) -> LawbookAcceptanceResult:
    manifest = EvidenceManifest.from_dict(__import__("json").loads(__import__("pathlib").Path(manifest_path).read_text(encoding="utf-8")))
    return validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=manifest_path)


def accept_lawbook_entry(
    entry: LawbookEntry | dict[str, Any],
    *,
    manifest: EvidenceManifest | dict[str, Any],
    evidence: TrustBoundaryEvidence | dict[str, Any],
    manifest_path: str,
    accepted_by: str = "mathgraph.lawbook_acceptance",
) -> LawbookEntry:
    result = validate_lawbook_acceptance(entry, manifest=manifest, evidence=evidence, manifest_path=manifest_path)
    if not result.ok or result.entry is None:
        raise ValueError("lawbook acceptance rejected: " + ",".join(v.code for v in result.violations))
    return replace(
        result.entry,
        status=LawbookEntryStatus.ACCEPTED,
        accepted_at=datetime.now(timezone.utc).isoformat(),
        accepted_by=accepted_by,
        verifier_boundary_crossed=True,
        advisory=False,
    )


def reject_lawbook_entry(entry: LawbookEntry | dict[str, Any], *, reason: str = "") -> LawbookEntry:
    entry_obj = entry if isinstance(entry, LawbookEntry) else LawbookEntry.from_dict(entry)
    return replace(entry_obj, status=LawbookEntryStatus.REJECTED, metadata={**entry_obj.metadata, "rejection_reason": reason})


def _entry_invariant_payload(entry: LawbookEntry, manifest: EvidenceManifest | None) -> dict[str, Any]:
    data = entry.to_dict()
    data["status"] = "ACCEPTED"
    data["accepted"] = True
    data["provenance"] = tuple((entry.provenance or {}).get("refs") or (manifest.provenance if manifest else ()))
    data["replay_manifest"] = manifest.to_dict() if manifest else {}
    return data


def _derived_guardrail_violations(entry: LawbookEntry, evidence: TrustBoundaryEvidence) -> tuple[InvariantViolation, ...]:
    data = entry.to_dict()
    derived = entry.kind == LawbookEntryKind.DERIVED_CERTIFICATE_ENTRY or bool(entry.metadata.get("derived"))
    if not derived:
        return ()
    violations: list[InvariantViolation] = []
    parent_refs = tuple(entry.metadata.get("parent_evidence_refs", ()) or ())
    parent_provenance = tuple(entry.metadata.get("parent_provenance", ()) or ())
    parent_trust = int(entry.metadata.get("parent_trust_level", evidence.trust_level) or 0)
    current_trust = int(entry.metadata.get("trust_level", evidence.trust_level) or 0)
    if not parent_provenance and not data.get("provenance"):
        violations.append(_violation("derived_missing_parent_provenance", "Derived entries must preserve parent provenance."))
    if not parent_refs:
        violations.append(_violation("derived_missing_parent_evidence_refs", "Derived entries must reference parent evidence."))
    if current_trust > parent_trust and evidence.verifier_boundary not in {"chain_audit", "trusted_import", "derived_verified"}:
        violations.append(_violation("derived_trust_upgrade_without_boundary", "Derived entries cannot upgrade trust without verifier/audit evidence."))
    return tuple(violations)


def _semantic_report_from_manifest(manifest: EvidenceManifest, entry: LawbookEntry) -> SemanticValidationReport:
    return SemanticValidationReport(
        status=manifest.semantic_validation_status,
        ok=manifest.semantic_validation_status == SemanticValidationStatus.VALIDATED,
        evidence_refs=manifest.semantic_validation_evidence_refs,
        informal_claim_id=manifest.informal_claim_id or str(entry.metadata.get("informal_claim_id", "")),
        formal_claim_id=manifest.formal_claim_id or manifest.claim_id,
    )


def _semantic_violations(report: SemanticValidationReport) -> tuple[InvariantViolation, ...]:
    return tuple(InvariantViolation(v.code, v.message, context=v.context) for v in report.violations)


def _kind_for_terminal(terminal: TerminalForm) -> LawbookEntryKind:
    return {
        TerminalForm.VERIFIED_PROOF: LawbookEntryKind.VERIFIED_PROOF_ENTRY,
        TerminalForm.FINITE_COUNTERMODEL: LawbookEntryKind.FINITE_COUNTERMODEL_ENTRY,
        TerminalForm.NAMED_OBSTRUCTION: LawbookEntryKind.NAMED_OBSTRUCTION_ENTRY,
    }[terminal]


def _boundary_for_terminal(terminal: TerminalForm) -> LawbookAcceptanceBoundary:
    return {
        TerminalForm.VERIFIED_PROOF: LawbookAcceptanceBoundary.VERIFIED_PROOF,
        TerminalForm.FINITE_COUNTERMODEL: LawbookAcceptanceBoundary.FINITE_COUNTERMODEL,
        TerminalForm.NAMED_OBSTRUCTION: LawbookAcceptanceBoundary.NAMED_OBSTRUCTION,
    }[terminal]


def _looks_like_reason_atlas_route(entry: LawbookEntry) -> bool:
    text = " ".join([entry.kind.value, str(entry.metadata.get("reason_type", "")), str(entry.metadata.get("promotion_status", ""))]).lower()
    return "reason_atlas" in text or "route_policy" in text or entry.kind in {LawbookEntryKind.ROUTE_RULE_ENTRY, LawbookEntryKind.BASIN_DETECTOR_ENTRY}


def _violation(code: str, message: str, context: dict[str, Any] | None = None) -> InvariantViolation:
    return InvariantViolation(code=code, message=message, context=dict(context or {}))

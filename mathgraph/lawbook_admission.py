"""Production Lawbook admission gate v0.

The admission gate is deliberately stricter than scheduler feedback and
PromotionGate candidates.  It decides which artifacts may become durable
Lawbook memory and which must remain advisory/candidate run evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence

from mathgraph.hashing import content_id


class AdmissionLevel(str, Enum):
    REJECTED = "rejected"
    ADVISORY_ONLY = "advisory_only"
    CANDIDATE = "candidate"
    BOUNDED_VERIFIED = "bounded_verified"
    FINITE_VERIFIED = "finite_verified"
    LEAN_VERIFIED = "lean_verified"
    DURABLE_LAWBOOK = "durable_lawbook"


class ArtifactKind(str, Enum):
    ADVISORY_ROUTE = "advisory_route"
    REASON_MOTIF = "reason_motif"
    DECODE_CANDIDATE = "decode_candidate"
    FINITE_COUNTERMODEL_CANDIDATE = "finite_countermodel_candidate"
    FINITE_COUNTERMODEL_VERIFIED = "finite_countermodel_verified"
    PROOF_TEMPLATE = "proof_template"
    LEAN_PROOF_VERIFIED = "lean_proof_verified"
    NAMED_OBSTRUCTION = "named_obstruction"
    DERIVED_CERTIFICATE = "derived_certificate"
    FALLBACK_SMOKE_ARTIFACT = "fallback_smoke_artifact"
    FAILED_FINITE_SEARCH = "failed_finite_search"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AdmissionEvidence:
    verifier_passed: bool = False
    source_satisfied: bool = False
    target_violated: bool = False
    concrete_witness: Any | None = None
    carrier_size: int | None = None
    lean_verified: bool = False
    proof_artifact: Any | None = None
    replayable: bool = False
    bounded: bool = False
    provenance: Any | None = None
    fallback_only: bool = False
    decode_success: bool = False
    linked_verified_artifact: bool = False
    obstruction_name: str = ""
    failure_trace: Any | None = None
    scope: str = ""
    supporting_failed_routes: int = 0
    verifier_backed_negative: bool = False
    failed_finite_search: bool = False
    claims_true: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_any(cls, value: Any) -> "AdmissionEvidence":
        if isinstance(value, cls):
            return value
        data = dict(value or {})
        return cls(
            verifier_passed=bool(data.get("verifier_passed", data.get("promotion_gate_accepted", False))),
            source_satisfied=bool(data.get("source_satisfied", data.get("source_satisfied_global", False))),
            target_violated=bool(data.get("target_violated", data.get("target_violated_at_witness", False))),
            concrete_witness=data.get("concrete_witness", data.get("witness_env")),
            carrier_size=_maybe_int(data.get("carrier_size")),
            lean_verified=bool(data.get("lean_verified", False)),
            proof_artifact=data.get("proof_artifact"),
            replayable=bool(data.get("replayable", data.get("replay_status") in {"replayable", "passed"})),
            bounded=bool(data.get("bounded", False)),
            provenance=data.get("provenance", data.get("provenance_type", data.get("source_artifact_id"))),
            fallback_only=bool(data.get("fallback_only", data.get("fallback_mode", False))),
            decode_success=bool(data.get("decode_success", False)),
            linked_verified_artifact=bool(data.get("linked_verified_artifact", False)),
            obstruction_name=str(data.get("obstruction_name", data.get("obstruction_type", "")) or ""),
            failure_trace=data.get("failure_trace", data.get("evidence")),
            scope=str(data.get("scope", data.get("basin", "")) or ""),
            supporting_failed_routes=int(data.get("supporting_failed_routes", 0) or 0),
            verifier_backed_negative=bool(data.get("verifier_backed_negative", False)),
            failed_finite_search=bool(data.get("failed_finite_search", data.get("finite_search_miss", False))),
            claims_true=bool(data.get("claims_true", data.get("terminal_form") in {"TRUE", "VERIFIED_PROOF"} and data.get("failed_finite_search", False))),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class AdmissionDecision:
    artifact_id: str
    artifact_kind: str
    admission_level: AdmissionLevel
    durable: bool
    accepted: bool
    reason_codes: list[str]
    evidence_summary: dict[str, Any]
    required_next_steps: list[str]
    advisory_boundary_preserved: bool
    may_influence_scheduler: bool
    may_enter_lawbook_attention: bool
    may_enter_durable_lawbook: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind,
            "admission_level": self.admission_level.value,
            "durable": self.durable,
            "accepted": self.accepted,
            "reason_codes": list(self.reason_codes),
            "evidence_summary": dict(self.evidence_summary),
            "required_next_steps": list(self.required_next_steps),
            "advisory_boundary_preserved": self.advisory_boundary_preserved,
            "may_influence_scheduler": self.may_influence_scheduler,
            "may_enter_lawbook_attention": self.may_enter_lawbook_attention,
            "may_enter_durable_lawbook": self.may_enter_durable_lawbook,
        }


@dataclass(frozen=True)
class LawbookAdmissionPolicy:
    verified_trust_level: int = 100
    require_replayable_for_durable: bool = True
    strict_provenance: bool = True
    allow_bounded_obstruction_without_replay: bool = True
    allow_advisory_attention: bool = True


class LawbookAdmissionGate:
    def __init__(self, policy: LawbookAdmissionPolicy | None = None) -> None:
        self.policy = policy or LawbookAdmissionPolicy()

    def evaluate_artifact(self, artifact: Any, evidence: Any, policy: LawbookAdmissionPolicy | None = None) -> AdmissionDecision:
        pol = policy or self.policy
        data = _artifact_dict(artifact)
        ev = AdmissionEvidence.from_any({**data, **_artifact_payload(data), **(evidence.to_dict() if hasattr(evidence, "to_dict") else dict(evidence or {}))})
        artifact_id = str(data.get("artifact_id") or content_id("admission-artifact", data))
        kind = _artifact_kind(data)
        reasons: list[str] = []
        steps: list[str] = []
        boundary_ok = True
        if ev.claims_true and ev.failed_finite_search:
            return _decision(artifact_id, kind, AdmissionLevel.REJECTED, ["failed_search_cannot_claim_true"], ["produce verifier proof or countermodel"], ev, False)
        if kind == ArtifactKind.FALLBACK_SMOKE_ARTIFACT or ev.fallback_only:
            return _decision(artifact_id, kind, AdmissionLevel.ADVISORY_ONLY, ["fallback_artifact_blocked_from_durable"], ["rerun on real corpus or verified source"], ev, True, scheduler=True, attention=False)
        if pol.strict_provenance and not ev.provenance:
            if kind in {ArtifactKind.ADVISORY_ROUTE, ArtifactKind.REASON_MOTIF, ArtifactKind.DECODE_CANDIDATE, ArtifactKind.PROOF_TEMPLATE}:
                return _decision(artifact_id, kind, AdmissionLevel.ADVISORY_ONLY, ["missing_provenance"], ["attach provenance before candidate promotion"], ev, True, scheduler=True, attention=False)
            return _decision(artifact_id, kind, AdmissionLevel.REJECTED, ["missing_provenance"], ["attach provenance"], ev, True)
        if kind in {ArtifactKind.FINITE_COUNTERMODEL_VERIFIED, ArtifactKind.FINITE_COUNTERMODEL_CANDIDATE}:
            return self._finite_countermodel_decision(artifact_id, kind, ev, pol)
        if kind == ArtifactKind.LEAN_PROOF_VERIFIED:
            return self._lean_decision(artifact_id, kind, ev, pol)
        if kind == ArtifactKind.NAMED_OBSTRUCTION:
            return self._obstruction_decision(artifact_id, kind, ev, pol)
        if kind == ArtifactKind.REASON_MOTIF:
            if ev.decode_success or ev.linked_verified_artifact:
                level = AdmissionLevel.CANDIDATE
                reasons.append("motif_has_decode_or_verified_link")
                steps.append("attach verifier-backed constructor/proof/obstruction evidence for durability")
                return _decision(artifact_id, kind, level, reasons, steps, ev, boundary_ok, scheduler=True, attention=True)
            return _decision(artifact_id, kind, AdmissionLevel.ADVISORY_ONLY, ["motif_advisory_without_decode_or_verified_link"], ["decode-to-verify on heldout tasks"], ev, boundary_ok, scheduler=True, attention=False)
        if kind == ArtifactKind.DECODE_CANDIDATE:
            if ev.decode_success and ev.linked_verified_artifact:
                return _decision(artifact_id, kind, AdmissionLevel.BOUNDED_VERIFIED, ["decode_success_with_verified_family_link"], ["attach terminal artifact for durable admission"], ev, True, scheduler=True, attention=True)
            if ev.decode_success:
                return _decision(artifact_id, kind, AdmissionLevel.CANDIDATE, ["decode_success_not_durable_without_verified_link"], ["link to verified artifact family"], ev, True, scheduler=True, attention=True)
            return _decision(artifact_id, kind, AdmissionLevel.CANDIDATE, ["decode_candidate_unverified"], ["run decode-to-verify"], ev, True, scheduler=True, attention=False)
        if kind == ArtifactKind.FAILED_FINITE_SEARCH or ev.failed_finite_search:
            return _decision(artifact_id, kind, AdmissionLevel.ADVISORY_ONLY, ["failed_finite_search_is_not_truth"], ["scope repeated failure before naming obstruction"], ev, True, scheduler=True, attention=False)
        return _decision(artifact_id, kind, AdmissionLevel.ADVISORY_ONLY, ["artifact_not_terminal_verified"], ["provide verifier boundary evidence"], ev, True, scheduler=True, attention=False)

    def evaluate_many(self, artifacts: Sequence[Any], evidence_map: dict[str, Any], policy: LawbookAdmissionPolicy | None = None) -> list[AdmissionDecision]:
        out = []
        for artifact in artifacts:
            data = _artifact_dict(artifact)
            artifact_id = str(data.get("artifact_id") or content_id("admission-artifact", data))
            out.append(self.evaluate_artifact(data, evidence_map.get(artifact_id, {}), policy))
        return out

    def admit_to_store(self, store: Any, artifact: Any, decision: AdmissionDecision) -> bool:
        if not decision.accepted:
            return False
        data = _artifact_dict(artifact)
        payload = _artifact_payload(data)
        payload["admission_decision"] = decision.to_dict()
        terminal = ""
        boundary = ""
        trust = 0
        if decision.admission_level == AdmissionLevel.DURABLE_LAWBOOK:
            if decision.artifact_kind == ArtifactKind.LEAN_PROOF_VERIFIED.value:
                terminal = "VERIFIED_PROOF"
                boundary = "proof_checker"
            elif decision.artifact_kind in {ArtifactKind.FINITE_COUNTERMODEL_VERIFIED.value, ArtifactKind.FINITE_COUNTERMODEL_CANDIDATE.value}:
                terminal = "FINITE_COUNTERMODEL"
                boundary = "finite_model_checker"
            elif decision.artifact_kind == ArtifactKind.NAMED_OBSTRUCTION.value:
                terminal = "NAMED_OBSTRUCTION"
                boundary = "obstruction_audit"
            trust = 100
        else:
            terminal = str(data.get("terminal_form") or "ADVISORY")
            if terminal in {"VERIFIED_PROOF", "FINITE_COUNTERMODEL", "NAMED_OBSTRUCTION"}:
                terminal = "ADVISORY"
        store.insert_artifact(
            {
                **data,
                "terminal_form": terminal,
                "trust_level": trust,
                "boundary_type": boundary,
                "payload": payload,
                "admission_level": decision.admission_level.value,
                "durable": decision.durable,
                "admission_reason_codes": decision.reason_codes,
                "artifact_kind": decision.artifact_kind,
                "replay_status": "replayable" if decision.evidence_summary.get("replayable") else "",
            }
        )
        return True

    def summarize_decisions(self, decisions: Sequence[AdmissionDecision]) -> dict[str, Any]:
        summary = {
            "total_artifacts_reviewed": len(decisions),
            "promoted_durable_count": 0,
            "finite_verified_count": 0,
            "lean_verified_count": 0,
            "named_obstruction_count": 0,
            "advisory_only_count": 0,
            "candidate_count": 0,
            "rejected_count": 0,
            "fallback_artifacts_blocked_count": 0,
            "boundary_violations_blocked_count": 0,
            "missing_provenance_blocked_count": 0,
            "failed_search_true_blocked_count": 0,
            "advisory_boundary_preserved": all(d.advisory_boundary_preserved for d in decisions),
        }
        for decision in decisions:
            if decision.durable:
                summary["promoted_durable_count"] += 1
            if decision.admission_level == AdmissionLevel.FINITE_VERIFIED or (decision.durable and decision.artifact_kind == ArtifactKind.FINITE_COUNTERMODEL_VERIFIED.value):
                summary["finite_verified_count"] += 1
            if decision.admission_level == AdmissionLevel.LEAN_VERIFIED or (decision.durable and decision.artifact_kind == ArtifactKind.LEAN_PROOF_VERIFIED.value):
                summary["lean_verified_count"] += 1
            if decision.artifact_kind == ArtifactKind.NAMED_OBSTRUCTION.value and decision.accepted:
                summary["named_obstruction_count"] += 1
            if decision.admission_level == AdmissionLevel.ADVISORY_ONLY:
                summary["advisory_only_count"] += 1
            if decision.admission_level == AdmissionLevel.CANDIDATE:
                summary["candidate_count"] += 1
            if decision.admission_level == AdmissionLevel.REJECTED:
                summary["rejected_count"] += 1
            codes = set(decision.reason_codes)
            summary["fallback_artifacts_blocked_count"] += int("fallback_artifact_blocked_from_durable" in codes)
            summary["boundary_violations_blocked_count"] += int("missing_finite_countermodel_boundary_evidence" in codes or "missing_lean_boundary_evidence" in codes)
            summary["missing_provenance_blocked_count"] += int("missing_provenance" in codes)
            summary["failed_search_true_blocked_count"] += int("failed_search_cannot_claim_true" in codes)
        return summary

    def _finite_countermodel_decision(self, artifact_id: str, kind: ArtifactKind, ev: AdmissionEvidence, pol: LawbookAdmissionPolicy) -> AdmissionDecision:
        missing = []
        for flag, code in (
            (ev.verifier_passed, "verifier_passed"),
            (ev.source_satisfied, "source_satisfied"),
            (ev.target_violated, "target_violated"),
            (ev.concrete_witness is not None, "concrete_witness"),
            (ev.carrier_size is not None, "carrier_size"),
            (ev.replayable or not pol.require_replayable_for_durable, "replayable"),
            (bool(ev.provenance), "provenance"),
        ):
            if not flag:
                missing.append(code)
        if not missing:
            return _decision(artifact_id, ArtifactKind.FINITE_COUNTERMODEL_VERIFIED, AdmissionLevel.DURABLE_LAWBOOK, ["finite_countermodel_durable"], [], ev, True, scheduler=True, attention=True, durable=True)
        if ev.verifier_passed and ev.source_satisfied and ev.target_violated:
            return _decision(artifact_id, kind, AdmissionLevel.FINITE_VERIFIED, ["finite_countermodel_verified_but_not_durable", *[f"missing_{m}" for m in missing]], [f"provide {m}" for m in missing], ev, True, scheduler=True, attention=True)
        return _decision(artifact_id, kind, AdmissionLevel.CANDIDATE, ["missing_finite_countermodel_boundary_evidence", *[f"missing_{m}" for m in missing]], ["run finite model checker and replay"], ev, True, scheduler=True, attention=False)

    def _lean_decision(self, artifact_id: str, kind: ArtifactKind, ev: AdmissionEvidence, pol: LawbookAdmissionPolicy) -> AdmissionDecision:
        missing = []
        for flag, code in (
            (ev.lean_verified, "lean_verified"),
            (ev.proof_artifact is not None, "proof_artifact"),
            (ev.replayable or not pol.require_replayable_for_durable, "replayable"),
            (bool(ev.provenance), "provenance"),
        ):
            if not flag:
                missing.append(code)
        if not missing:
            return _decision(artifact_id, kind, AdmissionLevel.DURABLE_LAWBOOK, ["lean_proof_durable"], [], ev, True, scheduler=True, attention=True, durable=True)
        return _decision(artifact_id, kind, AdmissionLevel.CANDIDATE, ["missing_lean_boundary_evidence", *[f"missing_{m}" for m in missing]], [f"provide {m}" for m in missing], ev, True, scheduler=True, attention=False)

    def _obstruction_decision(self, artifact_id: str, kind: ArtifactKind, ev: AdmissionEvidence, pol: LawbookAdmissionPolicy) -> AdmissionDecision:
        supported = ev.supporting_failed_routes > 0 or ev.verifier_backed_negative
        bounded_ok = ev.replayable or (pol.allow_bounded_obstruction_without_replay and ev.bounded)
        missing = []
        if not ev.obstruction_name:
            missing.append("obstruction_name")
        if ev.failure_trace is None:
            missing.append("failure_trace")
        if not ev.scope:
            missing.append("scope")
        if not supported:
            missing.append("supporting_failed_route_or_verifier_negative")
        if not bounded_ok:
            missing.append("replayable_or_bounded")
        if not missing:
            return _decision(artifact_id, kind, AdmissionLevel.DURABLE_LAWBOOK, ["named_obstruction_durable"], [], ev, True, scheduler=True, attention=True, durable=True)
        return _decision(artifact_id, kind, AdmissionLevel.CANDIDATE, ["named_obstruction_missing_scope_or_evidence", *[f"missing_{m}" for m in missing]], [f"provide {m}" for m in missing], ev, True, scheduler=True, attention=False)


def _decision(
    artifact_id: str,
    kind: ArtifactKind,
    level: AdmissionLevel,
    reasons: list[str],
    steps: list[str],
    ev: AdmissionEvidence,
    boundary_ok: bool,
    *,
    scheduler: bool = False,
    attention: bool = False,
    durable: bool = False,
) -> AdmissionDecision:
    return AdmissionDecision(
        artifact_id=artifact_id,
        artifact_kind=kind.value,
        admission_level=level,
        durable=durable,
        accepted=level != AdmissionLevel.REJECTED,
        reason_codes=reasons,
        evidence_summary=ev.to_dict(),
        required_next_steps=steps,
        advisory_boundary_preserved=boundary_ok,
        may_influence_scheduler=scheduler or level != AdmissionLevel.REJECTED,
        may_enter_lawbook_attention=attention or durable,
        may_enter_durable_lawbook=durable,
    )


def _artifact_dict(artifact: Any) -> dict[str, Any]:
    if hasattr(artifact, "to_dict"):
        return dict(artifact.to_dict())
    return dict(artifact or {})


def _artifact_payload(data: dict[str, Any]) -> dict[str, Any]:
    payload = data.get("payload", data.get("payload_json", {})) or {}
    return dict(payload) if isinstance(payload, dict) else {}


def _artifact_kind(data: dict[str, Any]) -> ArtifactKind:
    text = str(data.get("artifact_kind", "") or "").strip().lower()
    if not text:
        payload = _artifact_payload(data)
        if data.get("fallback_mode") or payload.get("fallback_mode"):
            text = "fallback_smoke_artifact"
        elif data.get("failed_finite_search") or payload.get("finite_search_miss"):
            text = "failed_finite_search"
        elif data.get("terminal_form") == "FINITE_COUNTERMODEL":
            text = "finite_countermodel_verified"
        elif data.get("terminal_form") == "VERIFIED_PROOF":
            text = "lean_proof_verified"
        elif data.get("terminal_form") == "NAMED_OBSTRUCTION":
            text = "named_obstruction"
        else:
            text = "unknown"
    for kind in ArtifactKind:
        if text == kind.value:
            return kind
    return ArtifactKind.UNKNOWN


def _maybe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except Exception:
        return None


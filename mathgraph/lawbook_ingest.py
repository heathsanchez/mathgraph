"""Canonical Lawbook ingest helpers.

These helpers keep terminal admission behind ``lawbook_boundary`` and delegate
storage to the existing LawbookStore façade when a store is supplied.
"""

from __future__ import annotations

from typing import Any

from mathgraph.hashing import content_id
from mathgraph.lawbook_boundary import evaluate_lawbook_admission
from mathgraph.lawbook_schema import TrustLevel


def ingest_external_certificate(store: Any, certificate: Any, *, domain: str = "", claim_id: str = "") -> dict[str, Any]:
    decision = evaluate_lawbook_admission(certificate)
    row = _row_from_candidate(certificate, decision, domain=domain, claim_id=claim_id)
    if store is not None and hasattr(store, "insert_artifact"):
        store.insert_artifact(row)
    return {"decision": decision.to_dict(), "artifact": row}


def ingest_promotion_gate_candidate(store: Any, candidate: Any, **kwargs: Any) -> dict[str, Any]:
    return ingest_external_certificate(store, candidate, **kwargs)


def ingest_named_obstruction(store: Any, obstruction: dict[str, Any], *, domain: str = "", claim_id: str = "") -> dict[str, Any]:
    row = {
        "artifact_id": obstruction.get("artifact_id") or content_id("named-obstruction", obstruction),
        "domain": domain or obstruction.get("domain", ""),
        "claim_id": claim_id or obstruction.get("claim_id", ""),
        "terminal_form": "NAMED_OBSTRUCTION",
        "trust_level": int(TrustLevel.CANDIDATE),
        "artifact_kind": "named_obstruction",
        "payload": dict(obstruction),
    }
    if store is not None and hasattr(store, "insert_artifact"):
        store.insert_artifact(row)
    return {"decision": {"accepted": True, "reason": "named_obstruction_candidate"}, "artifact": row}


def ingest_derived_closure_artifact(store: Any, artifact: dict[str, Any], *, parent_evidence_refs: list[str] | None = None) -> dict[str, Any]:
    refs = list(parent_evidence_refs or artifact.get("parent_evidence_refs", []) or [])
    row = dict(artifact)
    row.setdefault("artifact_id", content_id("derived-closure-artifact", row))
    row.setdefault("artifact_kind", "derived_certificate")
    row.setdefault("trust_level", int(TrustLevel.CANDIDATE if refs else TrustLevel.ADVISORY))
    row.setdefault("payload", {})
    row["payload"] = {**dict(row.get("payload", {})), "parent_evidence_refs": refs}
    row["terminal_form"] = "ADVISORY"
    if store is not None and hasattr(store, "insert_artifact"):
        store.insert_artifact(row)
    return {"decision": {"accepted": bool(refs), "reason": "derived_requires_parent_evidence"}, "artifact": row}


def reject_advisory_artifact(artifact: Any, reason: str = "advisory_artifact_not_terminal") -> dict[str, Any]:
    return {"accepted": False, "reason": reason, "advisory_only": True, "artifact": artifact}


def _row_from_candidate(candidate: Any, decision: Any, *, domain: str, claim_id: str) -> dict[str, Any]:
    data = candidate.to_dict() if hasattr(candidate, "to_dict") else dict(getattr(candidate, "__dict__", {}) or {})
    terminal = decision.terminal_form.value if decision.accepted else "ADVISORY"
    if terminal == "REFUTATION_CERTIFICATE":
        terminal = "FINITE_COUNTERMODEL"
    boundary_type = decision.boundary_evidence_type.value
    if boundary_type == "finite_checked":
        boundary_type = "finite_model_checker"
    elif boundary_type == "lean_typechecked":
        boundary_type = "proof_checker"
    return {
        "artifact_id": data.get("cert_id") or data.get("artifact_id") or content_id("lawbook-ingest", data),
        "domain": domain,
        "claim_id": claim_id or data.get("source_artifact_id", ""),
        "terminal_form": terminal,
        "trust_level": int(TrustLevel.VERIFIED if decision.accepted else TrustLevel.ADVISORY),
        "provenance_type": data.get("verifier", ""),
        "boundary_type": boundary_type,
        "payload": data,
        "artifact_kind": data.get("certificate_kind", "external_certificate"),
        "durable": bool(decision.accepted),
        "admission_level": "finite_verified" if terminal in {"FINITE_COUNTERMODEL", "REFUTATION_CERTIFICATE"} else ("lean_verified" if terminal == "VERIFIED_PROOF" else "advisory_only"),
    }

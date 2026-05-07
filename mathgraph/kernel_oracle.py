"""Read-only query oracle over a persistent LawbookStore."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mathgraph.lawbook_store import LawbookStore


@dataclass(frozen=True)
class OracleAnswer:
    status: str
    terminal_form: str
    verification_status: str
    source: str | None
    target: str | None
    claim: str | None
    route: str | None
    certificate_id: str | None
    trust_level: str
    explanation: str
    evidence: dict[str, Any]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "source": self.source,
            "target": self.target,
            "claim": self.claim,
            "route": self.route,
            "certificate_id": self.certificate_id,
            "trust_level": self.trust_level,
            "explanation": self.explanation,
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
        }


class KernelOracle:
    def __init__(self, store: LawbookStore, root_oracle: Any | None = None) -> None:
        self.store = store
        self.root_oracle = root_oracle

    def query(self, source: str, target: str) -> OracleAnswer:
        primitive = self.store.get_by_pair(source, target)
        if primitive is not None:
            return _answer_from_record(primitive)
        derived = self.store.get_derived_by_pair(source, target)
        if derived is not None:
            return _answer_from_record(derived)
        refutation = self.store.query_refutation(source, target)
        if refutation is not None:
            return _answer_from_warehouse_refutation(refutation)
        claim = self.store.query_claim(source, target)
        if claim.get("status") == "hit":
            return _answer_from_warehouse_claim(claim)
        answer = _answer_from_record(self.store.explain_pair(source, target))
        if self.root_oracle is not None:
            pressure = _root_pressure(self.root_oracle, source, target)
            answer.evidence.update(pressure)
        return answer

    def explain_claim(self, claim: str) -> OracleAnswer:
        return _answer_from_record(self.store.explain_claim(claim))

    def what_does_this_imply(self, source: str, limit: int = 50) -> list[OracleAnswer]:
        return [_answer_from_record(record) for record in self.store.find_by_source(source, limit)]

    def what_implies_this(self, target: str, limit: int = 50) -> list[OracleAnswer]:
        return [_answer_from_record(record) for record in self.store.find_by_target(target, limit)]

    def route_examples(self, route: str, limit: int = 50) -> list[OracleAnswer]:
        return [_answer_from_record(record) for record in self.store.find_by_route(route, limit)]

    def finite_countermodels(self, limit: int = 50) -> list[OracleAnswer]:
        return [
            _answer_from_record(record)
            for record in self.store.find_by_terminal_form("FINITE_COUNTERMODEL", limit)
        ]

    def verified_proofs(self, limit: int = 50) -> list[OracleAnswer]:
        return [
            _answer_from_record(record)
            for record in self.store.find_by_terminal_form("VERIFIED_PROOF", limit)
        ]

    def stats(self) -> dict[str, Any]:
        return self.store.stats().to_dict()


def _answer_from_record(record: dict[str, Any]) -> OracleAnswer:
    if record.get("status") == "missing":
        return OracleAnswer(
            status="UNKNOWN",
            terminal_form="NAMED_OBSTRUCTION",
            verification_status="UNKNOWN",
            source=record.get("source"),
            target=record.get("target"),
            claim=record.get("claim"),
            route=None,
            certificate_id=None,
            trust_level="no_exact_trace",
            explanation=record["explanation"],
            evidence={},
            warnings=[
                "No exact verified lawbook trace found.",
                "Do not promote advisory output to proof or refutation.",
            ],
        )

    if record.get("status") == "derived_hit":
        terminal = record["terminal_form"]
        status = "UNKNOWN"
        if terminal == "VERIFIED_PROOF":
            status = "VERIFIED"
        elif terminal == "FINITE_COUNTERMODEL":
            status = "REFUTED"
        return OracleAnswer(
            status=status,
            terminal_form=terminal,
            verification_status=record["verification_status"],
            source=record.get("source"),
            target=record.get("target"),
            claim=record.get("claim"),
            route=record.get("route"),
            certificate_id=record.get("certificate_id"),
            trust_level="derived_from_verified_traces",
            explanation=record.get("explanation", "Derived certificate found."),
            evidence={
                "derivation_rule": record.get("derivation_rule"),
                "parent_claims": record.get("parent_claims", []),
                "parent_pairs": record.get("parent_pairs", []),
                **dict(record.get("evidence", {})),
            },
            warnings=[
                "This is a derived certificate by logical composition of verified traces.",
                *list(record.get("warnings", [])),
            ],
        )

    terminal = record["terminal_form"]
    status = "UNKNOWN"
    if terminal == "VERIFIED_PROOF":
        status = "VERIFIED"
    elif terminal == "FINITE_COUNTERMODEL":
        status = "REFUTED"
    return OracleAnswer(
        status=status,
        terminal_form=terminal,
        verification_status=record["verification_status"],
        source=record.get("source"),
        target=record.get("target"),
        claim=record.get("claim"),
        route=record.get("route"),
        certificate_id=record.get("certificate_id"),
        trust_level="verified_trace",
        explanation=record.get("explanation", "Exact verified lawbook trace found."),
        evidence={
            "claim_hash": record.get("claim_hash"),
            "source_idx": record.get("source_idx"),
            "target_idx": record.get("target_idx"),
            "certificate_payload_keys": record.get("certificate_payload_keys", []),
            "metadata_keys": record.get("metadata_keys", []),
            "promotion_status": record.get("promotion_status"),
            "lean_status": record.get("lean_status"),
        },
        warnings=[],
    )


def _root_pressure(root_oracle: Any, source: str, target: str) -> dict[str, Any]:
    try:
        roots = root_oracle.top_roots(5)
        reasons = root_oracle.top_reasons(5)
        obstructions = root_oracle.top_obstructions(5)
    except Exception as exc:
        return {"root_pressure": {"advisory_only": True, "error": str(exc)}}
    return {
        "root_pressure": roots,
        "reason_pressure": reasons,
        "obstruction_pressure": obstructions,
        "advisory_only": True,
        "source": source,
        "target": target,
    }


def _answer_from_warehouse_refutation(record: dict[str, Any]) -> OracleAnswer:
    return OracleAnswer(
        status="REFUTED",
        terminal_form=record.get("terminal_form") or "FINITE_COUNTERMODEL",
        verification_status=record.get("verification_status") or "FINITE_VERIFIED",
        source=record.get("source"),
        target=record.get("target"),
        claim=record.get("claim_id"),
        route=record.get("derivation_rule") or "finite_countermodel",
        certificate_id=record.get("refutation_id"),
        trust_level=record.get("trust_level") or "finite_verified",
        explanation="Exact finite refutation certificate found in LawbookStore warehouse.",
        evidence={
            "table_hash": record.get("table_hash"),
            "table": record.get("table"),
            "witness": record.get("witness"),
            "derivation_rule": record.get("derivation_rule"),
            "elevation_method": record.get("elevation_method"),
        },
        warnings=[],
    )


def _answer_from_warehouse_claim(record: dict[str, Any]) -> OracleAnswer:
    terminal = record.get("terminal_form") or "NAMED_OBSTRUCTION"
    status = "UNKNOWN"
    if terminal == "VERIFIED_PROOF":
        status = "VERIFIED"
    elif terminal == "FINITE_COUNTERMODEL":
        status = "REFUTED"
    return OracleAnswer(
        status=status,
        terminal_form=terminal,
        verification_status=record.get("verification_status") or "UNKNOWN",
        source=record.get("source"),
        target=record.get("target"),
        claim=record.get("claim_id"),
        route=None,
        certificate_id=None,
        trust_level=record.get("trust_level") or "unknown",
        explanation="Exact claim row found in LawbookStore warehouse.",
        evidence={
            "provenance_type": record.get("provenance_type"),
            "metadata": record.get("metadata", {}),
        },
        warnings=[] if status != "UNKNOWN" else ["Warehouse claim row is not a verifier result."],
    )

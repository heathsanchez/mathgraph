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
    def __init__(self, store: LawbookStore) -> None:
        self.store = store

    def query(self, source: str, target: str) -> OracleAnswer:
        return _answer_from_record(self.store.explain_pair(source, target))

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

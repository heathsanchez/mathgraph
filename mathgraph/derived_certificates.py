"""Derived certificates by sound composition of verified lawbook traces."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.lawbook_store import LawbookStore


@dataclass(frozen=True)
class DerivedCertificate:
    derived_claim: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    terminal_form: str
    verification_status: str
    derivation_rule: str
    trust_level: str
    parent_claims: list[str]
    parent_pairs: list[dict[str, Any]]
    route: str
    explanation: str
    evidence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "derived_claim": self.derived_claim,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "derivation_rule": self.derivation_rule,
            "trust_level": self.trust_level,
            "parent_claims": list(self.parent_claims),
            "parent_pairs": list(self.parent_pairs),
            "route": self.route,
            "explanation": self.explanation,
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DerivedCertificate":
        return cls(
            derived_claim=str(data["derived_claim"]),
            source=str(data["source"]),
            target=str(data["target"]),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            terminal_form=str(data["terminal_form"]),
            verification_status=str(data["verification_status"]),
            derivation_rule=str(data["derivation_rule"]),
            trust_level=str(data["trust_level"]),
            parent_claims=[str(item) for item in data.get("parent_claims", [])],
            parent_pairs=list(data.get("parent_pairs", [])),
            route=str(data["route"]),
            explanation=str(data["explanation"]),
            evidence=dict(data.get("evidence", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


@dataclass(frozen=True)
class DerivedCertificateStats:
    input_trace_count: int
    input_true_count: int
    input_false_count: int
    derived_true_count: int
    derived_false_count: int
    duplicate_skipped_count: int
    malformed_skipped_count: int
    total_derived_count: int
    rule_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_trace_count": self.input_trace_count,
            "input_true_count": self.input_true_count,
            "input_false_count": self.input_false_count,
            "derived_true_count": self.derived_true_count,
            "derived_false_count": self.derived_false_count,
            "duplicate_skipped_count": self.duplicate_skipped_count,
            "malformed_skipped_count": self.malformed_skipped_count,
            "total_derived_count": self.total_derived_count,
            "rule_counts": dict(self.rule_counts),
        }


class DerivedCertificateGenerator:
    """Generate only logically sound derived certificates from verified traces."""

    def __init__(self, store: LawbookStore) -> None:
        self.store = store
        self._duplicate_skipped_count = 0
        self._malformed_skipped_count = 0

    def derive_all(
        self,
        max_per_rule: int | None = None,
        include_true_transitivity: bool = True,
        include_false_source_weakening: bool = True,
        include_false_target_strengthening: bool = True,
    ) -> tuple[list[DerivedCertificate], DerivedCertificateStats]:
        self._duplicate_skipped_count = 0
        self._malformed_skipped_count = 0
        certificates: list[DerivedCertificate] = []
        seen_pairs: set[tuple[str, str, str]] = set()
        rule_sets: list[list[DerivedCertificate]] = []
        if include_true_transitivity:
            rule_sets.append(self.derive_true_transitivity(max_per_rule))
        if include_false_source_weakening:
            rule_sets.append(self.derive_false_source_weakening(max_per_rule))
        if include_false_target_strengthening:
            rule_sets.append(self.derive_false_target_strengthening(max_per_rule))
        for rule_certs in rule_sets:
            for cert in rule_certs:
                key = (cert.source, cert.target, cert.terminal_form)
                if key in seen_pairs:
                    self._duplicate_skipped_count += 1
                    continue
                seen_pairs.add(key)
                certificates.append(cert)
        return certificates, self.stats_for(certificates)

    def derive_true_transitivity(
        self, max_results: int | None = None
    ) -> list[DerivedCertificate]:
        proofs = _verified_proofs(self.store)
        by_source: dict[str, list[dict[str, Any]]] = {}
        for proof in proofs:
            if not _has_pair(proof):
                self._malformed_skipped_count += 1
                continue
            by_source.setdefault(proof["source"], []).append(proof)

        derived: list[DerivedCertificate] = []
        seen: set[tuple[str, str]] = set()
        for left in proofs:
            if not _has_pair(left):
                continue
            for right in by_source.get(left["target"], []):
                source, target = left["source"], right["target"]
                if source == target:
                    continue
                if (source, target) in seen:
                    self._duplicate_skipped_count += 1
                    continue
                if self.store.get_by_pair(source, target) is not None:
                    self._duplicate_skipped_count += 1
                    continue
                seen.add((source, target))
                derived.append(
                    _make_derived(
                        source=source,
                        target=target,
                        terminal_form="VERIFIED_PROOF",
                        verification_status="DERIVED_VERIFIED",
                        derivation_rule="true_transitivity",
                        route="derived_true_transitivity",
                        parents=[left, right],
                        explanation="Composed verified implications A=>B and B=>C to derive A=>C.",
                    )
                )
                if max_results is not None and len(derived) >= max_results:
                    return derived
        return derived

    def derive_false_source_weakening(
        self, max_results: int | None = None
    ) -> list[DerivedCertificate]:
        proofs = _verified_proofs(self.store)
        false_records = _finite_countermodels(self.store)
        proofs_by_source: dict[str, list[dict[str, Any]]] = {}
        for proof in proofs:
            if not _has_pair(proof):
                self._malformed_skipped_count += 1
                continue
            proofs_by_source.setdefault(proof["source"], []).append(proof)

        derived: list[DerivedCertificate] = []
        seen: set[tuple[str, str]] = set()
        for false_record in false_records:
            if not _has_pair(false_record):
                self._malformed_skipped_count += 1
                continue
            # Sound direction: B=>A and B⇏C derives A⇏C.
            for proof in proofs_by_source.get(false_record["source"], []):
                source, target = proof["target"], false_record["target"]
                if source == target:
                    continue
                if (source, target) in seen:
                    self._duplicate_skipped_count += 1
                    continue
                if self.store.get_by_pair(source, target) is not None:
                    self._duplicate_skipped_count += 1
                    continue
                seen.add((source, target))
                derived.append(
                    _make_derived(
                        source=source,
                        target=target,
                        terminal_form="FINITE_COUNTERMODEL",
                        verification_status="DERIVED_REFUTED",
                        derivation_rule="false_source_weakening",
                        route="derived_false_source_weakening",
                        parents=[proof, false_record],
                        explanation=(
                            "Used B=>A and a countermodel for B⇏C; the witness "
                            "satisfies A because it satisfies stronger source B."
                        ),
                    )
                )
                if max_results is not None and len(derived) >= max_results:
                    return derived
        return derived

    def derive_false_target_strengthening(
        self, max_results: int | None = None
    ) -> list[DerivedCertificate]:
        proofs = _verified_proofs(self.store)
        false_records = _finite_countermodels(self.store)
        proofs_by_target: dict[str, list[dict[str, Any]]] = {}
        for proof in proofs:
            if not _has_pair(proof):
                self._malformed_skipped_count += 1
                continue
            proofs_by_target.setdefault(proof["target"], []).append(proof)

        derived: list[DerivedCertificate] = []
        seen: set[tuple[str, str]] = set()
        for false_record in false_records:
            if not _has_pair(false_record):
                self._malformed_skipped_count += 1
                continue
            # Sound direction: A⇏B and C=>B derives A⇏C.
            for proof in proofs_by_target.get(false_record["target"], []):
                source, target = false_record["source"], proof["source"]
                if source == target:
                    continue
                if (source, target) in seen:
                    self._duplicate_skipped_count += 1
                    continue
                if self.store.get_by_pair(source, target) is not None:
                    self._duplicate_skipped_count += 1
                    continue
                seen.add((source, target))
                derived.append(
                    _make_derived(
                        source=source,
                        target=target,
                        terminal_form="FINITE_COUNTERMODEL",
                        verification_status="DERIVED_REFUTED",
                        derivation_rule="false_target_strengthening",
                        route="derived_false_target_strengthening",
                        parents=[false_record, proof],
                        explanation=(
                            "Used A⇏B and C=>B; any witness refuting B also "
                            "refutes stronger target C."
                        ),
                    )
                )
                if max_results is not None and len(derived) >= max_results:
                    return derived
        return derived

    def save_jsonl(
        self, certificates: list[DerivedCertificate], path: str | Path
    ) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for cert in certificates:
                handle.write(json.dumps(cert.to_dict(), sort_keys=True) + "\n")

    def save_json(
        self, certificates: list[DerivedCertificate], path: str | Path
    ) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps([cert.to_dict() for cert in certificates], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def stats_for(
        self, certificates: list[DerivedCertificate]
    ) -> DerivedCertificateStats:
        store_stats = self.store.stats()
        return DerivedCertificateStats(
            input_trace_count=store_stats.trace_count,
            input_true_count=store_stats.terminal_form_counts.get("VERIFIED_PROOF", 0),
            input_false_count=store_stats.terminal_form_counts.get("FINITE_COUNTERMODEL", 0),
            derived_true_count=sum(
                1 for cert in certificates if cert.terminal_form == "VERIFIED_PROOF"
            ),
            derived_false_count=sum(
                1 for cert in certificates if cert.terminal_form == "FINITE_COUNTERMODEL"
            ),
            duplicate_skipped_count=self._duplicate_skipped_count,
            malformed_skipped_count=self._malformed_skipped_count,
            total_derived_count=len(certificates),
            rule_counts=dict(Counter(cert.derivation_rule for cert in certificates)),
        )


def _verified_proofs(store: LawbookStore) -> list[dict[str, Any]]:
    return [
        record
        for record in store.find_by_terminal_form("VERIFIED_PROOF", limit=1_000_000)
        if record.get("verification_status") == "VERIFIED"
    ]


def _finite_countermodels(store: LawbookStore) -> list[dict[str, Any]]:
    return [
        record
        for record in store.find_by_terminal_form("FINITE_COUNTERMODEL", limit=1_000_000)
        if record.get("verification_status") == "REFUTED"
    ]


def _has_pair(record: dict[str, Any]) -> bool:
    return record.get("source") not in (None, "") and record.get("target") not in (None, "")


def _make_derived(
    *,
    source: str,
    target: str,
    terminal_form: str,
    verification_status: str,
    derivation_rule: str,
    route: str,
    parents: list[dict[str, Any]],
    explanation: str,
) -> DerivedCertificate:
    payload = {
        "source": source,
        "target": target,
        "terminal_form": terminal_form,
        "verification_status": verification_status,
        "derivation_rule": derivation_rule,
        "parents": [_compact_parent(parent) for parent in parents],
    }
    return DerivedCertificate(
        derived_claim=content_id("derived", payload),
        source=source,
        target=target,
        source_idx=_shared_idx(parents, "source_idx", source),
        target_idx=_shared_idx(parents, "target_idx", target),
        terminal_form=terminal_form,
        verification_status=verification_status,
        derivation_rule=derivation_rule,
        trust_level="derived_from_verified_traces",
        parent_claims=[str(parent.get("claim")) for parent in parents if parent.get("claim")],
        parent_pairs=[
            {"source": parent.get("source"), "target": parent.get("target")}
            for parent in parents
        ],
        route=route,
        explanation=explanation,
        evidence={
            "parent_claims": [parent.get("claim") for parent in parents],
            "parent_pairs": [
                {"source": parent.get("source"), "target": parent.get("target")}
                for parent in parents
            ],
            "parent_terminal_forms": [parent.get("terminal_form") for parent in parents],
            "parent_verification_statuses": [
                parent.get("verification_status") for parent in parents
            ],
        },
        warnings=[
            "This is a derived certificate by logical composition of verified traces.",
            "Primitive certificates remain distinct from derived certificates.",
        ],
    )


def _compact_parent(parent: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim": parent.get("claim"),
        "source": parent.get("source"),
        "target": parent.get("target"),
        "terminal_form": parent.get("terminal_form"),
        "verification_status": parent.get("verification_status"),
    }


def _shared_idx(parents: list[dict[str, Any]], key: str, value: str) -> int | None:
    for parent in parents:
        if parent.get("source") == value and parent.get("source_idx") is not None:
            return _optional_int(parent.get("source_idx"))
        if parent.get("target") == value and parent.get("target_idx") is not None:
            return _optional_int(parent.get("target_idx"))
        if parent.get(key) is not None:
            candidate = _optional_int(parent.get(key))
            if candidate is not None:
                return candidate
    return None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

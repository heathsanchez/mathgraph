"""Pair outcome dataset and compounding diagnostics for MathGraph."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.lawbook_store import LawbookStore
from mathgraph.pair_advisor import extract_pair_features as _advisor_features


@dataclass(frozen=True)
class PairOutcome:
    pair_id: str
    source: str
    target: str
    source_idx: int | None
    target_idx: int | None
    claim_id: str | None
    terminal_form: str
    verification_status: str
    trust_level: str
    origin: str
    route: str | None
    derivation_rule: str | None
    parent_claims: list[str]
    features: dict[str, Any]
    labels: dict[str, Any]
    evidence: dict[str, Any]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "source": self.source,
            "target": self.target,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "claim_id": self.claim_id,
            "terminal_form": self.terminal_form,
            "verification_status": self.verification_status,
            "trust_level": self.trust_level,
            "origin": self.origin,
            "route": self.route,
            "derivation_rule": self.derivation_rule,
            "parent_claims": list(self.parent_claims),
            "features": dict(self.features),
            "labels": dict(self.labels),
            "evidence": dict(self.evidence),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PairOutcome":
        return cls(
            pair_id=str(data["pair_id"]),
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            claim_id=data.get("claim_id"),
            terminal_form=str(data["terminal_form"]),
            verification_status=str(data["verification_status"]),
            trust_level=str(data["trust_level"]),
            origin=str(data["origin"]),
            route=data.get("route"),
            derivation_rule=data.get("derivation_rule"),
            parent_claims=[str(item) for item in data.get("parent_claims", [])],
            features=dict(data.get("features", {})),
            labels=dict(data.get("labels", {})),
            evidence=dict(data.get("evidence", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


@dataclass(frozen=True)
class OutcomeDatasetStats:
    row_count: int
    primitive_count: int
    derived_count: int
    unknown_count: int
    advisory_count: int
    verified_true_count: int
    verified_false_count: int
    obstruction_count: int
    by_terminal_form: dict[str, int]
    by_verification_status: dict[str, int]
    by_route: dict[str, int]
    by_origin: dict[str, int]
    by_trust_level: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_count": self.row_count,
            "primitive_count": self.primitive_count,
            "derived_count": self.derived_count,
            "unknown_count": self.unknown_count,
            "advisory_count": self.advisory_count,
            "verified_true_count": self.verified_true_count,
            "verified_false_count": self.verified_false_count,
            "obstruction_count": self.obstruction_count,
            "by_terminal_form": dict(self.by_terminal_form),
            "by_verification_status": dict(self.by_verification_status),
            "by_route": dict(self.by_route),
            "by_origin": dict(self.by_origin),
            "by_trust_level": dict(self.by_trust_level),
        }


@dataclass(frozen=True)
class CompoundingDiagnostics:
    episode_id: str
    created_ts: str
    primitive_certificate_count: int
    derived_certificate_count: int
    total_certificate_count: int
    derived_per_primitive: float
    corpus_density: float | None
    verified_true_count: int
    verified_false_count: int
    unknown_count: int
    route_yield: dict[str, dict[str, int]]
    derivation_yield: dict[str, dict[str, int]]
    trust_level_counts: dict[str, int]
    terminal_form_counts: dict[str, int]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "created_ts": self.created_ts,
            "primitive_certificate_count": self.primitive_certificate_count,
            "derived_certificate_count": self.derived_certificate_count,
            "total_certificate_count": self.total_certificate_count,
            "derived_per_primitive": self.derived_per_primitive,
            "corpus_density": self.corpus_density,
            "verified_true_count": self.verified_true_count,
            "verified_false_count": self.verified_false_count,
            "unknown_count": self.unknown_count,
            "route_yield": self.route_yield,
            "derivation_yield": self.derivation_yield,
            "trust_level_counts": dict(self.trust_level_counts),
            "terminal_form_counts": dict(self.terminal_form_counts),
            "warnings": list(self.warnings),
        }


def extract_pair_features(source: str, target: str) -> dict[str, Any]:
    features = _advisor_features(source, target)
    features["len_delta"] = features["target_len"] - features["source_len"]
    return features


class OutcomeDatasetBuilder:
    def __init__(self, store: LawbookStore) -> None:
        self.store = store

    def build(
        self,
        include_primitive: bool = True,
        include_derived: bool = True,
        unknown_pairs: list[dict[str, Any]] | None = None,
        advisory_tasks: list[dict[str, Any]] | None = None,
    ) -> list[PairOutcome]:
        outcomes: list[PairOutcome] = []
        if include_primitive:
            outcomes.extend(_primitive_outcome(record) for record in self.store.iter_primitive_traces())
        if include_derived:
            outcomes.extend(_derived_outcome(record) for record in self.store.iter_derived_certificates())
        for item in unknown_pairs or []:
            outcomes.append(_unknown_outcome(item))
        for item in advisory_tasks or []:
            outcomes.append(_advisory_outcome(item))
        return outcomes

    def stats(self, outcomes: list[PairOutcome]) -> OutcomeDatasetStats:
        origin_counts = Counter(outcome.origin for outcome in outcomes)
        terminal_counts = Counter(outcome.terminal_form for outcome in outcomes)
        status_counts = Counter(outcome.verification_status for outcome in outcomes)
        route_counts = Counter(outcome.route for outcome in outcomes if outcome.route)
        trust_counts = Counter(outcome.trust_level for outcome in outcomes)
        return OutcomeDatasetStats(
            row_count=len(outcomes),
            primitive_count=origin_counts.get("primitive_trace", 0),
            derived_count=origin_counts.get("derived_certificate", 0),
            unknown_count=origin_counts.get("oracle_unknown", 0),
            advisory_count=origin_counts.get("advisory_task", 0),
            verified_true_count=sum(1 for outcome in outcomes if outcome.labels.get("is_verified_true")),
            verified_false_count=sum(1 for outcome in outcomes if outcome.labels.get("is_verified_false")),
            obstruction_count=sum(1 for outcome in outcomes if outcome.labels.get("is_obstruction")),
            by_terminal_form=dict(terminal_counts),
            by_verification_status=dict(status_counts),
            by_route=dict(route_counts),
            by_origin=dict(origin_counts),
            by_trust_level=dict(trust_counts),
        )

    def diagnostics(
        self,
        outcomes: list[PairOutcome],
        episode_id: str,
        equation_count: int | None = None,
    ) -> CompoundingDiagnostics:
        stats = self.stats(outcomes)
        derived_per_primitive = (
            stats.derived_count / stats.primitive_count if stats.primitive_count else 0.0
        )
        total_cert_count = stats.primitive_count + stats.derived_count
        corpus_density = None
        if equation_count:
            corpus_density = total_cert_count / float(equation_count * equation_count)
        warnings: list[str] = []
        if stats.derived_count == 0:
            warnings.append("No derived certificates found.")
        if stats.primitive_count == 0:
            warnings.append("No primitive certificates found.")
        if derived_per_primitive < 0.1:
            warnings.append("Derived certificates per primitive is below 0.1.")
        if corpus_density is not None and corpus_density < 0.001:
            warnings.append("Corpus density is below 0.001.")
        return CompoundingDiagnostics(
            episode_id=episode_id,
            created_ts=datetime.now(timezone.utc).isoformat(),
            primitive_certificate_count=stats.primitive_count,
            derived_certificate_count=stats.derived_count,
            total_certificate_count=total_cert_count,
            derived_per_primitive=derived_per_primitive,
            corpus_density=corpus_density,
            verified_true_count=stats.verified_true_count,
            verified_false_count=stats.verified_false_count,
            unknown_count=stats.unknown_count,
            route_yield=_route_yield(outcomes),
            derivation_yield=_derivation_yield(outcomes),
            trust_level_counts=stats.by_trust_level,
            terminal_form_counts=stats.by_terminal_form,
            warnings=warnings,
        )

    def save_jsonl(self, outcomes: list[PairOutcome], path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for outcome in outcomes:
                handle.write(json.dumps(outcome.to_dict(), sort_keys=True) + "\n")

    def save_json(self, outcomes: list[PairOutcome], path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps([outcome.to_dict() for outcome in outcomes], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def save_diagnostics(self, diagnostics: CompoundingDiagnostics, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(diagnostics.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def _primitive_outcome(record: dict[str, Any]) -> PairOutcome:
    source = str(record.get("source") or "")
    target = str(record.get("target") or "")
    terminal = str(record.get("terminal_form"))
    status = str(record.get("verification_status"))
    route = record.get("route")
    trust_level = _primitive_trust(record)
    labels = _labels(terminal, status, is_derived=False)
    return PairOutcome(
        pair_id=content_id("pair", {"origin": "primitive_trace", "claim": record.get("claim"), "source": source, "target": target}),
        source=source,
        target=target,
        source_idx=_optional_int(record.get("source_idx")),
        target_idx=_optional_int(record.get("target_idx")),
        claim_id=record.get("claim_hash") or record.get("claim"),
        terminal_form=terminal,
        verification_status=status,
        trust_level=trust_level,
        origin="primitive_trace",
        route=route,
        derivation_rule=None,
        parent_claims=[],
        features=extract_pair_features(source, target),
        labels=labels,
        evidence={
            "claim": record.get("claim"),
            "claim_hash": record.get("claim_hash"),
            "certificate_payload_keys": record.get("certificate_payload_keys", []),
            "lean_status": record.get("lean_status"),
            "promotion_status": record.get("promotion_status"),
        },
        warnings=[],
    )


def _derived_outcome(record: dict[str, Any]) -> PairOutcome:
    source = str(record.get("source") or "")
    target = str(record.get("target") or "")
    terminal = str(record.get("terminal_form"))
    status = str(record.get("verification_status"))
    labels = _labels(terminal, status, is_derived=True)
    return PairOutcome(
        pair_id=content_id("pair", {"origin": "derived_certificate", "claim": record.get("derived_claim"), "source": source, "target": target}),
        source=source,
        target=target,
        source_idx=_optional_int(record.get("source_idx")),
        target_idx=_optional_int(record.get("target_idx")),
        claim_id=record.get("derived_claim") or record.get("claim"),
        terminal_form=terminal,
        verification_status=status,
        trust_level="derived_from_verified_traces",
        origin="derived_certificate",
        route=record.get("route"),
        derivation_rule=record.get("derivation_rule"),
        parent_claims=[str(item) for item in record.get("parent_claims", [])],
        features=extract_pair_features(source, target),
        labels=labels,
        evidence={
            "parent_pairs": record.get("parent_pairs", []),
            "derivation_rule": record.get("derivation_rule"),
            **dict(record.get("evidence", {})),
        },
        warnings=list(record.get("warnings", [])),
    )


def _unknown_outcome(item: dict[str, Any]) -> PairOutcome:
    source = str(item.get("source", ""))
    target = str(item.get("target", ""))
    labels = _labels("NAMED_OBSTRUCTION", "UNKNOWN", is_derived=False)
    labels["is_unknown"] = True
    return PairOutcome(
        pair_id=content_id("pair", {"origin": "oracle_unknown", "source": source, "target": target}),
        source=source,
        target=target,
        source_idx=_optional_int(item.get("source_idx")),
        target_idx=_optional_int(item.get("target_idx")),
        claim_id=item.get("claim_id"),
        terminal_form="NAMED_OBSTRUCTION",
        verification_status="UNKNOWN",
        trust_level="unknown",
        origin="oracle_unknown",
        route=None,
        derivation_rule=None,
        parent_claims=[],
        features=extract_pair_features(source, target),
        labels=labels,
        evidence=dict(item),
        warnings=["Unknown pair is not a proof or refutation."],
    )


def _advisory_outcome(item: dict[str, Any]) -> PairOutcome:
    source = str(item.get("source", ""))
    target = str(item.get("target", ""))
    labels = _labels("NAMED_OBSTRUCTION", "UNKNOWN", is_derived=False)
    labels["is_advisory"] = True
    return PairOutcome(
        pair_id=str(item.get("task_id") or content_id("pair", {"origin": "advisory_task", "source": source, "target": target, "route": item.get("route")})),
        source=source,
        target=target,
        source_idx=_optional_int(item.get("source_idx")),
        target_idx=_optional_int(item.get("target_idx")),
        claim_id=item.get("claim_id"),
        terminal_form="NAMED_OBSTRUCTION",
        verification_status="UNKNOWN",
        trust_level="advisory_only",
        origin="advisory_task",
        route=item.get("route"),
        derivation_rule=None,
        parent_claims=[],
        features=extract_pair_features(source, target),
        labels=labels,
        evidence={
            "task_kind": item.get("task_kind"),
            "status": item.get("status"),
            "route": item.get("route"),
            "task": dict(item),
        },
        warnings=[
            "Advisory task rows are not proof or refutation.",
            *list(item.get("warnings", [])),
        ],
    )


def _labels(terminal_form: str, verification_status: str, is_derived: bool) -> dict[str, bool]:
    return {
        "is_verified_true": terminal_form == "VERIFIED_PROOF",
        "is_verified_false": terminal_form == "FINITE_COUNTERMODEL",
        "is_countermodel": terminal_form == "FINITE_COUNTERMODEL",
        "is_proof": terminal_form == "VERIFIED_PROOF",
        "is_obstruction": terminal_form == "NAMED_OBSTRUCTION",
        "is_derived": is_derived,
        "is_unknown": verification_status == "UNKNOWN",
    }


def _primitive_trust(record: dict[str, Any]) -> str:
    lean_status = str(record.get("lean_status") or "").lower()
    if "verified" in lean_status:
        return "lean_verified"
    if record.get("terminal_form") == "FINITE_COUNTERMODEL" and record.get("verification_status") == "REFUTED":
        return "finite_verified"
    return "unknown"


def _route_yield(outcomes: list[PairOutcome]) -> dict[str, dict[str, int]]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for outcome in outcomes:
        if not outcome.route:
            continue
        bucket = buckets[outcome.route]
        bucket["count"] += 1
        if outcome.labels.get("is_verified_true"):
            bucket["verified_true"] += 1
        if outcome.labels.get("is_verified_false"):
            bucket["verified_false"] += 1
        if outcome.labels.get("is_derived"):
            bucket["derived"] += 1
        if outcome.labels.get("is_obstruction"):
            bucket["obstruction"] += 1
        if outcome.labels.get("is_unknown"):
            bucket["unknown"] += 1
    return {route: dict(counts) for route, counts in buckets.items()}


def _derivation_yield(outcomes: list[PairOutcome]) -> dict[str, dict[str, int]]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for outcome in outcomes:
        if not outcome.derivation_rule:
            continue
        bucket = buckets[outcome.derivation_rule]
        bucket["count"] += 1
        if outcome.labels.get("is_verified_true"):
            bucket["verified_true"] += 1
        if outcome.labels.get("is_verified_false"):
            bucket["verified_false"] += 1
    return {rule: dict(counts) for rule, counts in buckets.items()}


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

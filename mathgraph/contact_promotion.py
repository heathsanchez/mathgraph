"""Promote repeated clean Lean contacts into advisory route-law records."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from mathgraph.hashing import content_id


class ContactKind(str, Enum):
    STRICT_CONTACT_SEED = "STRICT_CONTACT_SEED"
    VISIBILITY_CONTACT = "VISIBILITY_CONTACT"


class ContactStatus(str, Enum):
    STRICT_CONTACT_SEED = "STRICT_CONTACT_SEED"
    VISIBILITY_CONTACT = "VISIBILITY_CONTACT"
    REPAIRABLE_OBSTRUCTION = "REPAIRABLE_OBSTRUCTION"
    TRANSFER_TEST = "TRANSFER_TEST"
    PROMOTED_ROUTE_LAW = "PROMOTED_ROUTE_LAW"


@dataclass(frozen=True)
class ContactSeed:
    seed_id: str
    kind: ContactKind
    decl_name: str
    shape: str
    repair_strategy: str
    root_decl: str = ""
    target_decl: str = ""
    expected_type: str = ""
    proof_term: str = ""
    source_probe_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "kind": self.kind.value,
            "status": self.kind.value,
            "decl_name": self.decl_name,
            "shape": self.shape,
            "repair_strategy": self.repair_strategy,
            "root_decl": self.root_decl,
            "target_decl": self.target_decl,
            "expected_type": self.expected_type,
            "proof_term": self.proof_term,
            "source_probe_id": self.source_probe_id,
            "metadata": dict(self.metadata),
            "advisory": True,
        }


@dataclass(frozen=True)
class ContactObstruction:
    obstruction_id: str
    status: ContactStatus
    failure_class: str
    decl_name: str
    shape: str
    repair_strategy: str
    failure_detail: str = ""
    source_probe_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "obstruction_id": self.obstruction_id,
            "status": self.status.value,
            "failure_class": self.failure_class,
            "decl_name": self.decl_name,
            "shape": self.shape,
            "repair_strategy": self.repair_strategy,
            "failure_detail": self.failure_detail,
            "source_probe_id": self.source_probe_id,
            "metadata": dict(self.metadata),
            "advisory": True,
        }


@dataclass(frozen=True)
class TransferTest:
    transfer_test_id: str
    status: ContactStatus
    shape: str
    repair_strategy: str
    source_seed_id: str
    decl_name: str
    priority: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "transfer_test_id": self.transfer_test_id,
            "status": self.status.value,
            "shape": self.shape,
            "repair_strategy": self.repair_strategy,
            "source_seed_id": self.source_seed_id,
            "decl_name": self.decl_name,
            "priority": self.priority,
            "metadata": dict(self.metadata),
            "advisory": True,
        }


@dataclass(frozen=True)
class PromotedRouteLaw:
    law_id: str
    law_kind: str
    shape: str
    repair_strategy: str
    support: int
    clean_successes: int
    transfer_successes: int
    distinct_declarations: int
    failure_rate: float
    examples: tuple[str, ...]
    source_seed_ids: tuple[str, ...]
    trust_level: str = "REPEATED_CLEAN_CONTACT"
    advisory: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "law_id": self.law_id,
            "law_kind": self.law_kind,
            "shape": self.shape,
            "repair_strategy": self.repair_strategy,
            "support": self.support,
            "clean_successes": self.clean_successes,
            "transfer_successes": self.transfer_successes,
            "distinct_declarations": self.distinct_declarations,
            "failure_rate": self.failure_rate,
            "examples": list(self.examples),
            "source_seed_ids": list(self.source_seed_ids),
            "trust_level": self.trust_level,
            "advisory": True,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PromotionPolicy:
    min_clean_successes: int = 3
    min_transfer_successes: int = 2
    max_failure_rate: float = 0.20
    require_distinct_declarations: int = 2
    allow_visibility_promotion: bool = False


@dataclass(frozen=True)
class PromotionDecision:
    group_key: str
    promoted: bool
    law: PromotedRouteLaw | None
    reasons: tuple[str, ...]
    advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_key": self.group_key,
            "promoted": self.promoted,
            "law": self.law.to_dict() if self.law else None,
            "reasons": list(self.reasons),
            "advisory": True,
        }


class ContactPromotionEngine:
    def __init__(self, policy: PromotionPolicy | None = None) -> None:
        self.policy = policy or PromotionPolicy()
        self.seeds: list[ContactSeed] = []
        self.obstructions: list[ContactObstruction] = []
        self._decisions: list[PromotionDecision] = []
        self._rows: list[dict[str, Any]] = []

    def classify_probe_row(self, row: dict[str, Any]) -> ContactSeed | ContactObstruction:
        level = str(row.get("level", ""))
        repair_strategy = str(row.get("repair_strategy", row.get("strategy", "")))
        strict_success = _truthy(row.get("strict_success"))
        visibility = "VISIBILITY" in level.upper() or "visibility" in repair_strategy.lower()
        decl_name = _decl_name(row)
        shape = str(row.get("shape", ""))
        if strict_success and visibility:
            return self._seed(row, ContactKind.VISIBILITY_CONTACT, decl_name, shape, repair_strategy)
        if strict_success and level == "L2_STRICT_CONTACT":
            return self._seed(row, ContactKind.STRICT_CONTACT_SEED, decl_name, shape, repair_strategy)
        if strict_success and _markers_clean(row):
            return self._seed(row, ContactKind.STRICT_CONTACT_SEED, decl_name, shape, repair_strategy)
        return self._obstruction(row, decl_name, shape, repair_strategy)

    def ingest_probe_rows(self, rows: list[dict[str, Any]]) -> None:
        self._rows.extend(dict(row) for row in rows)
        for row in rows:
            classified = self.classify_probe_row(row)
            if isinstance(classified, ContactSeed):
                self.seeds.append(classified)
            else:
                self.obstructions.append(classified)

    def promote(self) -> list[PromotionDecision]:
        decisions: list[PromotionDecision] = []
        for key, seeds in sorted(self._seed_groups().items()):
            rows = self._rows_for_group(key)
            dirty_count = sum(1 for row in rows if not _is_clean_success(row))
            clean_count = sum(1 for seed in seeds if seed.kind == ContactKind.STRICT_CONTACT_SEED)
            visibility_count = sum(1 for seed in seeds if seed.kind == ContactKind.VISIBILITY_CONTACT)
            total = len(rows) if rows else len(seeds)
            failure_rate = dirty_count / total if total else 0.0
            distinct = len({_declaration_for_distinct(seed) for seed in seeds})
            transfer_successes = max(0, distinct - 1)
            reasons: list[str] = []
            if visibility_count and not self.policy.allow_visibility_promotion:
                reasons.append("visibility_contact_not_promotable")
            if clean_count < self.policy.min_clean_successes:
                reasons.append("insufficient_clean_successes")
            if transfer_successes < self.policy.min_transfer_successes:
                reasons.append("insufficient_transfer_successes")
            if failure_rate > self.policy.max_failure_rate:
                reasons.append("failure_rate_too_high")
            if distinct < self.policy.require_distinct_declarations:
                reasons.append("insufficient_distinct_declarations")
            promote = not reasons
            law = None
            if promote:
                law = PromotedRouteLaw(
                    law_id=content_id("promoted_route_law", [key, [seed.seed_id for seed in seeds]]),
                    law_kind="PROMOTED_ROUTE_LAW",
                    shape=seeds[0].shape,
                    repair_strategy=seeds[0].repair_strategy,
                    support=len(seeds),
                    clean_successes=clean_count,
                    transfer_successes=transfer_successes,
                    distinct_declarations=distinct,
                    failure_rate=failure_rate,
                    examples=tuple(seed.decl_name for seed in seeds),
                    source_seed_ids=tuple(seed.seed_id for seed in seeds),
                    metadata={"group_key": key, "not_truth_certificate": True},
                )
            decisions.append(PromotionDecision(key, promote, law, tuple(reasons or ["promotion_policy_satisfied"])))
        self._decisions = decisions
        return decisions

    def build_transfer_queue(self) -> list[TransferTest]:
        tests: list[TransferTest] = []
        for seed in self.seeds:
            if seed.kind != ContactKind.STRICT_CONTACT_SEED:
                continue
            tests.append(
                TransferTest(
                    transfer_test_id=content_id("transfer_test", [seed.seed_id, seed.shape, seed.repair_strategy]),
                    status=ContactStatus.TRANSFER_TEST,
                    shape=seed.shape,
                    repair_strategy=seed.repair_strategy,
                    source_seed_id=seed.seed_id,
                    decl_name=seed.decl_name,
                    priority=1.0,
                    metadata={"next_action": "transfer-test clean seed on nearby compatible declarations"},
                )
            )
        return tests

    def build_repair_queue(self) -> list[ContactObstruction]:
        return list(self.obstructions)

    def to_route_law_rows(self) -> list[dict[str, Any]]:
        decisions = self._decisions or self.promote()
        return [decision.law.to_dict() for decision in decisions if decision.law is not None]

    def to_contact_seed_rows(self) -> list[dict[str, Any]]:
        return [seed.to_dict() for seed in self.seeds]

    def to_obstruction_rows(self) -> list[dict[str, Any]]:
        return [obstruction.to_dict() for obstruction in self.obstructions]

    def to_next_queue_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for test in self.build_transfer_queue():
            row = test.to_dict()
            row["queue_kind"] = "TRANSFER_TEST"
            rows.append(row)
        for obstruction in self.build_repair_queue():
            row = obstruction.to_dict()
            row["queue_kind"] = "REPAIR_OBSTRUCTION"
            row["priority"] = 0.8
            rows.append(row)
        for law in self.to_route_law_rows():
            rows.append(
                {
                    "queue_kind": "EXPAND_PROMOTED_LAW",
                    "law_id": law["law_id"],
                    "shape": law["shape"],
                    "repair_strategy": law["repair_strategy"],
                    "priority": 0.7,
                    "advisory": True,
                    "metadata": json.dumps({"next_action": "expand promoted law to neighboring shape declarations"}),
                }
            )
        return rows

    def summary(self) -> dict[str, Any]:
        laws = self.to_route_law_rows()
        return {
            "seed_count": len(self.seeds),
            "strict_contact_seed_count": sum(1 for seed in self.seeds if seed.kind == ContactKind.STRICT_CONTACT_SEED),
            "visibility_contact_count": sum(1 for seed in self.seeds if seed.kind == ContactKind.VISIBILITY_CONTACT),
            "obstruction_count": len(self.obstructions),
            "promoted_route_law_count": len(laws),
            "transfer_queue_count": len(self.build_transfer_queue()),
            "repair_queue_count": len(self.build_repair_queue()),
            "advisory": True,
            "truth_boundary": "route_laws_guide_scheduling_not_truth",
        }

    def _seed(self, row: dict[str, Any], kind: ContactKind, decl_name: str, shape: str, repair_strategy: str) -> ContactSeed:
        return ContactSeed(
            seed_id=content_id("contact_seed", [row.get("probe_id", ""), decl_name, kind.value, shape, repair_strategy]),
            kind=kind,
            decl_name=decl_name,
            shape=shape,
            repair_strategy=repair_strategy,
            root_decl=str(row.get("root_decl", "")),
            target_decl=str(row.get("target_decl", "")),
            expected_type=str(row.get("expected_type", "")),
            proof_term=str(row.get("proof_term", "")),
            source_probe_id=str(row.get("probe_id", "")),
            metadata=_metadata(row),
        )

    def _obstruction(self, row: dict[str, Any], decl_name: str, shape: str, repair_strategy: str) -> ContactObstruction:
        return ContactObstruction(
            obstruction_id=content_id("contact_obstruction", [row.get("probe_id", ""), decl_name, row.get("failure_class", "")]),
            status=ContactStatus.REPAIRABLE_OBSTRUCTION,
            failure_class=_failure_class(row),
            decl_name=decl_name,
            shape=shape,
            repair_strategy=repair_strategy,
            failure_detail=str(row.get("failure_detail", "")),
            source_probe_id=str(row.get("probe_id", "")),
            metadata=_metadata(row),
        )

    def _seed_groups(self) -> dict[str, list[ContactSeed]]:
        groups: dict[str, list[ContactSeed]] = defaultdict(list)
        for seed in self.seeds:
            groups[_group_key(seed.shape, seed.repair_strategy, seed.kind)].append(seed)
        return groups

    def _rows_for_group(self, key: str) -> list[dict[str, Any]]:
        rows = []
        for row in self._rows:
            kind = ContactKind.VISIBILITY_CONTACT if "VISIBILITY" in str(row.get("level", "")).upper() else ContactKind.STRICT_CONTACT_SEED
            if _group_key(str(row.get("shape", "")), str(row.get("repair_strategy", row.get("strategy", ""))), kind) == key:
                rows.append(row)
        return rows


def _group_key(shape: str, repair_strategy: str, kind: ContactKind) -> str:
    return "|".join([shape or "unknown_shape", repair_strategy or "unknown_strategy", kind.value])


def _decl_name(row: dict[str, Any]) -> str:
    return str(row.get("theorem_decl") or row.get("target_decl") or row.get("root_decl") or row.get("decl_name") or "")


def _declaration_for_distinct(seed: ContactSeed) -> str:
    return seed.decl_name or seed.target_decl or seed.root_decl or seed.seed_id


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "ok", "success"}


def _markers_clean(row: dict[str, Any]) -> bool:
    return (
        _truthy(row.get("marker_start"))
        and _truthy(row.get("marker_ok"))
        and _truthy(row.get("marker_end"))
        and not _truthy(row.get("dirty_interval"))
        and not _truthy(row.get("operational_failure"))
        and str(row.get("failure_class", "")).strip() == ""
    )


def _is_clean_success(row: dict[str, Any]) -> bool:
    return _truthy(row.get("strict_success")) and _markers_clean(row)


def _failure_class(row: dict[str, Any]) -> str:
    failure = str(row.get("failure_class", "")).strip()
    if failure:
        return failure
    if _truthy(row.get("dirty_interval")):
        return "parse_or_command_boundary_error"
    if _truthy(row.get("operational_failure")):
        return "resource_limit"
    if not (_truthy(row.get("marker_start")) and _truthy(row.get("marker_ok")) and _truthy(row.get("marker_end"))):
        return "marker_missing"
    return "unknown_contact_failure"


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        base = dict(metadata)
    else:
        raw = row.get("metadata_json")
        if raw:
            try:
                base = json.loads(str(raw))
            except json.JSONDecodeError:
                base = {"metadata_json_parse_error": str(raw)}
        else:
            base = {}
    for key in ("line_start", "line_end", "batch_file", "batch_rc", "batch_elapsed", "interval_text"):
        if key in row:
            base[key] = row.get(key)
    base["advisory"] = True
    return base

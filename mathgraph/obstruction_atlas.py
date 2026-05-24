"""Obstruction atlas schemas and constructor-pressure records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.root_nodes import _float, _int


@dataclass(frozen=True)
class ConstructorPressure:
    constructor: str
    pressure_score: float = 0.0
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "constructor": self.constructor,
            "pressure_score": self.pressure_score,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class ObstructionNode:
    obstruction_id: str
    obstruction_signature: str
    failure_reason: str
    derivation_rule: str = ""
    source_target_basin: str = ""
    forced_transition: str = ""
    table_motif: str = ""
    rows: int = 0
    unique_sources: int = 0
    unique_targets: int = 0
    unique_seed_sources: int = 0
    unique_seed_targets: int = 0
    unique_tables: int = 0
    obstruction_pressure_score: float = 0.0
    next_constructor_pressure: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "obstruction_id": self.obstruction_id,
            "obstruction_signature": self.obstruction_signature,
            "failure_reason": self.failure_reason,
            "derivation_rule": self.derivation_rule,
            "source_target_basin": self.source_target_basin,
            "forced_transition": self.forced_transition,
            "table_motif": self.table_motif,
            "rows": self.rows,
            "unique_sources": self.unique_sources,
            "unique_targets": self.unique_targets,
            "unique_seed_sources": self.unique_seed_sources,
            "unique_seed_targets": self.unique_seed_targets,
            "unique_tables": self.unique_tables,
            "obstruction_pressure_score": self.obstruction_pressure_score,
            "next_constructor_pressure": dict(self.next_constructor_pressure),
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObstructionNode":
        signature = str(
            data.get("obstruction_signature")
            or data.get("failure_reason")
            or data.get("reason")
            or ""
        )
        return cls(
            obstruction_id=str(data.get("obstruction_id") or data.get("id") or signature),
            obstruction_signature=signature,
            failure_reason=str(data.get("failure_reason") or data.get("reason") or ""),
            derivation_rule=str(data.get("derivation_rule", "")),
            source_target_basin=str(data.get("source_target_basin") or data.get("basin") or ""),
            forced_transition=str(data.get("forced_transition", "")),
            table_motif=str(data.get("table_motif") or data.get("motif") or ""),
            rows=_int(data.get("rows", data.get("support_count", 0))),
            unique_sources=_int(data.get("unique_sources")),
            unique_targets=_int(data.get("unique_targets")),
            unique_seed_sources=_int(data.get("unique_seed_sources")),
            unique_seed_targets=_int(data.get("unique_seed_targets")),
            unique_tables=_int(data.get("unique_tables")),
            obstruction_pressure_score=_float(data.get("obstruction_pressure_score")),
            next_constructor_pressure=dict(data.get("next_constructor_pressure", {})),
            evidence=dict(data.get("evidence", {"row": dict(data)} if data else {})),
        )


@dataclass(frozen=True)
class ObstructionRecord:
    obstruction_id: str
    obstruction_name: str
    basin: str
    deep_ir_candidate: str
    stage: str
    support_count: int = 0
    failed_constructor_rules: tuple[str, ...] = ()
    residual_pair_ids: tuple[str, ...] = ()
    status: str = "named_obstruction_advisory"
    advisory_only: bool = True
    can_promote_truth: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "obstruction_id": self.obstruction_id,
            "obstruction_name": self.obstruction_name,
            "basin": self.basin,
            "deep_ir_candidate": self.deep_ir_candidate,
            "stage": self.stage,
            "support_count": self.support_count,
            "failed_constructor_rules": list(self.failed_constructor_rules),
            "residual_pair_ids": list(self.residual_pair_ids),
            "status": self.status,
            "advisory_only": True,
            "can_promote_truth": False,
            "metadata": dict(self.metadata),
        }


def make_obstruction_name(basin: str, deep_ir_candidate: str, stage: str = "residual") -> str:
    return f"{_slug(basin)}__{_slug(deep_ir_candidate)}__{_slug(stage)}_unresolved"


def summarize_obstructions(rows: Any, stage: str = "residual") -> list[ObstructionRecord]:
    data = _records(rows)
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in data:
        basin = str(row.get("basin", "mixed_sair_false_pair") or "mixed_sair_false_pair")
        deep = str(row.get("deep_ir_candidate", "shallow") or "shallow")
        buckets.setdefault((basin, deep), []).append(row)
    out = []
    for (basin, deep), group in sorted(buckets.items()):
        name = make_obstruction_name(basin, deep, stage)
        failed = tuple(failed_constructor_rules(group))
        pair_ids = tuple(str(row.get("pair_id") or row.get("task_id") or "") for row in group if row.get("pair_id") or row.get("task_id"))
        out.append(
            ObstructionRecord(
                obstruction_id=f"obs_{abs(hash((name, len(group)))):x}",
                obstruction_name=name,
                basin=basin,
                deep_ir_candidate=deep,
                stage=stage,
                support_count=len(group),
                failed_constructor_rules=failed,
                residual_pair_ids=pair_ids,
            )
        )
    return out


def failed_constructor_rules(rows: Any) -> list[str]:
    data = _records(rows)
    counts: dict[str, int] = {}
    for row in data:
        for key in ("failed_constructor", "constructor_family", "route", "policy"):
            value = row.get(key)
            if value:
                counts[str(value)] = counts.get(str(value), 0) + 1
    return [f"{name}:{count}" for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def residual_queue(records: list[ObstructionRecord]) -> list[dict[str, Any]]:
    return [
        {
            "task_kind": "obstruction_analysis",
            "obstruction_name": rec.obstruction_name,
            "basin": rec.basin,
            "priority": rec.support_count,
            "advisory_only": True,
            "can_promote_truth": False,
        }
        for rec in records
    ]


def _records(rows: Any) -> list[dict[str, Any]]:
    if rows is None:
        return []
    if hasattr(rows, "to_dict"):
        try:
            value = rows.to_dict("records")
            if isinstance(value, list):
                return [dict(row) for row in value]
        except TypeError:
            pass
    return [dict(row) for row in rows]


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value or "")).strip("_") or "unknown"

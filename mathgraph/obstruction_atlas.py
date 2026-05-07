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

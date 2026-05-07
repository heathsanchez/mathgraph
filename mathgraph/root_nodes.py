"""Root node atlas schemas for certificate-universe distillation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _fields(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value in (None, ""):
        return {}
    return {"raw": value}


@dataclass(frozen=True)
class RootAlias:
    alias: str
    canonical_name: str
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "canonical_name": self.canonical_name,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RootAlias":
        return cls(
            alias=str(data.get("alias", "")),
            canonical_name=str(data.get("canonical_name", "")),
            reason=str(data.get("reason", "")),
            evidence=dict(data.get("evidence", {})),
        )


@dataclass(frozen=True)
class RootReasonLink:
    root_node_id: str
    reason_node_id: str
    support_count: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_node_id": self.root_node_id,
            "reason_node_id": self.reason_node_id,
            "support_count": self.support_count,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class RootObstructionLink:
    root_node_id: str
    obstruction_id: str
    pressure_score: float = 0.0
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_node_id": self.root_node_id,
            "obstruction_id": self.obstruction_id,
            "pressure_score": self.pressure_score,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class RootCertificateCoverage:
    root_node_id: str
    rows: int = 0
    unique_pairs: int = 0
    unique_sources: int = 0
    unique_targets: int = 0
    unique_tables: int = 0
    unique_motifs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_node_id": self.root_node_id,
            "rows": self.rows,
            "unique_pairs": self.unique_pairs,
            "unique_sources": self.unique_sources,
            "unique_targets": self.unique_targets,
            "unique_tables": self.unique_tables,
            "unique_motifs": self.unique_motifs,
        }


@dataclass(frozen=True)
class RootNode:
    root_node_id: str
    canonical_name: str
    root_type: str = "certificate_root"
    root_key: str = ""
    root_key_fields: dict[str, Any] = field(default_factory=dict)
    table_motif: str = ""
    algebra_shape: str = ""
    source_target_basin: str = ""
    forced_transition: str = ""
    support_count: int = 0
    rows: int = 0
    unique_pairs: int = 0
    unique_sources: int = 0
    unique_targets: int = 0
    unique_tables: int = 0
    unique_motifs: int = 0
    load_bearing_score: float = 0.0
    compression_ratio: float = 0.0
    coverage_density: float = 0.0
    status: str = "candidate"
    evidence: dict[str, Any] = field(default_factory=dict)
    aliases: list[dict[str, Any]] = field(default_factory=list)
    created_from_run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_node_id": self.root_node_id,
            "canonical_name": self.canonical_name,
            "root_type": self.root_type,
            "root_key": self.root_key,
            "root_key_fields": dict(self.root_key_fields),
            "table_motif": self.table_motif,
            "algebra_shape": self.algebra_shape,
            "source_target_basin": self.source_target_basin,
            "forced_transition": self.forced_transition,
            "support_count": self.support_count,
            "rows": self.rows,
            "unique_pairs": self.unique_pairs,
            "unique_sources": self.unique_sources,
            "unique_targets": self.unique_targets,
            "unique_tables": self.unique_tables,
            "unique_motifs": self.unique_motifs,
            "load_bearing_score": self.load_bearing_score,
            "compression_ratio": self.compression_ratio,
            "coverage_density": self.coverage_density,
            "status": self.status,
            "evidence": dict(self.evidence),
            "aliases": list(self.aliases),
            "created_from_run_id": self.created_from_run_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RootNode":
        canonical = str(
            data.get("canonical_name")
            or data.get("root_name")
            or data.get("table_name")
            or data.get("table_motif")
            or "ROOT_UNKNOWN"
        )
        return cls(
            root_node_id=str(data.get("root_node_id") or data.get("root_id") or canonical),
            canonical_name=canonical,
            root_type=str(data.get("root_type", "certificate_root")),
            root_key=str(data.get("root_key", canonical)),
            root_key_fields=_fields(data.get("root_key_fields")),
            table_motif=str(data.get("table_motif") or data.get("motif") or ""),
            algebra_shape=str(data.get("algebra_shape") or ""),
            source_target_basin=str(data.get("source_target_basin") or data.get("basin") or ""),
            forced_transition=str(data.get("forced_transition") or ""),
            support_count=_int(data.get("support_count", data.get("rows", 0))),
            rows=_int(data.get("rows", data.get("support_count", 0))),
            unique_pairs=_int(data.get("unique_pairs")),
            unique_sources=_int(data.get("unique_sources")),
            unique_targets=_int(data.get("unique_targets")),
            unique_tables=_int(data.get("unique_tables")),
            unique_motifs=_int(data.get("unique_motifs")),
            load_bearing_score=_float(data.get("load_bearing_score")),
            compression_ratio=_float(data.get("compression_ratio")),
            coverage_density=_float(data.get("coverage_density")),
            status=str(data.get("status", "candidate")),
            evidence=dict(data.get("evidence", {"row": dict(data)} if data else {})),
            aliases=list(data.get("aliases", [])),
            created_from_run_id=str(data.get("created_from_run_id", "")),
        )

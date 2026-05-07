"""Reason node schemas: the atom of understanding in MathGraph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mathgraph.root_nodes import _fields, _float, _int


@dataclass(frozen=True)
class ReasonNode:
    reason_node_id: str
    reason_type: str
    reason_key: str
    reason_key_fields: dict[str, Any] = field(default_factory=dict)
    source_basin: str = ""
    target_basin: str = ""
    table_motif: str = ""
    algebra_shape: str = ""
    delta_var_bin: str = ""
    delta_ops_bin: str = ""
    forced_transition: str = ""
    derivation_rule: str = ""
    support_count: int = 0
    rows: int = 0
    unique_pairs: int = 0
    unique_sources: int = 0
    unique_targets: int = 0
    unique_tables: int = 0
    unique_motifs: int = 0
    reason_score: float = 0.0
    reason_compression_ratio: float = 0.0
    status: str = "candidate"
    explanation_template: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason_node_id": self.reason_node_id,
            "reason_type": self.reason_type,
            "reason_key": self.reason_key,
            "reason_key_fields": dict(self.reason_key_fields),
            "source_basin": self.source_basin,
            "target_basin": self.target_basin,
            "table_motif": self.table_motif,
            "algebra_shape": self.algebra_shape,
            "delta_var_bin": self.delta_var_bin,
            "delta_ops_bin": self.delta_ops_bin,
            "forced_transition": self.forced_transition,
            "derivation_rule": self.derivation_rule,
            "support_count": self.support_count,
            "rows": self.rows,
            "unique_pairs": self.unique_pairs,
            "unique_sources": self.unique_sources,
            "unique_targets": self.unique_targets,
            "unique_tables": self.unique_tables,
            "unique_motifs": self.unique_motifs,
            "reason_score": self.reason_score,
            "reason_compression_ratio": self.reason_compression_ratio,
            "status": self.status,
            "explanation_template": self.explanation_template,
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasonNode":
        key = str(data.get("reason_key") or data.get("reason_type") or data.get("table_motif") or "")
        return cls(
            reason_node_id=str(data.get("reason_node_id") or data.get("reason_id") or key),
            reason_type=str(data.get("reason_type") or "certificate_reason"),
            reason_key=key,
            reason_key_fields=_fields(data.get("reason_key_fields")),
            source_basin=str(data.get("source_basin", "")),
            target_basin=str(data.get("target_basin", "")),
            table_motif=str(data.get("table_motif") or data.get("motif") or ""),
            algebra_shape=str(data.get("algebra_shape", "")),
            delta_var_bin=str(data.get("delta_var_bin", "")),
            delta_ops_bin=str(data.get("delta_ops_bin", "")),
            forced_transition=str(data.get("forced_transition", "")),
            derivation_rule=str(data.get("derivation_rule", "")),
            support_count=_int(data.get("support_count", data.get("rows", 0))),
            rows=_int(data.get("rows", data.get("support_count", 0))),
            unique_pairs=_int(data.get("unique_pairs")),
            unique_sources=_int(data.get("unique_sources")),
            unique_targets=_int(data.get("unique_targets")),
            unique_tables=_int(data.get("unique_tables")),
            unique_motifs=_int(data.get("unique_motifs")),
            reason_score=_float(data.get("reason_score")),
            reason_compression_ratio=_float(data.get("reason_compression_ratio")),
            status=str(data.get("status", "candidate")),
            explanation_template=str(
                data.get("explanation_template")
                or "This reason compresses repeated certificate behavior."
            ),
            evidence=dict(data.get("evidence", {"row": dict(data)} if data else {})),
        )

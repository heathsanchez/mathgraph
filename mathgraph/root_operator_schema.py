"""Root operator schema IR for advisory constructor candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from mathgraph.hashing import content_id


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    kind: str
    values: tuple[Any, ...] = ()
    default: Any | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "values": list(self.values),
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParameterSpec":
        return cls(
            name=str(data.get("name", "")),
            kind=str(data.get("kind", "unknown")),
            values=tuple(data.get("values", ()) or ()),
            default=data.get("default"),
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class RootOperatorSchema:
    schema_id: str
    name: str
    atoms: tuple[dict[str, Any], ...]
    parameters: tuple[ParameterSpec, ...] = ()
    compact_name: str = ""
    advisory_only: bool = True
    verifier_promoted: bool = False
    evidence_kind: str = "ADVISORY_ROOT_OPERATOR_SCHEMA"
    source_trace_ids: tuple[str, ...] = ()
    support: int = 0
    family_count: int = 0
    latent_root_count: int = 0
    hidden_program_count: int = 0
    compression_gain_est: float = 0.0
    promotion_score: float = 0.0
    promoted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "advisory_only", True)
        object.__setattr__(self, "verifier_promoted", False)
        if not self.compact_name:
            object.__setattr__(self, "compact_name", compact_schema_name(self.atoms))

    @classmethod
    def create(
        cls,
        atoms: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        parameters: list[ParameterSpec] | tuple[ParameterSpec, ...] = (),
        *,
        name: str = "",
        source_trace_ids: tuple[str, ...] = (),
        support: int = 0,
        family_count: int = 0,
        latent_root_count: int = 0,
        hidden_program_count: int = 0,
        compression_gain_est: float = 0.0,
        promotion_score: float = 0.0,
        promoted: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "RootOperatorSchema":
        canonical_atoms = tuple(_canonical_atom(atom) for atom in atoms)
        canonical_params = tuple(parameters)
        schema_name = name or compact_schema_name(canonical_atoms)
        schema_id = make_root_operator_schema_id(canonical_atoms, canonical_params)
        return cls(
            schema_id=schema_id,
            name=schema_name,
            atoms=canonical_atoms,
            parameters=canonical_params,
            compact_name=compact_schema_name(canonical_atoms),
            source_trace_ids=tuple(source_trace_ids),
            support=support,
            family_count=family_count,
            latent_root_count=latent_root_count,
            hidden_program_count=hidden_program_count,
            compression_gain_est=float(compression_gain_est),
            promotion_score=float(promotion_score),
            promoted=bool(promoted),
            metadata=dict(metadata or {}),
        )

    def with_promotion(self, *, promotion_score: float, promoted: bool, compression_gain_est: float | None = None) -> "RootOperatorSchema":
        return RootOperatorSchema(
            schema_id=self.schema_id,
            name=self.name,
            atoms=self.atoms,
            parameters=self.parameters,
            compact_name=self.compact_name,
            advisory_only=True,
            verifier_promoted=False,
            evidence_kind=self.evidence_kind,
            source_trace_ids=self.source_trace_ids,
            support=self.support,
            family_count=self.family_count,
            latent_root_count=self.latent_root_count,
            hidden_program_count=self.hidden_program_count,
            compression_gain_est=self.compression_gain_est if compression_gain_est is None else float(compression_gain_est),
            promotion_score=float(promotion_score),
            promoted=bool(promoted),
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "name": self.name,
            "compact_name": self.compact_name,
            "atoms": [dict(atom) for atom in self.atoms],
            "parameters": [param.to_dict() for param in self.parameters],
            "advisory_only": True,
            "verifier_promoted": False,
            "evidence_kind": self.evidence_kind,
            "source_trace_ids": list(self.source_trace_ids),
            "support": self.support,
            "family_count": self.family_count,
            "latent_root_count": self.latent_root_count,
            "hidden_program_count": self.hidden_program_count,
            "compression_gain_est": self.compression_gain_est,
            "promotion_score": self.promotion_score,
            "promoted": self.promoted,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RootOperatorSchema":
        return cls(
            schema_id=str(data.get("schema_id") or make_root_operator_schema_id(tuple(data.get("atoms", ()) or ()), ())),
            name=str(data.get("name", "")),
            atoms=tuple(_canonical_atom(atom) for atom in data.get("atoms", []) or []),
            parameters=tuple(ParameterSpec.from_dict(item) for item in data.get("parameters", []) or []),
            compact_name=str(data.get("compact_name", "")),
            advisory_only=True,
            verifier_promoted=False,
            evidence_kind=str(data.get("evidence_kind", "ADVISORY_ROOT_OPERATOR_SCHEMA")),
            source_trace_ids=tuple(data.get("source_trace_ids", ()) or ()),
            support=int(data.get("support", 0) or 0),
            family_count=int(data.get("family_count", 0) or 0),
            latent_root_count=int(data.get("latent_root_count", 0) or 0),
            hidden_program_count=int(data.get("hidden_program_count", 0) or 0),
            compression_gain_est=float(data.get("compression_gain_est", 0.0) or 0.0),
            promotion_score=float(data.get("promotion_score", 0.0) or 0.0),
            promoted=bool(data.get("promoted", False)),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "RootOperatorSchema":
        return cls.from_dict(json.loads(text))

    def to_row(self) -> dict[str, Any]:
        data = self.to_dict()
        for key in ("atoms", "parameters", "source_trace_ids", "metadata"):
            data[key] = json.dumps(data[key], sort_keys=True, ensure_ascii=False)
        return data


@dataclass(frozen=True)
class RootOperatorInstance:
    instance_id: str
    schema_id: str
    parameter_values: dict[str, Any]
    atoms: tuple[dict[str, Any], ...]
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "schema_id": self.schema_id,
            "parameter_values": dict(self.parameter_values),
            "atoms": [dict(atom) for atom in self.atoms],
            "advisory_only": True,
        }


@dataclass(frozen=True)
class RootOperatorPromotionResult:
    schema: RootOperatorSchema
    promoted: bool
    promotion_score: float
    solve_rate_gain: float
    residual_compression: int
    oracle_fraction_captured: float
    reasons: tuple[str, ...] = ()
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema.to_dict(),
            "promoted": self.promoted,
            "promotion_score": self.promotion_score,
            "solve_rate_gain": self.solve_rate_gain,
            "residual_compression": self.residual_compression,
            "oracle_fraction_captured": self.oracle_fraction_captured,
            "reasons": list(self.reasons),
            "advisory_only": True,
            "terminal_form": None,
        }


@dataclass(frozen=True)
class RootOperatorEvaluationSummary:
    base_solve_rate: float
    literal_solve_rate: float
    root_schema_solve_rate: float
    oracle_solve_rate: float
    oracle_fraction_captured: float
    raw_schema_count: int
    promoted_schema_count: int
    residual_compression: dict[str, Any]
    overall: str
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_solve_rate": self.base_solve_rate,
            "literal_solve_rate": self.literal_solve_rate,
            "root_schema_solve_rate": self.root_schema_solve_rate,
            "oracle_solve_rate": self.oracle_solve_rate,
            "oracle_fraction_captured": self.oracle_fraction_captured,
            "raw_schema_count": self.raw_schema_count,
            "promoted_schema_count": self.promoted_schema_count,
            "residual_compression": dict(self.residual_compression),
            "overall": self.overall,
            "advisory_only": True,
        }


def make_root_operator_schema_id(atoms: tuple[dict[str, Any], ...], parameters: tuple[ParameterSpec, ...]) -> str:
    return content_id(
        "root_schema",
        {
            "atoms": [_canonical_atom(atom) for atom in atoms],
            "parameters": [param.to_dict() for param in parameters],
        },
    )


def make_root_operator_instance(schema: RootOperatorSchema, parameter_values: dict[str, Any]) -> RootOperatorInstance:
    atoms = []
    for atom in schema.atoms:
        params = {}
        for key, value in dict(atom.get("params", {})).items():
            if isinstance(value, str) and value.startswith("$"):
                params[key] = parameter_values.get(value[1:], value)
            else:
                params[key] = value
        atoms.append({"name": atom.get("name", ""), "kind": atom.get("kind", ""), "params": params})
    return RootOperatorInstance(
        instance_id=content_id("root_schema_instance", [schema.schema_id, parameter_values]),
        schema_id=schema.schema_id,
        parameter_values=dict(parameter_values),
        atoms=tuple(atoms),
    )


def compact_schema_name(atoms: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> str:
    parts = []
    for atom in atoms:
        params = dict(atom.get("params", {}))
        suffix = []
        for key in sorted(params):
            value = params[key]
            if isinstance(value, str) and value.startswith("$"):
                suffix.append(key)
            else:
                suffix.append(str(value))
        parts.append(atom.get("name", "op") + (("_" + "_".join(suffix)) if suffix else ""))
    return "__".join(parts)


def _canonical_atom(atom: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(atom.get("name", "")),
        "kind": str(atom.get("kind", "")),
        "params": {str(key): atom.get("params", {}).get(key) for key in sorted(dict(atom.get("params", {})))},
    }

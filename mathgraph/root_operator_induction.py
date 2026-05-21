"""Typed anti-unification for advisory root operator schemas."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from mathgraph.root_operator_schema import ParameterSpec, RootOperatorSchema


def normalize_atom(atom: dict[str, Any]) -> dict[str, Any]:
    params = dict(atom.get("params", {}) or {})
    return {
        "name": str(atom.get("name", "")),
        "kind": str(atom.get("kind", "")),
        "params": {str(key): params[key] for key in sorted(params)},
    }


def normalize_trace_atoms(atoms: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(normalize_atom(atom) for atom in atoms)


def trace_signature(trace: dict[str, Any]) -> tuple[str, ...]:
    return tuple(atom["name"] for atom in normalize_trace_atoms(trace.get("atoms", []) or []))


def anti_unify_trace_group(traces: list[dict[str, Any]]) -> RootOperatorSchema | None:
    if not traces:
        return None
    normalized = [normalize_trace_atoms(trace.get("atoms", []) or []) for trace in traces]
    lengths = {len(atoms) for atoms in normalized}
    if len(lengths) != 1 or not normalized[0]:
        return None
    schema_atoms: list[dict[str, Any]] = []
    parameters: dict[str, ParameterSpec] = {}
    for idx in range(len(normalized[0])):
        atoms_at_position = [atoms[idx] for atoms in normalized]
        names = sorted({atom["name"] for atom in atoms_at_position})
        kinds = sorted({atom["kind"] for atom in atoms_at_position})
        schema_name: str
        if len(names) == 1:
            schema_name = names[0]
        else:
            param_name = f"op_{idx}"
            schema_name = f"${param_name}"
            parameters[param_name] = ParameterSpec(param_name, "operator_name", tuple(names))
        schema_kind = kinds[0] if len(kinds) == 1 else "generic"
        all_param_keys = sorted({key for atom in atoms_at_position for key in atom["params"]})
        schema_params: dict[str, Any] = {}
        for key in all_param_keys:
            values = tuple(atom["params"].get(key) for atom in atoms_at_position)
            unique = tuple(sorted({value for value in values}, key=str))
            if len(unique) == 1:
                schema_params[key] = unique[0]
            else:
                kind = _parameter_kind(key, unique)
                param_name = _parameter_name(key, kind, idx)
                schema_params[key] = f"${param_name}"
                parameters[param_name] = ParameterSpec(param_name, kind, unique)
        schema_atoms.append({"name": schema_name, "kind": schema_kind, "params": schema_params})
    families = {str(trace.get("family", "")) for trace in traces if trace.get("family")}
    roots = {str(trace.get("latent_root", "")) for trace in traces if trace.get("latent_root")}
    hidden = {str(trace.get("hidden_program", "")) for trace in traces if trace.get("hidden_program")}
    compression_gain = max(0.0, float(len(traces) - 1))
    return RootOperatorSchema.create(
        schema_atoms,
        tuple(parameters.values()),
        source_trace_ids=tuple(str(trace.get("trace_id", "")) for trace in traces if trace.get("trace_id")),
        support=len(traces),
        family_count=len(families),
        latent_root_count=len(roots),
        hidden_program_count=len(hidden),
        compression_gain_est=compression_gain,
        promotion_score=compression_gain / max(1.0, len(schema_atoms)),
        promoted=False,
        metadata={"induction": "anti_unify_trace_group"},
    )


def induce_root_operator_schemas(trace_records: list[dict[str, Any]]) -> list[RootOperatorSchema]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for trace in trace_records:
        groups[trace_signature(trace)].append(trace)
    schemas = []
    for traces in groups.values():
        schema = anti_unify_trace_group(traces)
        if schema and _is_useful_schema(schema):
            schemas.append(schema)
    return _dedupe_schemas(schemas)


def induce_compositional_root_schemas(trace_records: list[dict[str, Any]]) -> list[RootOperatorSchema]:
    candidates = induce_root_operator_schemas(trace_records)
    subsequence_records: list[dict[str, Any]] = []
    for trace in trace_records:
        atoms = list(trace.get("atoms", []) or [])
        for start in range(len(atoms)):
            for end in range(start + 2, len(atoms) + 1):
                subtrace = dict(trace)
                subtrace["trace_id"] = f"{trace.get('trace_id', '')}:{start}:{end}"
                subtrace["atoms"] = atoms[start:end]
                subsequence_records.append(subtrace)
    candidates.extend(induce_root_operator_schemas(subsequence_records))
    return _dedupe_schemas(candidates)


def _parameter_kind(key: str, values: tuple[Any, ...]) -> str:
    lower = key.lower()
    if "color" in lower or all(isinstance(value, int) and 0 <= value <= 9 for value in values if value is not None):
        return "color"
    if lower in {"axis", "direction"} or set(values).issubset({"x", "y", "left", "right", "up", "down", "horizontal", "vertical"}):
        return "axis"
    if "distance" in lower or all(isinstance(value, int) for value in values if value is not None):
        return "distance"
    if "selector" in lower or any(str(value).startswith("extract_") for value in values):
        return "selector"
    return "value"


def _parameter_name(key: str, kind: str, idx: int) -> str:
    if kind in {"color", "axis", "distance", "selector"}:
        return key if key else f"{kind}_{idx}"
    return f"{key or 'value'}_{idx}"


def _is_useful_schema(schema: RootOperatorSchema) -> bool:
    if schema.support <= 1 and not schema.parameters:
        return False
    if schema.support < 2:
        return False
    return bool(schema.parameters) or schema.support >= 3


def _dedupe_schemas(schemas: list[RootOperatorSchema]) -> list[RootOperatorSchema]:
    by_id: dict[str, RootOperatorSchema] = {}
    for schema in schemas:
        current = by_id.get(schema.schema_id)
        if current is None or schema.support > current.support:
            by_id[schema.schema_id] = schema
    return sorted(by_id.values(), key=lambda schema: (-schema.support, schema.compact_name, schema.schema_id))

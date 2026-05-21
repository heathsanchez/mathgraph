"""Duck-typed adapters into advisory Reason Atlas entries."""

from __future__ import annotations

from typing import Any

from mathgraph.hashing import content_id
from mathgraph.reason_atlas_store import ReasonAtlasEntry, ReasonAtlasEntryKind, ReasonAtlasTrust


def entry_from_root_operator_schema(obj: Any, *, source_entry_ids: list[str] | None = None) -> ReasonAtlasEntry:
    payload = _to_dict(obj)
    atoms = _atom_names(getattr(obj, "atoms", payload.get("atoms", [])))
    entry_id = str(getattr(obj, "schema_id", "") or payload.get("schema_id") or content_id("reason_entry_root_schema", payload))
    return ReasonAtlasEntry(
        entry_id=entry_id,
        kind=ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA,
        name=str(getattr(obj, "compact_name", "") or getattr(obj, "name", "") or payload.get("compact_name", "")),
        atoms=atoms,
        pattern=str(getattr(obj, "compact_name", "") or payload.get("compact_name", "")),
        payload=payload,
        source_trace_ids=list(getattr(obj, "source_trace_ids", payload.get("source_trace_ids", [])) or []),
        source_entry_ids=list(source_entry_ids or []),
        evidence_kind=str(getattr(obj, "evidence_kind", "ADVISORY_ROOT_OPERATOR_SCHEMA")),
        trust=ReasonAtlasTrust.PROMOTED_ADVISORY if bool(getattr(obj, "promoted", payload.get("promoted", False))) else ReasonAtlasTrust.CANDIDATE,
        support=int(getattr(obj, "support", payload.get("support", 0)) or 0),
        family_count=int(getattr(obj, "family_count", payload.get("family_count", 0)) or 0),
        root_count=int(getattr(obj, "latent_root_count", payload.get("latent_root_count", 0)) or 0),
        hidden_program_count=int(getattr(obj, "hidden_program_count", payload.get("hidden_program_count", 0)) or 0),
        promotion_score=float(getattr(obj, "promotion_score", payload.get("promotion_score", 0.0)) or 0.0),
    )


def entry_from_root_operator_instance(obj: Any, *, source_entry_ids: list[str] | None = None) -> ReasonAtlasEntry:
    payload = _to_dict(obj)
    entry_id = str(getattr(obj, "instance_id", "") or payload.get("instance_id") or content_id("reason_entry_root_instance", payload))
    return ReasonAtlasEntry(
        entry_id=entry_id,
        kind=ReasonAtlasEntryKind.ROOT_OPERATOR_INSTANCE,
        name=entry_id,
        atoms=_atom_names(getattr(obj, "atoms", payload.get("atoms", []))),
        pattern=str(getattr(obj, "schema_id", payload.get("schema_id", ""))),
        payload=payload,
        source_entry_ids=list(source_entry_ids or []),
        trust=ReasonAtlasTrust.CANDIDATE,
    )


def entry_from_contact_promotion(obj: Any, *, source_entry_ids: list[str] | None = None) -> ReasonAtlasEntry:
    payload = _to_dict(obj)
    kind_text = str(payload.get("kind") or payload.get("status") or payload.get("law_kind") or "")
    kind = _kind_from_text(kind_text)
    entry_id = str(payload.get("law_id") or payload.get("seed_id") or payload.get("obstruction_id") or payload.get("entry_id") or content_id("reason_entry_contact", payload))
    return ReasonAtlasEntry(
        entry_id=entry_id,
        kind=kind,
        name=str(payload.get("name") or payload.get("decl_name") or payload.get("shape") or entry_id),
        atoms=[item for item in [payload.get("shape"), payload.get("repair_strategy"), payload.get("decl_name")] if item],
        pattern=str(payload.get("shape") or payload.get("pattern") or ""),
        payload=payload,
        source_trace_ids=list(payload.get("source_seed_ids") or ([payload.get("source_probe_id")] if payload.get("source_probe_id") else [])),
        source_entry_ids=list(source_entry_ids or []),
        evidence_kind="ADVISORY_CONTACT_PROMOTION",
        trust=ReasonAtlasTrust.PROMOTED_ADVISORY if kind == ReasonAtlasEntryKind.PROMOTED_ROUTE_LAW else ReasonAtlasTrust.CANDIDATE,
        support=int(payload.get("support", 1) or 1),
        promotion_score=float(payload.get("promotion_score", 0.0) or 0.0),
    )


def entry_from_route_law(obj: Any, *, source_entry_ids: list[str] | None = None) -> ReasonAtlasEntry:
    return entry_from_contact_promotion(obj, source_entry_ids=source_entry_ids)


def entry_from_dict(row_or_payload: dict[str, Any], kind: ReasonAtlasEntryKind | str | None = None) -> ReasonAtlasEntry:
    payload = dict(row_or_payload)
    if kind is not None:
        payload["kind"] = kind.value if hasattr(kind, "value") else str(kind)
    if str(payload.get("kind", "")).upper() in {item.value for item in ReasonAtlasEntryKind}:
        return ReasonAtlasEntry.from_dict(payload)
    if "schema_id" in payload or "compact_name" in payload:
        return entry_from_root_operator_schema(payload)
    return entry_from_contact_promotion(payload)


def _to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return dict(obj)


def _atom_names(atoms: Any) -> list[str]:
    names: list[str] = []
    for atom in atoms or []:
        if isinstance(atom, dict):
            name = str(atom.get("name", ""))
            if name:
                names.append(name)
            for value in dict(atom.get("params", {})).values():
                if isinstance(value, str):
                    names.append(value)
        else:
            names.append(str(atom))
    return names


def _kind_from_text(text: str) -> ReasonAtlasEntryKind:
    upper = text.upper()
    for kind in ReasonAtlasEntryKind:
        if upper == kind.value:
            return kind
    if "OBSTRUCTION" in upper:
        return ReasonAtlasEntryKind.REPAIRABLE_OBSTRUCTION
    if "VISIBILITY" in upper:
        return ReasonAtlasEntryKind.VISIBILITY_CONTACT
    if "STRICT_CONTACT_SEED" in upper:
        return ReasonAtlasEntryKind.STRICT_CONTACT_SEED
    return ReasonAtlasEntryKind.PROMOTED_ROUTE_LAW

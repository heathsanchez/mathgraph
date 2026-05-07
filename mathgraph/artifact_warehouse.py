"""High-level import helpers for external MathGraph artifact directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mathgraph.artifact_importers import (
    load_table_registry,
    load_v1662_elevated_false_certificates,
    load_v1662_finite_verified_oracle_update,
    load_v167_obstructions,
    load_v167_reason_nodes,
    load_v167_root_nodes,
    load_v167_table_atlas,
)
from mathgraph.lawbook_store import LawbookStore
from mathgraph.root_consolidation import build_root_alias_map, consolidate_root_nodes


def import_v16_6_2_elevated_false_dir(
    path: str | Path, store: LawbookStore, limit: int | None = None
) -> dict[str, Any]:
    directory = Path(path)
    summary: dict[str, Any] = {"directory": str(directory), "warnings": []}
    elevated = _first_existing(
        directory,
        (
            "elevated_derived_false_certificates_v16_6_2.csv",
            "elevated_derived_false_certificates.csv",
            "finite_verified_oracle_update_v16_6_2.csv",
        ),
    )
    if elevated:
        rows = load_v1662_elevated_false_certificates(elevated, limit=limit)
        summary["refutations"] = store.import_refutations(rows)
        summary["certificates"] = store.import_certificates(rows)
        store.record_artifact_import(elevated, "v16_6_2_elevated_false", len(rows))
    else:
        summary["warnings"].append("No v16.6.2 elevated false certificate CSV found.")
    oracle_update = _first_existing(directory, ("finite_verified_oracle_update_v16_6_2.csv",))
    if oracle_update and oracle_update != elevated:
        rows = load_v1662_finite_verified_oracle_update(oracle_update, limit=limit)
        summary["oracle_update_refutations"] = store.import_refutations(rows)
        store.record_artifact_import(oracle_update, "v16_6_2_oracle_update", len(rows))
    table_registry = _first_existing(directory, ("table_registry_hash_to_table.csv", "table_registry.csv"))
    if table_registry:
        rows = load_table_registry(table_registry, limit=limit)
        summary["tables"] = store.import_tables(rows)
        store.record_artifact_import(table_registry, "table_registry", len(rows))
    return summary


def import_v16_7_root_atlas_dir(
    path: str | Path, store: LawbookStore, limit: int | None = None
) -> dict[str, Any]:
    directory = Path(path)
    summary: dict[str, Any] = {"directory": str(directory), "warnings": []}
    roots_path = _find_pattern(directory, ("root_node_candidates", "roots", "root_nodes"))
    reasons_path = _find_pattern(directory, ("reason_node_candidates", "reasons", "reason_nodes"))
    obstructions_path = _find_pattern(directory, ("obstruction", "obstructions"))
    tables_path = _find_pattern(directory, ("table_atlas", "table_registry"))
    roots = []
    if roots_path:
        roots = load_v167_root_nodes(roots_path, limit=limit)
        canonical = consolidate_root_nodes(roots)
        summary["roots"] = store.import_roots(canonical)
        alias_rows = [
            {"alias": alias, "canonical_name": canonical_name}
            for alias, canonical_name in build_root_alias_map(canonical).items()
        ]
        summary["root_aliases"] = store.import_root_aliases(alias_rows)
        store.record_artifact_import(roots_path, "v16_7_roots", len(roots))
    else:
        summary["warnings"].append("No v16.7 root candidate file found.")
    if reasons_path:
        reasons = load_v167_reason_nodes(reasons_path, limit=limit)
        summary["reasons"] = store.import_reasons(reasons)
        store.record_artifact_import(reasons_path, "v16_7_reasons", len(reasons))
    if obstructions_path:
        obstructions = load_v167_obstructions(obstructions_path, limit=limit)
        summary["obstructions"] = store.import_obstructions(obstructions)
        store.record_artifact_import(obstructions_path, "v16_7_obstructions", len(obstructions))
    if tables_path:
        rows = load_v167_table_atlas(tables_path, limit=limit)
        summary["tables"] = store.import_tables(rows)
        store.record_artifact_import(tables_path, "v16_7_tables", len(rows))
    return summary


def import_closure_oracle_csv(path: str | Path, store: LawbookStore, limit: int | None = None) -> dict[str, Any]:
    rows = load_v1662_finite_verified_oracle_update(path, limit=limit)
    return {"refutations": store.import_refutations(rows), "row_count": len(rows)}


def import_table_registry_csv(path: str | Path, store: LawbookStore, limit: int | None = None) -> dict[str, Any]:
    rows = load_table_registry(path, limit=limit)
    return {"tables": store.import_tables(rows), "row_count": len(rows)}


def _first_existing(directory: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def _find_pattern(directory: Path, needles: tuple[str, ...]) -> Path | None:
    if not directory.exists():
        return None
    for path in sorted(directory.iterdir()):
        lower = path.name.lower()
        if path.suffix.lower() in {".csv", ".json", ".tsv"} and any(
            needle in lower for needle in needles
        ):
            return path
    return None

"""Artifact helpers for external MathGraph certificate files."""

from __future__ import annotations

import json
import math
from hashlib import sha256
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_exists(path: str | Path) -> bool:
    return Path(path).exists()


def normalize_external_path(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "<na>"}:
        return None
    return text


def read_json_artifact(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"artifact not found: {target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"artifact is not valid JSON: {target}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON artifact must contain an object: {target}")
    return data


def extract_countermodel_from_json(obj: Any) -> dict[str, Any] | list[Any] | None:
    return _extract_countermodel(obj, seen=set())


def build_artifact_record(
    path: str | Path,
    expected_sha256: str | None = None,
    kind: str | None = None,
    load_json: bool = False,
    inspect: bool = True,
    role: str | None = None,
    source_column: str | None = None,
    expected_hash_column: str | None = None,
    hash_applicable: bool | None = None,
    is_canonical: bool = False,
    is_legacy_or_prior: bool = False,
    is_executed: bool = False,
) -> dict[str, Any]:
    normalized = normalize_external_path(path)
    artifact_kind = kind or _infer_kind(normalized)
    applicable = bool(expected_sha256) if hash_applicable is None else hash_applicable
    paired_hash = expected_sha256 if applicable else None
    record: dict[str, Any] = {
        "path": normalized,
        "kind": artifact_kind,
        "role": role or _default_role(artifact_kind),
        "source_column": source_column,
        "expected_hash_column": expected_hash_column if applicable else None,
        "hash_applicable": applicable,
        "is_canonical": is_canonical,
        "is_legacy_or_prior": is_legacy_or_prior,
        "is_executed": is_executed,
        "exists": False,
        "sha256": None,
        "expected_sha256": paired_hash,
        "sha256_matches": None,
        "load_attempted": bool(load_json),
        "load_ok": None,
        "error": None,
        "json_preview_keys": [],
    }
    if normalized is None:
        record["error"] = "missing_path"
        return record

    if not inspect:
        record["exists"] = None
        record["error"] = None
        return record

    target = Path(normalized)
    if not target.exists():
        record["error"] = "file_not_found"
        if load_json:
            record["load_ok"] = False
        return record

    record["exists"] = True
    try:
        actual_hash = sha256_file(target)
        record["sha256"] = actual_hash
        if paired_hash:
            record["sha256_matches"] = actual_hash.lower() == paired_hash.lower()
    except OSError as exc:
        record["error"] = str(exc)

    if load_json:
        try:
            data = read_json_artifact(target)
            record["load_ok"] = True
            record["json_preview_keys"] = sorted(str(key) for key in data.keys())[:20]
        except (FileNotFoundError, ValueError, OSError) as exc:
            record["load_ok"] = False
            record["error"] = str(exc)

    return record


def build_artifact_records_from_record(
    record: dict[str, Any],
    *,
    load_artifacts: bool = False,
    artifact_base: str | Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build provenance-aware artifact records from a SAIR result row."""

    json_canonical = normalize_external_path(record.get("json_path"))
    json_hash = normalize_external_path(record.get("json_sha256_v19_1")) or normalize_external_path(
        record.get("json_sha256")
    )
    json_hash_column = "json_sha256_v19_1" if normalize_external_path(record.get("json_sha256_v19_1")) else "json_sha256"

    lean_canonical = normalize_external_path(record.get("lean_path"))
    lean_hash = normalize_external_path(record.get("lean_sha256_v19_1")) or normalize_external_path(
        record.get("lean_sha256")
    )
    lean_hash_column = "lean_sha256_v19_1" if normalize_external_path(record.get("lean_sha256_v19_1")) else "lean_sha256"

    json_specs = [
        ("json_path", "canonical_json", True, False, False),
        ("json_path_v19_1_input", "v19_1_input_json", False, True, False),
        ("json_path_prior", "prior_json", False, True, False),
    ]
    lean_specs = [
        ("lean_path", "canonical_lean", True, False, False),
        ("executed_lean_path_v19_1", "executed_lean", False, False, True),
        ("lean_path_v19_1_input", "v19_1_input_lean", False, True, False),
        ("lean_path_prior", "prior_lean", False, True, False),
    ]

    artifacts: dict[str, list[dict[str, Any]]] = {"json": [], "lean": []}
    seen: set[tuple[str, str, str]] = set()

    for column, role, is_canonical, is_prior, is_executed in json_specs:
        path = normalize_external_path(record.get(column))
        if path is None:
            continue
        matches_canonical = json_canonical is not None and _same_path(path, json_canonical)
        applicable = bool(json_hash) and (is_canonical or matches_canonical)
        resolved = _resolve_artifact_path(path, artifact_base)
        key = ("json", role, resolved)
        if key in seen:
            continue
        seen.add(key)
        artifacts["json"].append(
            build_artifact_record(
                resolved,
                expected_sha256=json_hash if applicable else None,
                kind="json",
                load_json=load_artifacts,
                inspect=load_artifacts,
                role=role,
                source_column=column,
                expected_hash_column=json_hash_column if applicable else None,
                hash_applicable=applicable,
                is_canonical=is_canonical,
                is_legacy_or_prior=is_prior,
                is_executed=is_executed,
            )
        )

    for column, role, is_canonical, is_prior, is_executed in lean_specs:
        path = normalize_external_path(record.get(column))
        if path is None:
            continue
        matches_canonical = lean_canonical is not None and _same_path(path, lean_canonical)
        applicable = bool(lean_hash) and (is_canonical or matches_canonical)
        resolved = _resolve_artifact_path(path, artifact_base)
        key = ("lean", role, resolved)
        if key in seen:
            continue
        seen.add(key)
        artifacts["lean"].append(
            build_artifact_record(
                resolved,
                expected_sha256=lean_hash if applicable else None,
                kind="lean",
                load_json=False,
                inspect=load_artifacts,
                role=role,
                source_column=column,
                expected_hash_column=lean_hash_column if applicable else None,
                hash_applicable=applicable,
                is_canonical=is_canonical,
                is_legacy_or_prior=is_prior,
                is_executed=is_executed,
            )
        )

    return {kind: records for kind, records in artifacts.items() if records}


def _extract_countermodel(obj: Any, seen: set[int]) -> dict[str, Any] | list[Any] | None:
    if id(obj) in seen:
        return None
    seen.add(id(obj))

    if isinstance(obj, dict):
        for key in (
            "countermodel",
            "model",
            "magma",
            "table",
            "operation_table",
            "cayley_table",
            "finite_magma",
            "witness",
        ):
            value = obj.get(key)
            if isinstance(value, (dict, list)):
                return value
        for value in obj.values():
            found = _extract_countermodel(value, seen)
            if found is not None:
                return found

    if isinstance(obj, list):
        if _looks_like_table(obj):
            return obj
        for value in obj:
            found = _extract_countermodel(value, seen)
            if found is not None:
                return found

    return None


def _looks_like_table(value: list[Any]) -> bool:
    return bool(value) and all(isinstance(row, list) for row in value)


def _infer_kind(path: str | None) -> str:
    if path is None:
        return "unknown"
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".lean":
        return "lean"
    return "unknown"


def _default_role(kind: str) -> str:
    if kind == "json":
        return "unknown_json"
    if kind == "lean":
        return "unknown_lean"
    return "unknown"


def _resolve_artifact_path(path: str, artifact_base: str | Path | None) -> str:
    target = Path(path)
    if target.is_absolute() or artifact_base is None:
        return str(target)
    return str(Path(artifact_base) / target)


def _same_path(left: str, right: str) -> bool:
    return str(Path(left)) == str(Path(right))

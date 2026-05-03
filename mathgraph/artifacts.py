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
) -> dict[str, Any]:
    normalized = normalize_external_path(path)
    artifact_kind = kind or _infer_kind(normalized)
    record: dict[str, Any] = {
        "path": normalized,
        "kind": artifact_kind,
        "exists": False,
        "sha256": None,
        "expected_sha256": expected_sha256,
        "sha256_matches": None,
        "load_attempted": bool(load_json),
        "load_ok": None,
        "error": None,
        "json_preview_keys": [],
    }
    if normalized is None:
        record["error"] = "missing_path"
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
        if expected_sha256:
            record["sha256_matches"] = actual_hash.lower() == expected_sha256.lower()
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

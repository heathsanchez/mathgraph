"""Lightweight importers for external v16.6/v16.7 MathGraph artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar

from mathgraph.obstruction_atlas import ObstructionNode
from mathgraph.reason_nodes import ReasonNode
from mathgraph.root_nodes import RootNode

T = TypeVar("T")


class ArtifactImportError(ValueError):
    pass


def load_v1662_elevated_false_certificates(
    path: str | Path, limit: int | None = None
) -> list[dict[str, Any]]:
    rows = _load_rows(path, limit=limit)
    _require_any(rows, path, ("source", "target", "terminal_form", "verification_status"))
    return rows


def load_v167_root_nodes(path: str | Path, limit: int | None = None) -> list[RootNode]:
    rows = _load_rows(path, limit=limit)
    _require_any(rows, path, ("root_node_id", "canonical_name", "table_motif", "root_key"))
    return [RootNode.from_dict(row) for row in rows]


def load_v167_reason_nodes(path: str | Path, limit: int | None = None) -> list[ReasonNode]:
    rows = _load_rows(path, limit=limit)
    _require_any(rows, path, ("reason_node_id", "reason_type", "reason_key", "table_motif"))
    return [ReasonNode.from_dict(row) for row in rows]


def load_v167_obstructions(path: str | Path, limit: int | None = None) -> list[ObstructionNode]:
    rows = _load_rows(path, limit=limit)
    _require_any(rows, path, ("obstruction_id", "obstruction_signature", "failure_reason"))
    return [ObstructionNode.from_dict(row) for row in rows]


def load_v167_table_atlas(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    return _load_rows(path, limit=limit)


def load_v167_motif_summary(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    return _load_rows(path, limit=limit)


def _load_rows(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key in ("rows", "data", "items", "roots", "reasons", "obstructions"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
        if not isinstance(data, list):
            raise ArtifactImportError(f"{file_path} must contain a JSON list or rows-like object")
        rows = [dict(row) for row in data if isinstance(row, dict)]
        return rows[:limit] if limit is not None else rows
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows: list[dict[str, Any]] = []
            for row in reader:
                rows.append(dict(row))
                if limit is not None and len(rows) >= limit:
                    break
            return rows
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - optional path
        raise ArtifactImportError(
            f"Unsupported artifact extension {suffix!r}; install pandas or use CSV/JSON"
        ) from exc
    frame = pd.read_parquet(file_path) if suffix == ".parquet" else pd.read_csv(file_path)
    if limit is not None:
        frame = frame.head(limit)
    return [dict(row) for row in frame.to_dict(orient="records")]


def _require_any(rows: list[dict[str, Any]], path: str | Path, columns: Iterable[str]) -> None:
    if not rows:
        return
    keys = set(rows[0].keys())
    if not any(column in keys for column in columns):
        raise ArtifactImportError(
            f"{Path(path)} missing required identifying columns; expected one of {sorted(columns)}"
        )


def write_json_rows(rows: Iterable[Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [row.to_dict() if hasattr(row, "to_dict") else dict(row) for row in rows]
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

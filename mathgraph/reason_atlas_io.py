"""CSV and JSON row helpers for Reason Atlas contact promotion artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


def load_probe_results_csv(path: str | Path) -> list[dict[str, Any]]:
    return _read_csv(path)


def load_declarations_csv(path: str | Path) -> list[dict[str, Any]]:
    return _read_csv(path)


def write_csv(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    materialized = [dict(row) for row in rows]
    fieldnames = _fieldnames(materialized)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: _cell(row.get(field, "")) for field in fieldnames})


def contact_seed_to_row(seed: Any) -> dict[str, Any]:
    return _to_row(seed)


def obstruction_to_row(obstruction: Any) -> dict[str, Any]:
    return _to_row(obstruction)


def promoted_route_law_to_row(law: Any) -> dict[str, Any]:
    return _to_row(law)


def signature_record_to_row(record: Any) -> dict[str, Any]:
    return _to_row(record)


def read_json_field(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def write_json_field(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _read_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _to_row(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        row = value.to_dict()
    else:
        row = dict(value)
    return {key: _row_value(item) for key, item in row.items()}


def _row_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return write_json_field(value)
    return value


def _cell(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return write_json_field(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    return fields

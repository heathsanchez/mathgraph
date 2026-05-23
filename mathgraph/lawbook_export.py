"""Lawbook export helpers for manifests, JSONL, and summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mathgraph.hashing import sha256_hex


def artifact_hash(artifact: Any) -> str:
    payload = artifact.to_dict() if hasattr(artifact, "to_dict") else artifact
    return sha256_hex(payload)


def replay_manifest_row(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": artifact.get("artifact_id", ""),
        "terminal_form": artifact.get("terminal_form", ""),
        "payload_hash": artifact.get("payload_hash") or artifact_hash(artifact.get("payload", artifact)),
        "replay_status": artifact.get("replay_status", ""),
        "advisory": int(artifact.get("trust_level", 0) or 0) < 100,
    }


def export_lawbook_manifest(store: Any, path: str | Path) -> dict[str, Any]:
    if hasattr(store, "export_manifest"):
        return store.export_manifest(path)
    rows = _rows(store)
    manifest = export_lawbook_summary(rows)
    Path(path).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def export_lawbook_jsonl(store: Any, path: str | Path) -> int:
    rows = _rows(store)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return len(rows)


def export_lawbook_summary(store_or_rows: Any) -> dict[str, Any]:
    rows = store_or_rows if isinstance(store_or_rows, list) else _rows(store_or_rows)
    buckets = {"terminal_verified": 0, "advisory": 0, "diagnostic": 0, "rejected": 0}
    for row in rows:
        level = str(row.get("admission_level", "")).lower()
        trust = int(row.get("trust_level", 0) or 0)
        terminal = str(row.get("terminal_form", "")).upper()
        if level == "rejected":
            buckets["rejected"] += 1
        elif terminal in {"VERIFIED_PROOF", "FINITE_COUNTERMODEL", "REFUTATION_CERTIFICATE", "NAMED_OBSTRUCTION"} and trust >= 100:
            buckets["terminal_verified"] += 1
        elif terminal in {"ADVISORY", "", "NONE"} or trust < 100:
            buckets["advisory"] += 1
        else:
            buckets["diagnostic"] += 1
    return {"artifact_count": len(rows), **buckets}


def _rows(store: Any) -> list[dict[str, Any]]:
    if isinstance(store, list):
        return store
    if hasattr(store, "query_artifacts"):
        return list(store.query_artifacts(limit=100000))
    return []

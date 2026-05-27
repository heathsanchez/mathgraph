"""Ingest Lean Project Digest v0 outputs into a small SQLite lawbook store.

This is structured memory ingestion, not Lean verification.  Every imported
textual digest record remains advisory and cannot promote truth.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from mathgraph.lean_project_digest import run_lean_project_digest


REQUIRED_DIGEST_FILES = ("project_manifest.json", "declaration_inventory.csv")
OPTIONAL_DIGEST_FILES = ("import_graph.csv", "trust_boundary_audit.json", "lawbook_entries.jsonl", "reason_atlas_routes.csv")


@dataclass(frozen=True)
class LeanDigestBundle:
    digest_dir: Path
    manifest: dict[str, Any]
    declarations: tuple[dict[str, Any], ...]
    import_edges: tuple[dict[str, Any], ...] = ()
    trust_audit: dict[str, Any] = field(default_factory=dict)
    lawbook_entries: tuple[dict[str, Any], ...] = ()
    reason_routes: tuple[dict[str, Any], ...] = ()
    missing_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class LeanDigestIngestionResult:
    sqlite_path: str
    ingestion_manifest_path: str
    imported_declarations_path: str
    imported_import_edges_path: str
    imported_trust_boundaries_path: str
    imported_reason_routes_path: str
    report_path: str
    declaration_count: int
    import_edge_count: int
    trust_boundary_count: int
    reason_route_count: int
    can_promote_truth_count: int
    advisory_boundary_ok: bool
    missing_files: tuple[str, ...] = ()
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sqlite_path": self.sqlite_path,
            "ingestion_manifest_path": self.ingestion_manifest_path,
            "imported_declarations_path": self.imported_declarations_path,
            "imported_import_edges_path": self.imported_import_edges_path,
            "imported_trust_boundaries_path": self.imported_trust_boundaries_path,
            "imported_reason_routes_path": self.imported_reason_routes_path,
            "report_path": self.report_path,
            "declaration_count": self.declaration_count,
            "import_edge_count": self.import_edge_count,
            "trust_boundary_count": self.trust_boundary_count,
            "reason_route_count": self.reason_route_count,
            "can_promote_truth_count": self.can_promote_truth_count,
            "advisory_boundary_ok": self.advisory_boundary_ok,
            "missing_files": list(self.missing_files),
            "manifest": dict(self.manifest),
        }


def load_digest_dir(digest_dir: Path) -> LeanDigestBundle:
    digest_dir = Path(digest_dir)
    if not digest_dir.exists():
        raise FileNotFoundError(digest_dir)
    missing = [name for name in REQUIRED_DIGEST_FILES + OPTIONAL_DIGEST_FILES if not (digest_dir / name).exists()]
    if all((digest_dir / name).name in missing for name in REQUIRED_DIGEST_FILES):
        raise FileNotFoundError(f"Missing required Lean digest files in {digest_dir}: {', '.join(REQUIRED_DIGEST_FILES)}")
    manifest = _read_json(digest_dir / "project_manifest.json") if (digest_dir / "project_manifest.json").exists() else {}
    declarations = tuple(_read_csv(digest_dir / "declaration_inventory.csv")) if (digest_dir / "declaration_inventory.csv").exists() else ()
    return LeanDigestBundle(
        digest_dir=digest_dir,
        manifest=manifest,
        declarations=declarations,
        import_edges=tuple(_read_csv(digest_dir / "import_graph.csv")) if (digest_dir / "import_graph.csv").exists() else (),
        trust_audit=_read_json(digest_dir / "trust_boundary_audit.json") if (digest_dir / "trust_boundary_audit.json").exists() else {},
        lawbook_entries=tuple(_read_jsonl(digest_dir / "lawbook_entries.jsonl")) if (digest_dir / "lawbook_entries.jsonl").exists() else (),
        reason_routes=tuple(_read_csv(digest_dir / "reason_atlas_routes.csv")) if (digest_dir / "reason_atlas_routes.csv").exists() else (),
        missing_files=tuple(missing),
    )


def ingest_lean_digest(bundle: LeanDigestBundle, out_dir: Path) -> LeanDigestIngestionResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    created_at = _now()
    declarations = [_imported_declaration(row, bundle.digest_dir, created_at) for row in bundle.declarations]
    import_edges = [_import_edge(row, created_at) for row in bundle.import_edges]
    trust_boundaries = [_trust_boundary(row, bundle.trust_audit, created_at) for row in bundle.declarations]
    reason_routes = [_reason_route(row, declarations, created_at) for row in bundle.reason_routes]
    source_can_promote_truth_count = _source_can_promote_truth_count(bundle)
    can_promote_truth_count = source_can_promote_truth_count + sum(
        1 for row in declarations + import_edges + trust_boundaries + reason_routes if _truthy(row.get("can_promote_truth"))
    )
    advisory_boundary_ok = can_promote_truth_count == 0
    run_id = stable_hash({"digest_dir": str(bundle.digest_dir), "created_at": created_at, "declaration_count": len(declarations)})
    ingestion_run = {
        "run_id": run_id,
        "source_digest_dir": str(bundle.digest_dir),
        "declaration_count": len(declarations),
        "import_edge_count": len(import_edges),
        "trust_boundary_count": len(trust_boundaries),
        "reason_route_count": len(reason_routes),
        "can_promote_truth_count": can_promote_truth_count,
        "advisory_boundary_ok": advisory_boundary_ok,
        "lean_execution_confirmed": bool(bundle.trust_audit.get("lean_execution_confirmed", False)),
        "source_can_promote_truth_count": source_can_promote_truth_count,
        "created_at": created_at,
    }
    manifest = {
        **ingestion_run,
        "boundary_type": "textual_digest",
        "provenance_type": "imported_lean_project",
        "missing_files": list(bundle.missing_files),
        "source_manifest": bundle.manifest,
        "outputs": {
            "sqlite": "lean_digest_lawbook.sqlite",
            "imported_declarations": "imported_declarations.csv",
            "imported_import_edges": "imported_import_edges.csv",
            "imported_trust_boundaries": "imported_trust_boundaries.csv",
            "imported_reason_routes": "imported_reason_routes.csv",
            "report": "lawbook_ingestion_report.md",
        },
    }
    sqlite_path = out_dir / "lean_digest_lawbook.sqlite"
    write_sqlite(
        {
            "imported_declarations": declarations,
            "import_edges": import_edges,
            "trust_boundaries": trust_boundaries,
            "reason_routes": reason_routes,
            "ingestion_runs": [{key: value for key, value in ingestion_run.items() if key != "source_can_promote_truth_count"}],
        },
        sqlite_path,
    )
    declarations_path = out_dir / "imported_declarations.csv"
    import_edges_path = out_dir / "imported_import_edges.csv"
    trust_boundaries_path = out_dir / "imported_trust_boundaries.csv"
    reason_routes_path = out_dir / "imported_reason_routes.csv"
    manifest_path = out_dir / "ingestion_manifest.json"
    report_path = out_dir / "lawbook_ingestion_report.md"
    _write_csv(declarations_path, declarations)
    _write_csv(import_edges_path, import_edges)
    _write_csv(trust_boundaries_path, trust_boundaries)
    _write_csv(reason_routes_path, reason_routes)
    write_ingestion_manifest(manifest, manifest_path)
    write_ingestion_report(manifest, report_path)
    return LeanDigestIngestionResult(
        sqlite_path=str(sqlite_path),
        ingestion_manifest_path=str(manifest_path),
        imported_declarations_path=str(declarations_path),
        imported_import_edges_path=str(import_edges_path),
        imported_trust_boundaries_path=str(trust_boundaries_path),
        imported_reason_routes_path=str(reason_routes_path),
        report_path=str(report_path),
        declaration_count=len(declarations),
        import_edge_count=len(import_edges),
        trust_boundary_count=len(trust_boundaries),
        reason_route_count=len(reason_routes),
        can_promote_truth_count=can_promote_truth_count,
        advisory_boundary_ok=advisory_boundary_ok,
        missing_files=bundle.missing_files,
        manifest=manifest,
    )


def write_sqlite(tables: Mapping[str, Sequence[Mapping[str, Any]]], sqlite_path: Path) -> None:
    if sqlite_path.exists():
        sqlite_path.unlink()
    conn = sqlite3.connect(sqlite_path)
    try:
        _create_schema(conn)
        for table, rows in tables.items():
            _insert_rows(conn, table, rows)
        conn.commit()
    finally:
        conn.close()


def write_ingestion_manifest(manifest: Mapping[str, Any], path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")


def write_ingestion_report(manifest: Mapping[str, Any], path: Path) -> None:
    path.write_text(_markdown(manifest), encoding="utf-8")


def run_fallback_demo(out_dir: Path) -> LeanDigestIngestionResult:
    out_dir = Path(out_dir)
    digest_dir = out_dir / "fallback_digest"
    run_lean_project_digest(digest_dir, fallback_demo=True)
    return ingest_lean_digest(load_digest_dir(digest_dir), out_dir)


def run_lean_digest_lawbook_ingestion(
    out_dir: str | Path,
    *,
    digest_dir: str | Path | None = None,
    fallback_demo: bool = False,
) -> LeanDigestIngestionResult:
    out_dir = Path(out_dir)
    if fallback_demo or digest_dir is None:
        return run_fallback_demo(out_dir)
    return ingest_lean_digest(load_digest_dir(Path(digest_dir)), out_dir)


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _source_can_promote_truth_count(bundle: LeanDigestBundle) -> int:
    rows: list[Mapping[str, Any]] = []
    rows.extend(bundle.declarations)
    rows.extend(bundle.import_edges)
    rows.extend(bundle.lawbook_entries)
    rows.extend(bundle.reason_routes)
    manifest_truth = 1 if _truthy(bundle.manifest.get("can_promote_truth")) else 0
    return manifest_truth + sum(1 for row in rows if _truthy(row.get("can_promote_truth")))


def _imported_declaration(row: Mapping[str, Any], digest_dir: Path, created_at: str) -> dict[str, Any]:
    warning = _warning_flags(row)
    replay_hint = {"file": row.get("file", ""), "line": _int(row.get("line")), "name": row.get("name", "")}
    out = {
        "artifact_id": stable_hash({"kind": "declaration", "id": row.get("declaration_id", "")})[:16],
        "declaration_id": row.get("declaration_id", ""),
        "declaration_kind": row.get("declaration_kind", ""),
        "name": row.get("name", ""),
        "file": row.get("file", ""),
        "line": _int(row.get("line")),
        "statement_text": row.get("statement_text", ""),
        "trust_status": _normalized_trust_status(row),
        "provenance_type": "imported_lean_project",
        "boundary_type": "textual_digest",
        "has_sorry": _truthy(row.get("has_sorry")),
        "has_admit": _truthy(row.get("has_admit")),
        "has_axiom": _truthy(row.get("has_axiom")),
        "has_unsafe": _truthy(row.get("has_unsafe")),
        "advisory_only": True,
        "can_promote_truth": False,
        "source_digest_dir": str(digest_dir),
        "payload_hash": "",
        "replay_hint_json": json.dumps(replay_hint, sort_keys=True),
        "created_at": created_at,
    }
    out["payload_hash"] = stable_hash({**out, "payload_hash": "", "warning_flags": warning})
    return out


def _import_edge(row: Mapping[str, Any], created_at: str) -> dict[str, Any]:
    out = {
        "edge_id": stable_hash({"file": row.get("file", ""), "import": row.get("import", "")})[:16],
        "source_file": row.get("file", ""),
        "imported_module": row.get("import", ""),
        "provenance_type": "imported_lean_project",
        "boundary_type": "textual_digest",
        "advisory_only": True,
        "can_promote_truth": False,
        "payload_hash": "",
        "created_at": created_at,
    }
    out["payload_hash"] = stable_hash({**out, "payload_hash": ""})
    return out


def _trust_boundary(row: Mapping[str, Any], audit: Mapping[str, Any], created_at: str) -> dict[str, Any]:
    warning = _warning_flags(row)
    out = {
        "boundary_id": stable_hash({"kind": "boundary", "id": row.get("declaration_id", "")})[:16],
        "declaration_id": row.get("declaration_id", ""),
        "name": row.get("name", ""),
        "trust_status": _normalized_trust_status(row),
        "boundary_type": "textual_digest",
        "lean_execution_confirmed": bool(audit.get("lean_execution_confirmed", False)),
        "textual_parsing_is_advisory": True,
        "can_promote_truth": False,
        "advisory_only": True,
        "warning_flags_json": json.dumps(warning, sort_keys=True),
        "notes": _boundary_notes(row),
        "created_at": created_at,
    }
    return out


def _reason_route(row: Mapping[str, Any], declarations: Sequence[Mapping[str, Any]], created_at: str) -> dict[str, Any]:
    by_id = {str(item.get("declaration_id", "")): item for item in declarations}
    decl = by_id.get(str(row.get("declaration_id", "")), {})
    route_type = row.get("route_suggestion") or row.get("route_type") or ""
    out = {
        "route_id": stable_hash({"kind": "route", "id": row.get("declaration_id", ""), "route": route_type})[:16],
        "declaration_id": row.get("declaration_id", ""),
        "name": decl.get("name", ""),
        "route_type": route_type,
        "route_reason": row.get("notes", "Advisory route imported from textual Lean digest."),
        "advisory_only": True,
        "can_promote_truth": False,
        "provenance_type": "imported_lean_project",
        "boundary_type": "textual_digest",
        "payload_hash": "",
        "created_at": created_at,
    }
    out["payload_hash"] = stable_hash({**out, "payload_hash": ""})
    return out


def _normalized_trust_status(row: Mapping[str, Any]) -> str:
    if _truthy(row.get("has_sorry")) or _truthy(row.get("has_admit")):
        return "incomplete_proof"
    if _truthy(row.get("has_axiom")) or row.get("declaration_kind") == "axiom":
        return "trusted_assumption_or_external_axiom"
    if _truthy(row.get("has_unsafe")):
        return "unsafe_requires_warning"
    return str(row.get("trust_status") or "imported_definition_metadata")


def _warning_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "has_sorry": _truthy(row.get("has_sorry")),
        "has_admit": _truthy(row.get("has_admit")),
        "has_axiom": _truthy(row.get("has_axiom")) or row.get("declaration_kind") == "axiom",
        "has_unsafe": _truthy(row.get("has_unsafe")),
    }


def _boundary_notes(row: Mapping[str, Any]) -> str:
    flags = _warning_flags(row)
    if flags["has_sorry"] or flags["has_admit"]:
        return "Incomplete proof marker preserved; not verified."
    if flags["has_axiom"]:
        return "Axiom preserved as trusted assumption or external axiom, not proof."
    if flags["has_unsafe"]:
        return "Unsafe marker preserved; explicit warning required."
    return "Textual-only imported candidate; Lean execution required for proof promotion."


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE imported_declarations (
          artifact_id TEXT, declaration_id TEXT, declaration_kind TEXT, name TEXT,
          file TEXT, line INTEGER, statement_text TEXT, trust_status TEXT,
          provenance_type TEXT, boundary_type TEXT, has_sorry INTEGER, has_admit INTEGER,
          has_axiom INTEGER, has_unsafe INTEGER, advisory_only INTEGER, can_promote_truth INTEGER,
          source_digest_dir TEXT, payload_hash TEXT, replay_hint_json TEXT, created_at TEXT
        );
        CREATE TABLE import_edges (
          edge_id TEXT, source_file TEXT, imported_module TEXT, provenance_type TEXT,
          boundary_type TEXT, advisory_only INTEGER, can_promote_truth INTEGER,
          payload_hash TEXT, created_at TEXT
        );
        CREATE TABLE trust_boundaries (
          boundary_id TEXT, declaration_id TEXT, name TEXT, trust_status TEXT,
          boundary_type TEXT, lean_execution_confirmed INTEGER, textual_parsing_is_advisory INTEGER,
          can_promote_truth INTEGER, advisory_only INTEGER, warning_flags_json TEXT,
          notes TEXT, created_at TEXT
        );
        CREATE TABLE reason_routes (
          route_id TEXT, declaration_id TEXT, name TEXT, route_type TEXT, route_reason TEXT,
          advisory_only INTEGER, can_promote_truth INTEGER, provenance_type TEXT, boundary_type TEXT,
          payload_hash TEXT, created_at TEXT
        );
        CREATE TABLE ingestion_runs (
          run_id TEXT, source_digest_dir TEXT, declaration_count INTEGER, import_edge_count INTEGER,
          trust_boundary_count INTEGER, reason_route_count INTEGER, can_promote_truth_count INTEGER,
          advisory_boundary_ok INTEGER, lean_execution_confirmed INTEGER, created_at TEXT
        );
        """
    )


def _insert_rows(conn: sqlite3.Connection, table: str, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in keys)
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({placeholders})",
        [[_sqlite_value(row.get(key)) for key in keys] for row in rows],
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    return value


def _sqlite_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    return value


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _markdown(manifest: Mapping[str, Any]) -> str:
    return f"""# Lean Digest Lawbook Ingestion v1

- declaration_count: `{manifest.get('declaration_count')}`
- import_edge_count: `{manifest.get('import_edge_count')}`
- trust_boundary_count: `{manifest.get('trust_boundary_count')}`
- reason_route_count: `{manifest.get('reason_route_count')}`
- can_promote_truth_count: `{manifest.get('can_promote_truth_count')}`
- advisory_boundary_ok: `{manifest.get('advisory_boundary_ok')}`
- lean_execution_confirmed: `{manifest.get('lean_execution_confirmed')}`

This is persistent imported Lean-project memory. It is not Lean verification.
Textual digest entries cannot become `VERIFIED_PROOF`; Lean execution or another
accepted verifier boundary is required for proof promotion.

Every imported declaration, import edge, trust-boundary record, and Reason Atlas
route from textual digest input is stored with `boundary_type=textual_digest`,
`provenance_type=imported_lean_project`, `advisory_only=true`, and
`can_promote_truth=false`.

Missing optional digest files: `{', '.join(manifest.get('missing_files', [])) or 'none'}`
"""

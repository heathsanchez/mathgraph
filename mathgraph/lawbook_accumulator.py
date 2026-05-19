"""Persistent SQLite accumulator for Mathlib digest Lawbook runs.

This module stores verifier-grounded observations and advisory digest structure.
It never promotes discovery text, generated files, stdout, or failed constructor
attempts as proof evidence.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "mathlib-digest-lawbook-v0.1"


def stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps([prefix, *parts], sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}_{sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def json_loads(text: str | None, default: Any = None) -> Any:
    if text in (None, ""):
        return default
    return json.loads(text)


def connect_lawbook(path: str | Path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    initialize_lawbook_schema(conn)
    return conn


def initialize_lawbook_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            created_at TEXT,
            run_name TEXT,
            run_version TEXT,
            mathlib_root TEXT,
            mathlib_revision TEXT,
            lean_toolchain TEXT,
            modules_json TEXT,
            targets_json TEXT,
            pack_id TEXT,
            config_path TEXT,
            summary_json TEXT
        );
        CREATE TABLE IF NOT EXISTS targets (
            target_id TEXT PRIMARY KEY,
            declaration_name TEXT UNIQUE,
            module TEXT,
            formal_statement TEXT,
            theorem_shape TEXT,
            status TEXT,
            axiom_profile_json TEXT,
            first_seen_run_id TEXT,
            last_seen_run_id TEXT,
            seen_count INTEGER,
            success_count INTEGER,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS target_observations (
            observation_id TEXT PRIMARY KEY,
            run_id TEXT,
            target_id TEXT,
            declaration_name TEXT,
            status TEXT,
            formal_statement TEXT,
            axiom_profile_json TEXT,
            print_refs_json TEXT,
            reference_classes_json TEXT,
            elapsed_sec REAL,
            returncode INTEGER,
            lean_file TEXT,
            stdout_path TEXT,
            stderr_path TEXT,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS root_observations (
            root_observation_id TEXT PRIMARY KEY,
            run_id TEXT,
            target_id TEXT,
            declaration_name TEXT,
            root_name TEXT,
            root_class TEXT,
            source TEXT,
            evidence_level TEXT,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS reason_basins (
            reason_id TEXT PRIMARY KEY,
            reason_name TEXT,
            basin_class TEXT,
            explanation TEXT,
            support_count INTEGER,
            confidence REAL,
            trust_level TEXT,
            root_nodes_json TEXT,
            axiom_profile_json TEXT,
            constructor_strategy TEXT,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS target_reason_edges (
            edge_id TEXT PRIMARY KEY,
            target_id TEXT,
            reason_id TEXT,
            confidence REAL,
            evidence_json TEXT
        );
        CREATE TABLE IF NOT EXISTS constructor_attempts (
            attempt_id TEXT PRIMARY KEY,
            run_id TEXT,
            target_id TEXT,
            reason_id TEXT,
            template_id TEXT,
            proof_body TEXT,
            status TEXT,
            returncode INTEGER,
            elapsed_sec REAL,
            lean_file TEXT,
            stdout_path TEXT,
            stderr_path TEXT,
            error_excerpt TEXT,
            trust_level TEXT,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS verified_constructors (
            constructor_id TEXT PRIMARY KEY,
            reason_id TEXT,
            template_id TEXT,
            proof_body TEXT,
            minimal_roots_json TEXT,
            success_count INTEGER,
            target_examples_json TEXT,
            first_seen_run_id TEXT,
            last_seen_run_id TEXT,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS obstructions (
            obstruction_id TEXT PRIMARY KEY,
            run_id TEXT,
            target_id TEXT,
            reason_id TEXT,
            template_id TEXT,
            obstruction_class TEXT,
            message TEXT,
            error_excerpt TEXT,
            next_action TEXT,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS pending_packs (
            pack_id TEXT PRIMARY KEY,
            module TEXT,
            targets_json TEXT,
            priority REAL,
            status TEXT,
            created_from_reason TEXT,
            metadata_json TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_targets_decl ON targets(declaration_name);
        CREATE INDEX IF NOT EXISTS idx_observations_run ON target_observations(run_id);
        CREATE INDEX IF NOT EXISTS idx_roots_name ON root_observations(root_name);
        CREATE INDEX IF NOT EXISTS idx_constructor_reason ON constructor_attempts(reason_id);
        CREATE INDEX IF NOT EXISTS idx_obstruction_class ON obstructions(obstruction_class);
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO schema_metadata(key,value) VALUES(?,?)",
        ("schema_version", SCHEMA_VERSION),
    )
    conn.commit()


def append_digest_run(conn: sqlite3.Connection, run: Mapping[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO runs(run_id,created_at,run_name,run_version,mathlib_root,mathlib_revision,
        lean_toolchain,modules_json,targets_json,pack_id,config_path,summary_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            run["run_id"],
            run.get("created_at"),
            run.get("run_name"),
            run.get("run_version"),
            run.get("mathlib_root"),
            run.get("mathlib_revision"),
            run.get("lean_toolchain"),
            json_dumps(run.get("modules", ())),
            json_dumps(run.get("targets", ())),
            run.get("pack_id"),
            run.get("config_path"),
            json_dumps(run.get("summary", {})),
        ),
    )
    conn.commit()


def upsert_target(conn: sqlite3.Connection, target: Mapping[str, Any]) -> None:
    existing = conn.execute(
        "SELECT first_seen_run_id, seen_count, success_count FROM targets WHERE declaration_name=?",
        (target["declaration_name"],),
    ).fetchone()
    seen = int(existing["seen_count"]) + 1 if existing else int(target.get("seen_count", 1) or 1)
    success = int(existing["success_count"]) if existing else 0
    if target.get("status") == "LEAN_ACCEPTED_TARGET":
        success += 1
    first = existing["first_seen_run_id"] if existing else target.get("first_seen_run_id")
    conn.execute(
        """
        INSERT OR REPLACE INTO targets(target_id,declaration_name,module,formal_statement,theorem_shape,status,
        axiom_profile_json,first_seen_run_id,last_seen_run_id,seen_count,success_count,metadata_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            target["target_id"],
            target["declaration_name"],
            target.get("module"),
            target.get("formal_statement", ""),
            target.get("theorem_shape", ""),
            target.get("status", ""),
            json_dumps(target.get("axiom_profile", {})),
            first,
            target.get("last_seen_run_id"),
            seen,
            success,
            json_dumps(target.get("metadata", {})),
        ),
    )
    conn.commit()


def insert_target_observation(conn: sqlite3.Connection, obs: Mapping[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO target_observations(observation_id,run_id,target_id,declaration_name,status,
        formal_statement,axiom_profile_json,print_refs_json,reference_classes_json,elapsed_sec,returncode,
        lean_file,stdout_path,stderr_path,metadata_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            obs["observation_id"],
            obs["run_id"],
            obs["target_id"],
            obs["declaration_name"],
            obs.get("status", ""),
            obs.get("formal_statement", ""),
            json_dumps(obs.get("axiom_profile", {})),
            json_dumps(obs.get("print_refs", ())),
            json_dumps(obs.get("reference_classes", {})),
            obs.get("elapsed_sec"),
            obs.get("returncode"),
            obs.get("lean_file"),
            obs.get("stdout_path"),
            obs.get("stderr_path"),
            json_dumps(obs.get("metadata", {})),
        ),
    )


def insert_root_observation(conn: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO root_observations VALUES(?,?,?,?,?,?,?,?,?)",
        (
            row["root_observation_id"],
            row["run_id"],
            row["target_id"],
            row["declaration_name"],
            row["root_name"],
            row["root_class"],
            row.get("source", "print_refs"),
            row.get("evidence_level", "ADVISORY_REFERENCE_HINT"),
            json_dumps(row.get("metadata", {})),
        ),
    )


def upsert_reason_basin(conn: sqlite3.Connection, reason: Mapping[str, Any]) -> None:
    existing = conn.execute(
        "SELECT support_count FROM reason_basins WHERE reason_id=?",
        (reason["reason_id"],),
    ).fetchone()
    support = max(int(reason.get("support_count", 0) or 0), int(existing["support_count"]) if existing else 0)
    conn.execute(
        """
        INSERT OR REPLACE INTO reason_basins(reason_id,reason_name,basin_class,explanation,support_count,
        confidence,trust_level,root_nodes_json,axiom_profile_json,constructor_strategy,metadata_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            reason["reason_id"],
            reason.get("reason_name", reason["reason_id"]),
            reason.get("basin_class", ""),
            reason.get("explanation", ""),
            support,
            float(reason.get("confidence", 0.5) or 0.5),
            reason.get("trust_level", "ADVISORY_REASON_FROM_FOCUSED_DIGEST"),
            json_dumps(reason.get("root_nodes", ())),
            json_dumps(reason.get("axiom_profile", {})),
            reason.get("constructor_strategy", ""),
            json_dumps(reason.get("metadata", {})),
        ),
    )


def upsert_target_reason_edge(conn: sqlite3.Connection, edge: Mapping[str, Any]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO target_reason_edges VALUES(?,?,?,?,?)",
        (
            edge["edge_id"],
            edge["target_id"],
            edge["reason_id"],
            float(edge.get("confidence", 0.5) or 0.5),
            json_dumps(edge.get("evidence", {})),
        ),
    )


def insert_constructor_attempt(conn: sqlite3.Connection, attempt: Mapping[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO constructor_attempts(attempt_id,run_id,target_id,reason_id,template_id,proof_body,
        status,returncode,elapsed_sec,lean_file,stdout_path,stderr_path,error_excerpt,trust_level,metadata_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            attempt["attempt_id"],
            attempt["run_id"],
            attempt["target_id"],
            attempt["reason_id"],
            attempt["template_id"],
            attempt.get("proof_body", ""),
            attempt.get("status", ""),
            attempt.get("returncode"),
            attempt.get("elapsed_sec"),
            attempt.get("lean_file"),
            attempt.get("stdout_path"),
            attempt.get("stderr_path"),
            attempt.get("error_excerpt", ""),
            attempt.get("trust_level", "ADVISORY_CONSTRUCTOR_ATTEMPT"),
            json_dumps(attempt.get("metadata", {})),
        ),
    )


def upsert_verified_constructor(conn: sqlite3.Connection, constructor: Mapping[str, Any]) -> None:
    existing = conn.execute(
        "SELECT success_count, target_examples_json, first_seen_run_id FROM verified_constructors WHERE constructor_id=?",
        (constructor["constructor_id"],),
    ).fetchone()
    count = int(existing["success_count"]) + 1 if existing else int(constructor.get("success_count", 1) or 1)
    examples = set(json_loads(existing["target_examples_json"], []) if existing else [])
    examples.update(constructor.get("target_examples", ()))
    first = existing["first_seen_run_id"] if existing else constructor.get("first_seen_run_id")
    conn.execute(
        "INSERT OR REPLACE INTO verified_constructors VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            constructor["constructor_id"],
            constructor["reason_id"],
            constructor["template_id"],
            constructor.get("proof_body", ""),
            json_dumps(constructor.get("minimal_roots", ())),
            count,
            json_dumps(sorted(examples)),
            first,
            constructor.get("last_seen_run_id"),
            json_dumps(constructor.get("metadata", {})),
        ),
    )


def insert_obstruction(conn: sqlite3.Connection, obstruction: Mapping[str, Any]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO obstructions VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            obstruction["obstruction_id"],
            obstruction["run_id"],
            obstruction["target_id"],
            obstruction["reason_id"],
            obstruction["template_id"],
            obstruction.get("obstruction_class", "lean_rejected"),
            obstruction.get("message", ""),
            obstruction.get("error_excerpt", ""),
            obstruction.get("next_action", ""),
            json_dumps(obstruction.get("metadata", {})),
        ),
    )


def upsert_pending_pack(conn: sqlite3.Connection, pack: Mapping[str, Any]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO pending_packs VALUES(?,?,?,?,?,?,?)",
        (
            pack["pack_id"],
            pack.get("module", ""),
            json_dumps(pack.get("targets", ())),
            float(pack.get("priority", 0.0) or 0.0),
            pack.get("status", "PENDING"),
            pack.get("created_from_reason", ""),
            json_dumps(pack.get("metadata", {})),
        ),
    )
    conn.commit()


def write_digest_payload(conn: sqlite3.Connection, payload: Mapping[str, Any]) -> None:
    append_digest_run(conn, payload["run"])
    for target in payload.get("targets", ()):
        upsert_target(conn, target)
    for obs in payload.get("target_observations", ()):
        insert_target_observation(conn, obs)
    for root in payload.get("root_observations", ()):
        insert_root_observation(conn, root)
    for reason in payload.get("reason_basins", ()):
        upsert_reason_basin(conn, reason)
    for edge in payload.get("target_reason_edges", ()):
        upsert_target_reason_edge(conn, edge)
    for attempt in payload.get("constructor_attempts", ()):
        insert_constructor_attempt(conn, attempt)
    for vc in payload.get("verified_constructors", ()):
        upsert_verified_constructor(conn, vc)
    for obstruction in payload.get("obstructions", ()):
        insert_obstruction(conn, obstruction)
    conn.commit()


def summarize_lawbook(conn: sqlite3.Connection, *, recent_limit: int = 5) -> dict[str, Any]:
    def one(sql: str) -> int:
        return int(conn.execute(sql).fetchone()[0])

    top_roots = [
        dict(row)
        for row in conn.execute(
            "SELECT root_name, root_class, COUNT(*) AS seen_count FROM root_observations GROUP BY root_name, root_class ORDER BY seen_count DESC, root_name LIMIT 20"
        )
    ]
    top_reasons = [
        dict(row)
        for row in conn.execute(
            "SELECT reason_id, reason_name, support_count, trust_level FROM reason_basins ORDER BY support_count DESC, reason_id LIMIT 20"
        )
    ]
    top_obstructions = [
        dict(row)
        for row in conn.execute(
            "SELECT obstruction_class, COUNT(*) AS count FROM obstructions GROUP BY obstruction_class ORDER BY count DESC, obstruction_class LIMIT 20"
        )
    ]
    recent_runs = [
        {**dict(row), "summary": json_loads(row["summary_json"], {})}
        for row in conn.execute(
            "SELECT run_id, created_at, run_name, pack_id, summary_json FROM runs ORDER BY created_at DESC LIMIT ?",
            (recent_limit,),
        )
    ]
    return {
        "total_runs": one("SELECT COUNT(*) FROM runs"),
        "total_targets": one("SELECT COUNT(*) FROM targets"),
        "accepted_targets": one("SELECT COUNT(*) FROM targets WHERE status='LEAN_ACCEPTED_TARGET'"),
        "total_roots": one("SELECT COUNT(DISTINCT root_name) FROM root_observations"),
        "total_reasons": one("SELECT COUNT(*) FROM reason_basins"),
        "constructor_attempts": one("SELECT COUNT(*) FROM constructor_attempts"),
        "verified_constructors": one("SELECT COUNT(*) FROM verified_constructors"),
        "obstructions": one("SELECT COUNT(*) FROM obstructions"),
        "top_roots": top_roots,
        "top_reason_basins": top_reasons,
        "top_obstruction_classes": top_obstructions,
        "recent_runs": recent_runs,
    }


def render_lawbook_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# MathGraph Digest Lawbook Summary",
        "",
        f"- Total runs: {summary['total_runs']}",
        f"- Total targets: {summary['total_targets']}",
        f"- Accepted targets: {summary['accepted_targets']}",
        f"- Total roots: {summary['total_roots']}",
        f"- Total reasons: {summary['total_reasons']}",
        f"- Constructor attempts: {summary['constructor_attempts']}",
        f"- Verified constructors: {summary['verified_constructors']}",
        f"- Obstructions: {summary['obstructions']}",
        "",
        "## Top Roots",
    ]
    lines += [f"- `{r['root_name']}` ({r['root_class']}): {r['seen_count']}" for r in summary["top_roots"]] or ["- None"]
    lines += ["", "## Top Reason Basins"]
    lines += [f"- `{r['reason_id']}`: support={r['support_count']} trust={r['trust_level']}" for r in summary["top_reason_basins"]] or ["- None"]
    lines += ["", "## Top Obstructions"]
    lines += [f"- `{r['obstruction_class']}`: {r['count']}" for r in summary["top_obstruction_classes"]] or ["- None"]
    lines += ["", "## Boundary Reminder", "Release/demo/digest success is not proof. Only verifier/importer/finite-validator/chain-audit evidence promotes truth."]
    return "\n".join(lines) + "\n"


def seed_synthetic_lawbook(conn: sqlite3.Connection, *, run_id: str = "synthetic-run") -> None:
    """Small helper for tests and examples."""
    payload = {
        "run": {
            "run_id": run_id,
            "created_at": now_iso(),
            "run_name": "synthetic",
            "run_version": "test",
            "mathlib_root": "",
            "modules": ["Mathlib.Data.Nat.Basic"],
            "targets": ["Nat.succ_injective"],
            "pack_id": "synthetic_pack",
            "summary": {"accepted_target_count": 1},
        },
        "targets": [
            {
                "target_id": stable_id("target", "Nat.succ_injective"),
                "declaration_name": "Nat.succ_injective",
                "module": "Mathlib.Data.Nat.Basic",
                "formal_statement": "Nat.succ_injective : Function.Injective Nat.succ",
                "status": "LEAN_ACCEPTED_TARGET",
                "first_seen_run_id": run_id,
                "last_seen_run_id": run_id,
                "axiom_profile": {},
            }
        ],
        "target_observations": [],
        "root_observations": [
            {
                "root_observation_id": stable_id("root-obs", run_id, "Function.Injective"),
                "run_id": run_id,
                "target_id": stable_id("target", "Nat.succ_injective"),
                "declaration_name": "Nat.succ_injective",
                "root_name": "Function.Injective",
                "root_class": "shared_root_candidate",
            }
        ],
        "reason_basins": [
            {
                "reason_id": "basin_nat_injectivity_cancellation",
                "reason_name": "Nat injectivity / cancellation reason",
                "basin_class": "nat_injectivity_cancellation",
                "support_count": 1,
                "trust_level": "VERIFIED_CONSTRUCTOR_REASON",
                "root_nodes": ["Function.Injective"],
                "axiom_profile": {},
            }
        ],
        "target_reason_edges": [
            {
                "edge_id": stable_id("edge", "Nat.succ_injective", "basin_nat_injectivity_cancellation"),
                "target_id": stable_id("target", "Nat.succ_injective"),
                "reason_id": "basin_nat_injectivity_cancellation",
                "confidence": 1.0,
            }
        ],
        "constructor_attempts": [
            {
                "attempt_id": stable_id("attempt", run_id, "Nat.succ_injective", "exact_existing"),
                "run_id": run_id,
                "target_id": stable_id("target", "Nat.succ_injective"),
                "reason_id": "basin_nat_injectivity_cancellation",
                "template_id": "exact_existing",
                "proof_body": "by\n  exact Nat.succ_injective\n",
                "status": "LEAN_ACCEPTED_CONSTRUCTOR_TEST",
                "trust_level": "VERIFIED_CONSTRUCTOR_TEST",
            }
        ],
        "verified_constructors": [
            {
                "constructor_id": stable_id("constructor", "basin_nat_injectivity_cancellation", "exact_existing"),
                "reason_id": "basin_nat_injectivity_cancellation",
                "template_id": "exact_existing",
                "proof_body": "by\n  exact Nat.succ_injective\n",
                "target_examples": ["Nat.succ_injective"],
                "first_seen_run_id": run_id,
                "last_seen_run_id": run_id,
            }
        ],
        "obstructions": [
            {
                "obstruction_id": stable_id("obstruction", run_id, "simp", "unsolved_goals"),
                "run_id": run_id,
                "target_id": stable_id("target", "Nat.succ_injective"),
                "reason_id": "basin_nat_injectivity_cancellation",
                "template_id": "simp",
                "obstruction_class": "unsolved_goals",
                "message": "Constructor left goals.",
                "next_action": "Mine goal state.",
            }
        ],
    }
    write_digest_payload(conn, payload)

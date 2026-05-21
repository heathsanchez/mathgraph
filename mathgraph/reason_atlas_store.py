"""SQLite-backed advisory Reason Atlas store."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.schema_feedback import apply_feedback_to_entry, compute_priority_score, compute_promotion_score


class ReasonAtlasEntryKind(str, Enum):
    PROMOTED_ROUTE_LAW = "PROMOTED_ROUTE_LAW"
    STRICT_CONTACT_SEED = "STRICT_CONTACT_SEED"
    VISIBILITY_CONTACT = "VISIBILITY_CONTACT"
    REPAIRABLE_OBSTRUCTION = "REPAIRABLE_OBSTRUCTION"
    ROOT_OPERATOR_SCHEMA = "ROOT_OPERATOR_SCHEMA"
    ROOT_OPERATOR_INSTANCE = "ROOT_OPERATOR_INSTANCE"
    CONSTRUCTOR_HINT = "CONSTRUCTOR_HINT"
    SCHEDULER_PRIOR = "SCHEDULER_PRIOR"
    NAMED_ADVISORY_OBSTRUCTION = "NAMED_ADVISORY_OBSTRUCTION"


class ReasonAtlasTrust(str, Enum):
    ADVISORY = "ADVISORY"
    CANDIDATE = "CANDIDATE"
    PROMOTED_ADVISORY = "PROMOTED_ADVISORY"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class ReasonAtlasEntryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"
    SUPERSEDED = "SUPERSEDED"
    UNDER_REVIEW = "UNDER_REVIEW"


class ReasonAtlasFeedbackOutcome(str, Enum):
    TRANSFER_SUCCESS = "TRANSFER_SUCCESS"
    TRANSFER_FAILURE = "TRANSFER_FAILURE"
    VERIFIER_SUCCESS = "VERIFIER_SUCCESS"
    VERIFIER_FAILURE = "VERIFIER_FAILURE"
    OBSTRUCTION_FOUND = "OBSTRUCTION_FOUND"
    RESIDUAL_COMPRESSED = "RESIDUAL_COMPRESSED"
    RESIDUAL_EXPANDED = "RESIDUAL_EXPANDED"
    DELETION_HURT = "DELETION_HURT"
    DELETION_SAFE = "DELETION_SAFE"
    DUPLICATE = "DUPLICATE"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class ReasonAtlasStoreConfig:
    db_path: str | Path


@dataclass(frozen=True)
class ReasonAtlasEntry:
    entry_id: str
    kind: ReasonAtlasEntryKind
    name: str
    atoms: list[str] = field(default_factory=list)
    pattern: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    source_trace_ids: list[str] = field(default_factory=list)
    source_entry_ids: list[str] = field(default_factory=list)
    evidence_kind: str = "ADVISORY_REASON_ATLAS_ENTRY"
    advisory_only: bool = True
    verifier_promoted: bool = False
    trust: ReasonAtlasTrust = ReasonAtlasTrust.ADVISORY
    status: ReasonAtlasEntryStatus = ReasonAtlasEntryStatus.ACTIVE
    support: int = 0
    family_count: int = 0
    root_count: int = 0
    hidden_program_count: int = 0
    transfer_successes: int = 0
    transfer_failures: int = 0
    verifier_successes: int = 0
    verifier_failures: int = 0
    obstruction_count: int = 0
    residual_compression_total: float = 0.0
    deletion_hurt_count: int = 0
    deletion_safe_count: int = 0
    promotion_score: float = 0.0
    priority_score: float = 0.0
    decay: float = 1.0
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _parse_enum(ReasonAtlasEntryKind, self.kind, ReasonAtlasEntryKind.CONSTRUCTOR_HINT))
        object.__setattr__(self, "trust", _parse_enum(ReasonAtlasTrust, self.trust, ReasonAtlasTrust.ADVISORY))
        object.__setattr__(self, "status", _parse_enum(ReasonAtlasEntryStatus, self.status, ReasonAtlasEntryStatus.ACTIVE))
        object.__setattr__(self, "advisory_only", True)
        object.__setattr__(self, "verifier_promoted", False)
        now = _utc_now()
        if not self.created_at:
            object.__setattr__(self, "created_at", now)
        if not self.updated_at:
            object.__setattr__(self, "updated_at", now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "kind": self.kind.value,
            "name": self.name,
            "atoms": list(self.atoms),
            "pattern": self.pattern,
            "payload": dict(self.payload),
            "source_trace_ids": list(self.source_trace_ids),
            "source_entry_ids": list(self.source_entry_ids),
            "evidence_kind": self.evidence_kind,
            "advisory_only": True,
            "verifier_promoted": False,
            "trust": self.trust.value,
            "status": self.status.value,
            "support": self.support,
            "family_count": self.family_count,
            "root_count": self.root_count,
            "hidden_program_count": self.hidden_program_count,
            "transfer_successes": self.transfer_successes,
            "transfer_failures": self.transfer_failures,
            "verifier_successes": self.verifier_successes,
            "verifier_failures": self.verifier_failures,
            "obstruction_count": self.obstruction_count,
            "residual_compression_total": self.residual_compression_total,
            "deletion_hurt_count": self.deletion_hurt_count,
            "deletion_safe_count": self.deletion_safe_count,
            "promotion_score": self.promotion_score,
            "priority_score": self.priority_score,
            "decay": self.decay,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasonAtlasEntry":
        return cls(
            entry_id=str(data.get("entry_id") or content_id("reason_atlas_entry", data)),
            kind=_parse_enum(ReasonAtlasEntryKind, data.get("kind"), ReasonAtlasEntryKind.CONSTRUCTOR_HINT),
            name=str(data.get("name", "")),
            atoms=list(data.get("atoms", []) or []),
            pattern=str(data.get("pattern", "")),
            payload=dict(data.get("payload", {}) or {}),
            source_trace_ids=list(data.get("source_trace_ids", []) or []),
            source_entry_ids=list(data.get("source_entry_ids", []) or []),
            evidence_kind=str(data.get("evidence_kind", "ADVISORY_REASON_ATLAS_ENTRY")),
            trust=_parse_enum(ReasonAtlasTrust, data.get("trust"), ReasonAtlasTrust.ADVISORY),
            status=_parse_enum(ReasonAtlasEntryStatus, data.get("status"), ReasonAtlasEntryStatus.ACTIVE),
            support=int(data.get("support", 0) or 0),
            family_count=int(data.get("family_count", 0) or 0),
            root_count=int(data.get("root_count", 0) or 0),
            hidden_program_count=int(data.get("hidden_program_count", 0) or 0),
            transfer_successes=int(data.get("transfer_successes", 0) or 0),
            transfer_failures=int(data.get("transfer_failures", 0) or 0),
            verifier_successes=int(data.get("verifier_successes", 0) or 0),
            verifier_failures=int(data.get("verifier_failures", 0) or 0),
            obstruction_count=int(data.get("obstruction_count", 0) or 0),
            residual_compression_total=float(data.get("residual_compression_total", 0.0) or 0.0),
            deletion_hurt_count=int(data.get("deletion_hurt_count", 0) or 0),
            deletion_safe_count=int(data.get("deletion_safe_count", 0) or 0),
            promotion_score=float(data.get("promotion_score", 0.0) or 0.0),
            priority_score=float(data.get("priority_score", 0.0) or 0.0),
            decay=float(data.get("decay", 1.0) or 1.0),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ReasonAtlasFeedbackEvent:
    event_id: str
    entry_id: str
    outcome: ReasonAtlasFeedbackOutcome
    created_at: str = ""
    residual_delta: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    advisory_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcome", _parse_enum(ReasonAtlasFeedbackOutcome, self.outcome, ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE))
        object.__setattr__(self, "advisory_only", True)
        if not self.created_at:
            object.__setattr__(self, "created_at", _utc_now())

    @classmethod
    def create(cls, entry_id: str, outcome: ReasonAtlasFeedbackOutcome | str, **kwargs: Any) -> "ReasonAtlasFeedbackEvent":
        return cls(content_id("reason_atlas_feedback", [entry_id, str(outcome), kwargs, _utc_now()]), entry_id, outcome, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "entry_id": self.entry_id,
            "outcome": self.outcome.value,
            "created_at": self.created_at,
            "residual_delta": self.residual_delta,
            "metadata": dict(self.metadata),
            "advisory_only": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasonAtlasFeedbackEvent":
        return cls(
            event_id=str(data.get("event_id") or content_id("reason_atlas_feedback", data)),
            entry_id=str(data.get("entry_id", "")),
            outcome=_parse_enum(ReasonAtlasFeedbackOutcome, data.get("outcome"), ReasonAtlasFeedbackOutcome.TRANSFER_FAILURE),
            created_at=str(data.get("created_at", "")),
            residual_delta=float(data.get("residual_delta", 0.0) or 0.0),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ReasonAtlasQuery:
    kind: ReasonAtlasEntryKind | str | None = None
    atom: str | None = None
    status: ReasonAtlasEntryStatus | str | None = None
    trust: ReasonAtlasTrust | str | None = None
    limit: int = 100


@dataclass(frozen=True)
class ReasonAtlasQueryResult:
    entries: list[ReasonAtlasEntry]
    total_count: int


@dataclass(frozen=True)
class ReasonAtlasStoreStats:
    entry_count: int
    feedback_count: int
    active_count: int
    advisory_boundary_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_count": self.entry_count,
            "feedback_count": self.feedback_count,
            "active_count": self.active_count,
            "advisory_boundary_ok": self.advisory_boundary_ok,
        }


class ReasonAtlasStore:
    def __init__(self, config: ReasonAtlasStoreConfig | str | Path) -> None:
        self.config = config if isinstance(config, ReasonAtlasStoreConfig) else ReasonAtlasStoreConfig(config)
        self.path = Path(self.config.db_path)
        self.conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS reason_atlas_entries (entry_id TEXT PRIMARY KEY, kind TEXT, name TEXT, atoms_json TEXT, pattern TEXT, payload_json TEXT, source_trace_ids_json TEXT, source_entry_ids_json TEXT, evidence_kind TEXT, advisory_only INTEGER, verifier_promoted INTEGER, trust TEXT, status TEXT, support INTEGER, family_count INTEGER, root_count INTEGER, hidden_program_count INTEGER, transfer_successes INTEGER, transfer_failures INTEGER, verifier_successes INTEGER, verifier_failures INTEGER, obstruction_count INTEGER, residual_compression_total REAL, deletion_hurt_count INTEGER, deletion_safe_count INTEGER, promotion_score REAL, priority_score REAL, decay REAL, created_at TEXT, updated_at TEXT, metadata_json TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS reason_atlas_feedback (event_id TEXT PRIMARY KEY, entry_id TEXT, outcome TEXT, created_at TEXT, residual_delta REAL, metadata_json TEXT, advisory_only INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS reason_atlas_edges (edge_id TEXT PRIMARY KEY, source_entry_id TEXT, target_entry_id TEXT, edge_kind TEXT, metadata_json TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS reason_atlas_metadata (key TEXT PRIMARY KEY, value_json TEXT)")
        for col in ("kind", "status", "trust", "priority_score", "promotion_score", "updated_at"):
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_reason_atlas_entries_{col} ON reason_atlas_entries ({col})")
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def upsert_entry(self, entry: ReasonAtlasEntry) -> ReasonAtlasEntry:
        self._ensure()
        if not entry.advisory_only:
            raise ValueError("Reason Atlas entries must remain advisory_only=True")
        scored = replace(
            entry,
            advisory_only=True,
            verifier_promoted=False,
            priority_score=entry.priority_score or compute_priority_score(entry),
            promotion_score=entry.promotion_score or compute_promotion_score(entry),
            updated_at=_utc_now(),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO reason_atlas_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            _entry_row(scored),
        )
        self.conn.commit()
        return scored

    def get_entry(self, entry_id: str) -> ReasonAtlasEntry | None:
        self._ensure()
        row = self.conn.execute("SELECT * FROM reason_atlas_entries WHERE entry_id=?", (entry_id,)).fetchone()
        return _entry_from_row(row) if row else None

    def query(self, query: ReasonAtlasQuery) -> ReasonAtlasQueryResult:
        self._ensure()
        clauses: list[str] = []
        params: list[Any] = []
        if query.kind:
            clauses.append("kind=?")
            params.append(_enum_value(query.kind))
        if query.status:
            clauses.append("status=?")
            params.append(_enum_value(query.status))
        if query.trust:
            clauses.append("trust=?")
            params.append(_enum_value(query.trust))
        sql = "SELECT * FROM reason_atlas_entries"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY priority_score DESC, updated_at DESC LIMIT ?"
        params.append(int(query.limit))
        entries = [_entry_from_row(row) for row in self.conn.execute(sql, params).fetchall()]
        if query.atom:
            entries = [entry for entry in entries if query.atom in entry.atoms]
        return ReasonAtlasQueryResult(entries, len(entries))

    def add_feedback(self, event: ReasonAtlasFeedbackEvent) -> ReasonAtlasFeedbackEvent:
        self._ensure()
        self.conn.execute(
            "INSERT OR REPLACE INTO reason_atlas_feedback VALUES (?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.entry_id,
                event.outcome.value,
                event.created_at,
                event.residual_delta,
                _json(event.metadata),
                1,
            ),
        )
        entry = self.get_entry(event.entry_id)
        if entry:
            self.upsert_entry(apply_feedback_to_entry(entry, event))
        self.conn.commit()
        return event

    def feedback_for_entry(self, entry_id: str) -> list[ReasonAtlasFeedbackEvent]:
        self._ensure()
        rows = self.conn.execute("SELECT * FROM reason_atlas_feedback WHERE entry_id=? ORDER BY created_at", (entry_id,)).fetchall()
        return [_feedback_from_row(row) for row in rows]

    def recompute_entry_scores(self, entry_id: str) -> ReasonAtlasEntry | None:
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        return self.upsert_entry(replace(entry, priority_score=compute_priority_score(entry), promotion_score=compute_promotion_score(entry)))

    def recompute_all_scores(self) -> None:
        for entry in self.query(ReasonAtlasQuery(limit=1_000_000)).entries:
            self.recompute_entry_scores(entry.entry_id)

    def export_reason_atlas_jsonl(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for entry in self.query(ReasonAtlasQuery(limit=1_000_000)).entries:
                handle.write(json.dumps(entry.to_dict(), sort_keys=True) + "\n")

    def export_next_queue_rows(self, path: str | Path, limit: int = 100) -> list[dict[str, Any]]:
        rows = [_next_queue_row(entry) for entry in self.query(ReasonAtlasQuery(status=ReasonAtlasEntryStatus.ACTIVE, limit=limit)).entries]
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        return rows

    def stats(self) -> ReasonAtlasStoreStats:
        self._ensure()
        entry_count = self.conn.execute("SELECT COUNT(*) FROM reason_atlas_entries").fetchone()[0]
        feedback_count = self.conn.execute("SELECT COUNT(*) FROM reason_atlas_feedback").fetchone()[0]
        active_count = self.conn.execute("SELECT COUNT(*) FROM reason_atlas_entries WHERE status='ACTIVE'").fetchone()[0]
        bad = self.conn.execute("SELECT COUNT(*) FROM reason_atlas_entries WHERE advisory_only != 1 OR verifier_promoted != 0").fetchone()[0]
        return ReasonAtlasStoreStats(entry_count, feedback_count, active_count, bad == 0)

    def retire_entry(self, entry_id: str, reason: str) -> ReasonAtlasEntry | None:
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        retired = replace(entry, status=ReasonAtlasEntryStatus.RETIRED, trust=ReasonAtlasTrust.RETIRED, metadata={**entry.metadata, "retired_reason": reason})
        return self.upsert_entry(retired)

    def supersede_entry(self, old_entry_id: str, new_entry_id: str, reason: str) -> ReasonAtlasEntry | None:
        entry = self.get_entry(old_entry_id)
        if not entry:
            return None
        superseded = replace(entry, status=ReasonAtlasEntryStatus.SUPERSEDED, metadata={**entry.metadata, "superseded_by": new_entry_id, "superseded_reason": reason})
        return self.upsert_entry(superseded)

    def _ensure(self) -> None:
        if self.conn is None:
            self.initialize()


def _next_queue_row(entry: ReasonAtlasEntry) -> dict[str, Any]:
    if entry.obstruction_count > 0 or entry.kind == ReasonAtlasEntryKind.REPAIRABLE_OBSTRUCTION:
        kind = "REPAIR_TEST"
    elif entry.transfer_failures > entry.transfer_successes:
        kind = "OBSTRUCTION_SPLIT"
    elif entry.transfer_successes == 0:
        kind = "TRANSFER_TEST"
    elif entry.deletion_hurt_count > entry.deletion_safe_count:
        kind = "SCHEMA_EXPANSION"
    else:
        kind = "VERIFIER_ATTEMPT"
    return {
        "task_id": content_id("reason_atlas_task", [entry.entry_id, kind, entry.priority_score]),
        "task_kind": kind,
        "entry_id": entry.entry_id,
        "entry_kind": entry.kind.value,
        "priority_score": entry.priority_score,
        "atoms": list(entry.atoms),
        "pattern": entry.pattern,
        "reason": "advisory_reason_atlas_feedback",
        "advisory_only": True,
        "payload": dict(entry.payload),
    }


def _entry_row(entry: ReasonAtlasEntry) -> tuple[Any, ...]:
    return (
        entry.entry_id, entry.kind.value, entry.name, _json(entry.atoms), entry.pattern, _json(entry.payload),
        _json(entry.source_trace_ids), _json(entry.source_entry_ids), entry.evidence_kind, 1, 0,
        entry.trust.value, entry.status.value, entry.support, entry.family_count, entry.root_count,
        entry.hidden_program_count, entry.transfer_successes, entry.transfer_failures, entry.verifier_successes,
        entry.verifier_failures, entry.obstruction_count, entry.residual_compression_total,
        entry.deletion_hurt_count, entry.deletion_safe_count, entry.promotion_score, entry.priority_score,
        entry.decay, entry.created_at, entry.updated_at, _json(entry.metadata),
    )


def _entry_from_row(row: sqlite3.Row) -> ReasonAtlasEntry:
    return ReasonAtlasEntry.from_dict({
        "entry_id": row["entry_id"], "kind": row["kind"], "name": row["name"], "atoms": _loads(row["atoms_json"]),
        "pattern": row["pattern"], "payload": _loads(row["payload_json"]), "source_trace_ids": _loads(row["source_trace_ids_json"]),
        "source_entry_ids": _loads(row["source_entry_ids_json"]), "evidence_kind": row["evidence_kind"],
        "trust": row["trust"], "status": row["status"], "support": row["support"], "family_count": row["family_count"],
        "root_count": row["root_count"], "hidden_program_count": row["hidden_program_count"], "transfer_successes": row["transfer_successes"],
        "transfer_failures": row["transfer_failures"], "verifier_successes": row["verifier_successes"], "verifier_failures": row["verifier_failures"],
        "obstruction_count": row["obstruction_count"], "residual_compression_total": row["residual_compression_total"],
        "deletion_hurt_count": row["deletion_hurt_count"], "deletion_safe_count": row["deletion_safe_count"],
        "promotion_score": row["promotion_score"], "priority_score": row["priority_score"], "decay": row["decay"],
        "created_at": row["created_at"], "updated_at": row["updated_at"], "metadata": _loads(row["metadata_json"]),
    })


def _feedback_from_row(row: sqlite3.Row) -> ReasonAtlasFeedbackEvent:
    return ReasonAtlasFeedbackEvent.from_dict({"event_id": row["event_id"], "entry_id": row["entry_id"], "outcome": row["outcome"], "created_at": row["created_at"], "residual_delta": row["residual_delta"], "metadata": _loads(row["metadata_json"])})


def _parse_enum(enum_cls: type[Enum], value: Any, default: Any) -> Any:
    if isinstance(value, enum_cls):
        return value
    text = str(value or "").upper()
    for item in enum_cls:
        if text == item.value or text == item.name:
            return item
    return default


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _loads(value: str) -> Any:
    return json.loads(value) if value else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

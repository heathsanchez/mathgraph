"""Small SQLite residual lawbook helpers for autonomous compounding runs."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ResidualLawbook:
    path: Path

    @classmethod
    def open(cls, path: str | Path) -> "ResidualLawbook":
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        book = cls(target)
        book.init()
        return book

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path))

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS run_summaries (run_id TEXT PRIMARY KEY, created_at TEXT, payload_json TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS episode_metrics (row_id TEXT PRIMARY KEY, run_id TEXT, episode INTEGER, payload_json TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS residual_obstructions (row_id TEXT PRIMARY KEY, run_id TEXT, obstruction_name TEXT, payload_json TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS terminal_audit (row_id TEXT PRIMARY KEY, run_id TEXT, payload_json TEXT NOT NULL)")
            conn.commit()

    def write_run_summary(self, run_id: str, payload: Mapping[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO run_summaries(run_id, created_at, payload_json) VALUES (?, ?, ?)",
                (run_id, utc_now(), json.dumps(dict(payload), sort_keys=True)),
            )
            conn.commit()

    def write_rows(self, table: str, run_id: str, rows: Iterable[Mapping[str, Any]]) -> int:
        allowed = {"episode_metrics", "residual_obstructions", "terminal_audit"}
        if table not in allowed:
            raise ValueError(f"unsupported residual lawbook table: {table}")
        count = 0
        with self.connect() as conn:
            for count, row in enumerate(rows, start=1):
                data = dict(row)
                row_id = str(data.get("row_id") or f"{run_id}:{table}:{count}")
                if table == "episode_metrics":
                    conn.execute(
                        "INSERT OR REPLACE INTO episode_metrics(row_id, run_id, episode, payload_json) VALUES (?, ?, ?, ?)",
                        (row_id, run_id, int(data.get("episode", 0) or 0), json.dumps(data, sort_keys=True)),
                    )
                elif table == "residual_obstructions":
                    conn.execute(
                        "INSERT OR REPLACE INTO residual_obstructions(row_id, run_id, obstruction_name, payload_json) VALUES (?, ?, ?, ?)",
                        (row_id, run_id, str(data.get("obstruction_name", "")), json.dumps(data, sort_keys=True)),
                    )
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO terminal_audit(row_id, run_id, payload_json) VALUES (?, ?, ?)",
                        (row_id, run_id, json.dumps(data, sort_keys=True)),
                    )
            conn.commit()
        return count

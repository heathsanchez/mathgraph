"""Simple next-pack scheduler for persistent Mathlib digest Lawbooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mathgraph.lawbook_accumulator import connect_lawbook, stable_id, upsert_pending_pack


def propose_next_packs(lawbook: str | Path, *, strategy: str = "residual_first", limit: int = 5) -> list[dict[str, Any]]:
    conn = connect_lawbook(lawbook)
    rows = []
    if strategy == "highest_obstruction_count_first":
        rows = conn.execute(
            "SELECT reason_id, COUNT(*) AS score FROM obstructions GROUP BY reason_id ORDER BY score DESC LIMIT ?",
            (limit,),
        ).fetchall()
    elif strategy == "low_constructor_success_first":
        rows = conn.execute(
            """
            SELECT r.reason_id, COALESCE(v.vc,0) * 1.0 / NULLIF(COALESCE(a.ac,0),0) AS rate
            FROM reason_basins r
            LEFT JOIN (SELECT reason_id, COUNT(*) AS ac FROM constructor_attempts GROUP BY reason_id) a USING(reason_id)
            LEFT JOIN (SELECT reason_id, COUNT(*) AS vc FROM verified_constructors GROUP BY reason_id) v USING(reason_id)
            ORDER BY COALESCE(rate,0) ASC, r.reason_id LIMIT ?
            """,
            (limit,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT reason_id, support_count AS score FROM reason_basins WHERE trust_level!='VERIFIED_CONSTRUCTOR_REASON' ORDER BY support_count DESC, reason_id LIMIT ?",
            (limit,),
        ).fetchall()
    packs = []
    for row in rows:
        reason_id = row["reason_id"]
        targets = [
            r["declaration_name"]
            for r in conn.execute(
                """
                SELECT t.declaration_name FROM targets t
                JOIN target_reason_edges e ON t.target_id=e.target_id
                WHERE e.reason_id=? ORDER BY t.declaration_name LIMIT 10
                """,
                (reason_id,),
            )
        ]
        pack = {
            "pack_id": stable_id("pending-pack", strategy, reason_id),
            "module": "Mathlib.Data.Nat.Basic",
            "targets": targets,
            "priority": float(row[1] or 0.0),
            "status": "PENDING",
            "created_from_reason": reason_id,
            "metadata": {"strategy": strategy},
        }
        upsert_pending_pack(conn, pack)
        packs.append(pack)
    conn.close()
    return packs


def export_next_pack_config(lawbook: str | Path, out_dir: str | Path, *, strategy: str = "residual_first", limit: int = 5) -> dict[str, str]:
    packs = propose_next_packs(lawbook, strategy=strategy, limit=limit)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "next_pack_config.json"
    path.write_text(json.dumps({"pack_id": f"scheduled_{strategy}", "modules": ["Mathlib.Data.Nat.Basic"], "packs": packs}, indent=2, sort_keys=True), encoding="utf-8")
    return {"next_pack_config": str(path)}

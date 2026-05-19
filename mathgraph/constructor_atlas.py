"""Constructor Atlas aggregation for persistent Mathlib digest Lawbooks."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from mathgraph.lawbook_accumulator import connect_lawbook, json_loads


def build_constructor_atlas(conn: sqlite3.Connection) -> dict[str, Any]:
    reasons = [dict(r) for r in conn.execute("SELECT * FROM reason_basins ORDER BY reason_id")]
    attempts = [dict(r) for r in conn.execute("SELECT * FROM constructor_attempts")]
    verified = [dict(r) for r in conn.execute("SELECT * FROM verified_constructors")]
    obstructions = [dict(r) for r in conn.execute("SELECT * FROM obstructions")]
    by_reason_attempts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_reason_verified: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_reason_obstructions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempts:
        by_reason_attempts[row["reason_id"]].append(row)
    for row in verified:
        by_reason_verified[row["reason_id"]].append(row)
    for row in obstructions:
        by_reason_obstructions[row["reason_id"]].append(row)
    records = []
    for reason in reasons:
        rid = reason["reason_id"]
        at = by_reason_attempts[rid]
        vf = by_reason_verified[rid]
        obs = by_reason_obstructions[rid]
        template_counts = Counter(row["template_id"] for row in vf)
        best_template = template_counts.most_common(1)[0][0] if template_counts else ""
        shortest = min((row["proof_body"] for row in vf if row.get("proof_body")), key=len, default="")
        obstruction_counts = Counter(row["obstruction_class"] for row in obs)
        records.append(
            {
                "reason_id": rid,
                "reason_name": reason["reason_name"],
                "constructor_tests": len(at),
                "verified_count": len(vf),
                "success_rate": (len(vf) / len(at)) if at else 0.0,
                "best_template_id": best_template,
                "shortest_verified_proof_body": shortest,
                "verified_targets": sorted({t for row in vf for t in json_loads(row["target_examples_json"], [])}),
                "failed_template_classes": sorted(set(row["template_id"] for row in obs)),
                "obstruction_class_counts": dict(obstruction_counts),
                "suggested_next_action": suggest_next_action(obstruction_counts),
            }
        )
    return {
        "constructor_atlas": records,
        "constructor_attempt_total": len(attempts),
        "verified_constructor_total": len(verified),
        "obstruction_total": len(obstructions),
    }


def suggest_next_action(counts: Counter[str]) -> str:
    if not counts:
        return "Keep reusing verified constructors."
    top = counts.most_common(1)[0][0]
    return {
        "unsolved_goals": "Mine goal states and split constructors.",
        "unknown_reference": "Filter invalid roots and add imports.",
        "type_mismatch": "Try equality transport/orientation constructors.",
        "typeclass_failure": "Add typeclass/instance root handling.",
        "timeout": "Reduce template complexity.",
    }.get(top, "Inspect stderr and refine basin.")


def write_csv(path: str | Path, rows: list[Mapping[str, Any]], fieldnames: list[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items() if k in fieldnames})


def export_constructor_atlas(lawbook: str | Path, out_dir: str | Path) -> dict[str, str]:
    conn = connect_lawbook(lawbook)
    atlas = build_constructor_atlas(conn)
    conn.close()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out / "constructor_atlas.json",
        "csv": out / "constructor_atlas.csv",
        "obstructions": out / "obstruction_summary.csv",
        "best": out / "best_constructors_by_reason.csv",
        "report": out / "constructor_distiller_report.md",
    }
    paths["json"].write_text(json.dumps(atlas, indent=2, sort_keys=True, default=str), encoding="utf-8")
    fields = ["reason_id", "reason_name", "constructor_tests", "verified_count", "success_rate", "best_template_id", "shortest_verified_proof_body", "verified_targets", "failed_template_classes", "obstruction_class_counts", "suggested_next_action"]
    write_csv(paths["csv"], atlas["constructor_atlas"], fields)
    obstruction_rows = []
    for row in atlas["constructor_atlas"]:
        for klass, count in row["obstruction_class_counts"].items():
            obstruction_rows.append({"reason_id": row["reason_id"], "obstruction_class": klass, "count": count})
    write_csv(paths["obstructions"], obstruction_rows, ["reason_id", "obstruction_class", "count"])
    best_rows = [{k: row[k] for k in ("reason_id", "best_template_id", "verified_count", "success_rate", "suggested_next_action")} for row in atlas["constructor_atlas"]]
    write_csv(paths["best"], best_rows, ["reason_id", "best_template_id", "verified_count", "success_rate", "suggested_next_action"])
    paths["report"].write_text(render_constructor_report(atlas), encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def render_constructor_report(atlas: Mapping[str, Any]) -> str:
    lines = [
        "# Constructor Distiller Report",
        "",
        f"- Constructor attempts: {atlas['constructor_attempt_total']}",
        f"- Verified constructors: {atlas['verified_constructor_total']}",
        f"- Obstructions: {atlas['obstruction_total']}",
        "",
        "## By Reason",
    ]
    for row in atlas["constructor_atlas"]:
        lines.append(f"- `{row['reason_id']}`: verified={row['verified_count']} tests={row['constructor_tests']} best=`{row['best_template_id']}` action={row['suggested_next_action']}")
    return "\n".join(lines) + "\n"

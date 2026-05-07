#!/usr/bin/env python
"""Import external root/reason/obstruction atlas artifacts to JSON summaries."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathgraph.artifact_importers import (  # noqa: E402
    load_v167_motif_summary,
    load_v167_obstructions,
    load_v167_reason_nodes,
    load_v167_root_nodes,
    load_v167_table_atlas,
    write_json_rows,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots-csv")
    parser.add_argument("--reasons-csv")
    parser.add_argument("--obstructions-csv")
    parser.add_argument("--tables-csv")
    parser.add_argument("--motifs-csv")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--summary-json")
    parser.add_argument("--sqlite-index")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    roots = load_v167_root_nodes(args.roots_csv, args.limit) if args.roots_csv else []
    reasons = load_v167_reason_nodes(args.reasons_csv, args.limit) if args.reasons_csv else []
    obstructions = (
        load_v167_obstructions(args.obstructions_csv, args.limit) if args.obstructions_csv else []
    )
    tables = load_v167_table_atlas(args.tables_csv, args.limit) if args.tables_csv else []
    motifs = load_v167_motif_summary(args.motifs_csv, args.limit) if args.motifs_csv else []

    write_json_rows(roots, out_dir / "root_nodes.json")
    write_json_rows(reasons, out_dir / "reason_nodes.json")
    write_json_rows(obstructions, out_dir / "obstructions.json")
    write_json_rows(tables, out_dir / "table_atlas.json")
    write_json_rows(motifs, out_dir / "motif_summary.json")
    summary = {
        "root_count": len(roots),
        "reason_count": len(reasons),
        "obstruction_count": len(obstructions),
        "table_count": len(tables),
        "motif_count": len(motifs),
        "advisory_only": True,
    }
    summary_path = Path(args.summary_json) if args.summary_json else out_dir / "root_atlas_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if args.sqlite_index:
        _write_sqlite(Path(args.sqlite_index), roots, reasons, obstructions)
    print(json.dumps(summary, sort_keys=True))
    return 0


def _write_sqlite(path: Path, roots: list[object], reasons: list[object], obstructions: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS atlas(kind TEXT, id TEXT, payload_json TEXT)")
    conn.execute("DELETE FROM atlas")
    for kind, rows, id_key in (
        ("root", roots, "root_node_id"),
        ("reason", reasons, "reason_node_id"),
        ("obstruction", obstructions, "obstruction_id"),
    ):
        for row in rows:
            data = row.to_dict()
            conn.execute(
                "INSERT INTO atlas(kind, id, payload_json) VALUES (?, ?, ?)",
                (kind, data.get(id_key), json.dumps(data, sort_keys=True)),
            )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

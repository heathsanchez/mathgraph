#!/usr/bin/env python
"""Consolidate root candidates into canonical root families."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse
import json
import sys
from pathlib import Path

from mathgraph.artifact_importers import load_v167_obstructions, load_v167_reason_nodes, load_v167_root_nodes, write_json_rows  # noqa: E402
from mathgraph.obstruction_atlas import ObstructionNode  # noqa: E402
from mathgraph.reason_nodes import ReasonNode  # noqa: E402
from mathgraph.root_consolidation import (  # noqa: E402
    build_root_alias_map,
    consolidate_root_nodes,
    link_roots_to_obstructions,
    link_roots_to_reasons,
)
from mathgraph.root_nodes import RootNode  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots-json")
    parser.add_argument("--roots-csv")
    parser.add_argument("--reasons-json")
    parser.add_argument("--obstructions-json")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--sqlite-index")
    args = parser.parse_args(argv)
    if not args.roots_json and not args.roots_csv:
        parser.error("--roots-json or --roots-csv is required")

    roots = _load_json_nodes(args.roots_json, RootNode) if args.roots_json else load_v167_root_nodes(args.roots_csv)
    reasons = _load_json_nodes(args.reasons_json, ReasonNode) if args.reasons_json else []
    obstructions = (
        _load_json_nodes(args.obstructions_json, ObstructionNode) if args.obstructions_json else []
    )
    canonical = consolidate_root_nodes(roots)
    alias_map = build_root_alias_map(canonical)
    reason_links = link_roots_to_reasons(canonical, reasons)
    obstruction_links = link_roots_to_obstructions(canonical, obstructions)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_rows(canonical, out_dir / "canonical_root_nodes.json")
    (out_dir / "root_alias_map.json").write_text(json.dumps(alias_map, indent=2, sort_keys=True), encoding="utf-8")
    write_json_rows(reason_links, out_dir / "root_reason_links.json")
    write_json_rows(obstruction_links, out_dir / "root_obstruction_links.json")
    summary = {
        "input_root_count": len(roots),
        "canonical_root_count": len(canonical),
        "alias_count": len(alias_map),
        "reason_link_count": len(reason_links),
        "obstruction_link_count": len(obstruction_links),
        "advisory_only": True,
    }
    (out_dir / "canonical_root_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


def _load_json_nodes(path: str | None, cls: object) -> list[object]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("rows", data.get("items", []))
    return [cls.from_dict(row) for row in data]


if __name__ == "__main__":
    raise SystemExit(main())

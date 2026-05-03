#!/usr/bin/env python
"""Discover external MathGraph/SAIR assets without mutating them by default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph.asset_discovery import (  # noqa: E402
    AssetDiscoveryConfig,
    discover_mathgraph_assets,
    materialize_assets,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--copy-assets", action="store_true")
    parser.add_argument("--symlink-assets", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--max-files", type=int, default=5000)
    args = parser.parse_args(argv)

    if args.copy_assets and args.symlink_assets:
        parser.error("--copy-assets and --symlink-assets are mutually exclusive")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = discover_mathgraph_assets(
        AssetDiscoveryConfig(max_depth=args.max_depth, max_files=args.max_files)
    )
    materialized = materialize_assets(
        result,
        out_dir,
        copy=args.copy_assets,
        symlink=args.symlink_assets,
    )
    payload = {
        **result.to_dict(),
        "materialized": materialized,
        "outputs": {
            "json": str(out_dir / "asset_discovery_report.json"),
            "markdown": str(out_dir / "asset_discovery_report.md"),
        },
    }
    _write_json(payload, out_dir / "asset_discovery_report.json")
    _write_md(payload, out_dir / "asset_discovery_report.md")
    if args.json_only:
        print(json.dumps(result.summary, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _write_json(payload: dict, path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_md(payload: dict, path: Path) -> None:
    selected = payload.get("selected", {})
    lines = [
        "# MathGraph Asset Discovery Report",
        "",
        f"- traces_json: {_selected_path(selected.get('traces_json'))}",
        f"- equations: {_selected_path(selected.get('equations'))}",
        f"- matrix: {_selected_path(selected.get('matrix'))}",
        "",
        "Asset discovery is read-only unless copy or symlink materialization is requested.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _selected_path(value: dict | None) -> str | None:
    return value.get("path") if value else None


if __name__ == "__main__":
    raise SystemExit(main())

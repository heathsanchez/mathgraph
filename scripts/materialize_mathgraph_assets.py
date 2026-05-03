#!/usr/bin/env python
"""Materialize external MathGraph assets into a stable local assets directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph.asset_materialization import (  # noqa: E402
    AssetMaterializationConfig,
    default_search_roots,
    materialize_mathgraph_assets,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", default=None)
    parser.add_argument("--equations-path", default=None)
    parser.add_argument("--matrix-path", default=None)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--mode", choices=["copy", "symlink", "manifest-only"], default="copy")
    parser.add_argument("--search-root", action="append", default=None)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--max-files", type=int, default=20000)
    args = parser.parse_args(argv)

    roots = args.search_root if args.search_root else default_search_roots(ROOT)
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=args.out_dir,
            traces_json=args.traces_json,
            equations_path=args.equations_path,
            matrix_path=args.matrix_path,
            mode=args.mode,
            search_roots=roots,
            max_depth=args.max_depth,
            max_files=args.max_files,
        )
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

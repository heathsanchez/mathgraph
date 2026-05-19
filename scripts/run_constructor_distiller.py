#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.constructor_atlas import export_constructor_atlas


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lawbook", required=True)
    p.add_argument("--out-dir", required=True)
    a = p.parse_args(argv)
    paths = export_constructor_atlas(a.lawbook, a.out_dir)
    print("MathGraph Constructor Distiller")
    for key, path in paths.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

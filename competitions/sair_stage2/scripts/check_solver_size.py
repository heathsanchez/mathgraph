#!/usr/bin/env python
"""Check standalone solver size and imports."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

BANNED = {"mathgraph", "competitions", "numpy", "pandas", "z3", "requests", "sqlite3", "sklearn", "torch", "tensorflow"}
ALLOWED = {"argparse", "json", "os", "sys", "itertools", "__future__"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", required=True)
    parser.add_argument("--max-bytes", type=int, default=500000)
    args = parser.parse_args(argv)
    path = Path(args.solver)
    if not path.exists():
        print(json.dumps({"status": "missing", "solver": str(path)}))
        return 2
    size = path.stat().st_size
    imports = _imports(path)
    banned = sorted(name for name in imports if name.split(".")[0] in BANNED)
    nonstdlib = sorted(name for name in imports if name.split(".")[0] not in ALLOWED)
    ok = size < args.max_bytes and not banned and not nonstdlib
    payload = {
        "status": "ok" if ok else "failed",
        "solver": str(path),
        "size_bytes": size,
        "max_bytes": args.max_bytes,
        "under_budget": size < args.max_bytes,
        "imports": sorted(imports),
        "banned_imports": banned,
        "nonstdlib_imports": nonstdlib,
        "standalone": ok,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if ok else 2


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
    return found


if __name__ == "__main__":
    raise SystemExit(main())

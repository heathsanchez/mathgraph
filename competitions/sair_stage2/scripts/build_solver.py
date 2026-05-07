#!/usr/bin/env python
"""Build the standalone SAIR Stage 2 solver.py."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets")
    parser.add_argument("--out", default=str(ROOT / "dist" / "solver.py"))
    parser.add_argument("--max-bytes", type=int, default=500000)
    args = parser.parse_args(argv)
    out = Path(args.out)
    assets = Path(args.assets) if args.assets else SRC / "solver_assets.py"
    modules = [
        SRC / "equation_core.py",
        SRC / "finite_magma_core.py",
        SRC / "true_constructors.py",
        SRC / "false_constructors.py",
        assets,
        SRC / "solver_runtime.py",
    ]
    sections = {}
    chunks = [_header()]
    for path in modules:
        text = _compact(path.read_text(encoding="utf-8"))
        sections[path.name] = len(text.encode("utf-8"))
        chunks.append("\n# section: %s\n%s\n" % (path.name, text))
    out.parent.mkdir(parents=True, exist_ok=True)
    solver = "\n".join(chunks)
    out.write_text(solver, encoding="utf-8")
    size = out.stat().st_size
    report = {
        "solver": str(out),
        "size_bytes": size,
        "max_bytes": args.max_bytes,
        "under_budget": size < args.max_bytes,
        "sections": sections,
        "standalone": True,
    }
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "solver_size_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (artifacts / "solver_build_report.md").write_text(_report_md(report), encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    if size >= args.max_bytes:
        return 2
    return 0


def _header():
    return '''#!/usr/bin/env python
"""Standalone SAIR Stage 2 compact solver.

Generated from competitions/sair_stage2. Uses only Python stdlib.
"""
from __future__ import annotations
import argparse
import json
import sys
from itertools import product

SOLVER_BUILD = %r
''' % datetime.now(timezone.utc).isoformat()


def _compact(text):
    text = _strip_relative_import_blocks(text)
    out = []
    skip_doc = False
    quote = None
    for line in text.splitlines():
        stripped = line.strip()
        if skip_doc:
            if quote and quote in stripped:
                skip_doc = False
            continue
        if stripped.startswith("from __future__") or stripped.startswith("import ") or stripped.startswith("from "):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if stripped.count(stripped[:3]) == 1:
                skip_doc = True
                quote = stripped[:3]
            continue
        if stripped.startswith("#"):
            continue
        out.append(line.rstrip())
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _strip_relative_import_blocks(text):
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "try:" and i + 1 < len(lines) and "from ." in lines[i + 1]:
            i += 1
            while i < len(lines) and not lines[i].startswith("except ImportError"):
                i += 1
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith("    ")):
                if lines[i].strip() == "pass":
                    i += 1
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _report_md(report):
    lines = ["# Solver Build Report", "", f"- Solver: `{report['solver']}`", f"- Size: {report['size_bytes']} bytes", f"- Max: {report['max_bytes']} bytes", f"- Under budget: {report['under_budget']}", "", "## Sections"]
    for name, size in sorted(report["sections"].items()):
        lines.append(f"- `{name}`: {size} bytes")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

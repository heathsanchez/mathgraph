#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.digest_exports import export_lawbook_summary


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lawbook", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--html", action="store_true")
    p.add_argument("--print-json", action="store_true")
    a = p.parse_args(argv)
    paths = export_lawbook_summary(a.lawbook, a.out_dir, html=a.html)
    if a.print_json:
        print(json.dumps(paths, sort_keys=True))
    else:
        print("MathGraph Lawbook Summary")
        for key, path in paths.items():
            print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Audit a LawbookStore for the Milestone 0 trust boundary."""

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

from mathgraph.m0_audit import audit_m0_store, write_audit_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--report")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)
    report = audit_m0_store(args.store)
    if args.report:
        write_audit_report(report, args.report)
    print(json.dumps(report.to_dict(), sort_keys=True))
    return 2 if args.fail_on_critical and report.critical_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())


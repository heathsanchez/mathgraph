#!/usr/bin/env python
"""Serve the local MathGraph M0 HTTP middleware surface."""

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

from mathgraph.local_service import SERVICE_WARNINGS, make_server, schema


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--working-dir")
    parser.add_argument("--no-audit-after-write", action="store_true")
    parser.add_argument("--no-fail-on-critical-audit", action="store_true")
    parser.add_argument("--max-countermodel-order", type=int, default=3)
    args = parser.parse_args(argv)

    server = make_server(
        store_path=args.store,
        host=args.host,
        port=args.port,
        working_dir=args.working_dir,
        audit_after_write=not args.no_audit_after_write,
        fail_on_critical_audit=not args.no_fail_on_critical_audit,
        max_countermodel_order=args.max_countermodel_order,
    )
    url = f"http://{args.host}:{server.server_address[1]}"
    print(f"MathGraph local service: {url}")
    print(f"Store: {args.store}")
    print("Endpoints:")
    for endpoint in schema(args.store)["endpoints"]:
        print(f"  {endpoint['method']} {endpoint['path']}")
    for warning in SERVICE_WARNINGS:
        print(f"Warning: {warning}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

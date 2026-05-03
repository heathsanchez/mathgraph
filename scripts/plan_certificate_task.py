#!/usr/bin/env python
"""Plan certificate tasks from lawbook-backed pair advice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import CertificateLawbook, plan_certificate_task, plan_many_certificate_tasks
from mathgraph.task_planner import save_certificate_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-json", required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--target", default=None)
    parser.add_argument("--pairs-json", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-routes", type=int, default=5)
    args = parser.parse_args(argv)

    lawbook = CertificateLawbook.from_json(args.traces_json)
    if args.pairs_json:
        pairs = json.loads(Path(args.pairs_json).read_text(encoding="utf-8"))
        tasks = plan_many_certificate_tasks(lawbook, pairs, max_routes=args.max_routes)
        payload = [task.to_dict() for task in tasks]
        if args.out:
            save_certificate_task(args.out, tasks)
    else:
        if args.source is None or args.target is None:
            parser.error("--source and --target are required unless --pairs-json is provided")
        task = plan_certificate_task(
            lawbook,
            args.source,
            args.target,
            max_routes=args.max_routes,
        )
        payload = task.to_dict()
        if args.out:
            save_certificate_task(args.out, task)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

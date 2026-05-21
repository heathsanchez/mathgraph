#!/usr/bin/env python
"""Run a small advisory closed-loop scheduling smoke test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path(__file__)

from mathgraph.closed_loop import ClosedVerificationLoop  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="/tmp/mathgraph_closed_loop_smoke")
    args = parser.parse_args()

    loop = ClosedVerificationLoop(beta=1.0)
    loop.submit_many(
        [
            ("x * y = y * x", "a * b = b * a"),
            ("x = x", "y = y"),
            ("x * x = x", "(x * x) * x = x"),
            ("x * y = x", "a * b = a"),
            ("x * y = y", "a * b = b"),
        ]
    )
    initial = loop.schedule(top_k=5)
    loop.record_outcome(
        "x = x",
        "y = y",
        "VERIFIED_PROOF",
        "direct_substitution_instance",
        evidence={"boundary_kind": "toy_smoke"},
    )
    loop.record_outcome(
        "x * y = y",
        "a * b = b",
        "FINITE_COUNTERMODEL",
        "finite_countermodel",
        verification_status="REFUTED",
        evidence={"boundary_kind": "toy_smoke"},
    )
    followup = loop.schedule(top_k=5)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "closed_loop_smoke.json"
    loop.save_json(output)
    summary = {
        "initial_tasks": len(initial),
        "followup_tasks": len(followup),
        "pending": len(loop.pending),
        "outcomes": len(loop.outcomes),
        "events": len(loop.events),
        "output": str(output),
        "advisory": True,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

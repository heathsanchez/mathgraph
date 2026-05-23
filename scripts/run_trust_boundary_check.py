#!/usr/bin/env python3
"""Run MathGraph executable trust-boundary checks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TESTS = [
    "tests/test_core_invariants.py",
    "tests/test_terminal_form_contract.py",
    "tests/test_no_advisory_truth_promotion.py",
    "tests/test_finite_failure_not_true.py",
    "tests/test_replayable_evidence_manifest.py",
    "tests/test_lawbook_acceptance_contract.py",
    "tests/test_evidence_manifest_replay.py",
    "tests/test_canonical_demo_lawbook_acceptance.py",
    "tests/test_derived_certificate_guardrails.py",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    commands = [
        [sys.executable, "-m", "pytest", *TESTS, "-q"],
        [sys.executable, "scripts/run_canonical_finite_countermodel_demo.py", "--out-dir", "/tmp/mathgraph_trust_boundary_canonical_demo"],
        [sys.executable, "scripts/replay_evidence_manifest.py", "/tmp/mathgraph_trust_boundary_canonical_demo/evidence_manifest.json"],
    ]
    results = []
    ok = True
    for command in commands:
        proc = subprocess.run(command, cwd=root, text=True, capture_output=True)
        passed = proc.returncode == 0
        ok = ok and passed
        results.append(
            {
                "command": command,
                "passed": passed,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-2000:],
            }
        )
    summary = {"status": "PASS" if ok else "FAIL", "checks": results}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Replay a MathGraph EvidenceManifest and fail closed on mismatch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

from mathgraph.evidence_replay import replay_evidence_manifest


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest_path")
    parser.add_argument("--expected-terminal-form")
    args = parser.parse_args(argv)
    result = replay_evidence_manifest(args.manifest_path, expected_terminal_form=args.expected_terminal_form)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

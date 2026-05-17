#!/usr/bin/env python
"""Build persistent filtration evidence for root candidates."""

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
from pathlib import Path

from mathgraph.persistent_filtration import build_filtration_evidence, summarize_persistence


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--telemetry-jsonl", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots-json")
    group.add_argument("--roots-jsonl")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-jsonl")
    parser.add_argument("--summary")
    args = parser.parse_args(argv)
    rows = _read_jsonl(args.telemetry_jsonl)
    roots = _read_json_or_jsonl(args.roots_json, args.roots_jsonl)
    evidence = build_filtration_evidence(rows, roots)
    summaries = summarize_persistence(roots, evidence)
    payload = {
        "filtration_evidence": [item.to_dict() for item in evidence],
        "persistence_summaries": [item.to_dict() for item in summaries],
        "advisory_only": True,
    }
    _write_json(args.out_json, payload)
    if args.out_jsonl:
        _write_jsonl(args.out_jsonl, [item.to_dict() for item in evidence])
    if args.summary:
        _write_json(args.summary, {"root_count": len(roots), "evidence_count": len(evidence), "summary_count": len(summaries)})
    return 0


def _read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_json_or_jsonl(json_path: str | None, jsonl_path: str | None) -> list[dict]:
    if jsonl_path:
        return _read_jsonl(jsonl_path)
    data = json.loads(Path(str(json_path)).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("roots", "root_candidates", "canonical_roots"):
            if isinstance(data.get(key), list):
                return data[key]
    return data


def _write_json(path: str, payload: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: str, rows: list[dict]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

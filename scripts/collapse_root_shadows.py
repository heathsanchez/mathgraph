#!/usr/bin/env python
"""Collapse advisory root shadows while preserving alias records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mathgraph.root_shadow_collapse import collapse_root_shadows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots-json")
    group.add_argument("--roots-jsonl")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--aliases-json")
    parser.add_argument("--summary")
    parser.add_argument("--overlap-threshold", type=float, default=0.72)
    args = parser.parse_args(argv)
    roots = _read_json_or_jsonl(args.roots_json, args.roots_jsonl)
    result = collapse_root_shadows(roots, overlap_threshold=args.overlap_threshold)
    payload = result.to_dict()
    _write_json(args.out_json, payload)
    if args.aliases_json:
        _write_json(args.aliases_json, payload["alias_records"])
    if args.summary:
        _write_json(args.summary, payload["summary"])
    return 0


def _read_json_or_jsonl(json_path: str | None, jsonl_path: str | None) -> list[dict]:
    if jsonl_path:
        return [json.loads(line) for line in Path(jsonl_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(Path(str(json_path)).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("roots", "root_candidates", "canonical_roots"):
            if isinstance(data.get(key), list):
                return data[key]
    return data


def _write_json(path: str, payload) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

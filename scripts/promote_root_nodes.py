#!/usr/bin/env python
"""Create advisory root promotion records from persistence and shadow data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mathgraph.root_promotion import RootPromotionPolicy, promote_roots, promotion_summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots-json")
    group.add_argument("--roots-jsonl")
    parser.add_argument("--persistence-json", required=True)
    parser.add_argument("--shadow-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--min-persistence-score", type=float, default=2.0)
    parser.add_argument("--min-effective-filtration-count", type=float, default=2.0)
    parser.add_argument("--min-load-bearing-score", type=float, default=2.5)
    parser.add_argument("--min-sat-count", type=int, default=2)
    parser.add_argument("--max-shadow-penalty", type=float, default=0.75)
    parser.add_argument("--allow-shadows", action="store_true")
    args = parser.parse_args(argv)
    roots = _read_json_or_jsonl(args.roots_json, args.roots_jsonl)
    persistence_payload = json.loads(Path(args.persistence_json).read_text(encoding="utf-8"))
    persistence = persistence_payload.get("persistence_summaries", persistence_payload)
    shadow = json.loads(Path(args.shadow_json).read_text(encoding="utf-8"))
    policy = RootPromotionPolicy(
        min_persistence_score=args.min_persistence_score,
        min_effective_filtration_count=args.min_effective_filtration_count,
        min_load_bearing_score=args.min_load_bearing_score,
        min_sat_count=args.min_sat_count,
        max_shadow_penalty=args.max_shadow_penalty,
        require_non_shadow=not args.allow_shadows,
    )
    records = promote_roots(roots, persistence, shadow, policy=policy)
    payload = {"promotion_records": [record.to_dict() for record in records], "summary": promotion_summary(records)}
    _write_json(args.out_json, payload)
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

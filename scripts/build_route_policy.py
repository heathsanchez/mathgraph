#!/usr/bin/env python
"""Build deterministic route policy cards from pair outcomes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mathgraph import PairOutcome, RouteLearner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcomes-jsonl", required=True)
    parser.add_argument("--out-policy-json", default=None)
    parser.add_argument("--out-policy-jsonl", default=None)
    parser.add_argument("--out-stats", default=None)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--recommend-source", default=None)
    parser.add_argument("--recommend-target", default=None)
    parser.add_argument("--out-recommendation", default=None)
    args = parser.parse_args(argv)

    outcomes = _read_outcomes_jsonl(args.outcomes_jsonl)
    learner = RouteLearner(outcomes)
    cards = learner.build_policy_cards(min_support=args.min_support)
    stats = learner.stats()

    if args.out_policy_json:
        learner.save_policy_cards_json(args.out_policy_json)
    if args.out_policy_jsonl:
        learner.save_policy_cards_jsonl(args.out_policy_jsonl)
    if args.out_stats:
        learner.save_stats_json(args.out_stats)

    recommendation = None
    if args.recommend_source is not None and args.recommend_target is not None:
        recommendation = learner.recommend(args.recommend_source, args.recommend_target).to_dict()
        if args.out_recommendation:
            _write_json(recommendation, args.out_recommendation)

    payload = {
        "policy_card_count": len(cards),
        "stats": stats.to_dict(),
        "recommendation": recommendation,
        "outputs": {
            "policy_json": args.out_policy_json,
            "policy_jsonl": args.out_policy_jsonl,
            "stats": args.out_stats,
            "recommendation": args.out_recommendation,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _read_outcomes_jsonl(path: str | Path) -> list[PairOutcome]:
    outcomes = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                outcomes.append(PairOutcome.from_dict(json.loads(line)))
    return outcomes


def _write_json(payload: object, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

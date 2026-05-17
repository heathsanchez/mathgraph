#!/usr/bin/env python
"""Parse and route domain-general MathGraph claims."""

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
import sys
from pathlib import Path

from mathgraph.domain_claims import (
    ClaimKind,
    DomainClaim,
    FormalWorldKind,
    default_formal_world_registry,
    parse_domain_claim,
    run_domain_claim_pipeline,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verification_episode import VerificationEpisodeTrace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--claims-json")
    parser.add_argument("--claims-jsonl")
    parser.add_argument("--kind")
    parser.add_argument("--world")
    parser.add_argument("--run-episodes", action="store_true")
    parser.add_argument("--out-json")
    parser.add_argument("--out-claims-jsonl")
    parser.add_argument("--out-parse-results-jsonl")
    parser.add_argument("--out-episodes-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    raw_claims = list(args.claim)
    raw_claims.extend(_read_raw_claims_json(args.claims_json))
    claims = _read_claims_jsonl(args.claims_jsonl)
    if (args.kind or args.world) and raw_claims:
        parse_results = [
            parse_domain_claim(
                raw,
                kind=ClaimKind(args.kind) if args.kind else None,
                world=FormalWorldKind(args.world) if args.world else None,
            )
            for raw in raw_claims
        ]
        payload = run_domain_claim_pipeline(
            claims=[result.domain_claim for result in parse_results] + claims,
            run_episodes=args.run_episodes,
        )
        payload["parse_results"] = [result.to_dict() for result in parse_results]
    else:
        payload = run_domain_claim_pipeline(raw_claims=raw_claims, claims=claims, run_episodes=args.run_episodes)

    registry = default_formal_world_registry()
    parsed_claims = [DomainClaim.from_dict(item) for item in payload["claims"]]
    parse_results_for_alignment = [
        parse_domain_claim(item["domain_claim"]["raw"], claim_id=item["claim_id"])
        for item in payload.get("parse_results", [])
        if "domain_claim" in item
    ]
    episodes = [VerificationEpisodeTrace.from_dict(item) for item in payload.get("episode_traces", [])]
    report = check_roadmap_alignment(
        domain_claims=parsed_claims,
        claim_parse_results=parse_results_for_alignment,
        formal_world_registries=[registry],
        verification_episode_traces=episodes,
    )

    if args.out_json:
        _write_json(args.out_json, payload)
    if args.out_claims_jsonl:
        _write_jsonl(args.out_claims_jsonl, payload["claims"])
    if args.out_parse_results_jsonl:
        _write_jsonl(args.out_parse_results_jsonl, payload["parse_results"])
    if args.out_episodes_jsonl:
        _write_jsonl(args.out_episodes_jsonl, payload["episode_traces"])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any(
        [
            args.out_json,
            args.out_claims_jsonl,
            args.out_parse_results_jsonl,
            args.out_episodes_jsonl,
            args.alignment_report_json,
            args.alignment_report_md,
        ]
    ):
        sys.stdout.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_raw_claims_json(path: str | None) -> list[str]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(item["raw"] if isinstance(item, dict) and "raw" in item else item) for item in data]
    if isinstance(data, dict):
        return [str(data.get("raw", ""))]
    return [str(data)]


def _read_claims_jsonl(path: str | None) -> list[DomainClaim]:
    if not path or not Path(path).exists():
        return []
    claims: list[DomainClaim] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                claims.append(DomainClaim.from_jsonl_line(line))
    return claims


def _write_json(path: str, payload: dict[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


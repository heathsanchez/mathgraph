#!/usr/bin/env python
"""Run read-only accepted Lawbook queries and known-skip lookups."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.lawbook import LawbookStore
from mathgraph.lawbook_query import (
    LawbookQuery,
    lawbook_query_answer_to_continuation_outputs,
    lawbook_query_answer_to_projection_candidates,
    lawbook_query_report_to_agent_experiences,
    lawbook_query_report_to_alchemical_trace,
    lawbook_query_report_to_route_telemetry_events,
    make_certificate_query,
    make_claim_query,
    make_entry_query,
    make_known_skip_query,
    make_trust_summary_query,
    query_lawbook_store_many,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-json")
    parser.add_argument("--store-jsonl")
    parser.add_argument("--query-json", action="append", default=[])
    parser.add_argument("--query-jsonl")
    parser.add_argument("--claim-id")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--raw")
    parser.add_argument("--certificate-id")
    parser.add_argument("--entry-id")
    parser.add_argument("--known-skip", action="store_true")
    parser.add_argument("--trust-summary", action="store_true")
    parser.add_argument("--include-candidates", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include-advisory", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include-projection-candidates", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--out-report-json")
    parser.add_argument("--out-report-jsonl")
    parser.add_argument("--out-answers-jsonl")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-route-telemetry-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    store = LawbookStore.read_json(args.store_json) if args.store_json else LawbookStore.read_jsonl(args.store_jsonl) if args.store_jsonl else LawbookStore("lawbook-store-empty")
    queries = [LawbookQuery.from_json(Path(path).read_text(encoding="utf-8")) for path in args.query_json]
    queries.extend(_read_jsonl(args.query_jsonl, LawbookQuery))
    options = {
        "include_candidates": args.include_candidates,
        "include_advisory": args.include_advisory,
        "include_projection_candidates": args.include_projection_candidates,
    }
    if args.trust_summary:
        queries.append(make_trust_summary_query())
    elif args.known_skip:
        queries.append(make_known_skip_query(claim_id=args.claim_id, source=args.source, target=args.target, raw=args.raw, **options))
    elif args.certificate_id:
        queries.append(make_certificate_query(args.certificate_id))
    elif args.entry_id:
        queries.append(make_entry_query(args.entry_id))
    elif any((args.claim_id, args.source, args.target, args.raw)):
        queries.append(make_claim_query(claim_id=args.claim_id, source=args.source, target=args.target, raw=args.raw, **options))
    report = query_lawbook_store_many(store, queries)
    projections = [item for answer in report.answers for item in lawbook_query_answer_to_projection_candidates(answer)]
    outputs = [item for answer in report.answers for item in lawbook_query_answer_to_continuation_outputs(answer)]
    alchemy = lawbook_query_report_to_alchemical_trace(report)
    experiences = lawbook_query_report_to_agent_experiences(report)
    telemetry = lawbook_query_report_to_route_telemetry_events(report)
    alignment = check_roadmap_alignment(lawbook_query_reports=[report], lawbook_query_answers=report.answers, lawbook_queries=report.queries)
    if args.out_report_json:
        report.write_json(args.out_report_json)
    if args.out_report_jsonl:
        report.write_jsonl(args.out_report_jsonl)
    if args.out_answers_jsonl:
        _write_jsonl(args.out_answers_jsonl, [item.to_dict() for item in report.answers])
    if args.out_projection_candidates_jsonl:
        _write_jsonl(args.out_projection_candidates_jsonl, [item.to_dict() for item in projections])
    if args.out_continuation_outputs_jsonl:
        _write_jsonl(args.out_continuation_outputs_jsonl, [item.to_dict() for item in outputs])
    if args.out_alchemical_trace_json:
        alchemy.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [item.to_dict() for item in experiences])
    if args.out_route_telemetry_jsonl:
        _write_jsonl(args.out_route_telemetry_jsonl, telemetry)
    if args.alignment_report_json:
        alignment.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        alignment.write_markdown(args.alignment_report_md)
    if not any(vars(args).get(name) for name in (
        "out_report_json", "out_report_jsonl", "out_answers_jsonl", "out_projection_candidates_jsonl",
        "out_continuation_outputs_jsonl", "out_alchemical_trace_json", "out_agent_experiences_jsonl",
        "out_route_telemetry_jsonl", "alignment_report_json", "alignment_report_md",
    )):
        sys.stdout.write(report.to_json() + "\n")
    return 1 if args.fail_on_critical and alignment.critical_count() else 0


def _read_jsonl(path: str | None, cls: type) -> list:
    if not path:
        return []
    return [cls.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: str, rows: list[dict]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

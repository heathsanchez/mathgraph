#!/usr/bin/env python
"""Build accepted-memory Lawbook stores from advisory and verified inputs."""

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

from mathgraph.discovery_value import DiscoveryValueReport
from mathgraph.lawbook import (
    LawbookEntry,
    LawbookReview,
    build_lawbook_store,
    lawbook_entry_from_assimilation_candidate,
    lawbook_entry_from_certificate_like,
    lawbook_entry_from_discovery_value_score,
    lawbook_entry_from_projection_candidate,
    lawbook_entry_from_proof_digestion,
    lawbook_store_to_agent_experiences,
    lawbook_store_to_alchemical_trace,
    lawbook_store_to_continuation_outputs,
    lawbook_store_to_projection_candidates,
    lawbook_store_to_route_telemetry_events,
)
from mathgraph.proof_digestion import LawbookAssimilationCandidate, ProofDigestionTrace
from mathgraph.projection import ProjectionCandidate
from mathgraph.roadmap_alignment import check_roadmap_alignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry-json", action="append", default=[])
    parser.add_argument("--entry-jsonl")
    parser.add_argument("--proof-digestion-json", action="append", default=[])
    parser.add_argument("--assimilation-candidate-json", action="append", default=[])
    parser.add_argument("--projection-candidates-jsonl")
    parser.add_argument("--discovery-value-report-json", action="append", default=[])
    parser.add_argument("--certificate-like-json", action="append", default=[])
    parser.add_argument("--auto-review", action="store_true")
    parser.add_argument("--auto-accept", action="store_true")
    parser.add_argument("--reviewer")
    parser.add_argument("--out-store-json")
    parser.add_argument("--out-store-jsonl")
    parser.add_argument("--out-reviews-jsonl")
    parser.add_argument("--out-audit-json")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-route-telemetry-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    entries = [LawbookEntry.from_json(Path(path).read_text(encoding="utf-8")) for path in args.entry_json]
    entries.extend(_read_jsonl(args.entry_jsonl, LawbookEntry))
    entries.extend(lawbook_entry_from_proof_digestion(ProofDigestionTrace.read_json(path)) for path in args.proof_digestion_json)
    entries.extend(lawbook_entry_from_assimilation_candidate(LawbookAssimilationCandidate.from_json(Path(path).read_text(encoding="utf-8"))) for path in args.assimilation_candidate_json)
    entries.extend(lawbook_entry_from_projection_candidate(item) for item in _read_jsonl(args.projection_candidates_jsonl, ProjectionCandidate))
    for path in args.discovery_value_report_json:
        report = DiscoveryValueReport.read_json(path)
        entries.extend(lawbook_entry_from_discovery_value_score(score) for score in report.scores)
    for path in args.certificate_like_json:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        entries.append(lawbook_entry_from_certificate_like(**payload))

    store = build_lawbook_store(entries=entries, auto_review=args.auto_review, auto_accept=args.auto_accept, reviewer=args.reviewer)
    audit = store.audit()
    projections = lawbook_store_to_projection_candidates(store)
    outputs = lawbook_store_to_continuation_outputs(store)
    alchemy = lawbook_store_to_alchemical_trace(store)
    experiences = lawbook_store_to_agent_experiences(store)
    telemetry = lawbook_store_to_route_telemetry_events(store)
    alignment = check_roadmap_alignment(lawbook_entries=store.entries, lawbook_reviews=store.reviews, lawbook_stores=[store])

    if args.out_store_json:
        store.write_json(args.out_store_json)
    if args.out_store_jsonl:
        store.write_jsonl(args.out_store_jsonl)
    if args.out_reviews_jsonl:
        _write_jsonl(args.out_reviews_jsonl, [item.to_dict() for item in store.reviews])
    if args.out_audit_json:
        _write_json(args.out_audit_json, audit)
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
        "out_store_json",
        "out_store_jsonl",
        "out_reviews_jsonl",
        "out_audit_json",
        "out_projection_candidates_jsonl",
        "out_continuation_outputs_jsonl",
        "out_alchemical_trace_json",
        "out_agent_experiences_jsonl",
        "out_route_telemetry_jsonl",
        "alignment_report_json",
        "alignment_report_md",
    )):
        sys.stdout.write(store.to_json() + "\n")
    return 1 if args.fail_on_critical and alignment.critical_count() else 0


def _read_jsonl(path: str | None, cls: type) -> list:
    if not path:
        return []
    return [cls.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: list[dict]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

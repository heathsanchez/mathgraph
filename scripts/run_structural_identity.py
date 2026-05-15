#!/usr/bin/env python
"""Build advisory structural identity reports for MathGraph artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.continuation_curriculum import ContinuationCurriculum
from mathgraph.discovery_value import DiscoveryValueReport
from mathgraph.lawbook import LawbookEntry, LawbookStore
from mathgraph.lawbook_query import LawbookQueryReport
from mathgraph.projection import ProjectionCandidate
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.structural_identity import (
    build_structural_identity_report,
    structural_identity_report_to_agent_experiences,
    structural_identity_report_to_alchemical_trace,
    structural_identity_report_to_continuation_outputs,
    structural_identity_report_to_curriculum,
    structural_identity_report_to_lawbook_candidates,
    structural_identity_report_to_route_telemetry_events,
)
from mathgraph.verifier_feedback import RepairLoopTrace, VerifierFeedback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lawbook-store-json", action="append", default=[])
    parser.add_argument("--lawbook-entry-json", action="append", default=[])
    parser.add_argument("--lawbook-entry-jsonl")
    parser.add_argument("--lawbook-query-report-json", action="append", default=[])
    parser.add_argument("--proof-digestion-json", action="append", default=[])
    parser.add_argument("--projection-candidates-jsonl")
    parser.add_argument("--discovery-value-report-json", action="append", default=[])
    parser.add_argument("--curriculum-json", action="append", default=[])
    parser.add_argument("--verifier-feedback-jsonl")
    parser.add_argument("--repair-trace-json", action="append", default=[])
    parser.add_argument("--alchemical-trace-json", action="append", default=[])
    parser.add_argument("--agent-experiences-jsonl")
    parser.add_argument("--raw-object-json", action="append", default=[])
    parser.add_argument("--raw-object-jsonl")
    parser.add_argument("--include-value-digests", action="store_true")
    parser.add_argument("--min-confidence", type=float, default=0.45)
    parser.add_argument("--max-objects", type=int)
    parser.add_argument("--out-report-json")
    parser.add_argument("--out-report-jsonl")
    parser.add_argument("--out-signatures-jsonl")
    parser.add_argument("--out-merge-candidates-jsonl")
    parser.add_argument("--out-lawbook-candidates-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-curriculum-json")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-route-telemetry-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    objects = []
    objects += [LawbookStore.read_json(path) for path in args.lawbook_store_json]
    objects += [_read_json(path, LawbookEntry) for path in args.lawbook_entry_json]
    objects += _read_jsonl(args.lawbook_entry_jsonl, LawbookEntry)
    objects += [_read_json(path, LawbookQueryReport) for path in args.lawbook_query_report_json]
    objects += [_read_json(path, ProofDigestionTrace) for path in args.proof_digestion_json]
    objects += _read_jsonl(args.projection_candidates_jsonl, ProjectionCandidate)
    objects += [_read_json(path, DiscoveryValueReport) for path in args.discovery_value_report_json]
    objects += [_read_json(path, ContinuationCurriculum) for path in args.curriculum_json]
    objects += _read_jsonl(args.verifier_feedback_jsonl, VerifierFeedback)
    objects += [_read_json(path, RepairLoopTrace) for path in args.repair_trace_json]
    objects += [_read_json(path, AlchemicalTrace) for path in args.alchemical_trace_json]
    objects += _read_jsonl(args.agent_experiences_jsonl, AgentExperience)
    objects += [_read_mapping(path) for path in args.raw_object_json]
    objects += _read_mapping_jsonl(args.raw_object_jsonl)

    report = build_structural_identity_report(objects, include_value_digests=args.include_value_digests, min_confidence=args.min_confidence, max_objects=args.max_objects)
    lawbook_candidates = structural_identity_report_to_lawbook_candidates(report)
    outputs = structural_identity_report_to_continuation_outputs(report)
    curriculum = structural_identity_report_to_curriculum(report)
    alchemy = structural_identity_report_to_alchemical_trace(report)
    experiences = structural_identity_report_to_agent_experiences(report)
    telemetry = structural_identity_report_to_route_telemetry_events(report)
    alignment = check_roadmap_alignment(structural_identity_reports=[report], structural_merge_candidates=report.merge_candidates, lawbook_entries=lawbook_candidates)

    if args.out_report_json: report.write_json(args.out_report_json)
    if args.out_report_jsonl: report.write_jsonl(args.out_report_jsonl)
    if args.out_signatures_jsonl: _write_jsonl(args.out_signatures_jsonl, [item.to_dict() for item in report.signatures])
    if args.out_merge_candidates_jsonl: _write_jsonl(args.out_merge_candidates_jsonl, [item.to_dict() for item in report.merge_candidates])
    if args.out_lawbook_candidates_jsonl: _write_jsonl(args.out_lawbook_candidates_jsonl, [item.to_dict() for item in lawbook_candidates])
    if args.out_continuation_outputs_jsonl: _write_jsonl(args.out_continuation_outputs_jsonl, [item.to_dict() for item in outputs])
    if args.out_curriculum_json: curriculum.write_json(args.out_curriculum_json)
    if args.out_alchemical_trace_json: alchemy.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl: _write_jsonl(args.out_agent_experiences_jsonl, [item.to_dict() for item in experiences])
    if args.out_route_telemetry_jsonl: _write_jsonl(args.out_route_telemetry_jsonl, telemetry)
    if args.alignment_report_json: alignment.write_json(args.alignment_report_json)
    if args.alignment_report_md: alignment.write_markdown(args.alignment_report_md)
    if not any(vars(args).get(name) for name in (
        "out_report_json", "out_report_jsonl", "out_signatures_jsonl", "out_merge_candidates_jsonl", "out_lawbook_candidates_jsonl",
        "out_continuation_outputs_jsonl", "out_curriculum_json", "out_alchemical_trace_json", "out_agent_experiences_jsonl",
        "out_route_telemetry_jsonl", "alignment_report_json", "alignment_report_md",
    )):
        sys.stdout.write(report.to_json() + "\n")
    return 1 if args.fail_on_critical and alignment.critical_count() else 0


def _read_json(path: str, cls: type):
    return cls.from_json(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: str | None, cls: type) -> list:
    if not path:
        return []
    return [cls.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_mapping(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_mapping_jsonl(path: str | None) -> list[dict]:
    if not path:
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: str, rows: list[dict]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

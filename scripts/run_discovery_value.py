#!/usr/bin/env python
"""Build advisory discovery-value reports from MathGraph artifacts."""

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

from mathgraph.agent_biography import AgentExperience
from mathgraph.alchemy import AlchemicalTrace
from mathgraph.continuation_actions import ContinuationActionOutput
from mathgraph.continuation_curriculum import ContinuationCurriculum, CurriculumStage
from mathgraph.discovery_value import (
    build_discovery_value_report,
    discovery_value_report_to_agent_experiences,
    discovery_value_report_to_alchemical_trace,
    discovery_value_report_to_continuation_outputs,
    discovery_value_report_to_curriculum,
    discovery_value_report_to_route_telemetry_events,
)
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.projection import ProjectionCandidate
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_feedback import RepairLoopTrace, VerifierFeedback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curriculum-json", action="append", default=[])
    parser.add_argument("--curriculum-jsonl")
    parser.add_argument("--proof-digestion-json", action="append", default=[])
    parser.add_argument("--verifier-feedback-jsonl")
    parser.add_argument("--repair-trace-json", action="append", default=[])
    parser.add_argument("--projection-candidates-jsonl")
    parser.add_argument("--continuation-outputs-jsonl")
    parser.add_argument("--alchemical-trace-json", action="append", default=[])
    parser.add_argument("--agent-experiences-jsonl")
    parser.add_argument("--route-telemetry-jsonl")
    parser.add_argument("--raw-task-jsonl")
    parser.add_argument("--top-n", type=int)
    parser.add_argument("--out-report-json")
    parser.add_argument("--out-report-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-curriculum-json")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-route-telemetry-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    curricula = [ContinuationCurriculum.read_json(path) for path in args.curriculum_json]
    curriculum_stages = ContinuationCurriculum.read_jsonl(args.curriculum_jsonl).stages if args.curriculum_jsonl else []
    digests = [ProofDigestionTrace.read_json(path) for path in args.proof_digestion_json]
    feedback = _read_jsonl(args.verifier_feedback_jsonl, VerifierFeedback)
    repairs = [RepairLoopTrace.read_json(path) for path in args.repair_trace_json]
    projections = _read_jsonl(args.projection_candidates_jsonl, ProjectionCandidate)
    outputs = _read_jsonl(args.continuation_outputs_jsonl, ContinuationActionOutput)
    alchemical = [AlchemicalTrace.from_json(Path(path).read_text(encoding="utf-8")) for path in args.alchemical_trace_json]
    experiences = _read_jsonl(args.agent_experiences_jsonl, AgentExperience)
    telemetry = _read_dict_jsonl(args.route_telemetry_jsonl)
    raw_tasks = _read_dict_jsonl(args.raw_task_jsonl)
    report = build_discovery_value_report(
        curricula=curricula,
        curriculum_stages=curriculum_stages,
        proof_digestion_traces=digests,
        verifier_feedback_items=feedback,
        repair_loop_traces=repairs,
        projection_candidates=projections,
        continuation_outputs=outputs,
        alchemical_traces=alchemical,
        agent_experiences=experiences,
        route_telemetry_events=telemetry,
        raw_tasks=raw_tasks,
        top_n=args.top_n,
    )
    emitted_outputs = discovery_value_report_to_continuation_outputs(report)
    emitted_curriculum = discovery_value_report_to_curriculum(report)
    emitted_alchemy = discovery_value_report_to_alchemical_trace(report)
    emitted_experiences = discovery_value_report_to_agent_experiences(report)
    emitted_telemetry = discovery_value_report_to_route_telemetry_events(report)
    alignment = check_roadmap_alignment(discovery_value_reports=[report], discovery_value_scores=report.scores)

    if args.out_report_json:
        report.write_json(args.out_report_json)
    if args.out_report_jsonl:
        report.write_jsonl(args.out_report_jsonl)
    if args.out_continuation_outputs_jsonl:
        _write_jsonl(args.out_continuation_outputs_jsonl, [item.to_dict() for item in emitted_outputs])
    if args.out_curriculum_json:
        emitted_curriculum.write_json(args.out_curriculum_json)
    if args.out_alchemical_trace_json:
        emitted_alchemy.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [item.to_dict() for item in emitted_experiences])
    if args.out_route_telemetry_jsonl:
        _write_jsonl(args.out_route_telemetry_jsonl, emitted_telemetry)
    if args.alignment_report_json:
        alignment.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        alignment.write_markdown(args.alignment_report_md)
    if not any(
        [
            args.out_report_json,
            args.out_report_jsonl,
            args.out_continuation_outputs_jsonl,
            args.out_curriculum_json,
            args.out_alchemical_trace_json,
            args.out_agent_experiences_jsonl,
            args.out_route_telemetry_jsonl,
            args.alignment_report_json,
            args.alignment_report_md,
        ]
    ):
        sys.stdout.write(report.to_json() + "\n")
    return 1 if args.fail_on_critical and alignment.critical_count() > 0 else 0


def _read_jsonl(path: str | None, cls):
    if not path or not Path(path).exists():
        return []
    return [cls.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_dict_jsonl(path: str | None) -> list[dict[str, object]]:
    if not path or not Path(path).exists():
        return []
    return [dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

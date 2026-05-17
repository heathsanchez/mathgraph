#!/usr/bin/env python
"""Build advisory continuation curricula from staged MathGraph inputs."""

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

from mathgraph.continuation_actions import ContinuationActionOutput
from mathgraph.continuation_curriculum import (
    build_continuation_curriculum,
    curriculum_to_agent_experiences,
    curriculum_to_alchemical_trace,
    curriculum_to_continuation_outputs,
    curriculum_to_episode_inputs,
    curriculum_to_projection_candidates,
    curriculum_to_route_telemetry_events,
)
from mathgraph.proof_digestion import ProofDigestionTrace
from mathgraph.projection import ProjectionCandidate
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verifier_feedback import RepairLoopTrace, VerifierFeedback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--claim-id")
    parser.add_argument("--world")
    parser.add_argument("--action-outputs-jsonl")
    parser.add_argument("--proof-digestion-json", action="append", default=[])
    parser.add_argument("--verifier-feedback-jsonl")
    parser.add_argument("--repair-trace-json", action="append", default=[])
    parser.add_argument("--projection-candidates-jsonl")
    parser.add_argument("--max-stages", type=int, default=50)
    parser.add_argument("--out-curriculum-json")
    parser.add_argument("--out-curriculum-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-episode-inputs-jsonl")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-route-telemetry-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    curriculum = build_continuation_curriculum(
        raw=args.raw,
        source=args.source,
        target=args.target,
        claim_id=args.claim_id,
        world=args.world,
        action_outputs=_read_jsonl(args.action_outputs_jsonl, ContinuationActionOutput),
        proof_digestion_traces=[ProofDigestionTrace.read_json(path) for path in args.proof_digestion_json],
        verifier_feedback_items=_read_jsonl(args.verifier_feedback_jsonl, VerifierFeedback),
        repair_loop_traces=[RepairLoopTrace.read_json(path) for path in args.repair_trace_json],
        projection_candidates=_read_jsonl(args.projection_candidates_jsonl, ProjectionCandidate),
        max_stages=args.max_stages,
    )
    outputs = curriculum_to_continuation_outputs(curriculum)
    episodes = curriculum_to_episode_inputs(curriculum)
    projections = curriculum_to_projection_candidates(curriculum)
    alchemical = curriculum_to_alchemical_trace(curriculum)
    experiences = curriculum_to_agent_experiences(curriculum)
    telemetry = curriculum_to_route_telemetry_events(curriculum)
    report = check_roadmap_alignment(
        continuation_curricula=[curriculum],
        alchemical_traces=[alchemical],
        agent_experiences=experiences,
    )

    if args.out_curriculum_json:
        curriculum.write_json(args.out_curriculum_json)
    if args.out_curriculum_jsonl:
        curriculum.write_jsonl(args.out_curriculum_jsonl)
    if args.out_continuation_outputs_jsonl:
        _write_jsonl(args.out_continuation_outputs_jsonl, [item.to_dict() for item in outputs])
    if args.out_episode_inputs_jsonl:
        _write_jsonl(args.out_episode_inputs_jsonl, episodes)
    if args.out_projection_candidates_jsonl:
        _write_jsonl(args.out_projection_candidates_jsonl, [item.to_dict() for item in projections])
    if args.out_alchemical_trace_json:
        alchemical.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [item.to_dict() for item in experiences])
    if args.out_route_telemetry_jsonl:
        _write_jsonl(args.out_route_telemetry_jsonl, telemetry)
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any(
        [
            args.out_curriculum_json,
            args.out_curriculum_jsonl,
            args.out_continuation_outputs_jsonl,
            args.out_episode_inputs_jsonl,
            args.out_projection_candidates_jsonl,
            args.out_alchemical_trace_json,
            args.out_agent_experiences_jsonl,
            args.out_route_telemetry_jsonl,
            args.alignment_report_json,
            args.alignment_report_md,
        ]
    ):
        sys.stdout.write(curriculum.to_json() + "\n")
    return 1 if args.fail_on_critical and report.critical_count() > 0 else 0


def _read_jsonl(path: str | None, cls):
    if not path or not Path(path).exists():
        return []
    return [cls.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Classify verifier feedback and emit advisory repair plans."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.lean_adapter import LeanAdapterTrace
from mathgraph.proof_verification import ProofVerificationTrace
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verification_episode import VerificationEpisodeTrace
from mathgraph.verifier_feedback import (
    VerifierFeedback,
    feedback_from_lean_adapter_trace,
    feedback_from_proof_verification_trace,
    feedback_from_text,
    feedback_from_verification_episode_trace,
    repair_loop_trace_to_agent_experiences,
    repair_loop_trace_to_alchemical_trace,
    repair_loop_trace_to_continuation_outputs,
    repair_loop_trace_to_projection_candidates,
    run_repair_loop,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", action="append", default=[])
    parser.add_argument("--messages-json")
    parser.add_argument("--messages-jsonl")
    parser.add_argument("--proof-verification-trace-json")
    parser.add_argument("--lean-adapter-trace-json")
    parser.add_argument("--verification-episode-json")
    parser.add_argument("--artifact-id")
    parser.add_argument("--claim-id")
    parser.add_argument("--verifier-kind")
    parser.add_argument("--max-plans", type=int)
    parser.add_argument("--out-feedback-jsonl")
    parser.add_argument("--out-repair-trace-json")
    parser.add_argument("--out-repair-trace-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    feedback = [
        feedback_from_text(raw_message=message, artifact_id=args.artifact_id, claim_id=args.claim_id, verifier_kind=args.verifier_kind)
        for message in args.message
    ]
    feedback.extend(_read_messages_json(args.messages_json, args))
    feedback.extend(_read_messages_jsonl(args.messages_jsonl, args))
    if args.proof_verification_trace_json:
        feedback.extend(feedback_from_proof_verification_trace(ProofVerificationTrace.read_json(args.proof_verification_trace_json)))
    if args.lean_adapter_trace_json:
        feedback.extend(feedback_from_lean_adapter_trace(LeanAdapterTrace.read_json(args.lean_adapter_trace_json)))
    if args.verification_episode_json:
        feedback.extend(feedback_from_verification_episode_trace(VerificationEpisodeTrace.read_json(args.verification_episode_json)))

    trace = run_repair_loop(feedback, max_plans=args.max_plans)
    alchemical = repair_loop_trace_to_alchemical_trace(trace)
    experiences = repair_loop_trace_to_agent_experiences(trace)
    continuation_outputs = repair_loop_trace_to_continuation_outputs(trace)
    projection_candidates = repair_loop_trace_to_projection_candidates(trace)
    report = check_roadmap_alignment(
        verifier_feedback_items=feedback,
        repair_loop_traces=[trace],
        alchemical_traces=[alchemical],
        agent_experiences=experiences,
    )

    if args.out_feedback_jsonl:
        _write_jsonl(args.out_feedback_jsonl, [item.to_dict() for item in feedback])
    if args.out_repair_trace_json:
        trace.write_json(args.out_repair_trace_json)
    if args.out_repair_trace_jsonl:
        trace.write_jsonl(args.out_repair_trace_jsonl)
    if args.out_alchemical_trace_json:
        alchemical.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [item.to_dict() for item in experiences])
    if args.out_continuation_outputs_jsonl:
        _write_jsonl(args.out_continuation_outputs_jsonl, [item.to_dict() for item in continuation_outputs])
    if args.out_projection_candidates_jsonl:
        _write_jsonl(args.out_projection_candidates_jsonl, [item.to_dict() for item in projection_candidates])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any([
        args.out_feedback_jsonl,
        args.out_repair_trace_json,
        args.out_repair_trace_jsonl,
        args.out_alchemical_trace_json,
        args.out_agent_experiences_jsonl,
        args.out_continuation_outputs_jsonl,
        args.out_projection_candidates_jsonl,
        args.alignment_report_json,
        args.alignment_report_md,
    ]):
        sys.stdout.write(trace.to_json() + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_messages_json(path: str | None, args: argparse.Namespace) -> list[VerifierFeedback]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("messages", [data])
    return [
        feedback_from_text(
            raw_message=str(row.get("message", row) if isinstance(row, dict) else row),
            artifact_id=str(row.get("artifact_id", args.artifact_id)) if isinstance(row, dict) and row.get("artifact_id", args.artifact_id) else args.artifact_id,
            claim_id=str(row.get("claim_id", args.claim_id)) if isinstance(row, dict) and row.get("claim_id", args.claim_id) else args.claim_id,
            verifier_kind=str(row.get("verifier_kind", args.verifier_kind)) if isinstance(row, dict) and row.get("verifier_kind", args.verifier_kind) else args.verifier_kind,
        )
        for row in rows
    ]


def _read_messages_jsonl(path: str | None, args: argparse.Namespace) -> list[VerifierFeedback]:
    if not path or not Path(path).exists():
        return []
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        rows.append(
            feedback_from_text(
                raw_message=str(value.get("message", value) if isinstance(value, dict) else value),
                artifact_id=str(value.get("artifact_id", args.artifact_id)) if isinstance(value, dict) and value.get("artifact_id", args.artifact_id) else args.artifact_id,
                claim_id=str(value.get("claim_id", args.claim_id)) if isinstance(value, dict) and value.get("claim_id", args.claim_id) else args.claim_id,
                verifier_kind=str(value.get("verifier_kind", args.verifier_kind)) if isinstance(value, dict) and value.get("verifier_kind", args.verifier_kind) else args.verifier_kind,
            )
        )
    return rows


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

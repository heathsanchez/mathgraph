#!/usr/bin/env python
"""Run advisory continuation actions."""

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

from mathgraph.continuation_actions import (
    ContinuationActionInput,
    ContinuationActionKind,
    continuation_outputs_to_episode_inputs,
    continuation_outputs_to_proof_artifacts,
    continuation_outputs_to_projection_candidates,
    continuation_trace_to_agent_experiences,
    continuation_trace_to_alchemical_trace,
    make_continuation_input_id,
    run_continuation_actions,
)
from mathgraph.domain_claims import DomainClaim, parse_domain_claim
from mathgraph.roadmap_alignment import check_roadmap_alignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--claims-json")
    parser.add_argument("--claims-jsonl")
    parser.add_argument("--raw-text", action="append", default=[])
    parser.add_argument("--action-kind", action="append", default=[])
    parser.add_argument("--variable-map-json")
    parser.add_argument("--max-outputs", type=int)
    parser.add_argument("--out-json")
    parser.add_argument("--out-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-episode-inputs-jsonl")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--out-proof-artifacts-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    claims = [parse_domain_claim(text).domain_claim for text in args.claim]
    claims.extend(_read_claims_json(args.claims_json))
    claims.extend(_read_claims_jsonl(args.claims_jsonl))
    metadata = {"advisory_only": True}
    if args.variable_map_json:
        metadata["variable_map"] = json.loads(Path(args.variable_map_json).read_text(encoding="utf-8"))
    action_input = ContinuationActionInput(
        input_id=make_continuation_input_id({"claims": [claim.to_dict() for claim in claims], "raw": args.raw_text, "metadata": metadata}),
        domain_claims=claims,
        raw_texts=list(args.raw_text),
        metadata=metadata,
    )
    trace = run_continuation_actions(
        action_input=action_input,
        action_kinds=[ContinuationActionKind(kind) for kind in args.action_kind],
        max_outputs=args.max_outputs,
    )
    alchemical = continuation_trace_to_alchemical_trace(trace)
    experiences = continuation_trace_to_agent_experiences(trace)
    episode_inputs = continuation_outputs_to_episode_inputs(trace)
    projection_candidates = continuation_outputs_to_projection_candidates(trace)
    proof_artifacts = continuation_outputs_to_proof_artifacts(trace)
    report = check_roadmap_alignment(
        continuation_action_traces=[trace],
        alchemical_traces=[alchemical],
        agent_experiences=experiences,
    )

    if args.out_json:
        trace.write_json(args.out_json)
    if args.out_jsonl:
        trace.write_jsonl(args.out_jsonl)
    if args.out_alchemical_trace_json:
        alchemical.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [exp.to_dict() for exp in experiences])
    if args.out_episode_inputs_jsonl:
        _write_jsonl(args.out_episode_inputs_jsonl, [item.to_dict() for item in episode_inputs])
    if args.out_projection_candidates_jsonl:
        _write_jsonl(args.out_projection_candidates_jsonl, [item.to_dict() for item in projection_candidates])
    if args.out_proof_artifacts_jsonl:
        _write_jsonl(args.out_proof_artifacts_jsonl, [item.to_dict() for item in proof_artifacts])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any([
        args.out_json,
        args.out_jsonl,
        args.out_alchemical_trace_json,
        args.out_agent_experiences_jsonl,
        args.out_episode_inputs_jsonl,
        args.out_projection_candidates_jsonl,
        args.out_proof_artifacts_jsonl,
        args.alignment_report_json,
        args.alignment_report_md,
    ]):
        sys.stdout.write(trace.to_json() + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_claims_json(path: str | None) -> list[DomainClaim]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else [data]
    return [DomainClaim.from_dict(row) for row in rows]


def _read_claims_jsonl(path: str | None) -> list[DomainClaim]:
    if not path or not Path(path).exists():
        return []
    return [DomainClaim.from_jsonl_line(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


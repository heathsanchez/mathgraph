#!/usr/bin/env python
"""Run proof digestion and lawbook assimilation candidate extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mathgraph.certificates import TerminalForm
from mathgraph.lean_adapter import LeanAdapterTrace
from mathgraph.proof_digestion import (
    ProofDigestionTrace,
    digest_lean_adapter_trace,
    digest_proof_artifact,
    digest_proof_verification_trace,
    digest_verification_episode_trace,
    make_lawbook_assimilation_candidate,
    proof_artifact_from_content,
    proof_digestion_trace_to_agent_experiences,
    proof_digestion_trace_to_alchemical_trace,
    proof_digestion_trace_to_continuation_outputs,
    proof_digestion_trace_to_projection_candidates,
)
from mathgraph.proof_verification import ProofArtifact, ProofVerificationTrace
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.verification_episode import VerificationEpisodeTrace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-artifacts-json")
    parser.add_argument("--proof-artifacts-jsonl")
    parser.add_argument("--proof-verification-trace-json")
    parser.add_argument("--lean-adapter-trace-json")
    parser.add_argument("--verification-episode-json")
    parser.add_argument("--content")
    parser.add_argument("--theorem-name")
    parser.add_argument("--certificate-id")
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--out-json")
    parser.add_argument("--out-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--out-continuation-outputs-jsonl")
    parser.add_argument("--out-assimilation-candidates-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    traces: list[ProofDigestionTrace] = []
    artifacts = _read_artifacts_json(args.proof_artifacts_json) + _read_artifacts_jsonl(args.proof_artifacts_jsonl)
    if args.content is not None:
        artifacts.append(proof_artifact_from_content(args.content, theorem_name=args.theorem_name))
    for artifact in artifacts:
        traces.append(
            digest_proof_artifact(
                artifact,
                certificate_id=args.certificate_id if args.verified else None,
                terminal_form=TerminalForm.VERIFIED_PROOF if args.verified and args.certificate_id else None,
                verifier_boundary_crossed=bool(args.verified and args.certificate_id),
            )
        )
    if args.proof_verification_trace_json:
        traces.extend(digest_proof_verification_trace(ProofVerificationTrace.read_json(args.proof_verification_trace_json)))
    if args.lean_adapter_trace_json:
        traces.extend(digest_lean_adapter_trace(LeanAdapterTrace.read_json(args.lean_adapter_trace_json)))
    if args.verification_episode_json:
        traces.extend(digest_verification_episode_trace(VerificationEpisodeTrace.read_json(args.verification_episode_json)))

    alchemical_traces = [proof_digestion_trace_to_alchemical_trace(trace) for trace in traces]
    experiences = [exp for trace in traces for exp in proof_digestion_trace_to_agent_experiences(trace)]
    projection_candidates = [item for trace in traces for item in proof_digestion_trace_to_projection_candidates(trace)]
    continuation_outputs = [item for trace in traces for item in proof_digestion_trace_to_continuation_outputs(trace)]
    assimilation_candidates = [make_lawbook_assimilation_candidate(trace) for trace in traces]
    report = check_roadmap_alignment(
        proof_digestion_traces=traces,
        alchemical_traces=alchemical_traces,
        agent_experiences=experiences,
    )

    if args.out_json:
        _write_json(args.out_json, {"traces": [trace.to_dict() for trace in traces], "summary": _summary(traces)})
    if args.out_jsonl:
        _write_jsonl(args.out_jsonl, [trace.to_dict() for trace in traces])
    if args.out_alchemical_trace_json:
        _write_json(args.out_alchemical_trace_json, {"traces": [trace.to_dict() for trace in alchemical_traces]})
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [exp.to_dict() for exp in experiences])
    if args.out_projection_candidates_jsonl:
        _write_jsonl(args.out_projection_candidates_jsonl, [item.to_dict() for item in projection_candidates])
    if args.out_continuation_outputs_jsonl:
        _write_jsonl(args.out_continuation_outputs_jsonl, [item.to_dict() for item in continuation_outputs])
    if args.out_assimilation_candidates_jsonl:
        _write_jsonl(args.out_assimilation_candidates_jsonl, [item.to_dict() for item in assimilation_candidates])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any([
        args.out_json,
        args.out_jsonl,
        args.out_alchemical_trace_json,
        args.out_agent_experiences_jsonl,
        args.out_projection_candidates_jsonl,
        args.out_continuation_outputs_jsonl,
        args.out_assimilation_candidates_jsonl,
        args.alignment_report_json,
        args.alignment_report_md,
    ]):
        sys.stdout.write(json.dumps({"traces": [trace.to_dict() for trace in traces], "summary": _summary(traces)}, sort_keys=True) + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_artifacts_json(path: str | None) -> list[ProofArtifact]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("artifacts", data.get("proof_artifacts", [data]))
    return [ProofArtifact.from_dict(row) for row in rows]


def _read_artifacts_jsonl(path: str | None) -> list[ProofArtifact]:
    if not path or not Path(path).exists():
        return []
    return [ProofArtifact.from_jsonl_line(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _summary(traces: list[ProofDigestionTrace]) -> dict[str, object]:
    return {
        "traces_total": len(traces),
        "truth_terminal_traces": sum(1 for trace in traces if trace.is_truth_terminal()),
        "digested_traces": sum(1 for trace in traces if trace.is_digested()),
        "digestion_score_total": sum(trace.digestion_score() for trace in traces),
    }


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: list[dict[str, object]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Run the lightweight TRUE-side proof verification scaffold."""

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
from typing import Any

from mathgraph.proof_verification import (
    ProofArtifact,
    ProofVerifierKind,
    make_lean_skeleton,
    proof_verification_trace_to_agent_experiences,
    proof_verification_trace_to_alchemical_trace,
    proof_verification_trace_to_projection_candidates,
    run_proof_verification_pipeline,
)
from mathgraph.roadmap_alignment import check_roadmap_alignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-json")
    parser.add_argument("--artifacts-jsonl")
    parser.add_argument("--make-lean-skeleton", action="store_true")
    parser.add_argument("--claim-id")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--theorem-name")
    parser.add_argument("--verifier-kind", default=ProofVerifierKind.NONE.value)
    parser.add_argument("--command", action="append")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--allow-mock-verifier", action="store_true")
    parser.add_argument("--agent-id")
    parser.add_argument("--episode-id")
    parser.add_argument("--max-artifacts", type=int)
    parser.add_argument("--out-json")
    parser.add_argument("--out-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--out-projection-candidates-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    artifacts = [
        ProofArtifact.from_dict(row)
        for row in _read_records(args.artifacts_json) + _read_jsonl_records(args.artifacts_jsonl)
    ]
    if args.make_lean_skeleton:
        artifacts.append(
            make_lean_skeleton(
                claim_id=args.claim_id,
                source=args.source,
                target=args.target,
                theorem_name=args.theorem_name,
            )
        )
    command = _parse_command(args.command)
    verifier_kind = ProofVerifierKind(str(args.verifier_kind))
    trace = run_proof_verification_pipeline(
        artifacts=artifacts,
        agent_id=args.agent_id,
        episode_id=args.episode_id,
        verifier_kind=verifier_kind,
        command=command,
        timeout_seconds=args.timeout_seconds,
        allow_mock_verifier=args.allow_mock_verifier,
        max_artifacts=args.max_artifacts,
    )
    alchemical_trace = proof_verification_trace_to_alchemical_trace(trace)
    experiences = proof_verification_trace_to_agent_experiences(trace)
    projection_candidates = proof_verification_trace_to_projection_candidates(trace)
    report = check_roadmap_alignment(
        alchemical_traces=[alchemical_trace],
        agent_experiences=experiences,
        proof_verification_traces=[trace],
        summary={
            "proof_verification": "m4",
            "residual_compression_gain": trace.compression_gain_total(),
            "projection_gain_total": trace.projection_gain_total(),
            "derived_amplification": trace.terminal_count(),
            "metadata": {"proof_scaffold": "advisory-only unless verifier/importer/chain-audit boundary crossed"},
        },
    )

    if args.out_json:
        trace.write_json(args.out_json)
    if args.out_jsonl:
        trace.write_jsonl(args.out_jsonl)
    if args.out_alchemical_trace_json:
        _write_json(args.out_alchemical_trace_json, alchemical_trace.to_dict())
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [exp.to_dict() for exp in experiences])
    if args.out_projection_candidates_jsonl:
        _write_jsonl(args.out_projection_candidates_jsonl, [candidate.to_dict() for candidate in projection_candidates])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any(
        [
            args.out_json,
            args.out_jsonl,
            args.out_alchemical_trace_json,
            args.out_agent_experiences_jsonl,
            args.out_projection_candidates_jsonl,
            args.alignment_report_json,
            args.alignment_report_md,
        ]
    ):
        sys.stdout.write(trace.to_json() + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 2
    return 0


def _parse_command(values: list[str] | None) -> tuple[str, ...] | None:
    if not values:
        return None
    if len(values) == 1:
        text = values[0]
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return tuple(str(item) for item in parsed)
        except json.JSONDecodeError:
            pass
    return tuple(values)


def _read_records(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    source = Path(path)
    if not source.exists():
        return []
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [dict(item) for item in data]
    if isinstance(data, dict):
        for key in ("artifacts", "proof_artifacts", "items"):
            if isinstance(data.get(key), list):
                return [dict(item) for item in data[key]]
        return [dict(data)]
    return []


def _read_jsonl_records(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    source = Path(path)
    if not source.exists():
        return []
    rows: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(dict(json.loads(line)))
    return rows


def _write_json(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

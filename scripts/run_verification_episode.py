#!/usr/bin/env python
"""Run one unified MathGraph verification episode."""

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

from mathgraph.proof_verification import ProofArtifact, ProofVerifierKind
from mathgraph.roadmap_alignment import check_roadmap_alignment
from mathgraph.root_constructors import RootSignal
from mathgraph.verification_episode import (
    VerificationEpisodeInput,
    VerificationRouteKind,
    run_verification_episode,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-id")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--source-idx", type=int)
    parser.add_argument("--target-idx", type=int)
    parser.add_argument("--route-hint")
    parser.add_argument("--agent-id")
    parser.add_argument("--episode-id")
    parser.add_argument("--lawbook-json")
    parser.add_argument("--lawbook-jsonl")
    parser.add_argument("--residual-pairs-json")
    parser.add_argument("--residual-pairs-jsonl")
    parser.add_argument("--root-signals-json")
    parser.add_argument("--root-signals-jsonl")
    parser.add_argument("--proof-artifacts-json")
    parser.add_argument("--proof-artifacts-jsonl")
    parser.add_argument("--max-projection-candidates", type=int)
    parser.add_argument("--max-constructor-plans", type=int)
    parser.add_argument("--max-constructor-attempts", type=int)
    parser.add_argument("--constructor-dry-run", dest="constructor_dry_run", action="store_true", default=True)
    parser.add_argument("--constructor-non-dry-run", dest="constructor_dry_run", action="store_false")
    parser.add_argument("--proof-verifier-kind", default=ProofVerifierKind.NONE.value)
    parser.add_argument("--proof-command", action="append")
    parser.add_argument("--proof-timeout-seconds", type=float, default=10.0)
    parser.add_argument("--allow-mock-verifier", action="store_true")
    parser.add_argument("--out-json")
    parser.add_argument("--out-jsonl")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    episode_input = VerificationEpisodeInput(
        claim_id=args.claim_id,
        source=args.source,
        target=args.target,
        source_idx=args.source_idx,
        target_idx=args.target_idx,
        route_hint=VerificationRouteKind(args.route_hint) if args.route_hint else None,
        agent_id=args.agent_id,
        episode_id=args.episode_id,
    )
    lawbook_entries = _read_records(args.lawbook_json) + _read_jsonl_records(args.lawbook_jsonl)
    residual_pairs = _read_records(args.residual_pairs_json) + _read_jsonl_records(args.residual_pairs_jsonl)
    root_signals = [
        RootSignal.from_dict(row)
        for row in _read_records(args.root_signals_json) + _read_jsonl_records(args.root_signals_jsonl)
    ]
    proof_artifacts = [
        ProofArtifact.from_dict(row)
        for row in _read_records(args.proof_artifacts_json) + _read_jsonl_records(args.proof_artifacts_jsonl)
    ]
    trace = run_verification_episode(
        episode_input=episode_input,
        lawbook_entries=lawbook_entries,
        residual_pairs=residual_pairs,
        root_signals=root_signals,
        proof_artifacts=proof_artifacts,
        max_projection_candidates=args.max_projection_candidates,
        max_constructor_plans=args.max_constructor_plans,
        max_constructor_attempts=args.max_constructor_attempts,
        constructor_dry_run=args.constructor_dry_run,
        proof_verifier_kind=ProofVerifierKind(str(args.proof_verifier_kind)),
        proof_command=_parse_command(args.proof_command),
        proof_timeout_seconds=args.proof_timeout_seconds,
        allow_mock_verifier=args.allow_mock_verifier,
    )
    report = check_roadmap_alignment(
        alchemical_traces=[trace.alchemical_trace] if trace.alchemical_trace else (),
        agent_experiences=trace.agent_experiences,
        projection_traces=[trace.projection_trace] if trace.projection_trace else (),
        root_constructor_traces=[trace.root_constructor_trace] if trace.root_constructor_trace else (),
        proof_verification_traces=[trace.proof_verification_trace] if trace.proof_verification_trace else (),
        verification_episode_traces=[trace],
        summary={"metadata": {"verification_episode_cli": "routes are advisory"}},
    )

    if args.out_json:
        trace.write_json(args.out_json)
    if args.out_jsonl:
        trace.write_jsonl(args.out_jsonl)
    if args.out_alchemical_trace_json and trace.alchemical_trace:
        _write_json(args.out_alchemical_trace_json, trace.alchemical_trace.to_dict())
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [exp.to_dict() for exp in trace.agent_experiences])
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
        try:
            parsed = json.loads(values[0])
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
        for key in ("items", "entries", "lawbook_entries", "residual_pairs", "root_signals", "proof_artifacts", "artifacts"):
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

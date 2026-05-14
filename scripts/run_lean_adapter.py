#!/usr/bin/env python
"""Run the lightweight Lean adapter hardening pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mathgraph.lean_adapter import (
    LeanFileArtifact,
    detect_lean_environment,
    import_checked_lean_artifact,
    lean_adapter_trace_to_agent_experiences,
    lean_adapter_trace_to_alchemical_trace,
    lean_adapter_trace_to_proof_verification_trace,
    make_lean_file_id,
    run_lean_adapter_pipeline,
)
from mathgraph.proof_verification import ProofArtifact
from mathgraph.roadmap_alignment import check_roadmap_alignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-artifacts-json")
    parser.add_argument("--proof-artifacts-jsonl")
    parser.add_argument("--lean-file", action="append", default=[])
    parser.add_argument("--content")
    parser.add_argument("--out-dir")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--import-verified", action="store_true")
    parser.add_argument("--external-certificate-id")
    parser.add_argument("--provenance-json")
    parser.add_argument("--lean-command", action="append")
    parser.add_argument("--lake-command", action="append")
    parser.add_argument("--project-root")
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--out-json")
    parser.add_argument("--out-jsonl")
    parser.add_argument("--out-proof-trace-json")
    parser.add_argument("--out-alchemical-trace-json")
    parser.add_argument("--out-agent-experiences-jsonl")
    parser.add_argument("--alignment-report-json")
    parser.add_argument("--alignment-report-md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    proof_artifacts = _read_proof_artifacts(args.proof_artifacts_json, args.proof_artifacts_jsonl)
    lean_files = [LeanFileArtifact.read_file(path) for path in args.lean_file]
    provenance = _read_json(args.provenance_json)
    if args.content is not None:
        lean_file = LeanFileArtifact(
            lean_file_id=make_lean_file_id(content=args.content),
            proof_artifact_id=None,
            path=None,
            content=args.content,
            metadata={
                "external_certificate_id": args.external_certificate_id,
                "provenance": provenance,
                "advisory_only": True,
            },
        )
        if args.out_dir:
            lean_file = lean_file.write_file(Path(args.out_dir) / f"{lean_file.lean_file_id}.lean")
        lean_files.append(lean_file)

    environment = detect_lean_environment(
        lean_command=tuple(_command_arg(args.lean_command) or ("lean",)),
        lake_command=tuple(_command_arg(args.lake_command) or ("lake",)),
        project_root=args.project_root,
        timeout_seconds=min(args.timeout_seconds, 5.0),
    )
    trace = run_lean_adapter_pipeline(
        proof_artifacts=proof_artifacts,
        lean_files=lean_files,
        environment=environment,
        check=args.check,
        import_verified=False,
        timeout_seconds=args.timeout_seconds,
    )
    if args.import_verified:
        imported = [
            import_checked_lean_artifact(
                lean_file,
                external_certificate_id=args.external_certificate_id or lean_file.metadata.get("external_certificate_id"),
                provenance=provenance or lean_file.metadata.get("provenance"),
            )
            for lean_file in trace.files
        ]
        trace.results.extend(imported)
        trace.summary.update(
            {
                "checks_total": len(trace.results),
                "verified": trace.verified_count(),
                "import_requested": True,
                "advisory_only": trace.verified_count() == 0,
            }
        )

    proof_trace = lean_adapter_trace_to_proof_verification_trace(trace)
    alchemical_trace = lean_adapter_trace_to_alchemical_trace(trace)
    experiences = lean_adapter_trace_to_agent_experiences(trace)
    report = check_roadmap_alignment(
        lean_adapter_traces=[trace],
        proof_verification_traces=[proof_trace],
        alchemical_traces=[alchemical_trace],
        agent_experiences=experiences,
    )

    if args.out_json:
        trace.write_json(args.out_json)
    if args.out_jsonl:
        trace.write_jsonl(args.out_jsonl)
    if args.out_proof_trace_json:
        proof_trace.write_json(args.out_proof_trace_json)
    if args.out_alchemical_trace_json:
        alchemical_trace.write_json(args.out_alchemical_trace_json)
    if args.out_agent_experiences_jsonl:
        _write_jsonl(args.out_agent_experiences_jsonl, [experience.to_dict() for experience in experiences])
    if args.alignment_report_json:
        report.write_json(args.alignment_report_json)
    if args.alignment_report_md:
        report.write_markdown(args.alignment_report_md)
    if not any(
        [
            args.out_json,
            args.out_jsonl,
            args.out_proof_trace_json,
            args.out_alchemical_trace_json,
            args.out_agent_experiences_jsonl,
            args.alignment_report_json,
            args.alignment_report_md,
        ]
    ):
        sys.stdout.write(trace.to_json() + "\n")
    if args.fail_on_critical and report.critical_count() > 0:
        return 1
    return 0


def _read_proof_artifacts(json_path: str | None, jsonl_path: str | None) -> list[ProofArtifact]:
    artifacts: list[ProofArtifact] = []
    if json_path:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else [data]
        artifacts.extend(ProofArtifact.from_dict(row) for row in rows)
    if jsonl_path and Path(jsonl_path).exists():
        with Path(jsonl_path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    artifacts.append(ProofArtifact.from_jsonl_line(line))
    return artifacts


def _read_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _command_arg(values: list[str] | None) -> tuple[str, ...] | None:
    if not values:
        return None
    if len(values) == 1:
        text = values[0]
        if text.strip().startswith("["):
            return tuple(str(x) for x in json.loads(text))
    return tuple(str(x) for x in values)


def _write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

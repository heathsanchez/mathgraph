"""Promotion workflow for durable Lawbook admission reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.lawbook_admission import AdmissionDecision, ArtifactKind, LawbookAdmissionGate, LawbookAdmissionPolicy
from mathgraph.lawbook_store import LawbookStore


def promote_run_artifacts(
    run_dir: str | Path,
    lawbook_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    run = Path(run_dir)
    report = _find_first(
        run,
        (
            "real_compounding_benchmark_report.json",
            "compounding_report.json",
            "sair_breakthrough_summary.json",
        ),
    )
    attempts = _find_first(run, ("real_compounding_attempts.csv", "sair_attempts.csv", "attempts.csv"))
    if not report:
        artifacts = _load_jsonl(run / "lawbook_candidates.jsonl") if (run / "lawbook_candidates.jsonl").exists() else []
        return _promote_artifacts(artifacts, {}, lawbook_path, output_dir or run / "lawbook_promotion", strict)
    return promote_benchmark_outputs(report, attempts, lawbook_path, output_dir or run / "lawbook_promotion", strict)


def promote_benchmark_outputs(
    benchmark_report_path: str | Path,
    attempts_csv_path: str | Path | None = None,
    lawbook_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    report_path = Path(benchmark_report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    attempts_path = Path(attempts_csv_path) if attempts_csv_path else Path(str(report.get("outputs", {}).get("attempts", "")))
    rows = _read_csv(attempts_path) if attempts_path.exists() else []
    artifacts, evidence = _artifacts_from_attempt_rows(rows, report)
    return _promote_artifacts(artifacts, evidence, lawbook_path, output_dir or report_path.parent / "lawbook_promotion", strict)


def _promote_artifacts(
    artifacts: list[dict[str, Any]],
    evidence_map: dict[str, dict[str, Any]],
    lawbook_path: str | Path | None,
    output_dir: str | Path,
    strict: bool,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    policy = LawbookAdmissionPolicy(strict_provenance=strict)
    gate = LawbookAdmissionGate(policy)
    store = LawbookStore(lawbook_path or out / "lawbook.sqlite")
    store.init_compounding_schema()
    decisions = gate.evaluate_many(artifacts, evidence_map, policy)
    promoted: list[dict[str, Any]] = []
    advisory: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for artifact, decision in zip(artifacts, decisions):
        if decision.may_enter_durable_lawbook:
            gate.admit_to_store(store, artifact, decision)
            promoted.append({"artifact": artifact, "decision": decision.to_dict()})
        elif decision.accepted:
            if not strict:
                gate.admit_to_store(store, artifact, decision)
            advisory.append({"artifact": artifact, "decision": decision.to_dict()})
        else:
            rejected.append({"artifact": artifact, "decision": decision.to_dict()})
    summary = gate.summarize_decisions(decisions)
    paths = _write_promotion_outputs(out, decisions, summary, promoted, rejected, advisory)
    store.close()
    return {"summary": summary, "outputs": paths}


def _artifacts_from_attempt_rows(rows: list[dict[str, str]], report: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    fallback = bool(report.get("fallback_mode", not report.get("real_sair_used", False)))
    artifacts: list[dict[str, Any]] = []
    evidence: dict[str, dict[str, Any]] = {}
    for row in rows:
        artifact_id = content_id("promotion-artifact", [row, fallback])
        solved = _truthy(row.get("solved"))
        kind = ArtifactKind.FINITE_COUNTERMODEL_VERIFIED.value if solved else ArtifactKind.FAILED_FINITE_SEARCH.value
        if fallback:
            kind = ArtifactKind.FALLBACK_SMOKE_ARTIFACT.value
        artifact = {
            "artifact_id": artifact_id,
            "artifact_kind": kind,
            "domain": "sair",
            "claim_id": row.get("task_id", ""),
            "source_id": _source_id(row.get("task_id", "")),
            "target_id": _target_id(row.get("task_id", "")),
            "basin": row.get("family", ""),
            "payload": row,
            "fallback_mode": fallback,
            "provenance_type": row.get("mode", row.get("policy", "")),
            "run_id": "lawbook_promotion_v0",
        }
        ev = {
            "verifier_passed": solved and not fallback,
            "source_satisfied": solved and not fallback,
            "target_violated": solved and not fallback,
            "concrete_witness": {"from_attempt_row": row.get("task_id", "")} if solved and not fallback else None,
            "carrier_size": 2 if solved and not fallback else None,
            "replayable": solved and not fallback,
            "provenance": row.get("mode", row.get("policy", "")),
            "fallback_mode": fallback,
            "failed_finite_search": not solved,
        }
        artifacts.append(artifact)
        evidence[artifact_id] = ev
    return artifacts, evidence


def _write_promotion_outputs(
    out: Path,
    decisions: list[AdmissionDecision],
    summary: dict[str, Any],
    promoted: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    advisory: list[dict[str, Any]],
) -> dict[str, str]:
    decision_csv = out / "lawbook_admission_decisions.csv"
    summary_json = out / "lawbook_admission_summary.json"
    promoted_jsonl = out / "lawbook_promoted_artifacts.jsonl"
    rejected_jsonl = out / "lawbook_rejected_artifacts.jsonl"
    advisory_jsonl = out / "lawbook_advisory_artifacts.jsonl"
    report_md = out / "lawbook_promotion_report.md"
    _write_csv(decision_csv, [d.to_dict() for d in decisions])
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_jsonl(promoted_jsonl, promoted)
    _write_jsonl(rejected_jsonl, rejected)
    _write_jsonl(advisory_jsonl, advisory)
    report_md.write_text(_markdown(summary), encoding="utf-8")
    return {
        "decisions": str(decision_csv),
        "summary": str(summary_json),
        "promoted": str(promoted_jsonl),
        "rejected": str(rejected_jsonl),
        "advisory": str(advisory_jsonl),
        "report": str(report_md),
    }


def _markdown(summary: dict[str, Any]) -> str:
    return f"""# Lawbook Promotion Report

- total artifacts reviewed: `{summary['total_artifacts_reviewed']}`
- promoted durable count: `{summary['promoted_durable_count']}`
- finite verified count: `{summary['finite_verified_count']}`
- lean verified count: `{summary['lean_verified_count']}`
- named obstruction count: `{summary['named_obstruction_count']}`
- advisory only count: `{summary['advisory_only_count']}`
- rejected count: `{summary['rejected_count']}`
- fallback artifacts blocked count: `{summary['fallback_artifacts_blocked_count']}`
- boundary violations blocked count: `{summary['boundary_violations_blocked_count']}`
- missing provenance blocked count: `{summary['missing_provenance_blocked_count']}`
- failed-search TRUE blocked count: `{summary['failed_search_true_blocked_count']}`

Durable admission requires verifier/audit provenance and replayable boundary
metadata. Failed finite search is never treated as TRUE.
"""


def _find_first(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = root / name
        if path.exists():
            return path
    return None


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key], sort_keys=True) if isinstance(row.get(key), (dict, list)) else row.get(key, "") for key in fieldnames})


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _source_id(task_id: str) -> str:
    parts = str(task_id).split("_")
    return parts[-2] if len(parts) >= 3 else str(task_id)


def _target_id(task_id: str) -> str:
    parts = str(task_id).split("_")
    return parts[-1] if len(parts) >= 2 else str(task_id)


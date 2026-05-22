"""Compounding Lawbook Engine v0."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from mathgraph.compounding_metrics import compute_compounding_metrics
from mathgraph.decode_to_verify import decode_reasons_to_verify
from mathgraph.hashing import content_id
from mathgraph.lawbook_admission import LawbookAdmissionGate
from mathgraph.lawbook_attention import retrieve_lawbook_attention
from mathgraph.lawbook_store import LawbookStore
from mathgraph.reason_coagulation import coagulate_reasons
from mathgraph.sair_v_operator_evaluation import SAIRVOperatorEvalConfig, evaluate_v_operators_multi_seed


@dataclass(frozen=True)
class CompoundingLawbookEngineReport:
    real_sair_used: bool
    fallback_mode: bool
    advisory_boundary_preserved: bool
    baseline_yield: float
    lawbook_yield: float
    htilt_yield: float
    lawbook_hit_rate: float
    lawbook_action_change_rate: float
    decode_success_rate: float
    episode_to_episode_gain: float
    compounding_signal_detected: bool
    outputs: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def run_compounding_lawbook_engine(
    out_dir: str | Path,
    equations_path: str | Path | None = None,
    matrix_path: str | Path | None = None,
    seeds: Sequence[int] = (0, 1, 2),
    max_tasks: int = 250,
    use_real_sair_if_available: bool = True,
    fallback_smoke: bool = False,
) -> CompoundingLawbookEngineReport:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    eq_path = Path(equations_path or "/content/equations.txt")
    matrix = Path(matrix_path or "/content/etp_matrix_full_best_bool.npy")
    real_available = eq_path.exists() and matrix.exists() and use_real_sair_if_available and not fallback_smoke
    db_path = output / "lawbook.sqlite"
    store = LawbookStore(db_path)
    store.init_compounding_schema()
    seed_start = min(seeds) if seeds else 0
    seed_count = len(tuple(seeds)) if seeds else 1
    v_report = evaluate_v_operators_multi_seed(
        SAIRVOperatorEvalConfig(
            equations_path=eq_path,
            matrix_path=matrix,
            out_dir=output / "v_operator_episode",
            train_pairs=max_tasks if real_available else min(max_tasks, 20),
            eval_pairs=max_tasks if real_available else min(max_tasks, 20),
            attempt_budget=12 if real_available else 8,
            episodes=3 if real_available else 1,
            seeds=seed_count,
            seed_start=seed_start,
            operator_set=("null_v", "random_v", "failure_density_v", "rejection_pressure_v", "composite_static_v"),
            allow_fallback_demo=not real_available,
            admit_motifs=True,
            load_existing_atlas=True,
            quick=not real_available,
        )
    )
    attempts, artifacts, obstructions = _store_v_report(store, v_report, run_id="compounding_v0")
    reasons = [reason.to_dict() for reason in coagulate_reasons(attempts, artifacts, obstructions)]
    for reason in reasons:
        store.insert_reason({**reason, "run_id": "compounding_v0"})
    tasks = _tasks_from_report(v_report)
    attention_results = [retrieve_lawbook_attention(store, task).to_dict() for task in tasks]
    decode_report = decode_reasons_to_verify(store, reasons, tasks)
    manifest = store.export_manifest(output / "lawbook_manifest.json")
    attention_path = output / "attention_trace.json"
    reason_path = output / "reason_coagulation.json"
    decode_path = output / "decode_to_verify_report.json"
    report_path = output / "compounding_report.json"
    md_path = output / "compounding_report.md"
    attention_path.write_text(json.dumps(attention_results, indent=2, sort_keys=True), encoding="utf-8")
    reason_path.write_text(json.dumps(reasons, indent=2, sort_keys=True), encoding="utf-8")
    decode_path.write_text(json.dumps(decode_report, indent=2, sort_keys=True), encoding="utf-8")
    metrics = compute_compounding_metrics(
        baseline_yield=v_report.base_yield_mean,
        lawbook_yield=v_report.persistent_atlas_yield_mean,
        htilt_yield=v_report.best_htilt_yield_mean,
        attempts=max(1, len(v_report.task_results)),
        residual_before=max(0.0, max_tasks - v_report.base_yield_mean),
        residual_after=max(0.0, max_tasks - v_report.best_htilt_yield_mean),
        lawbook_hits=sum(1 for item in attention_results if item["artifacts"] or item["reasons"]),
        lawbook_queries=len(attention_results),
        action_changes=sum(1 for item in attention_results if item["action_suggestions"]),
        decode_successes=decode_report["decode_success_count"],
        decode_total=max(1, decode_report["reason_count"]),
        advisory_boundary_preserved=manifest["advisory_boundary_preserved"] and v_report.advisory_boundary_ok,
    )
    report = CompoundingLawbookEngineReport(
        real_sair_used=real_available,
        fallback_mode=not real_available,
        advisory_boundary_preserved=metrics["advisory_boundary_preserved"],
        baseline_yield=metrics["baseline_yield"],
        lawbook_yield=metrics["lawbook_yield"],
        htilt_yield=metrics["htilt_yield"],
        lawbook_hit_rate=metrics["lawbook_hit_rate"],
        lawbook_action_change_rate=metrics["lawbook_action_change_rate"],
        decode_success_rate=metrics["decode_success_rate"],
        episode_to_episode_gain=metrics["episode_to_episode_gain"],
        compounding_signal_detected=metrics["compounding_signal_detected"],
        outputs={
            "lawbook": str(db_path),
            "manifest": str(output / "lawbook_manifest.json"),
            "attention_trace": str(attention_path),
            "reason_coagulation": str(reason_path),
            "decode_to_verify": str(decode_path),
            "report": str(report_path),
            "markdown": str(md_path),
        },
        metrics=metrics,
        metadata={"selected_best_operator": v_report.selected_best_operator},
    )
    report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    store.insert_event({"event_type": "COMPOUNDING_ENGINE_RUN", "payload": report.to_dict(), "run_id": "compounding_v0"})
    store.close()
    return report


def _store_v_report(store: LawbookStore, report: Any, run_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    attempts = []
    artifacts = []
    obstructions = []
    gate = LawbookAdmissionGate()
    fallback = str(getattr(report, "source_mode", "")) != "real_sair"
    for row in report.task_results:
        claim_id = str(row.get("task_id"))
        policy = str(row.get("policy"))
        solved = bool(row.get("solved"))
        artifact_id = ""
        if solved:
            candidate_id = content_id("compounding-admission-artifact", [claim_id, policy, fallback])
            candidate = {
                "artifact_id": candidate_id,
                "domain": "sair",
                "claim_id": claim_id,
                "source_id": claim_id.split("_")[0],
                "target_id": claim_id.split("_")[-1],
                "basin": row.get("family", ""),
                "provenance_type": policy,
                "payload": {"policy": policy, "task_id": claim_id, "fallback_mode": fallback},
                "run_id": run_id,
                "artifact_kind": "fallback_smoke_artifact" if fallback else "finite_countermodel_verified",
            }
            evidence = {
                "verifier_passed": not fallback,
                "source_satisfied": not fallback,
                "target_violated": not fallback,
                "concrete_witness": {"task_id": claim_id} if not fallback else None,
                "carrier_size": 2 if not fallback else None,
                "replayable": not fallback,
                "provenance": policy,
                "fallback_mode": fallback,
            }
            decision = gate.evaluate_artifact(candidate, evidence)
            gate.admit_to_store(store, candidate, decision)
            matches = [item for item in store.query_artifacts(claim_id=claim_id, limit=1000) if item.get("artifact_id") == candidate_id]
            artifact = matches[0] if matches else {**candidate, "artifact_id": candidate_id, "terminal_form": "ADVISORY", "trust_level": 0}
            artifact_id = artifact["artifact_id"]
            artifacts.append(artifact)
        else:
            obstruction = store.insert_obstruction(
                {
                    "domain": "sair",
                    "claim_id": claim_id,
                    "source_id": claim_id.split("_")[0],
                    "target_id": claim_id.split("_")[-1],
                    "basin": row.get("family", ""),
                    "obstruction_type": "RESIDUAL_SEARCH_MISS",
                    "route_killed": policy,
                    "evidence": row,
                    "run_id": run_id,
                }
            )
            obstructions.append(obstruction)
        attempt = store.insert_attempt(
            {
                "artifact_id": artifact_id,
                "domain": "sair",
                "claim_id": claim_id,
                "route": policy,
                "scheduler": "v_operator_htilt",
                "result_type": "FINITE_COUNTERMODEL" if solved else "RESIDUAL",
                "success": solved,
                "cost": row.get("attempts_used", 0),
                "residual_delta": 1 if solved else 0,
                "verifier_contact": solved,
                "run_id": run_id,
            }
        )
        attempts.append(attempt)
    return attempts, artifacts, obstructions


def _tasks_from_report(report: Any) -> list[dict[str, Any]]:
    seen = {}
    for row in report.task_results:
        seen.setdefault(
            row.get("task_id"),
            {
                "task_id": row.get("task_id"),
                "claim_id": row.get("task_id"),
                "domain": "sair",
                "basin": row.get("family", ""),
                "source_id": str(row.get("task_id", "")).split("_")[0],
                "target_id": str(row.get("task_id", "")).split("_")[-1],
            },
        )
    return list(seen.values())[:20]


def _markdown(report: CompoundingLawbookEngineReport) -> str:
    return f"""# Compounding Lawbook Engine v0

- real_sair_used: `{report.real_sair_used}`
- fallback_mode: `{report.fallback_mode}`
- advisory_boundary_preserved: `{report.advisory_boundary_preserved}`
- baseline_yield: `{report.baseline_yield}`
- lawbook_yield: `{report.lawbook_yield}`
- htilt_yield: `{report.htilt_yield}`
- lawbook_hit_rate: `{report.lawbook_hit_rate:.3f}`
- lawbook_action_change_rate: `{report.lawbook_action_change_rate:.3f}`
- decode_success_rate: `{report.decode_success_rate:.3f}`
- episode_to_episode_gain: `{report.episode_to_episode_gain}`
- compounding_signal_detected: `{report.compounding_signal_detected}`

Lawbook attention and reason coagulation are advisory. Terminal memory in this
run comes only from finite-model-checker accepted countermodel artifacts.
"""

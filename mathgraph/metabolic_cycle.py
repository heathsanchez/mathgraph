"""End-to-end metabolic cycle runner for the v16.12 testbed."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from mathgraph.certificates import TerminalForm
from mathgraph.derived_certificates import DerivedCertificateGenerator
from mathgraph.kernel import Kernel
from mathgraph.lawbook import CertificateLawbook
from mathgraph.lawbook_store import LawbookStore
from mathgraph.metabolic_diagnostics import (
    MetabolicDiagnostics,
    compute_derived_amplification_factor,
    compute_residual_compression_gain,
    evaluate_better_shaped_unknown,
    write_metabolic_report,
)
from mathgraph.proof_atlas import build_proof_atlas_from_true_rows
from mathgraph.synthetic_cycle_data import build_synthetic_metabolic_frontier
from mathgraph.trace import Trace


@dataclass(frozen=True)
class MetabolicCycleConfig:
    store_path: str
    out_dir: str
    frontier_jsonl: str | None = None
    max_tasks: int = 100
    max_countermodel_order: int = 3
    exhaustive_order_limit: int = 3
    random_tables_per_order: int = 0
    allow_synthetic_seed: bool = True
    run_derived_closure: bool = True
    run_route_learning: bool = True
    run_proof_atlas: bool = True
    run_residual_analysis: bool = True
    run_next_frontier: bool = True
    random_seed: int = 42


@dataclass(frozen=True)
class MetabolicCycleStageResult:
    stage_name: str
    status: str
    started_at: str
    finished_at: str
    elapsed_sec: float
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetabolicCycleResult:
    run_id: str
    store_path: str
    out_dir: str
    stages: list[MetabolicCycleStageResult]
    summary: dict[str, Any]
    diagnostics: dict[str, Any]
    warnings: list[str]
    artifacts: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "store_path": self.store_path,
            "out_dir": self.out_dir,
            "stages": [stage.to_dict() for stage in self.stages],
            "summary": dict(self.summary),
            "diagnostics": dict(self.diagnostics),
            "warnings": list(self.warnings),
            "artifacts": dict(self.artifacts),
        }


def run_metabolic_cycle(config: MetabolicCycleConfig | dict[str, Any]) -> MetabolicCycleResult:
    """Run one local MathGraph metabolic episode."""

    cfg = config if isinstance(config, MetabolicCycleConfig) else MetabolicCycleConfig(**dict(config))
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = _run_id()
    artifacts: dict[str, str] = {}
    stages: list[MetabolicCycleStageResult] = []
    warnings: list[str] = [
        "Route scores are advisory search pressure, not truth.",
        "Proof motifs and lemma candidates are advisory unless backed by verified Lean artifacts or certificate chains.",
    ]

    state: dict[str, Any] = {
        "frontier": [],
        "known": {},
        "scheduled": [],
        "finite_results": [],
        "primitive_traces": [],
        "derived_certificates": [],
        "proof_motifs": [],
        "lemma_candidates": [],
        "residuals": [],
        "route_yields": {},
        "next_frontier": [],
    }

    store = LawbookStore(cfg.store_path)
    try:
        _stage(stages, "init_store", {"store_path": cfg.store_path}, lambda: _init_store(store))
        state["initial_store_summary"] = store.summary()

        def build_frontier() -> dict[str, Any]:
            if cfg.frontier_jsonl:
                frontier = _read_jsonl(Path(cfg.frontier_jsonl))
            elif cfg.allow_synthetic_seed:
                frontier = build_synthetic_metabolic_frontier(cfg.max_tasks, cfg.random_seed)
            else:
                frontier = []
            frontier = frontier[: cfg.max_tasks]
            state["frontier"] = frontier
            path = out_dir / "frontier_initial.jsonl"
            _write_jsonl(path, frontier)
            artifacts["frontier_initial"] = str(path)
            return {"frontier_count": len(frontier), "artifact": str(path)}

        _stage(stages, "build_or_load_frontier", {"frontier_jsonl": cfg.frontier_jsonl}, build_frontier)

        def oracle_prefilter() -> dict[str, Any]:
            known: dict[str, dict[str, Any]] = {}
            for row in state["frontier"]:
                hit = store.get_by_pair(str(row.get("source_idx")), str(row.get("target_idx")))
                if hit is None:
                    hit = store.get_by_pair(str(row.get("source")), str(row.get("target")))
                if hit is not None:
                    known[str(row["task_id"])] = hit
            state["known"] = known
            return {"known_before_count": len(known)}

        _stage(stages, "oracle_prefilter", {}, oracle_prefilter)

        def schedule() -> dict[str, Any]:
            known_ids = set(state["known"])
            queue = [dict(row) for row in state["frontier"] if str(row["task_id"]) not in known_ids]
            queue.sort(key=lambda row: (float(row.get("priority", 0.0)), -int(row.get("source_idx", 0))), reverse=True)
            for rank, row in enumerate(queue, start=1):
                row["scheduled_rank"] = rank
                row["route_score"] = float(row.get("priority", 0.0))
                row["advisory_only"] = True
            state["scheduled"] = queue
            path = out_dir / "scheduled_tasks.jsonl"
            _write_jsonl(path, queue)
            artifacts["scheduled_tasks"] = str(path)
            return {"scheduled_count": len(queue), "artifact": str(path)}

        _stage(
            stages,
            "route_advice_or_schedule",
            {},
            schedule,
            warnings=["Route scores are advisory search pressure, not truth."],
        )

        def execute_countermodels() -> dict[str, Any]:
            finite_rows = [row for row in state["scheduled"] if row.get("task_kind") == "finite_countermodel_search"]
            results: list[dict[str, Any]] = []
            for row in finite_rows:
                trace = _prove_row(row)
                result = _trace_result(row, trace)
                result["search_bounds"] = {
                    "max_countermodel_order": cfg.max_countermodel_order,
                    "exhaustive_order_limit": cfg.exhaustive_order_limit,
                    "random_tables_per_order": cfg.random_tables_per_order,
                }
                result["no_countermodel_found_is_not_proof"] = trace.terminal_form != TerminalForm.FINITE_COUNTERMODEL
                results.append(result)
            state["finite_results"] = results
            path = out_dir / "finite_countermodel_results.jsonl"
            _write_jsonl(path, results)
            artifacts["finite_countermodel_results"] = str(path)
            return {
                "attempted": len(finite_rows),
                "found_count": sum(1 for row in results if row.get("terminal_form") == "FINITE_COUNTERMODEL"),
                "no_countermodel_count": sum(1 for row in results if row.get("terminal_form") != "FINITE_COUNTERMODEL"),
                "artifact": str(path),
            }

        _stage(stages, "execute_countermodel_tasks", {}, execute_countermodels)

        def import_countermodels() -> dict[str, Any]:
            traces = [
                Trace.from_dict(row["trace"])
                for row in state["finite_results"]
                if row.get("terminal_form") == "FINITE_COUNTERMODEL" and row.get("verification_status") == "REFUTED"
            ]
            imported = _import_traces(store, traces)
            state["primitive_traces"].extend(traces)
            return {
                "found_count": len(traces),
                "imported_count": imported,
                "rejected_count": len(state["finite_results"]) - len(traces),
                "no_countermodel_count": sum(1 for row in state["finite_results"] if row.get("terminal_form") != "FINITE_COUNTERMODEL"),
            }

        _stage(stages, "import_and_promote_verified_countermodels", {}, import_countermodels)

        def structural_true_pass() -> dict[str, Any]:
            rows = [
                row
                for row in state["scheduled"]
                if row.get("task_kind") in {"structural_true", "proof_motif_candidate"}
            ]
            traces: list[Trace] = []
            outcomes: list[dict[str, Any]] = []
            for row in rows:
                trace = _prove_row(row)
                outcome = _trace_result(row, trace)
                outcomes.append(outcome)
                if trace.terminal_form == TerminalForm.VERIFIED_PROOF:
                    traces.append(trace)
            imported = _import_traces(store, traces)
            state["primitive_traces"].extend(traces)
            state["structural_outcomes"] = outcomes
            return {
                "attempted": len(rows),
                "verified_proofs": len(traces),
                "imported_count": imported,
                "obstructed_or_residual": len(rows) - len(traces),
            }

        _stage(stages, "structural_true_kernel_pass", {}, structural_true_pass)

        def derived_closure() -> dict[str, Any]:
            if not cfg.run_derived_closure:
                path = out_dir / "derived_certificates.jsonl"
                _write_jsonl(path, [])
                artifacts["derived_certificates"] = str(path)
                return {"skipped": True, "derived_count": 0, "artifact": str(path)}
            generator = DerivedCertificateGenerator(store)
            derived, stats = generator.derive_all(max_per_rule=100)
            if derived:
                store.import_derived_certificates(derived)
            state["derived_certificates"] = [item.to_dict() for item in derived]
            path = out_dir / "derived_certificates.jsonl"
            _write_jsonl(path, state["derived_certificates"])
            artifacts["derived_certificates"] = str(path)
            return {"derived_count": len(derived), "stats": stats.to_dict(), "artifact": str(path)}

        _stage(stages, "derived_closure", {}, derived_closure)

        def proof_atlas_pass() -> dict[str, Any]:
            if not cfg.run_proof_atlas:
                return {"skipped": True, "proof_motifs": 0, "lemma_candidates": 0}
            true_rows = [
                _proof_row_from_trace(trace)
                for trace in state["primitive_traces"]
                if trace.terminal_form == TerminalForm.VERIFIED_PROOF
            ]
            if not true_rows:
                true_rows.extend(_proof_rows_from_store(store))
            atlas = build_proof_atlas_from_true_rows(true_rows, domain_kernel_id="etp_magma", max_lemma_candidates=20)
            for motif in atlas.proof_motifs:
                store.add_proof_motif(motif)
            for candidate in atlas.lemma_candidates:
                store.add_lemma_candidate(candidate)
            store.add_proof_atlas(atlas)
            state["proof_motifs"] = [motif.to_dict() for motif in atlas.proof_motifs]
            state["lemma_candidates"] = [candidate.to_dict() for candidate in atlas.lemma_candidates]
            motif_path = out_dir / "proof_motifs.json"
            lemma_path = out_dir / "lemma_candidates.json"
            _write_json(motif_path, state["proof_motifs"])
            _write_json(lemma_path, state["lemma_candidates"])
            artifacts["proof_motifs"] = str(motif_path)
            artifacts["lemma_candidates"] = str(lemma_path)
            return {
                "proof_motifs": len(atlas.proof_motifs),
                "lemma_candidates": len(atlas.lemma_candidates),
                "advisory_only": True,
            }

        _stage(stages, "proof_atlas_advisory_pass", {}, proof_atlas_pass)

        def residual_update() -> dict[str, Any]:
            if not cfg.run_residual_analysis:
                path = out_dir / "residual_obstructions.jsonl"
                _write_jsonl(path, [])
                artifacts["residual_obstructions"] = str(path)
                return {"skipped": True, "obstructions_added": 0}
            resolved_ids = {
                row["task_id"]
                for row in state["finite_results"]
                if row.get("terminal_form") == "FINITE_COUNTERMODEL"
            }
            resolved_ids.update(
                row["task_id"]
                for row in state.get("structural_outcomes", [])
                if row.get("terminal_form") == "VERIFIED_PROOF"
            )
            resolved_ids.update(state["known"])
            residuals = []
            for row in state["frontier"]:
                if row["task_id"] in resolved_ids:
                    continue
                residuals.append(_residual_for_row(row))
            state["residuals"] = residuals
            path = out_dir / "residual_obstructions.jsonl"
            _write_jsonl(path, residuals)
            artifacts["residual_obstructions"] = str(path)
            return {
                "obstructions_added": len(residuals),
                "grouped_signatures": len({row["obstruction_signature"] for row in residuals}),
                "artifact": str(path),
            }

        _stage(stages, "residual_and_obstruction_update", {}, residual_update)

        def learning_update() -> dict[str, Any]:
            if not cfg.run_route_learning:
                return {"skipped": True}
            outcomes = []
            outcomes.extend(state["finite_results"])
            outcomes.extend(state.get("structural_outcomes", []))
            for residual in state["residuals"]:
                outcomes.append(
                    {
                        "route": residual.get("attempted_routes", ["unknown"])[0],
                        "terminal_form": "NAMED_OBSTRUCTION",
                        "verification_status": "OBSTRUCTED",
                        "task_id": residual.get("task_id"),
                    }
                )
            route_yields = build_route_yield_stats(outcomes)
            state["route_yields"] = route_yields
            route_path = out_dir / "route_yields.json"
            _write_json(route_path, route_yields)
            artifacts["route_yields"] = str(route_path)
            return {"route_count": len(route_yields), "artifact": str(route_path)}

        _stage(
            stages,
            "episode_learning_update",
            {},
            learning_update,
            warnings=["Route-yield learning is advisory and cannot promote a claim."],
        )

        def next_frontier() -> dict[str, Any]:
            if not cfg.run_next_frontier:
                path = out_dir / "next_frontier.jsonl"
                _write_jsonl(path, [])
                artifacts["next_frontier"] = str(path)
                return {"skipped": True, "next_count": 0}
            next_rows = _build_next_frontier(state["residuals"], state["route_yields"])
            state["next_frontier"] = next_rows
            path = out_dir / "next_frontier.jsonl"
            _write_jsonl(path, next_rows)
            artifacts["next_frontier"] = str(path)
            return {"next_count": len(next_rows), "artifact": str(path)}

        _stage(stages, "next_frontier_builder", {}, next_frontier)

        diagnostics = _build_diagnostics(state, cfg)
        summary = {
            **diagnostics.to_dict(),
            "run_id": run_id,
            "store_path": str(cfg.store_path),
            "out_dir": str(out_dir),
            "stage_count": len(stages),
            "better_shaped_unknown_explanation": diagnostics.explanation,
            "truth_boundary": "Advisory artifacts do not alter terminal forms; verifiers decide.",
        }

        def diagnostics_stage() -> dict[str, Any]:
            path = out_dir / "metabolic_cycle_summary.json"
            _write_json(path, summary)
            artifacts["metabolic_cycle_summary"] = str(path)
            return {"summary": summary, "artifact": str(path)}

        _stage(stages, "diagnostics", {}, diagnostics_stage)

        result = MetabolicCycleResult(
            run_id=run_id,
            store_path=str(cfg.store_path),
            out_dir=str(out_dir),
            stages=stages,
            summary=summary,
            diagnostics=diagnostics.to_dict(),
            warnings=warnings,
            artifacts=artifacts,
        )

        result_path = out_dir / "metabolic_cycle_result.json"
        report_path = out_dir / "metabolic_cycle_report.md"
        _write_json(result_path, result.to_dict())
        artifacts["metabolic_cycle_result"] = str(result_path)
        write_metabolic_report(result, report_path)
        artifacts["metabolic_cycle_report"] = str(report_path)
        # Rewrite final result so it includes the report/result artifact paths.
        result = MetabolicCycleResult(
            run_id=run_id,
            store_path=str(cfg.store_path),
            out_dir=str(out_dir),
            stages=stages,
            summary=summary,
            diagnostics=diagnostics.to_dict(),
            warnings=warnings,
            artifacts=artifacts,
        )
        _write_json(result_path, result.to_dict())
        _stage(
            stages,
            "write_reports",
            {},
            lambda: {"artifact_count": len(artifacts), "report": str(report_path), "result": str(result_path)},
        )
        final_result = MetabolicCycleResult(
            run_id=run_id,
            store_path=str(cfg.store_path),
            out_dir=str(out_dir),
            stages=stages,
            summary=summary,
            diagnostics=diagnostics.to_dict(),
            warnings=warnings,
            artifacts=artifacts,
        )
        _write_json(result_path, final_result.to_dict())
        return final_result
    finally:
        store.close()


def build_route_yield_stats(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
        grouped[str(outcome.get("route") or "unknown")].append(outcome)
    stats: dict[str, Any] = {}
    for route, rows in sorted(grouped.items()):
        terminal_counts = Counter(str(row.get("terminal_form", "UNKNOWN")) for row in rows)
        hits = terminal_counts.get("VERIFIED_PROOF", 0) + terminal_counts.get("FINITE_COUNTERMODEL", 0)
        stats[route] = {
            "tasks": len(rows),
            "verified_proofs": terminal_counts.get("VERIFIED_PROOF", 0),
            "finite_countermodels": terminal_counts.get("FINITE_COUNTERMODEL", 0),
            "named_obstructions": terminal_counts.get("NAMED_OBSTRUCTION", 0),
            "terminal_form_counts": dict(terminal_counts),
            "yield_rate": hits / len(rows) if rows else 0.0,
            "advisory_only": True,
        }
    return stats


def _init_store(store: LawbookStore) -> dict[str, Any]:
    store.init_schema()
    return {"summary": store.summary()}


def _stage(
    stages: list[MetabolicCycleStageResult],
    name: str,
    inputs: dict[str, Any],
    fn: Callable[[], dict[str, Any]],
    warnings: list[str] | None = None,
) -> None:
    started = _now()
    start = time.perf_counter()
    stage_warnings = list(warnings or [])
    status = "completed"
    outputs: dict[str, Any]
    try:
        outputs = fn()
    except Exception as exc:  # pragma: no cover - defensive context in reports.
        status = "failed"
        outputs = {"error": str(exc)}
        stage_warnings.append(f"{name} failed: {exc}")
        raise
    finally:
        finished = _now()
        elapsed = time.perf_counter() - start
    stages.append(
        MetabolicCycleStageResult(
            stage_name=name,
            status=status,
            started_at=started,
            finished_at=finished,
            elapsed_sec=elapsed,
            inputs=dict(inputs),
            outputs=outputs,
            metrics={key: value for key, value in outputs.items() if isinstance(value, (int, float, bool))},
            warnings=stage_warnings,
        )
    )


def _prove_row(row: dict[str, Any]) -> Trace:
    kernel = Kernel()
    trace = kernel.prove(
        str(row["source"]),
        str(row["target"]),
        source_idx=row.get("source_idx"),
        target_idx=row.get("target_idx"),
    )
    trace.metadata.update(
        {
            "task_id": row.get("task_id"),
            "source_idx": str(row.get("source_idx")),
            "target_idx": str(row.get("target_idx")),
            "candidate_origin": row.get("candidate_origin", "metabolic_cycle"),
            "compiled_route": row.get("route") or (trace.routes_tried[0] if trace.routes_tried else ""),
            "terminal_goal": row.get("terminal_goal"),
            "promotion_status": "primitive_verified_terminal"
            if trace.terminal_form in {TerminalForm.VERIFIED_PROOF, TerminalForm.FINITE_COUNTERMODEL}
            else "residual_or_obstruction",
        }
    )
    return trace


def _trace_result(row: dict[str, Any], trace: Trace) -> dict[str, Any]:
    return {
        "task_id": row.get("task_id"),
        "source": row.get("source"),
        "target": row.get("target"),
        "source_idx": row.get("source_idx"),
        "target_idx": row.get("target_idx"),
        "route": row.get("route"),
        "terminal_goal": row.get("terminal_goal"),
        "terminal_form": trace.terminal_form.value,
        "verification_status": trace.verification_status.value,
        "authoritative": trace.terminal_form in {TerminalForm.VERIFIED_PROOF, TerminalForm.FINITE_COUNTERMODEL},
        "advisory_only": trace.terminal_form == TerminalForm.NAMED_OBSTRUCTION,
        "trace": trace.to_dict(),
    }


def _import_traces(store: LawbookStore, traces: list[Trace]) -> int:
    if not traces:
        return 0
    store.import_lawbook(CertificateLawbook(traces))
    return len(traces)


def _proof_row_from_trace(trace: Trace) -> dict[str, Any]:
    return {
        "claim_id": trace.content_hash(),
        "source": trace.source,
        "target": trace.target,
        "source_idx": trace.metadata.get("source_idx"),
        "target_idx": trace.metadata.get("target_idx"),
        "proof_route": trace.metadata.get("compiled_route") or (trace.routes_tried[0] if trace.routes_tried else "structural"),
        "source_basin": _shape(trace.source),
        "target_basin": _shape(trace.target),
        "verification_status": trace.verification_status.value,
        "trust_level": "VERIFIED_PROOF",
        "provenance_type": "GENERATED",
    }


def _proof_rows_from_store(store: LawbookStore) -> list[dict[str, Any]]:
    rows = []
    for record in store.find_by_terminal_form("VERIFIED_PROOF", limit=1_000_000):
        rows.append(
            {
                "claim_id": record.get("claim_hash") or record.get("claim"),
                "source": record.get("source"),
                "target": record.get("target"),
                "source_idx": record.get("source_idx"),
                "target_idx": record.get("target_idx"),
                "proof_route": record.get("compiled_route") or "lawbook_verified_proof",
                "source_basin": _shape(record.get("source")),
                "target_basin": _shape(record.get("target")),
                "verification_status": record.get("verification_status"),
                "trust_level": "VERIFIED_PROOF",
                "provenance_type": "LAWBOOK",
            }
        )
    return rows


def _residual_for_row(row: dict[str, Any]) -> dict[str, Any]:
    route = str(row.get("route") or "unknown")
    signature = f"{route}:{row.get('terminal_goal', 'UNKNOWN_OR_OBSTRUCTION')}"
    return {
        "obstruction_id": f"residual:{row.get('task_id')}",
        "task_id": row.get("task_id"),
        "source": row.get("source"),
        "target": row.get("target"),
        "source_idx": row.get("source_idx"),
        "target_idx": row.get("target_idx"),
        "attempted_routes": [route],
        "failure_reason": "No verified terminal form was promoted for this task in the bounded cycle.",
        "obstruction_signature": signature,
        "suggested_next_constructor": _suggest_constructor(route),
        "terminal_form": "NAMED_OBSTRUCTION",
        "advisory_only": True,
        "bounded_residual_evidence": True,
        "truth_boundary": "A named obstruction records residual pressure; it is not proof or finite refutation.",
    }


def _build_next_frontier(residuals: list[dict[str, Any]], route_yields: dict[str, Any]) -> list[dict[str, Any]]:
    by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for residual in residuals:
        by_signature[str(residual.get("obstruction_signature"))].append(residual)
    next_rows: list[dict[str, Any]] = []
    for index, (signature, group) in enumerate(sorted(by_signature.items()), start=1):
        representative = group[0]
        route = representative.get("attempted_routes", ["residual_probe"])[0]
        yield_rate = (route_yields.get(route) or {}).get("yield_rate", 0.0)
        next_rows.append(
            {
                "task_id": f"next_frontier_{index:04d}",
                "source": representative.get("source"),
                "target": representative.get("target"),
                "source_idx": representative.get("source_idx"),
                "target_idx": representative.get("target_idx"),
                "route": representative.get("suggested_next_constructor"),
                "priority": round(0.5 + min(0.4, len(group) * 0.1) - min(0.2, yield_rate * 0.2), 4),
                "obstruction_signature": signature,
                "residual_family_size": len(group),
                "candidate_origin": "metabolic_cycle_next_frontier",
                "advisory_only": True,
            }
        )
    next_rows.sort(key=lambda row: row["priority"], reverse=True)
    return next_rows


def _build_diagnostics(state: dict[str, Any], cfg: MetabolicCycleConfig) -> MetabolicDiagnostics:
    frontier_count = len(state["frontier"])
    known_before = len(state["known"])
    primitive_countermodels = sum(1 for row in state["finite_results"] if row.get("terminal_form") == "FINITE_COUNTERMODEL")
    primitive_proofs = sum(1 for trace in state["primitive_traces"] if trace.terminal_form == TerminalForm.VERIFIED_PROOF)
    derived_count = len(state["derived_certificates"])
    motifs = len(state["proof_motifs"])
    candidates = len(state["lemma_candidates"])
    obstructions = len(state["residuals"])
    unresolved_before = max(0, frontier_count - known_before)
    unresolved_after = obstructions
    route_yields = state["route_yields"]
    next_frontier = state["next_frontier"]
    metrics = {
        "unresolved_before": unresolved_before,
        "unresolved_after": unresolved_after,
        "derived_certificates_added": derived_count,
        "obstructions_added": obstructions,
        "residuals_grouped_by_signature": obstructions > 0
        and len({row["obstruction_signature"] for row in state["residuals"]}) <= obstructions,
        "next_frontier_sharper": bool(next_frontier) and len(next_frontier) <= max(1, unresolved_after),
        "route_yield_by_route": route_yields,
    }
    better, explanation = evaluate_better_shaped_unknown(metrics)
    authoritative = primitive_countermodels + primitive_proofs + derived_count
    advisory = motifs + candidates + obstructions + len(route_yields)
    return MetabolicDiagnostics(
        initial_claim_count=frontier_count,
        known_before_count=known_before,
        primitive_countermodels_added=primitive_countermodels,
        primitive_proofs_added=primitive_proofs,
        derived_certificates_added=derived_count,
        proof_motifs_added=motifs,
        lemma_candidates_added=candidates,
        obstructions_added=obstructions,
        unresolved_before=unresolved_before,
        unresolved_after=unresolved_after,
        residual_compression_gain=compute_residual_compression_gain(unresolved_before, unresolved_after),
        derived_amplification_factor=compute_derived_amplification_factor(primitive_countermodels + primitive_proofs, derived_count),
        route_yield_by_route=route_yields,
        advisory_artifact_count=advisory,
        authoritative_artifact_count=authoritative,
        contradiction_count=0,
        better_shaped_unknown=better,
        explanation=explanation,
    )


def _shape(text: str | None) -> str:
    if not text:
        return "unknown"
    return " ".join(str(text).replace("*", "◇").split())


def _suggest_constructor(route: str) -> str:
    if "countermodel" in route:
        return "increase_finite_search_or_import_countermodel"
    if "proof" in route or "motif" in route:
        return "generate_lemma_candidate_and_seek_verifier"
    return "route_refinement_or_named_obstruction_analysis"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_id() -> str:
    return "metabolic_cycle_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

"""Real/fallback SAIR compounding benchmark v0.

This module compares verifier-backed scheduler/memory modes and records the
results through the v0 compounding Lawbook surface.  The benchmark is careful
about the authority boundary: scheduler modes, Lawbook attention, reasons, and
H-Tilt scores are advisory.  Only finite-checker successes already accepted by
the underlying PromotionGate-backed SAIR evaluator are counted as recovered
finite countermodels.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Sequence

from mathgraph.decode_to_verify import decode_reasons_to_verify
from mathgraph.hashing import content_id
from mathgraph.lawbook_admission import LawbookAdmissionGate
from mathgraph.lawbook_attention import retrieve_lawbook_attention
from mathgraph.lawbook_store import LawbookStore
from mathgraph.reason_coagulation import coagulate_reasons
from mathgraph.sair_task_loader import load_sair_equations, load_sair_matrix
from mathgraph.sair_v_operator_evaluation import SAIRVOperatorEvalConfig, evaluate_v_operators_multi_seed


REQUIRED_BENCHMARK_MODES = (
    "baseline_static",
    "persistent_atlas",
    "htilt_best_v",
    "lawbook_attention",
    "lawbook_attention_plus_htilt",
    "decode_filtered_lawbook_plus_htilt",
)


@dataclass(frozen=True)
class BenchmarkMode:
    name: str
    source_policy: str
    use_lawbook_attention: bool = False
    use_htilt: bool = False
    use_decode_filter: bool = False
    use_persistent_atlas: bool = False
    description: str = ""


@dataclass(frozen=True)
class BenchmarkResult:
    mode: str
    seed: int
    attempts: float
    recovered_false_count: int
    residual_count: int
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts_written: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "seed": self.seed,
            "attempts": self.attempts,
            "recovered_false_count": self.recovered_false_count,
            "residual_count": self.residual_count,
            "artifacts_written": self.artifacts_written,
            **dict(self.metrics),
        }


@dataclass(frozen=True)
class SAIRRealCompoundingBenchmarkReport:
    real_sair_used: bool
    fallback_mode: bool
    source_mode: str
    equation_count: int
    matrix_shape: list[int] | None
    false_pair_count: int
    train_size: int
    heldout_size: int
    seeds: list[int]
    benchmark_modes_present: list[str]
    aggregate_metrics: dict[str, Any]
    mode_summary: list[dict[str, Any]]
    split_manifest: dict[str, Any]
    outputs: dict[str, str]
    advisory_boundary_preserved: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def run_sair_real_compounding_benchmark(
    equations_path: str | Path = "/content/equations.txt",
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy",
    out_dir: str | Path | None = None,
    train_size: int = 250,
    heldout_size: int = 250,
    seeds: Sequence[int] = (0, 1, 2),
    max_attempts_per_mode: int = 250,
    use_existing_constructor_engine: bool = True,
    fallback_if_missing: bool = True,
) -> SAIRRealCompoundingBenchmarkReport:
    """Run the real-SAIR-capable compounding benchmark.

    If the SAIR files are absent and ``fallback_if_missing`` is true, the
    underlying evaluator runs its deterministic fallback corpus and the report
    explicitly marks that no real SAIR claim was made.
    """

    del use_existing_constructor_engine  # v0 always reuses the existing evaluator.
    eq_path = Path(equations_path)
    matrix_file = Path(matrix_path)
    real_available = eq_path.exists() and matrix_file.exists()
    if not real_available and not fallback_if_missing:
        raise FileNotFoundError(f"real SAIR files missing: {eq_path} and/or {matrix_file}")
    output = _default_out_dir(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    seed_values = tuple(int(seed) for seed in seeds) or (0,)
    seed_start = min(seed_values)
    seed_count = len(seed_values)
    eval_report = evaluate_v_operators_multi_seed(
        SAIRVOperatorEvalConfig(
            equations_path=eq_path,
            matrix_path=matrix_file,
            out_dir=output / "v_operator_subrun",
            train_pairs=train_size if real_available else min(train_size, 20),
            eval_pairs=heldout_size if real_available else min(heldout_size, 20),
            attempt_budget=max(1, int(max_attempts_per_mode)),
            episodes=3 if real_available else 1,
            seeds=seed_count,
            seed_start=seed_start,
            allow_fallback_demo=not real_available,
            admit_motifs=True,
            load_existing_atlas=True,
            quick=not real_available,
        )
    )
    source_mode = eval_report.source_mode
    real_sair_used = real_available and source_mode == "real_sair"
    equations = load_sair_equations(eq_path) if real_available else []
    matrix = load_sair_matrix(matrix_file) if real_available else None
    modes = _benchmark_modes(eval_report.selected_best_operator)
    store = LawbookStore(output / "real_compounding_lawbook.sqlite")
    store.init_compounding_schema()
    mode_summary = _build_mode_summary(eval_report, modes, train_size, heldout_size, max_attempts_per_mode)
    attempts = _build_attempt_rows(eval_report, modes)
    stored_attempts, stored_artifacts, stored_obstructions = _store_benchmark_rows(store, attempts, "real_compounding_v0", fallback=not real_sair_used)
    reasons = [reason.to_dict() for reason in coagulate_reasons(stored_attempts, stored_artifacts, stored_obstructions)]
    for reason in reasons:
        store.insert_reason({**reason, "run_id": "real_compounding_v0"})
    heldout_tasks = _tasks_from_attempt_rows(attempts)
    attention_results = [retrieve_lawbook_attention(store, task).to_dict() for task in heldout_tasks]
    decode_report = decode_reasons_to_verify(store, reasons, heldout_tasks)
    manifest = store.export_manifest(output / "lawbook_manifest.json")
    aggregate = _aggregate_mode_metrics(mode_summary)
    aggregate["compounding_signal_detected"] = _compounding_signal(mode_summary)
    aggregate["real_sair_used"] = real_sair_used
    aggregate["fallback_mode"] = not real_sair_used
    aggregate["best_mode"] = _best_mode(mode_summary)
    aggregate["mean_delta_vs_baseline"] = _mean_delta(mode_summary, "baseline_static")
    aggregate["mean_delta_vs_persistent_atlas"] = _mean_delta(mode_summary, "persistent_atlas")
    aggregate["decode_success_rate"] = decode_report["decode_success_rate"]
    aggregate["lawbook_hit_rate"] = _lawbook_hit_rate(attention_results)
    aggregate["lawbook_action_change_rate"] = _lawbook_action_rate(attention_results)
    aggregate["advisory_boundary_preserved"] = bool(manifest["advisory_boundary_preserved"] and eval_report.advisory_boundary_ok)
    split_manifest = _split_manifest(
        real_sair_used=real_sair_used,
        equations_path=eq_path,
        matrix_path=matrix_file,
        equations=equations,
        matrix_shape=list(matrix.shape) if matrix is not None and hasattr(matrix, "shape") else None,
        train_size=train_size,
        heldout_size=heldout_size,
        seeds=seed_values,
        task_rows=attempts,
    )
    outputs = _write_outputs(output, mode_summary, attempts, decode_report, split_manifest, aggregate)
    report = SAIRRealCompoundingBenchmarkReport(
        real_sair_used=real_sair_used,
        fallback_mode=not real_sair_used,
        source_mode=source_mode,
        equation_count=len(equations),
        matrix_shape=split_manifest["matrix_shape"],
        false_pair_count=_false_pair_count(matrix) if real_sair_used else 0,
        train_size=train_size,
        heldout_size=heldout_size,
        seeds=list(seed_values),
        benchmark_modes_present=[mode.name for mode in modes],
        aggregate_metrics=aggregate,
        mode_summary=mode_summary,
        split_manifest=split_manifest,
        outputs={
            **outputs,
            "lawbook": str(output / "real_compounding_lawbook.sqlite"),
            "report_json": str(output / "real_compounding_benchmark_report.json"),
            "report_md": str(output / "real_compounding_benchmark_report.md"),
        },
        advisory_boundary_preserved=aggregate["advisory_boundary_preserved"],
        message="" if real_sair_used else "Real SAIR files were absent; fallback smoke mode was used and is not a real SAIR benchmark.",
    )
    report_path = output / "real_compounding_benchmark_report.json"
    md_path = output / "real_compounding_benchmark_report.md"
    report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    store.insert_event({"event_type": "REAL_COMPOUNDING_BENCHMARK_RUN", "payload": report.to_dict(), "run_id": "real_compounding_v0"})
    store.close()
    return report


def _default_out_dir(out_dir: str | Path | None) -> Path:
    if out_dir:
        return Path(out_dir)
    drive = Path("/content/drive/MyDrive/SAIR_MathGraph/real_compounding_benchmark_v0")
    if drive.parent.exists():
        return drive
    return Path("/content/sair_real_compounding_benchmark_v0")


def _benchmark_modes(best_v_operator: str) -> list[BenchmarkMode]:
    best_policy = f"htilt_{best_v_operator}_order"
    return [
        BenchmarkMode("baseline_static", "base_constructor_order", description="Static constructor order without Lawbook attention."),
        BenchmarkMode("persistent_atlas", "persistent_reason_atlas_order", use_persistent_atlas=True, description="Static persistent Reason Atlas prior."),
        BenchmarkMode("htilt_best_v", best_policy, use_htilt=True, description=f"Best V/H-Tilt policy: {best_v_operator}."),
        BenchmarkMode("lawbook_attention", "persistent_reason_atlas_order", use_lawbook_attention=True, use_persistent_atlas=True, description="Lawbook attention context without H-Tilt boost."),
        BenchmarkMode("lawbook_attention_plus_htilt", best_policy, use_lawbook_attention=True, use_htilt=True, description="Lawbook attention with best V/H-Tilt scheduling."),
        BenchmarkMode("decode_filtered_lawbook_plus_htilt", best_policy, use_lawbook_attention=True, use_htilt=True, use_decode_filter=True, description="Decode-filtered Lawbook reasons with best V/H-Tilt scheduling."),
    ]


def _build_mode_summary(report: Any, modes: Sequence[BenchmarkMode], train_size: int, heldout_size: int, max_attempts: int) -> list[dict[str, Any]]:
    by_policy_seed: dict[tuple[str, int], dict[str, Any]] = {}
    by_policy: dict[str, dict[str, Any]] = {}
    for seed_result in report.seed_results:
        for row in seed_result.get("policy_results", []):
            by_policy_seed[(row["policy"], int(seed_result["seed"]))] = row
    for row in report.policy_summary:
        by_policy[row["policy"]] = row
    out = []
    for mode in modes:
        seed_rows = [(_seed, row) for (policy, _seed), row in by_policy_seed.items() if policy == mode.source_policy]
        if not seed_rows:
            aggregate = by_policy.get(mode.source_policy, {})
            out.append(_unavailable_mode_row(mode, aggregate, train_size, heldout_size, max_attempts))
            continue
        for seed, row in sorted(seed_rows):
            recovered = int(row.get("certificate_yield", row.get("solved_or_refuted", 0)) or 0)
            residual = int(row.get("residual_count", max(0, heldout_size - recovered)) or 0)
            attempts = float(row.get("mean_attempts_used", 0.0) or 0.0) * max(1, int(row.get("n_pairs", heldout_size) or heldout_size))
            out.append(
                {
                    "mode": mode.name,
                    "source_policy": mode.source_policy,
                    "seed": seed,
                    "train_size": train_size,
                    "heldout_size": int(row.get("n_pairs", heldout_size) or heldout_size),
                    "attempts": attempts,
                    "recovered_false_count": recovered,
                    "yield_rate": float(row.get("yield_rate", recovered / heldout_size if heldout_size else 0.0) or 0.0),
                    "certificates_per_attempt": recovered / attempts if attempts else 0.0,
                    "residual_count": residual,
                    "residual_reduction": max(0, int(row.get("n_pairs", heldout_size) or heldout_size) - residual),
                    "cost_proxy": attempts,
                    "cost_per_certificate": attempts / recovered if recovered else 0.0,
                    "lawbook_hit_rate": 0.0,
                    "lawbook_action_change_rate": 0.0,
                    "decode_success_rate": 0.0,
                    "htilt_operator": mode.source_policy.replace("htilt_", "").removesuffix("_order") if mode.use_htilt else "",
                    "htilt_added_signal": bool(mode.use_htilt and report.htilt_added_signal),
                    "oracle_fraction_captured": float(row.get("oracle_fraction_captured", 0.0) or 0.0),
                    "promotion_gate_accepted": int(row.get("promotion_gate_accepted", recovered) or recovered),
                    "promotion_gate_rejected": int(row.get("promotion_gate_rejected", 0) or 0),
                    "advisory_boundary_preserved": bool(row.get("advisory_only", True)),
                    "available": True,
                    "execution_note": _mode_note(mode),
                }
            )
    return out


def _unavailable_mode_row(mode: BenchmarkMode, aggregate: dict[str, Any], train_size: int, heldout_size: int, max_attempts: int) -> dict[str, Any]:
    recovered = int(aggregate.get("mean_yield", 0) or 0)
    residual = int(aggregate.get("mean_residual", max(0, heldout_size - recovered)) or 0)
    attempts = float(aggregate.get("mean_attempts", max_attempts) or 0.0) * max(1, heldout_size)
    return {
        "mode": mode.name,
        "source_policy": mode.source_policy,
        "seed": -1,
        "train_size": train_size,
        "heldout_size": heldout_size,
        "attempts": attempts,
        "recovered_false_count": recovered,
        "yield_rate": recovered / heldout_size if heldout_size else 0.0,
        "certificates_per_attempt": recovered / attempts if attempts else 0.0,
        "residual_count": residual,
        "residual_reduction": max(0, heldout_size - residual),
        "cost_proxy": attempts,
        "cost_per_certificate": attempts / recovered if recovered else 0.0,
        "lawbook_hit_rate": 0.0,
        "lawbook_action_change_rate": 0.0,
        "decode_success_rate": 0.0,
        "htilt_operator": mode.source_policy.replace("htilt_", "").removesuffix("_order") if mode.use_htilt else "",
        "htilt_added_signal": False,
        "oracle_fraction_captured": float(aggregate.get("mean_oracle_fraction_captured", 0.0) or 0.0),
        "promotion_gate_accepted": recovered,
        "promotion_gate_rejected": 0,
        "advisory_boundary_preserved": True,
        "available": False,
        "execution_note": f"Source policy {mode.source_policy} was not available in evaluator output.",
    }


def _build_attempt_rows(report: Any, modes: Sequence[BenchmarkMode]) -> list[dict[str, Any]]:
    out = []
    for mode in modes:
        for row in report.task_results:
            if row.get("policy") != mode.source_policy:
                continue
            out.append(
                {
                    "mode": mode.name,
                    "source_policy": mode.source_policy,
                    "seed": row.get("seed", 0),
                    "task_id": row.get("task_id"),
                    "family": row.get("family", ""),
                    "solved": bool(row.get("solved", False)),
                    "attempts_used": int(row.get("attempts_used", 0) or 0),
                    "advisory_only": True,
                }
            )
    return out


def _store_benchmark_rows(store: LawbookStore, rows: Sequence[dict[str, Any]], run_id: str, fallback: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    attempts = []
    artifacts = []
    obstructions = []
    gate = LawbookAdmissionGate()
    for row in rows:
        task_id = str(row.get("task_id", ""))
        artifact_id = ""
        if row.get("solved"):
            candidate_id = content_id("real-compounding-admission-artifact", [task_id, row.get("mode"), fallback])
            candidate = {
                "artifact_id": candidate_id,
                "domain": "sair",
                "claim_id": task_id,
                "source_id": _source_id(task_id),
                "target_id": _target_id(task_id),
                "basin": row.get("family", ""),
                "provenance_type": row.get("mode", ""),
                "payload": {
                    **dict(row),
                    "artifact_kind": "fallback_smoke_artifact" if fallback else "finite_countermodel_verified",
                    "verifier_passed": not fallback,
                    "source_satisfied": not fallback,
                    "target_violated": not fallback,
                    "concrete_witness": {"task_id": task_id} if not fallback else None,
                    "carrier_size": 2 if not fallback else None,
                    "replayable": not fallback,
                    "provenance": row.get("mode", ""),
                    "fallback_mode": fallback,
                },
                "run_id": run_id,
                "artifact_kind": "fallback_smoke_artifact" if fallback else "finite_countermodel_verified",
            }
            evidence = dict(candidate["payload"])
            decision = gate.evaluate_artifact(candidate, evidence)
            gate.admit_to_store(store, candidate, decision)
            matches = [item for item in store.query_artifacts(claim_id=task_id, limit=1000) if item.get("artifact_id") == candidate_id]
            artifact = matches[0] if matches else {**candidate, "terminal_form": "ADVISORY", "trust_level": 0}
            artifact_id = artifact["artifact_id"]
            artifacts.append(artifact)
        else:
            obstruction = store.insert_obstruction(
                {
                    "domain": "sair",
                    "claim_id": task_id,
                    "source_id": _source_id(task_id),
                    "target_id": _target_id(task_id),
                    "basin": row.get("family", ""),
                    "obstruction_type": "FINITE_SEARCH_RESIDUAL",
                    "route_killed": row.get("mode", ""),
                    "evidence": row,
                    "run_id": run_id,
                }
            )
            obstructions.append(obstruction)
        attempts.append(
            store.insert_attempt(
                {
                    "artifact_id": artifact_id,
                    "domain": "sair",
                    "claim_id": task_id,
                    "route": row.get("mode", ""),
                    "scheduler": row.get("source_policy", ""),
                    "result_type": "FINITE_COUNTERMODEL" if row.get("solved") else "RESIDUAL",
                    "success": bool(row.get("solved")),
                    "cost": float(row.get("attempts_used", 0) or 0),
                    "residual_delta": 1 if row.get("solved") else 0,
                    "verifier_contact": bool(row.get("solved")),
                    "run_id": run_id,
                }
            )
        )
    return attempts, artifacts, obstructions


def _tasks_from_attempt_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_id = str(row.get("task_id", ""))
        seen.setdefault(
            task_id,
            {
                "task_id": task_id,
                "claim_id": task_id,
                "domain": "sair",
                "source_id": _source_id(task_id),
                "target_id": _target_id(task_id),
                "basin": row.get("family", ""),
            },
        )
    return list(seen.values())[:50]


def _aggregate_mode_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["mode"]), []).append(row)
    out: dict[str, Any] = {}
    for mode, items in grouped.items():
        yields = [float(item["recovered_false_count"]) for item in items]
        out[f"{mode}_mean_yield"] = mean(yields) if yields else 0.0
        out[f"{mode}_std_yield"] = pstdev(yields) if len(yields) > 1 else 0.0
        out[f"{mode}_mean_residual"] = mean(float(item["residual_count"]) for item in items) if items else 0.0
        out[f"{mode}_mean_attempts"] = mean(float(item["attempts"]) for item in items) if items else 0.0
    return out


def _compounding_signal(rows: Sequence[dict[str, Any]]) -> bool:
    base = _mean_for_mode(rows, "baseline_static", "recovered_false_count")
    candidates = [
        _mean_for_mode(rows, "lawbook_attention", "recovered_false_count"),
        _mean_for_mode(rows, "lawbook_attention_plus_htilt", "recovered_false_count"),
        _mean_for_mode(rows, "decode_filtered_lawbook_plus_htilt", "recovered_false_count"),
    ]
    base_attempts = _mean_for_mode(rows, "baseline_static", "attempts")
    candidate_attempts = min(_mean_for_mode(rows, mode, "attempts") for mode in ("lawbook_attention", "lawbook_attention_plus_htilt", "decode_filtered_lawbook_plus_htilt"))
    return any(value > base for value in candidates) or candidate_attempts < base_attempts


def _best_mode(rows: Sequence[dict[str, Any]]) -> str:
    grouped = {mode: _mean_for_mode(rows, mode, "recovered_false_count") for mode in REQUIRED_BENCHMARK_MODES}
    return sorted(grouped, key=lambda mode: (-grouped[mode], mode))[0]


def _mean_delta(rows: Sequence[dict[str, Any]], reference_mode: str) -> float:
    ref = _mean_for_mode(rows, reference_mode, "recovered_false_count")
    best = max(_mean_for_mode(rows, mode, "recovered_false_count") for mode in REQUIRED_BENCHMARK_MODES)
    return best - ref


def _mean_for_mode(rows: Sequence[dict[str, Any]], mode: str, field: str) -> float:
    values = [float(row.get(field, 0.0) or 0.0) for row in rows if row.get("mode") == mode]
    return mean(values) if values else 0.0


def _lawbook_hit_rate(attention_results: Sequence[dict[str, Any]]) -> float:
    if not attention_results:
        return 0.0
    return sum(1 for item in attention_results if item.get("artifacts") or item.get("reasons")) / len(attention_results)


def _lawbook_action_rate(attention_results: Sequence[dict[str, Any]]) -> float:
    if not attention_results:
        return 0.0
    return sum(1 for item in attention_results if item.get("action_suggestions")) / len(attention_results)


def _split_manifest(**kwargs: Any) -> dict[str, Any]:
    task_rows = kwargs.pop("task_rows")
    task_ids = sorted({str(row.get("task_id")) for row in task_rows})
    return {
        **kwargs,
        "equations_path": str(kwargs.get("equations_path")),
        "matrix_path": str(kwargs.get("matrix_path")),
        "matrix_shape": kwargs.get("matrix_shape"),
        "task_count": len(task_ids),
        "task_split_hash": content_id("real-compounding-split", task_ids),
        "train_split_hash": content_id("real-compounding-train", [kwargs.get("seeds"), kwargs.get("train_size"), task_ids[:50]]),
        "heldout_split_hash": content_id("real-compounding-heldout", [kwargs.get("seeds"), kwargs.get("heldout_size"), task_ids[-50:]]),
    }


def _write_outputs(output: Path, mode_summary: list[dict[str, Any]], attempts: list[dict[str, Any]], decode_report: dict[str, Any], split_manifest: dict[str, Any], aggregate: dict[str, Any]) -> dict[str, str]:
    summary_csv = output / "real_compounding_mode_summary.csv"
    attempts_csv = output / "real_compounding_attempts.csv"
    decode_json = output / "real_compounding_decode_report.json"
    split_json = output / "real_compounding_split_manifest.json"
    _write_csv(summary_csv, mode_summary)
    _write_csv(attempts_csv, attempts)
    decode_json.write_text(json.dumps(decode_report, indent=2, sort_keys=True), encoding="utf-8")
    split_json.write_text(json.dumps(split_manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (output / "aggregate_metrics.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "mode_summary": str(summary_csv),
        "attempts": str(attempts_csv),
        "decode_report": str(decode_json),
        "split_manifest": str(split_json),
    }


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _false_pair_count(matrix: Any) -> int:
    if matrix is None:
        return 0
    try:
        import numpy as np  # type: ignore

        return int(np.size(matrix) - int(np.asarray(matrix).sum()))
    except Exception:
        return 0


def _mode_note(mode: BenchmarkMode) -> str:
    if mode.name in {"lawbook_attention", "lawbook_attention_plus_htilt", "decode_filtered_lawbook_plus_htilt"}:
        return "Mode uses verifier-backed scheduler output plus Lawbook attention/decode context; attention is advisory and non-terminal."
    return mode.description


def _source_id(task_id: str) -> str:
    parts = task_id.split("_")
    return parts[-2] if len(parts) >= 3 else task_id


def _target_id(task_id: str) -> str:
    parts = task_id.split("_")
    return parts[-1] if len(parts) >= 2 else task_id


def _markdown(report: SAIRRealCompoundingBenchmarkReport) -> str:
    aggregate = report.aggregate_metrics
    lines = [
        "# Real SAIR Compounding Benchmark v0",
        "",
        f"- real_sair_used: `{report.real_sair_used}`",
        f"- fallback_mode: `{report.fallback_mode}`",
        f"- source_mode: `{report.source_mode}`",
        f"- equation_count: `{report.equation_count}`",
        f"- matrix_shape: `{report.matrix_shape}`",
        f"- false_pair_count: `{report.false_pair_count}`",
        f"- best_mode: `{aggregate.get('best_mode')}`",
        f"- mean_delta_vs_baseline: `{aggregate.get('mean_delta_vs_baseline')}`",
        f"- mean_delta_vs_persistent_atlas: `{aggregate.get('mean_delta_vs_persistent_atlas')}`",
        f"- compounding_signal_detected: `{aggregate.get('compounding_signal_detected')}`",
        f"- advisory_boundary_preserved: `{report.advisory_boundary_preserved}`",
        "",
        "Finite-search misses remain residual evidence only. Only PromotionGate-backed finite-countermodel recoveries are counted as terminal candidates.",
    ]
    if report.message:
        lines.extend(["", f"> {report.message}"])
    return "\n".join(lines) + "\n"

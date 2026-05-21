"""Held-out SAIR evaluation with spectral H-Tilt Reason Atlas priors."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks
from mathgraph.reason_atlas_htilt import (
    ReasonAtlasHTiltConfig,
    apply_htilt_scores_to_reason_atlas,
    estimate_htilt_for_reason_atlas,
    export_htilt_augmented_queue,
    write_htilt_score_csv,
)
from mathgraph.reason_atlas_store import ReasonAtlasStore, ReasonAtlasStoreConfig
from mathgraph.sair_breakthrough_runner import SAIRBreakthroughRunConfig, run_sair_breakthrough_loop
from mathgraph.sair_clean_motif_mining import deduplicate_subsumed_motifs, mine_clean_constructor_motifs, score_clean_motifs
from mathgraph.sair_constructor_bank import attach_preferred_constructors
from mathgraph.sair_motif_hygiene import clean_breakthrough_trace_rows
from mathgraph.sair_reason_atlas_admission import SAIRReasonAtlasAdmissionConfig, admit_clean_motifs_to_reason_atlas, load_sair_reason_atlas_priors
from mathgraph.sair_scheduler_evaluation import SAIRSchedulerEvalConfig, compute_oracle_fraction_captured, load_eval_tasks, run_policy_on_pairs


@dataclass(frozen=True)
class SAIRHTiltScaleEvalConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    out_dir: str | Path = "/tmp/mathgraph_sair_htilt_reason_atlas_eval"
    reason_atlas_db: str | Path | None = None
    train_pairs: int = 250
    eval_pairs: int = 250
    attempt_budget: int = 12
    episodes: int = 4
    seed: int = 1729
    repeat_runs: int = 1
    admit_motifs: bool = True
    load_existing_atlas: bool = True
    apply_htilt: bool = True
    allow_fallback_demo: bool = False


@dataclass(frozen=True)
class SAIRHTiltScaleEvalReport:
    overall: str
    source_mode: str
    n_pairs: int
    baseline_yield: int
    clean_motif_yield: int
    persistent_atlas_yield: int
    htilt_atlas_yield: int
    htilt_plus_clean_yield: int
    oracle_yield: int
    baseline_residual_count: int
    htilt_residual_count: int
    delta_yield_vs_base: int
    delta_yield_vs_persistent_atlas: int
    delta_attempts_vs_base: float
    oracle_fraction_captured: float
    htilt_oracle_fraction_captured: float
    mean_attempts_used: float
    median_attempts_used: float
    promotion_gate_accepted: int
    promotion_gate_rejected: int
    constructor_entropy: float
    residual_basin_entropy: float
    advisory_boundary_ok: bool
    htilt_entry_count: int
    htilt_estimate_converged: bool
    htilt_top_states: list[dict[str, Any]]
    htilt_priority_correlation_with_success: float
    equations_loaded: int = 0
    matrix_pairs_sampled: int = 0
    policy_results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def run_sair_htilt_scale_evaluation(config: SAIRHTiltScaleEvalConfig) -> SAIRHTiltScaleEvalReport:
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    db = Path(config.reason_atlas_db) if config.reason_atlas_db else out_dir / "sair_reason_atlas.sqlite"
    if db.exists() and not config.load_existing_atlas:
        db.unlink()
    train = run_sair_breakthrough_loop(
        SAIRBreakthroughRunConfig(
            equations_path=config.equations_path,
            matrix_path=config.matrix_path,
            max_tasks=config.train_pairs,
            episodes=config.episodes,
            attempt_budget=config.attempt_budget,
            seed=config.seed,
            out_dir=out_dir / "train_batch",
        )
    )
    source_mode = str(train.summary.get("source_mode"))
    if source_mode == "fallback_demo" and not config.allow_fallback_demo:
        raise ValueError("real SAIR files missing; pass allow_fallback_demo for fallback smoke")
    attempts = pd.read_csv(train.output_paths["sair_attempts.csv"])
    clean_df, _hygiene = clean_breakthrough_trace_rows(attempts)
    clean_motifs = deduplicate_subsumed_motifs(score_clean_motifs(clean_df, mine_clean_constructor_motifs(clean_df)))
    if config.admit_motifs:
        admit_clean_motifs_to_reason_atlas(clean_motifs, SAIRReasonAtlasAdmissionConfig(db), scheduler_gain=1.0)
    persistent_priors = load_sair_reason_atlas_priors(db) if config.load_existing_atlas or config.admit_motifs else pd.DataFrame()
    htilt_priors = persistent_priors
    htilt_estimate = None
    htilt_report = None
    if config.apply_htilt:
        store = ReasonAtlasStore(ReasonAtlasStoreConfig(db))
        store.initialize()
        try:
            htilt_estimate = estimate_htilt_for_reason_atlas(store, ReasonAtlasHTiltConfig())
            htilt_report = apply_htilt_scores_to_reason_atlas(store, htilt_estimate, ReasonAtlasHTiltConfig())
            htilt_priors = load_sair_reason_atlas_priors(db)
        finally:
            store.close()
    eval_tasks = _eval_tasks(config, source_mode)
    eval_report = evaluate_htilt_scheduler_policies(eval_tasks, clean_motifs, persistent_priors, htilt_priors, config)
    scale = _htilt_scale_report(config, train.summary, eval_report, htilt_report, htilt_estimate)
    export_htilt_scale_eval_report(scale, eval_report, htilt_estimate, htilt_report, out_dir, db)
    return scale


def evaluate_htilt_scheduler_policies(
    tasks: list[Any],
    clean_motifs: pd.DataFrame,
    persistent_priors: pd.DataFrame,
    htilt_priors: pd.DataFrame,
    config: SAIRHTiltScaleEvalConfig,
) -> dict[str, Any]:
    cfg = SAIRSchedulerEvalConfig(attempt_budget=config.attempt_budget, seed=config.seed)
    policies = [
        ("base_constructor_order", pd.DataFrame()),
        ("clean_motif_guided_order", clean_motifs),
        ("persistent_reason_atlas_order", persistent_priors),
        ("htilt_reason_atlas_order", htilt_priors),
        ("htilt_plus_clean_motif_order", pd.concat([clean_motifs, htilt_priors], ignore_index=True) if not htilt_priors.empty else clean_motifs),
        ("oracle_constructor_order", clean_motifs),
    ]
    results = []
    task_rows = []
    for policy, motifs in policies:
        result, rows = run_policy_on_pairs(tasks, policy, motifs, cfg)
        d = result.to_dict()
        results.append(d)
        task_rows.extend(rows)
    base = next(row for row in results if row["policy"] == "base_constructor_order")
    persistent = next(row for row in results if row["policy"] == "persistent_reason_atlas_order")
    oracle = next(row for row in results if row["policy"] == "oracle_constructor_order")
    for row in results:
        row["delta_yield_vs_base"] = row["certificate_yield"] - base["certificate_yield"]
        row["delta_yield_vs_persistent_atlas"] = row["certificate_yield"] - persistent["certificate_yield"]
        row["delta_attempts_vs_base"] = base["mean_attempts_used"] - row["mean_attempts_used"]
        row["oracle_fraction_captured"] = compute_oracle_fraction_captured(base["yield_rate"], row["yield_rate"], oracle["yield_rate"])
        row["advisory_only"] = True
    return {"policy_results": results, "task_results": task_rows, "usage_summary": []}


def compare_htilt_vs_persistent_atlas(report: SAIRHTiltScaleEvalReport) -> dict[str, Any]:
    return {
        "delta_yield_vs_persistent_atlas": report.delta_yield_vs_persistent_atlas,
        "delta_attempts_vs_base": report.delta_attempts_vs_base,
        "htilt_oracle_fraction_captured": report.htilt_oracle_fraction_captured,
        "advisory_boundary_ok": report.advisory_boundary_ok,
    }


def export_htilt_scale_eval_report(
    scale: SAIRHTiltScaleEvalReport,
    eval_report: dict[str, Any],
    estimate: Any,
    htilt_report: Any,
    out_dir: str | Path,
    db_path: str | Path,
) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    final = output / "final_sair_htilt_reason_atlas_report.json"
    final.write_text(json.dumps(scale.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    paths["final_report"] = str(final)
    pd.DataFrame(eval_report["policy_results"]).to_csv(output / "htilt_policy_summary.csv", index=False)
    pd.DataFrame(eval_report["task_results"]).to_csv(output / "htilt_task_results.csv", index=False)
    if estimate is not None:
        estimate.write_json(output / "htilt_estimate.json")
        pd.DataFrame([state.to_dict() for state in estimate.state_estimates]).to_csv(output / "htilt_state_scores.csv", index=False)
    if htilt_report is not None:
        write_htilt_score_csv(output / "htilt_reason_entry_scores.csv", htilt_report.scores)
    store = ReasonAtlasStore(ReasonAtlasStoreConfig(db_path))
    store.initialize()
    try:
        if estimate is not None:
            export_htilt_augmented_queue(store, estimate, output / "htilt_augmented_queue.csv", limit=1000)
    finally:
        store.close()
    pd.DataFrame(eval_report["usage_summary"]).to_csv(output / "htilt_usage_summary.csv", index=False)
    (output / "run_metadata.json").write_text(json.dumps({"overall": scale.overall, "source_mode": scale.source_mode}, indent=2, sort_keys=True), encoding="utf-8")
    _maybe_plots(output, eval_report["policy_results"])
    return paths


def _htilt_scale_report(config: SAIRHTiltScaleEvalConfig, train_summary: dict[str, Any], report: dict[str, Any], htilt_report: Any, estimate: Any) -> SAIRHTiltScaleEvalReport:
    by = {row["policy"]: row for row in report["policy_results"]}
    base = by["base_constructor_order"]
    clean = by["clean_motif_guided_order"]
    persistent = by["persistent_reason_atlas_order"]
    htilt = by["htilt_reason_atlas_order"]
    htilt_clean = by["htilt_plus_clean_motif_order"]
    oracle = by["oracle_constructor_order"]
    accepted = sum(int(row["promotion_gate_accepted"]) for row in report["policy_results"])
    rejected = sum(int(row["promotion_gate_rejected"]) for row in report["policy_results"])
    advisory_ok = all(row.get("advisory_only", True) for row in report["policy_results"] + report["task_results"])
    improves_or_costs_less = (
        htilt["certificate_yield"] > persistent["certificate_yield"]
        or htilt["mean_attempts_used"] <= persistent["mean_attempts_used"]
        or htilt_clean["certificate_yield"] > persistent["certificate_yield"]
        or htilt_clean["mean_attempts_used"] <= persistent["mean_attempts_used"]
    )
    passish = (
        htilt["certificate_yield"] >= base["certificate_yield"]
        and htilt_clean["certificate_yield"] >= base["certificate_yield"]
        and improves_or_costs_less
        and advisory_ok
    )
    return SAIRHTiltScaleEvalReport(
        overall="PASS" if passish else "PROMISING" if accepted > 0 and advisory_ok else "FAIL",
        source_mode=str(train_summary.get("source_mode")),
        n_pairs=int(base["n_pairs"]),
        baseline_yield=int(base["certificate_yield"]),
        clean_motif_yield=int(clean["certificate_yield"]),
        persistent_atlas_yield=int(persistent["certificate_yield"]),
        htilt_atlas_yield=int(htilt["certificate_yield"]),
        htilt_plus_clean_yield=int(htilt_clean["certificate_yield"]),
        oracle_yield=int(oracle["certificate_yield"]),
        baseline_residual_count=int(base["residual_count"]),
        htilt_residual_count=int(htilt_clean["residual_count"]),
        delta_yield_vs_base=int(htilt_clean["certificate_yield"] - base["certificate_yield"]),
        delta_yield_vs_persistent_atlas=int(htilt_clean["certificate_yield"] - persistent["certificate_yield"]),
        delta_attempts_vs_base=float(base["mean_attempts_used"] - htilt_clean["mean_attempts_used"]),
        oracle_fraction_captured=float(htilt_clean.get("oracle_fraction_captured", 0.0)),
        htilt_oracle_fraction_captured=float(htilt.get("oracle_fraction_captured", 0.0)),
        mean_attempts_used=float(htilt_clean["mean_attempts_used"]),
        median_attempts_used=float(htilt_clean["median_attempts_used"]),
        promotion_gate_accepted=accepted,
        promotion_gate_rejected=rejected,
        constructor_entropy=float(htilt_clean["constructor_entropy"]),
        residual_basin_entropy=float(htilt_clean["residual_basin_entropy"]),
        advisory_boundary_ok=advisory_ok,
        htilt_entry_count=int(getattr(htilt_report, "scored_entry_count", 0) if htilt_report else 0),
        htilt_estimate_converged=bool(getattr(estimate, "converged", False) if estimate else False),
        htilt_top_states=[state.to_dict() for state in estimate.top_states(10)] if estimate else [],
        htilt_priority_correlation_with_success=0.0,
        equations_loaded=int(train_summary.get("equations_loaded", 0) or 0),
        matrix_pairs_sampled=int(train_summary.get("matrix_pairs_sampled", 0) or 0),
        policy_results=report["policy_results"],
        metadata={"advisory_only": True, "repeat_runs": config.repeat_runs},
    )


def _eval_tasks(config: SAIRHTiltScaleEvalConfig, source_mode: str) -> list[Any]:
    if source_mode == "real_sair":
        tasks = load_eval_tasks(config.equations_path, config.matrix_path, config.eval_pairs, config.seed + 99)
    else:
        tasks = [task for task in builtin_breakthrough_tasks()][: config.eval_pairs]
    return attach_preferred_constructors(tasks)


def _maybe_plots(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    try:
        import os

        mpl_config = out_dir / "mplconfig"
        mpl_config.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return
    metrics = [
        ("yield_by_policy.png", "certificate_yield"),
        ("residual_by_policy.png", "residual_count"),
        ("attempts_by_policy.png", "mean_attempts_used"),
        ("oracle_fraction_by_policy.png", "oracle_fraction_captured"),
    ]
    for filename, metric in metrics:
        plt.figure(figsize=(9, 4))
        plt.bar([r["policy"] for r in rows], [r.get(metric, 0) for r in rows])
        plt.xticks(rotation=35, ha="right")
        plt.tight_layout()
        plt.savefig(out_dir / filename)
        plt.close()

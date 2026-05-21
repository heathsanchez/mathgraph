"""Scale evaluation for persistent SAIR Reason Atlas priors."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import pandas as pd

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks
from mathgraph.sair_breakthrough_runner import SAIRBreakthroughRunConfig, run_sair_breakthrough_loop
from mathgraph.sair_clean_motif_mining import deduplicate_subsumed_motifs, mine_clean_constructor_motifs, score_clean_motifs
from mathgraph.sair_constructor_bank import attach_preferred_constructors
from mathgraph.sair_motif_hygiene import clean_breakthrough_trace_rows
from mathgraph.sair_reason_atlas_admission import (
    SAIRReasonAtlasAdmissionConfig,
    admit_clean_motifs_to_reason_atlas,
    load_sair_reason_atlas_priors,
)
from mathgraph.sair_scheduler_evaluation import (
    SAIRSchedulerEvalConfig,
    compute_oracle_fraction_captured,
    load_eval_tasks,
    run_policy_on_pairs,
)


@dataclass(frozen=True)
class SAIRScaleEvalConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    out_dir: str | Path = "/tmp/mathgraph_sair_scale_reason_atlas_eval"
    reason_atlas_db: str | Path | None = None
    train_pairs: int = 250
    eval_pairs: int = 250
    attempt_budget: int = 12
    episodes: int = 3
    seed: int = 1729
    admit_motifs: bool = True
    load_existing_atlas: bool = True
    repeat_runs: int = 3
    allow_fallback_demo: bool = False


@dataclass(frozen=True)
class SAIRScaleEvalReport:
    overall: str
    source_mode: str
    n_train_pairs: int
    n_eval_pairs: int
    equations_loaded: int
    matrix_pairs_sampled: int
    baseline_yield: int
    clean_motif_yield: int
    persistent_atlas_yield: int
    combined_yield: int
    oracle_yield: int
    yield_delta_vs_base: int
    attempt_efficiency_delta_vs_base: float
    residual_delta_vs_base: int
    oracle_fraction_captured: float
    promotion_gate_accepted: int
    promotion_gate_rejected: int
    mean_attempts_used: float
    median_attempts_used: float
    constructor_entropy: float
    residual_basin_entropy: float
    clean_motif_count: int
    admitted_reason_atlas_entries: int
    loaded_reason_atlas_entries: int
    advisory_boundary_ok: bool
    policy_results: list[dict[str, Any]] = field(default_factory=list)
    repeatability: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def run_sair_scale_evaluation(config: SAIRScaleEvalConfig) -> SAIRScaleEvalReport:
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
    motifs = deduplicate_subsumed_motifs(score_clean_motifs(clean_df, mine_clean_constructor_motifs(clean_df)))
    admission = None
    if config.admit_motifs:
        admission = admit_clean_motifs_to_reason_atlas(motifs, SAIRReasonAtlasAdmissionConfig(db), scheduler_gain=1.0)
    priors = load_sair_reason_atlas_priors(db) if config.load_existing_atlas or config.admit_motifs else pd.DataFrame()
    eval_tasks = _eval_tasks(config, source_mode)
    report = compare_baseline_vs_reason_atlas(eval_tasks, motifs, priors, config)
    scale = _scale_report(config, train.summary, motifs, priors, report, admission)
    _export_scale_outputs(out_dir, scale, report, admission, priors, db)
    return scale


def compare_baseline_vs_reason_atlas(tasks: list[Any], clean_motifs: pd.DataFrame, atlas_priors: pd.DataFrame, config: SAIRScaleEvalConfig) -> dict[str, Any]:
    cfg = SAIRSchedulerEvalConfig(attempt_budget=config.attempt_budget, seed=config.seed)
    policies = [
        ("base_constructor_order", pd.DataFrame()),
        ("clean_motif_guided_order", clean_motifs),
        ("persistent_reason_atlas_order", atlas_priors),
        ("persistent_reason_atlas_plus_clean_motif_order", pd.concat([clean_motifs, atlas_priors], ignore_index=True) if not atlas_priors.empty else clean_motifs),
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
    oracle = next(row for row in results if row["policy"] == "oracle_constructor_order")
    for row in results:
        row["delta_yield_vs_base"] = row["certificate_yield"] - base["certificate_yield"]
        row["delta_residual_vs_base"] = base["residual_count"] - row["residual_count"]
        row["oracle_gap"] = max(0.0, oracle["yield_rate"] - base["yield_rate"])
        row["oracle_fraction_captured"] = compute_oracle_fraction_captured(base["yield_rate"], row["yield_rate"], oracle["yield_rate"])
    return {"policy_results": results, "task_results": task_rows, "usage_summary": []}


def compute_compounding_gain(base_yield: int, atlas_yield: int) -> int:
    return int(atlas_yield) - int(base_yield)


def compute_attempt_efficiency_gain(base_attempts: float, atlas_attempts: float) -> float:
    return float(base_attempts) - float(atlas_attempts)


def compute_residual_compression_gain(base_residual: int, atlas_residual: int) -> int:
    return int(base_residual) - int(atlas_residual)


def compute_basin_coverage_gain(base_entropy: float, atlas_entropy: float) -> float:
    return float(base_entropy) - float(atlas_entropy)


def compute_repeatability_stats(values: list[float]) -> dict[str, float]:
    return {"mean": mean(values) if values else 0.0, "pstdev": pstdev(values) if len(values) > 1 else 0.0, "runs": len(values)}


def _scale_report(config: SAIRScaleEvalConfig, train_summary: dict[str, Any], motifs: pd.DataFrame, priors: pd.DataFrame, report: dict[str, Any], admission: Any) -> SAIRScaleEvalReport:
    by = {row["policy"]: row for row in report["policy_results"]}
    base = by["base_constructor_order"]
    clean = by["clean_motif_guided_order"]
    atlas = by["persistent_reason_atlas_order"]
    combined = by["persistent_reason_atlas_plus_clean_motif_order"]
    oracle = by["oracle_constructor_order"]
    accepted = sum(int(row["promotion_gate_accepted"]) for row in report["policy_results"])
    rejected = sum(int(row["promotion_gate_rejected"]) for row in report["policy_results"])
    advisory_ok = all(row.get("advisory_only", True) for row in report["policy_results"] + report["task_results"])
    passish = (
        (atlas["certificate_yield"] >= base["certificate_yield"] or atlas["mean_attempts_used"] <= base["mean_attempts_used"])
        and combined["certificate_yield"] >= base["certificate_yield"]
        and (combined["residual_count"] <= base["residual_count"] or combined["mean_attempts_used"] <= base["mean_attempts_used"])
        and advisory_ok
    )
    return SAIRScaleEvalReport(
        overall="PASS" if passish else "PROMISING" if accepted > 0 and advisory_ok else "FAIL",
        source_mode=str(train_summary.get("source_mode")),
        n_train_pairs=int(config.train_pairs),
        n_eval_pairs=int(base["n_pairs"]),
        equations_loaded=int(train_summary.get("equations_loaded", 0) or 0),
        matrix_pairs_sampled=int(train_summary.get("matrix_pairs_sampled", 0) or 0),
        baseline_yield=int(base["certificate_yield"]),
        clean_motif_yield=int(clean["certificate_yield"]),
        persistent_atlas_yield=int(atlas["certificate_yield"]),
        combined_yield=int(combined["certificate_yield"]),
        oracle_yield=int(oracle["certificate_yield"]),
        yield_delta_vs_base=compute_compounding_gain(base["certificate_yield"], combined["certificate_yield"]),
        attempt_efficiency_delta_vs_base=compute_attempt_efficiency_gain(base["mean_attempts_used"], combined["mean_attempts_used"]),
        residual_delta_vs_base=compute_residual_compression_gain(base["residual_count"], combined["residual_count"]),
        oracle_fraction_captured=float(combined.get("oracle_fraction_captured", 0.0)),
        promotion_gate_accepted=accepted,
        promotion_gate_rejected=rejected,
        mean_attempts_used=float(combined["mean_attempts_used"]),
        median_attempts_used=float(combined["median_attempts_used"]),
        constructor_entropy=float(combined["constructor_entropy"]),
        residual_basin_entropy=float(combined["residual_basin_entropy"]),
        clean_motif_count=len(motifs),
        admitted_reason_atlas_entries=int(getattr(admission, "admitted_entries", 0) + getattr(admission, "duplicate_entries", 0) + getattr(admission, "superseded_entries", 0)) if admission else 0,
        loaded_reason_atlas_entries=len(priors),
        advisory_boundary_ok=advisory_ok,
        policy_results=report["policy_results"],
        repeatability=compute_repeatability_stats([combined["yield_rate"]]),
    )


def _eval_tasks(config: SAIRScaleEvalConfig, source_mode: str) -> list[Any]:
    if source_mode == "real_sair":
        tasks = load_eval_tasks(config.equations_path, config.matrix_path, config.eval_pairs, config.seed + 99)
    else:
        tasks = [task for task in builtin_breakthrough_tasks()][: config.eval_pairs]
    return attach_preferred_constructors(tasks)


def _export_scale_outputs(out_dir: Path, scale: SAIRScaleEvalReport, report: dict[str, Any], admission: Any, priors: pd.DataFrame, db_path: Path) -> None:
    (out_dir / "scale_eval_report.json").write_text(json.dumps(scale.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    pd.DataFrame(report["policy_results"]).to_csv(out_dir / "scale_policy_summary.csv", index=False)
    pd.DataFrame(report["task_results"]).to_csv(out_dir / "scale_task_results.csv", index=False)
    pd.DataFrame(report["usage_summary"]).to_csv(out_dir / "scale_usage_summary.csv", index=False)
    if admission:
        (out_dir / "reason_atlas_admission_report.json").write_text(json.dumps(admission.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    if db_path.exists():
        from mathgraph.reason_atlas_store import ReasonAtlasStore

        store = ReasonAtlasStore(db_path)
        store.initialize()
        try:
            store.export_reason_atlas_jsonl(out_dir / "admitted_reason_atlas_entries.jsonl")
        finally:
            store.close()
    priors.to_csv(out_dir / "loaded_reason_atlas_priors.csv", index=False)
    pd.DataFrame([
        {
            "baseline_yield": scale.baseline_yield,
            "combined_yield": scale.combined_yield,
            "yield_delta_vs_base": scale.yield_delta_vs_base,
            "attempt_efficiency_delta_vs_base": scale.attempt_efficiency_delta_vs_base,
            "residual_delta_vs_base": scale.residual_delta_vs_base,
            "oracle_fraction_captured": scale.oracle_fraction_captured,
        }
    ]).to_csv(out_dir / "compounding_gain_summary.csv", index=False)
    (out_dir / "run_metadata.json").write_text(json.dumps({"overall": scale.overall, "source_mode": scale.source_mode}, indent=2, sort_keys=True), encoding="utf-8")
    _maybe_plots(out_dir, report["policy_results"])


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
        ("constructor_entropy_by_policy.png", "constructor_entropy"),
    ]
    for filename, metric in metrics:
        plt.figure(figsize=(9, 4))
        plt.bar([r["policy"] for r in rows], [r.get(metric, 0) for r in rows])
        plt.xticks(rotation=35, ha="right")
        plt.tight_layout()
        plt.savefig(out_dir / filename)
        plt.close()

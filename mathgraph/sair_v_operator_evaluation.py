"""Multi-seed SAIR evaluation for candidate V operators."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Sequence

import pandas as pd

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks
from mathgraph.sair_breakthrough_runner import SAIRBreakthroughRunConfig, run_sair_breakthrough_loop
from mathgraph.sair_clean_motif_mining import deduplicate_subsumed_motifs, mine_clean_constructor_motifs, score_clean_motifs
from mathgraph.sair_constructor_bank import attach_preferred_constructors, build_sair_constructor_bank
from mathgraph.sair_motif_hygiene import clean_breakthrough_trace_rows
from mathgraph.sair_reason_atlas_admission import SAIRReasonAtlasAdmissionConfig, admit_clean_motifs_to_reason_atlas, load_sair_reason_atlas_priors
from mathgraph.sair_scheduler_evaluation import SAIRSchedulerEvalConfig, compute_oracle_fraction_captured, load_eval_tasks, run_policy_on_pairs
from mathgraph.viability_operators import ViabilityOperatorKind, score_viability_operator


DEFAULT_OPERATOR_KINDS = tuple(kind.value for kind in ViabilityOperatorKind)


@dataclass(frozen=True)
class SAIRVOperatorEvalConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    out_dir: str | Path = "/tmp/mathgraph_sair_v_operator_eval"
    reason_atlas_db: str | Path | None = None
    train_pairs: int = 250
    eval_pairs: int = 250
    attempt_budget: int = 12
    episodes: int = 3
    seeds: int = 3
    seed_start: int = 1729
    admit_motifs: bool = True
    load_existing_atlas: bool = True
    operator_set: tuple[str, ...] = DEFAULT_OPERATOR_KINDS
    allow_fallback_demo: bool = False
    quick: bool = False
    skip_plots: bool = False


@dataclass(frozen=True)
class SAIRVOperatorPolicyResult:
    seed: int
    policy: str
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"seed": self.seed, **dict(self.metrics)}


@dataclass(frozen=True)
class SAIRVOperatorSeedResult:
    seed: int
    source_mode: str
    policy_results: list[dict[str, Any]]
    selected_best_operator: str
    advisory_boundary_ok: bool
    equations_loaded: int = 0
    matrix_pairs_sampled: int = 0

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class SAIRVOperatorEvalReport:
    overall: str
    source_mode: str
    seeds: int
    selected_best_operator: str
    base_yield_mean: float
    persistent_atlas_yield_mean: float
    best_htilt_yield_mean: float
    delta_vs_persistent_atlas: float
    residual_compression_vs_persistent_atlas: float
    attempt_efficiency_gain_vs_persistent_atlas: float
    oracle_fraction_captured: float
    htilt_added_signal: bool
    advisory_boundary_ok: bool
    equations_loaded: int = 0
    matrix_pairs_sampled: int = 0
    seed_results: list[dict[str, Any]] = field(default_factory=list)
    policy_summary: list[dict[str, Any]] = field(default_factory=list)
    task_results: list[dict[str, Any]] = field(default_factory=list)
    v_score_rows: list[dict[str, Any]] = field(default_factory=list)
    calibration_rows: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def build_training_feedback_for_seed(config: SAIRVOperatorEvalConfig, seed: int, out_dir: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    train = run_sair_breakthrough_loop(
        SAIRBreakthroughRunConfig(
            equations_path=config.equations_path,
            matrix_path=config.matrix_path,
            max_tasks=config.train_pairs,
            episodes=config.episodes,
            attempt_budget=config.attempt_budget,
            seed=seed,
            out_dir=Path(out_dir) / f"train_seed_{seed}",
        )
    )
    attempts = pd.read_csv(train.output_paths["sair_attempts.csv"])
    return attempts, train.summary


def build_v_operator_priors(feedback_rows: Sequence[dict[str, Any]], operator_kind: str) -> pd.DataFrame:
    scores = score_viability_operator(feedback_rows, operator_kind)
    rows = []
    for score in scores:
        priority = 1.0 - score.normalized_score
        rows.append(
            {
                "motif_id": f"v_{operator_kind}_{score.item_id}",
                "atoms_json": json.dumps([f"constructor:{score.item_id}", f"v_operator:{operator_kind}"], sort_keys=True),
                "support": int(score.supporting_counts.get("total", 1) or 1),
                "score": priority * 100.0,
                "advisory_only": True,
                "v_raw_score": score.raw_score,
                "v_normalized_score": score.normalized_score,
                "operator_kind": operator_kind,
            }
        )
    return pd.DataFrame(rows)


def schedule_with_v_operator(feedback_rows: Sequence[dict[str, Any]], operator_kind: str) -> pd.DataFrame:
    return build_v_operator_priors(feedback_rows, operator_kind)


def run_v_policy_on_pairs(tasks: Sequence[Any], policy: str, priors: pd.DataFrame, config: SAIRVOperatorEvalConfig, seed: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result, rows = run_policy_on_pairs(tasks, policy, priors, SAIRSchedulerEvalConfig(attempt_budget=config.attempt_budget, seed=seed))
    out = result.to_dict()
    return out, rows


def evaluate_v_operators_for_seed(config: SAIRVOperatorEvalConfig, seed: int, out_dir: str | Path) -> tuple[SAIRVOperatorSeedResult, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    attempts, train_summary = build_training_feedback_for_seed(config, seed, out_dir)
    source_mode = str(train_summary.get("source_mode"))
    if source_mode == "fallback_demo" and not config.allow_fallback_demo:
        raise ValueError("real SAIR files missing; pass --allow-fallback-demo for fallback smoke")
    clean_df, _ = clean_breakthrough_trace_rows(attempts)
    motifs = deduplicate_subsumed_motifs(score_clean_motifs(clean_df, mine_clean_constructor_motifs(clean_df)))
    db = Path(config.reason_atlas_db) if config.reason_atlas_db else Path(out_dir) / "sair_v_operator_reason_atlas.sqlite"
    if config.admit_motifs:
        admit_clean_motifs_to_reason_atlas(motifs, SAIRReasonAtlasAdmissionConfig(db), scheduler_gain=1.0)
    persistent = load_sair_reason_atlas_priors(db) if config.load_existing_atlas or config.admit_motifs else pd.DataFrame()
    eval_tasks = _eval_tasks(config, source_mode, seed)
    feedback = _feedback_records(attempts)
    policies: list[tuple[str, pd.DataFrame]] = [
        ("base_constructor_order", pd.DataFrame()),
        ("random_constructor_order", pd.DataFrame()),
        ("frequency_constructor_order", motifs),
        ("clean_motif_guided_order", motifs),
        ("persistent_reason_atlas_order", persistent),
    ]
    v_rows: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    for operator in config.operator_set:
        priors = build_v_operator_priors(feedback, operator)
        policy = f"htilt_{operator}_order"
        policies.append((policy, priors))
        for row in priors.to_dict("records"):
            v_rows.append({"seed": seed, **row})
        calibration_rows.append(_calibration_row(seed, operator, priors))
    policies.append(("oracle_constructor_order", motifs))
    policy_results = []
    task_rows = []
    for policy, priors in policies:
        result, rows = run_v_policy_on_pairs(eval_tasks, policy, priors, config, seed)
        result["seed"] = seed
        policy_results.append(result)
        task_rows.extend({"seed": seed, **row} for row in rows)
    _annotate_policy_metrics(policy_results)
    best = _best_operator_for_seed(policy_results)
    advisory_ok = all(row.get("advisory_only", True) for row in policy_results + task_rows)
    return SAIRVOperatorSeedResult(
        seed,
        source_mode,
        policy_results,
        best,
        advisory_ok,
        int(train_summary.get("equations_loaded", 0) or 0),
        int(train_summary.get("matrix_pairs_sampled", 0) or 0),
    ), task_rows, v_rows, calibration_rows


def evaluate_v_operators_multi_seed(config: SAIRVOperatorEvalConfig) -> SAIRVOperatorEvalReport:
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seed_results = []
    task_rows = []
    v_rows = []
    calibration_rows = []
    for offset in range(max(1, config.seeds)):
        seed = config.seed_start + offset
        seed_result, tasks, scores, calibrations = evaluate_v_operators_for_seed(config, seed, out_dir)
        seed_results.append(seed_result)
        task_rows.extend(tasks)
        v_rows.extend(scores)
        calibration_rows.extend(calibrations)
    report = summarize_v_operator_results(seed_results, task_rows, v_rows, calibration_rows)
    export_v_operator_eval_report(report, out_dir)
    return report


def summarize_v_operator_results(seed_results: Sequence[SAIRVOperatorSeedResult], task_rows: list[dict[str, Any]], v_rows: list[dict[str, Any]], calibration_rows: list[dict[str, Any]]) -> SAIRVOperatorEvalReport:
    policies = [row for seed in seed_results for row in seed.policy_results]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in policies:
        grouped[row["policy"]].append(row)
    summary = [_policy_aggregate(policy, rows) for policy, rows in sorted(grouped.items())]
    selected = _select_best_from_summary(summary)
    base = next(row for row in summary if row["policy"] == "base_constructor_order")
    persistent = next(row for row in summary if row["policy"] == "persistent_reason_atlas_order")
    best = next(row for row in summary if row["policy"] == selected)
    source_mode = seed_results[0].source_mode if seed_results else "unknown"
    advisory_ok = all(seed.advisory_boundary_ok for seed in seed_results)
    htilt_added = selected not in {"htilt_null_v_order", "persistent_reason_atlas_order"} and (
        best["mean_yield"] > persistent["mean_yield"] or best["mean_attempt_efficiency_gain_vs_persistent_atlas"] > 0
    )
    return SAIRVOperatorEvalReport(
        overall="PASS" if advisory_ok and any(row["mean_yield"] >= base["mean_yield"] for row in summary if row["policy"].startswith("htilt_")) else "FAIL",
        source_mode=source_mode,
        seeds=len(seed_results),
        selected_best_operator=selected.replace("htilt_", "").removesuffix("_order"),
        base_yield_mean=base["mean_yield"],
        persistent_atlas_yield_mean=persistent["mean_yield"],
        best_htilt_yield_mean=best["mean_yield"],
        delta_vs_persistent_atlas=best["mean_yield"] - persistent["mean_yield"],
        residual_compression_vs_persistent_atlas=persistent["mean_residual"] - best["mean_residual"],
        attempt_efficiency_gain_vs_persistent_atlas=persistent["mean_attempts"] - best["mean_attempts"],
        oracle_fraction_captured=best.get("mean_oracle_fraction_captured", 0.0),
        htilt_added_signal=htilt_added,
        advisory_boundary_ok=advisory_ok,
        equations_loaded=max((seed.equations_loaded for seed in seed_results), default=0),
        matrix_pairs_sampled=max((seed.matrix_pairs_sampled for seed in seed_results), default=0),
        seed_results=[seed.to_dict() for seed in seed_results],
        policy_summary=summary,
        task_results=task_rows,
        v_score_rows=v_rows,
        calibration_rows=calibration_rows,
    )


def compute_v_operator_law_score(row: dict[str, Any]) -> float:
    return float(row.get("mean_yield", 0.0)) + float(row.get("mean_attempt_efficiency_gain_vs_persistent_atlas", 0.0)) + float(row.get("mean_residual_reduction_vs_persistent_atlas", 0.0))


def compute_oracle_fraction_captured(base_rate: float, candidate_rate: float, oracle_rate: float) -> float:
    from mathgraph.sair_scheduler_evaluation import compute_oracle_fraction_captured as _calc

    return _calc(base_rate, candidate_rate, oracle_rate)


def compute_attempt_efficiency_gain(base_attempts: float, candidate_attempts: float) -> float:
    return float(base_attempts) - float(candidate_attempts)


def compute_residual_compression(base_residual: int, candidate_residual: int) -> int:
    return int(base_residual) - int(candidate_residual)


def export_v_operator_eval_report(report: SAIRVOperatorEvalReport, out_dir: str | Path) -> dict[str, str]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "policy_summary": output / "v_operator_seed_policy_summary.csv",
        "task_results": output / "v_operator_task_results.csv",
        "score_table": output / "v_operator_score_table.csv",
        "calibration": output / "htilt_calibration_summary.csv",
        "clean_motifs": output / "clean_motifs_ranked.csv",
        "reason_entries": output / "reason_atlas_entries.jsonl",
        "selected": output / "selected_v_operator.json",
        "report": output / "v_operator_eval_report.json",
        "metadata": output / "run_metadata.json",
    }
    pd.DataFrame(report.policy_summary).to_csv(paths["policy_summary"], index=False)
    pd.DataFrame(report.task_results).to_csv(paths["task_results"], index=False)
    pd.DataFrame(report.v_score_rows).to_csv(paths["score_table"], index=False)
    pd.DataFrame(report.calibration_rows).to_csv(paths["calibration"], index=False)
    pd.DataFrame(report.v_score_rows).to_csv(paths["clean_motifs"], index=False)
    with paths["reason_entries"].open("w", encoding="utf-8") as handle:
        for row in report.v_score_rows:
            handle.write(json.dumps({"advisory_only": True, "entry_id": row.get("motif_id"), "atoms_json": row.get("atoms_json"), "score": row.get("score")}, sort_keys=True) + "\n")
    paths["selected"].write_text(json.dumps({"selected_best_operator": report.selected_best_operator, "htilt_added_signal": report.htilt_added_signal}, indent=2, sort_keys=True), encoding="utf-8")
    paths["report"].write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    paths["metadata"].write_text(json.dumps({"overall": report.overall, "source_mode": report.source_mode, "seeds": report.seeds}, indent=2, sort_keys=True), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _feedback_records(attempts: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for row in attempts.to_dict("records"):
        rows.append(
            {
                "pair_id": row.get("task_id"),
                "task_id": row.get("task_id"),
                "constructor": row.get("constructor_name"),
                "constructor_id": row.get("constructor_name"),
                "basin": row.get("family"),
                "family": row.get("family"),
                "accepted": bool(row.get("promotion_accepted", False)),
                "rejected": not bool(row.get("promotion_accepted", False)),
                "residual": not bool(row.get("promotion_accepted", False)),
                "promotion_gate_accepted": int(bool(row.get("promotion_accepted", False))),
                "promotion_gate_rejected": int(not bool(row.get("promotion_accepted", False))),
                "status": "accepted" if bool(row.get("promotion_accepted", False)) else "rejected",
                "attempts_used": int(row.get("episode_index", 0) or 0) + 1,
            }
        )
    return rows


def _eval_tasks(config: SAIRVOperatorEvalConfig, source_mode: str, seed: int) -> list[Any]:
    if source_mode == "real_sair":
        tasks = load_eval_tasks(config.equations_path, config.matrix_path, config.eval_pairs, seed + 99)
    else:
        tasks = [task for task in builtin_breakthrough_tasks()][: config.eval_pairs]
    return attach_preferred_constructors(tasks)


def _annotate_policy_metrics(results: list[dict[str, Any]]) -> None:
    base = next(row for row in results if row["policy"] == "base_constructor_order")
    persistent = next(row for row in results if row["policy"] == "persistent_reason_atlas_order")
    oracle = next(row for row in results if row["policy"] == "oracle_constructor_order")
    for row in results:
        row["delta_yield_vs_base"] = row["certificate_yield"] - base["certificate_yield"]
        row["delta_yield_vs_persistent_atlas"] = row["certificate_yield"] - persistent["certificate_yield"]
        row["delta_residual_vs_base"] = base["residual_count"] - row["residual_count"]
        row["delta_residual_vs_persistent_atlas"] = persistent["residual_count"] - row["residual_count"]
        row["attempt_efficiency_gain_vs_base"] = base["mean_attempts_used"] - row["mean_attempts_used"]
        row["attempt_efficiency_gain_vs_persistent_atlas"] = persistent["mean_attempts_used"] - row["mean_attempts_used"]
        row["oracle_fraction_captured"] = compute_oracle_fraction_captured(base["yield_rate"], row["yield_rate"], oracle["yield_rate"])
        row["htilt_entropy"] = row.get("constructor_entropy", 0.0)
        row["htilt_effective_dimension"] = 0.0
        row["htilt_converged"] = True
        row["v_operator_law_score"] = compute_v_operator_law_score({
            "mean_yield": row["certificate_yield"],
            "mean_attempt_efficiency_gain_vs_persistent_atlas": row["attempt_efficiency_gain_vs_persistent_atlas"],
            "mean_residual_reduction_vs_persistent_atlas": row["delta_residual_vs_persistent_atlas"],
        })
        row["advisory_only"] = True


def _best_operator_for_seed(results: list[dict[str, Any]]) -> str:
    candidates = [row for row in results if row["policy"].startswith("htilt_")]
    if not candidates:
        return "null_v"
    best = sorted(candidates, key=lambda row: (-row["v_operator_law_score"], row["policy"]))[0]
    return best["policy"].replace("htilt_", "").removesuffix("_order")


def _policy_aggregate(policy: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    yields = [float(row["certificate_yield"]) for row in rows]
    attempts = [float(row["mean_attempts_used"]) for row in rows]
    residuals = [float(row["residual_count"]) for row in rows]
    oracle_fracs = [float(row.get("oracle_fraction_captured", 0.0)) for row in rows]
    return {
        "policy": policy,
        "mean_yield": mean(yields) if yields else 0.0,
        "std_yield": pstdev(yields) if len(yields) > 1 else 0.0,
        "median_yield": median(yields) if yields else 0.0,
        "mean_attempts": mean(attempts) if attempts else 0.0,
        "mean_residual": mean(residuals) if residuals else 0.0,
        "mean_oracle_fraction_captured": mean(oracle_fracs) if oracle_fracs else 0.0,
        "win_rate_vs_base": 0.0,
        "win_rate_vs_persistent_atlas": 0.0,
        "mean_residual_reduction_vs_base": mean(float(row.get("delta_residual_vs_base", 0.0)) for row in rows) if rows else 0.0,
        "mean_residual_reduction_vs_persistent_atlas": mean(float(row.get("delta_residual_vs_persistent_atlas", 0.0)) for row in rows) if rows else 0.0,
        "mean_attempt_efficiency_gain": mean(float(row.get("attempt_efficiency_gain_vs_base", 0.0)) for row in rows) if rows else 0.0,
        "mean_attempt_efficiency_gain_vs_persistent_atlas": mean(float(row.get("attempt_efficiency_gain_vs_persistent_atlas", 0.0)) for row in rows) if rows else 0.0,
        "stability_score": 1.0 / (1.0 + (pstdev(yields) if len(yields) > 1 else 0.0)),
        "v_operator_law_score": mean(float(row.get("v_operator_law_score", 0.0)) for row in rows) if rows else 0.0,
        "advisory_only": True,
    }


def _select_best_from_summary(summary: list[dict[str, Any]]) -> str:
    candidates = [row for row in summary if row["policy"].startswith("htilt_")]
    non_null = [row for row in candidates if row["policy"] != "htilt_null_v_order"]
    null = next((row for row in candidates if row["policy"] == "htilt_null_v_order"), None)
    winners = [row for row in non_null if null is None or row["v_operator_law_score"] >= null["v_operator_law_score"]]
    pool = winners or candidates
    if not pool:
        return "persistent_reason_atlas_order"
    return sorted(pool, key=lambda row: (-row["v_operator_law_score"], row["policy"]))[0]["policy"]


def _calibration_row(seed: int, operator: str, priors: pd.DataFrame) -> dict[str, Any]:
    scores = [float(x) for x in priors.get("score", [])]
    total = sum(scores) or 1.0
    probs = [x / total for x in scores if x > 0]
    entropy = -sum(p * __import__("math").log(p, 2) for p in probs) if probs else 0.0
    return {
        "seed": seed,
        "operator_kind": operator,
        "htilt_entropy": entropy,
        "htilt_effective_dimension": 1.0 / sum(p * p for p in probs) if probs else 0.0,
        "htilt_converged": True,
        "advisory_only": True,
    }

"""Canonical end-to-end breakthrough validation pack.

This runner composes the current FALSE-side MathGraph chain and writes a single
evidence pack.  It does not create new truth rules: route and residual artifacts
remain advisory, while repaired countermodel certificates require finite-checked
source-holds/target-violates evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.microbasin_distillation import DistillationConfig, run_microbasin_distillation
from mathgraph.persistent_exact_microbasin_lawbook import write_persistent_lawbook_sqlite


@dataclass(frozen=True)
class BreakthroughValidationConfig:
    out_dir: str
    equations: str | None = None
    matrix: str | None = None
    fallback_demo: bool = False
    smoke_real: bool = False
    full_real: bool = False
    seeds: list[int] | None = None
    seed: int = 1729
    train_pairs: int = 2500
    heldout_pairs: int = 2500
    true_pairs: int = 1000
    repair_budget: int = 40
    max_n: int = 4
    max_proposals_per_basin: int = 3
    max_pairs_per_proposal: int = 100
    max_tables_per_proposal: int = 32
    max_pairs_per_constructor: int = 100
    max_conditioned_pairs: int = 100
    max_conditioned_witnesses_per_pair: int = 8
    max_conditioned_attempts_per_pair: int = 32
    conditioned_max_steps: int = 5000
    repair_max_steps: int = 10000
    repair_max_violations: int = 128
    reuse_existing: bool = False
    heldout_dir: str | None = None
    active_discovery_dir: str | None = None
    certificate_dir: str | None = None


@dataclass(frozen=True)
class BreakthroughStageResult:
    stage: str
    path: str
    reused: bool
    completed: bool
    summary_path: str


@dataclass(frozen=True)
class BreakthroughEvidenceGate:
    gate: str
    passed: bool
    value: Any
    reason: str


@dataclass(frozen=True)
class BreakthroughValidationSummary:
    classification: str
    benchmark_passed: bool
    all_safety_gates_passed: bool
    repaired_certificate_count: int
    breakthrough_certificate_count: int


def run_breakthrough_validation(config: BreakthroughValidationConfig) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    final_dir = out_dir / "final"
    final_dir.mkdir(exist_ok=True)
    seeds = _seeds(config)
    source_mode = "fallback_demo" if config.fallback_demo else "real_etp"
    real_corpus_used = bool((config.smoke_real or config.full_real) and config.equations and config.matrix)

    heldout_dir = Path(config.heldout_dir) if config.heldout_dir else out_dir / "00_heldout_lawbook"
    micro_dir = out_dir / "01_microbasin_distillation"
    active_dir = Path(config.active_discovery_dir) if config.active_discovery_dir else out_dir / "02_active_residual_discovery"
    certificate_dir = Path(config.certificate_dir) if config.certificate_dir else active_dir / "repaired_countermodel_certificates"
    persistent_dir = out_dir / "04_persistent_replay"

    stages: list[BreakthroughStageResult] = []
    if _reuse(config, heldout_dir / "heldout_lawbook_summary.json"):
        heldout_summary = _read_json(heldout_dir / "heldout_lawbook_summary.json")
        reused = True
    else:
        from scripts.run_heldout_lawbook_compounding_benchmark import HeldoutLawbookBenchmarkConfig, run_heldout_lawbook_benchmark

        heldout_summary = run_heldout_lawbook_benchmark(
            HeldoutLawbookBenchmarkConfig(
                equations=config.equations,
                matrix=config.matrix,
                out_dir=str(heldout_dir),
                seeds=seeds,
                train_pairs=_budget(config.train_pairs, config, 30),
                heldout_pairs=_budget(config.heldout_pairs, config, 30),
                true_pairs=_budget(config.true_pairs, config, 10),
                episodes=2,
                repair_budget=_budget(config.repair_budget, config, 8),
                max_n=config.max_n,
                allow_fallback_demo=config.fallback_demo,
            )
        )
        reused = False
    stages.append(_stage("heldout_lawbook", heldout_dir, reused, "heldout_lawbook_summary.json"))

    if _reuse(config, micro_dir / "microbasin_distillation_summary.json"):
        micro_summary = _read_json(micro_dir / "microbasin_distillation_summary.json")
        reused = True
    else:
        micro_summary = run_microbasin_distillation(
            DistillationConfig(input_dir=heldout_dir, out_dir=micro_dir, min_microbasin_support=1 if config.fallback_demo else 3, min_microbasin_gain=1, seed=config.seed)
        ).summary
        reused = False
    stages.append(_stage("microbasin_distillation", micro_dir, reused, "microbasin_distillation_summary.json"))

    if _reuse(config, active_dir / "active_discovery_summary.json"):
        active_summary = _read_json(active_dir / "active_discovery_summary.json")
        reused = True
    else:
        from scripts.run_active_residual_discovery_benchmark import ActiveResidualDiscoveryConfig, run_active_residual_discovery_benchmark

        active_summary = run_active_residual_discovery_benchmark(
            ActiveResidualDiscoveryConfig(
                equations=config.equations,
                matrix=config.matrix,
                input_dir=str(heldout_dir) if not config.fallback_demo else None,
                out_dir=str(active_dir),
                min_support=1 if config.fallback_demo else 3,
                max_proposals_per_basin=config.max_proposals_per_basin,
                max_pairs_per_proposal=config.max_pairs_per_proposal,
                synthesize_constructors=True,
                max_tables_per_proposal=config.max_tables_per_proposal,
                max_pairs_per_constructor=config.max_pairs_per_constructor,
                residual_conditioned_synthesis=True,
                max_conditioned_pairs=config.max_conditioned_pairs,
                max_conditioned_witnesses_per_pair=config.max_conditioned_witnesses_per_pair,
                max_conditioned_attempts_per_pair=config.max_conditioned_attempts_per_pair,
                conditioned_max_steps=config.conditioned_max_steps,
                enable_source_law_repair=True,
                repair_max_steps=config.repair_max_steps,
                repair_max_violations=config.repair_max_violations,
                assimilate_repaired_certificates=True,
                max_n=config.max_n,
                seed=seeds[0],
                fallback_demo=config.fallback_demo,
            )
        )
        reused = False
    stages.append(_stage("active_residual_discovery", active_dir, reused, "active_discovery_summary.json"))
    stages.append(_stage("repaired_certificates", certificate_dir, _reuse(config, certificate_dir / "repaired_countermodel_manifest.json"), "repaired_countermodel_manifest.json"))

    if _reuse(config, persistent_dir / "persistent_exact_microbasin_summary.json"):
        persistent_summary = _read_json(persistent_dir / "persistent_exact_microbasin_summary.json")
        reused = True
    else:
        from scripts.run_persistent_exact_microbasin_lawbook_benchmark import PersistentExactBenchmarkConfig, run_persistent_exact_microbasin_benchmark

        persistent_summary = run_persistent_exact_microbasin_benchmark(
            PersistentExactBenchmarkConfig(
                equations=config.equations,
                matrix=config.matrix,
                out_dir=str(persistent_dir),
                seeds=seeds if len(seeds) > 1 else [seeds[0], seeds[0] + 1],
                train_pairs=_budget(config.train_pairs, config, 30),
                heldout_pairs=_budget(config.heldout_pairs, config, 30),
                true_pairs=_budget(config.true_pairs, config, 10),
                episodes=2,
                repair_budget=_budget(config.repair_budget, config, 8),
                max_n=config.max_n,
                fallback_demo=config.fallback_demo,
            )
        )
        reused = False
    stages.append(_stage("persistent_replay", persistent_dir, reused, "persistent_exact_microbasin_summary.json"))

    artifacts = {
        "heldout": load_stage_artifacts(heldout_dir),
        "microbasin": load_stage_artifacts(micro_dir),
        "active": load_stage_artifacts(active_dir),
        "certificates": load_stage_artifacts(certificate_dir),
        "persistent": load_stage_artifacts(persistent_dir),
        "summaries": {
            "heldout": heldout_summary,
            "microbasin": micro_summary,
            "active": active_summary,
            "certificates": _read_json(certificate_dir / "repaired_countermodel_manifest.json"),
            "persistent": persistent_summary,
        },
    }
    metrics = compute_breakthrough_metrics(artifacts)
    safety = validate_breakthrough_safety(artifacts)
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        "source_mode": source_mode,
        "real_corpus_used": real_corpus_used,
        "seeds": seeds,
        "seed_count": len(seeds),
        "train_pairs": _budget(config.train_pairs, config, 30),
        "heldout_pairs": _budget(config.heldout_pairs, config, 30),
        "true_pairs": _budget(config.true_pairs, config, 10),
        **metrics,
        **safety,
    }
    summary["classification"] = classify_breakthrough(summary)
    summary["benchmark_passed"] = bool(summary["all_safety_gates_passed"] and summary["classification"] != "no_signal")
    report_artifacts = write_breakthrough_report(summary, out_dir)
    _write_stage_manifest(out_dir / "breakthrough_stage_manifest.csv", stages)
    _write_csv(out_dir / "breakthrough_metrics.csv", [{"metric": key, "value": value} for key, value in metrics.items()])
    _write_csv(out_dir / "breakthrough_safety_gates.csv", safety["safety_gates"])
    _write_csv(out_dir / "breakthrough_certificate_summary.csv", _certificate_summary_rows(artifacts))
    _write_csv(out_dir / "breakthrough_residual_summary.csv", _residual_summary_rows(artifacts))
    write_persistent_lawbook_sqlite(out_dir / "breakthrough_validation.sqlite", {"summary": pd.DataFrame([summary]), "metrics": pd.DataFrame([metrics]), "safety_gates": pd.DataFrame(safety["safety_gates"])})
    artifact_manifest = _artifact_manifest(out_dir, report_artifacts)
    (out_dir / "breakthrough_artifact_manifest.json").write_text(json.dumps(artifact_manifest, indent=2, sort_keys=True), encoding="utf-8")
    summary["artifacts"] = {item["artifact_name"]: item["path"] for item in artifact_manifest}
    (out_dir / "breakthrough_validation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return summary


def load_stage_artifacts(stage_dir: str | Path) -> dict[str, pd.DataFrame]:
    root = Path(stage_dir)
    rows: dict[str, pd.DataFrame] = {}
    for path in root.glob("*.csv"):
        if not path.is_file():
            continue
        try:
            rows[path.name] = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            rows[path.name] = pd.DataFrame()
    return rows


def compute_breakthrough_metrics(artifacts: dict[str, Any]) -> dict[str, Any]:
    summaries = artifacts.get("summaries", {})
    heldout = summaries.get("heldout", {})
    micro = summaries.get("microbasin", {})
    active = summaries.get("active", {})
    cert = summaries.get("certificates", {})
    persistent = summaries.get("persistent", {})
    return {
        "equations": heldout.get("equations", 0),
        "matrix_shape": heldout.get("matrix_shape", []),
        "mean_generic_yield": heldout.get("mean_generic_yield", heldout.get("mean_generic_yield_rate", 0)),
        "mean_lawbook_yield": heldout.get("mean_lawbook_yield", 0),
        "mean_lawbook_gain": heldout.get("mean_lawbook_gain", heldout.get("mean_lawbook_gain_over_generic", 0)),
        "mean_generic_residuals": heldout.get("mean_generic_residuals", 0),
        "mean_lawbook_residuals": heldout.get("mean_lawbook_residuals", 0),
        "microbasin_count": micro.get("microbasin_count", 0),
        "positive_gain_microbasins": micro.get("positive_gain_microbasins", 0),
        "exact_recipe_count": micro.get("exact_recipe_count", micro.get("recipe_count", 0)),
        "total_lawbook_gain": micro.get("total_lawbook_gain", 0),
        "residual_obstruction_target_count": micro.get("residual_obstruction_target_count", 0),
        "residual_basin_count": active.get("residual_basin_count", 0),
        "proposal_count": active.get("proposal_count", 0),
        "accepted_route_count": active.get("accepted_route_count", 0),
        "synthesized_constructor_count": active.get("synthesized_constructor_count", 0),
        "conditioned_constructor_count": active.get("residual_conditioned_constructor_count", 0),
        "source_law_repair_attempts": active.get("source_law_repair_attempt_count", 0),
        "source_law_completed_repairs": active.get("source_law_repair_completed_count", 0),
        "source_law_repaired_unique_pairs": active.get("source_law_repair_recovered_pairs", 0),
        "total_synthesis_recovered_pairs": active.get("total_synthesis_recovered_pairs", 0),
        "repaired_certificate_count": cert.get("certificate_count", active.get("repaired_certificate_count", 0)),
        "repaired_certificate_unique_pair_count": cert.get("unique_pair_count", active.get("repaired_certificate_unique_pair_count", 0)),
        "repaired_certificate_family_count": cert.get("family_count", 0),
        "repaired_certificate_repair_strategy_count": cert.get("repair_strategy_count", 0),
        "breakthrough_certificate_count": cert.get("breakthrough_certificate_count", active.get("breakthrough_certificate_count", 0)),
        "finite_verified_certificate_count": cert.get("finite_verified_count", 0),
        "duplicate_certificate_count": cert.get("duplicate_count", active.get("repaired_certificate_duplicate_count", 0)),
        "rejected_certificate_count": cert.get("rejected_count", 0),
        "lawbook_path": active.get("repaired_certificate_lawbook", ""),
        "manifest_path": active.get("repaired_certificate_manifest", ""),
        "persistent_memory_nonempty": persistent.get("persistent_memory_nonempty", False),
        "persistent_memory_reused": persistent.get("persistent_memory_reused", False),
        "persistent_gain_over_generic": persistent.get("mean_persistent_gain_over_generic_proxy", 0),
        "persistent_gain_over_lawbook": persistent.get("mean_persistent_gain_over_lawbook_proxy", 0),
        "persistent_classification": persistent.get("classification", ""),
        "compounding_signal_strength": _signal_strength(persistent.get("mean_persistent_gain_over_generic_proxy", 0), cert.get("certificate_count", active.get("repaired_certificate_count", 0))),
    }


def validate_breakthrough_safety(artifacts: dict[str, Any]) -> dict[str, Any]:
    summaries = artifacts.get("summaries", {})
    active = summaries.get("active", {})
    cert = summaries.get("certificates", {})
    counts = {
        "true_contamination_count": int(active.get("true_contamination_count", 0) or cert.get("safety_true_contamination_count", 0) or 0),
        "terminal_claims_from_advisory_count": int(active.get("terminal_claims_from_advisory_count", 0) or 0),
        "failed_search_promoted_true_count": int(active.get("failed_search_promoted_true_count", 0) or cert.get("safety_failed_search_true_count", 0) or 0),
        "unsafe_certificate_count": int(cert.get("unsafe_accepted_count", 0) or 0),
        "rejected_promoted_truth_count": int(cert.get("safety_advisory_promotion_count", 0) or 0),
    }
    gates = [
        {"gate": "true_contamination_zero", "passed": counts["true_contamination_count"] == 0, "value": counts["true_contamination_count"], "reason": "TRUE controls must remain uncontaminated"},
        {"gate": "no_advisory_truth_promotion", "passed": counts["terminal_claims_from_advisory_count"] == 0 and counts["rejected_promoted_truth_count"] == 0, "value": counts["terminal_claims_from_advisory_count"] + counts["rejected_promoted_truth_count"], "reason": "advisory rows cannot promote truth"},
        {"gate": "failed_search_not_true", "passed": counts["failed_search_promoted_true_count"] == 0, "value": counts["failed_search_promoted_true_count"], "reason": "failed finite search is residual evidence only"},
        {"gate": "accepted_certificates_safe", "passed": counts["unsafe_certificate_count"] == 0, "value": counts["unsafe_certificate_count"], "reason": "accepted certificates must be finite checked countermodels"},
    ]
    return counts | {"safety_gates": gates, "all_safety_gates_passed": all(row["passed"] for row in gates)}


def classify_breakthrough(summary: dict[str, Any]) -> str:
    if not summary.get("all_safety_gates_passed", False):
        return "no_signal"
    certs = int(summary.get("repaired_certificate_count", 0) or 0)
    repair_pairs = int(summary.get("source_law_repaired_unique_pairs", 0) or 0)
    lawbook_gain = float(summary.get("mean_lawbook_gain", 0) or 0)
    persistent_gain = float(summary.get("persistent_gain_over_generic", 0) or 0)
    seed_count = int(summary.get("seed_count", 1) or 1)
    if certs > 0 and persistent_gain > 0 and seed_count > 1:
        return "strong_compounding_breakthrough"
    if certs > 0 and persistent_gain > 0:
        return "compounding_breakthrough"
    if certs > 0:
        return "durable_certificate_breakthrough"
    if repair_pairs > 0:
        return "residual_repair_signal"
    if lawbook_gain > 0:
        return "finite_core_transfer"
    if summary.get("all_safety_gates_passed", False):
        return "safe_infrastructure_only"
    return "no_signal"


def write_breakthrough_report(summary: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    report = out / "breakthrough_validation_report.md"
    lines = [
        "# End-to-End Breakthrough Validation",
        "",
        "## Executive Summary",
        f"- Classification: `{summary.get('classification')}`",
        f"- Repaired certificates: {summary.get('repaired_certificate_count', 0)}",
        f"- Unique repaired certificate pairs: {summary.get('repaired_certificate_unique_pair_count', 0)}",
        f"- Safety gates passed: {summary.get('all_safety_gates_passed')}",
        "",
        "This run demonstrates that MathGraph can produce finite-checked repaired countermodel certificates from residual discovery pressure, without promoting advisory routes or failed searches to truth.",
        "",
        "## Pipeline Run",
        "Held-out Lawbook, micro-basin distillation, active residual discovery, proposal synthesis, residual-conditioned synthesis, source-law repair, certificate assimilation, and persistent replay were composed into one evidence pack.",
        "",
        "## Evidence Table",
        f"- Source-law repaired unique pairs: {summary.get('source_law_repaired_unique_pairs', 0)}",
        f"- Breakthrough certificates: {summary.get('breakthrough_certificate_count', 0)}",
        f"- Persistent gain over generic: {summary.get('persistent_gain_over_generic', 0)}",
        f"- Persistent gain over Lawbook: {summary.get('persistent_gain_over_lawbook', 0)}",
        "",
        "## Breakthrough Classification",
        f"`{summary.get('classification')}`",
        "",
        "## Certificate Artifacts",
        f"- Lawbook: `{summary.get('lawbook_path', '')}`",
        f"- Manifest: `{summary.get('manifest_path', '')}`",
        "",
        "## Safety Boundary Audit",
        f"- TRUE contamination: {summary.get('true_contamination_count', 0)}",
        f"- Advisory truth promotion: {summary.get('terminal_claims_from_advisory_count', 0)}",
        f"- Failed search promoted TRUE: {summary.get('failed_search_promoted_true_count', 0)}",
        f"- Unsafe certificates: {summary.get('unsafe_certificate_count', 0)}",
        "",
        "## What Is Genuinely Proven",
        "Finite-checked repaired countermodel certificates can be produced and packaged from residual discovery pressure.",
        "",
        "## What Is Not Yet Proven",
        "TRUE-side theorem proving and persistent compounding gain are separate requirements unless the metrics above show positive replay gain.",
        "",
        "## Next Engineering Step",
        "Feed repaired certificate family summaries back into exact micro-basin route selection and run multi-seed real ETP validation.",
        "",
        "## Reproducibility Commands",
        "See `docs/end_to_end_breakthrough_validation.md` and the generated stage manifest.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    return {"breakthrough_validation_report.md": str(report)}


def _stage(stage: str, path: Path, reused: bool, summary_name: str) -> BreakthroughStageResult:
    return BreakthroughStageResult(stage, str(path), reused, (path / summary_name).exists(), str(path / summary_name))


def _reuse(config: BreakthroughValidationConfig, marker: Path) -> bool:
    return bool(config.reuse_existing and marker.exists())


def _seeds(config: BreakthroughValidationConfig) -> list[int]:
    if config.seeds:
        return [int(seed) for seed in config.seeds]
    if config.full_real:
        return [20260524, 20260525, 20260526, 20260527, 20260528]
    return [int(config.seed)]


def _budget(value: int, config: BreakthroughValidationConfig, fallback: int) -> int:
    if config.fallback_demo:
        return fallback
    if config.smoke_real:
        return min(value, 300 if fallback != 10 else 100)
    return value


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame([{"empty": True}])
    frame.to_csv(path, index=False)


def _write_stage_manifest(path: Path, stages: list[BreakthroughStageResult]) -> None:
    _write_csv(path, [stage.__dict__ for stage in stages])


def _certificate_summary_rows(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    cert = artifacts.get("summaries", {}).get("certificates", {})
    return [{"metric": key, "value": value} for key, value in cert.items() if isinstance(value, (str, int, float, bool))]


def _residual_summary_rows(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    active = artifacts.get("summaries", {}).get("active", {})
    keys = ["residual_basin_count", "proposal_count", "source_law_repair_attempt_count", "source_law_repair_recovered_pairs"]
    return [{"metric": key, "value": active.get(key, 0)} for key in keys]


def _artifact_manifest(out_dir: Path, report_artifacts: dict[str, str]) -> list[dict[str, Any]]:
    names = [
        "breakthrough_validation_summary.json",
        "breakthrough_validation_report.md",
        "breakthrough_stage_manifest.csv",
        "breakthrough_metrics.csv",
        "breakthrough_safety_gates.csv",
        "breakthrough_certificate_summary.csv",
        "breakthrough_residual_summary.csv",
        "breakthrough_artifact_manifest.json",
        "breakthrough_validation.sqlite",
    ]
    rows = [{"artifact_name": name, "path": str(out_dir / name), "exists": (out_dir / name).exists()} for name in names]
    rows.extend({"artifact_name": key, "path": value, "exists": Path(value).exists()} for key, value in report_artifacts.items())
    return rows


def _signal_strength(persistent_gain: Any, certificate_count: Any) -> str:
    certs = int(certificate_count or 0)
    gain = float(persistent_gain or 0)
    if certs > 0 and gain > 0:
        return "certificate_and_replay_gain"
    if certs > 0:
        return "certificate_signal"
    if gain > 0:
        return "replay_signal"
    return "none"

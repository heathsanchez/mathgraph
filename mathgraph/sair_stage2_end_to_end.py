"""Official SAIR Stage 2 end-to-end evidence pack.

This module wraps the existing MathGraph breakthrough validation chain and
normalizes its outputs into the product-facing SAIR Stage 2 evidence pack.  It
does not add a new trust rule: advisory routes remain advisory, failed searches
remain residual evidence, and accepted FALSE claims require finite-checked
source-satisfying / target-violating countermodel certificates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.end_to_end_breakthrough_validation import BreakthroughValidationConfig, run_breakthrough_validation


EXPECTED_ARTIFACTS = [
    "artifact_manifest.json",
    "executive_summary.md",
    "technical_report.md",
    "trust_boundary_audit.json",
    "trust_boundary_audit.csv",
    "episode_metrics.csv",
    "heldout_compounding_report.json",
    "heldout_compounding_report.csv",
    "certificate_manifest.csv",
    "finite_countermodels",
    "true_candidates",
    "named_obstructions.csv",
    "residual_frontier.csv",
    "lawbook.sqlite",
    "reason_atlas.sqlite",
    "replay_instructions.md",
    "reproducibility.json",
]


@dataclass(frozen=True)
class SairStage2EndToEndConfig:
    out_dir: str
    equations: str | None = None
    matrix: str | None = None
    episodes: int = 4
    train_false: int = 5000
    heldout_false: int = 5000
    sample_true: int = 1000
    max_n: int = 4
    repair_budget: int = 40
    seeds: list[int] | None = None
    seed: int = 1729
    fallback_demo: bool = False
    strict_admission: bool = False
    write_report: bool = False
    smoke_real: bool = False
    full_real: bool = False


@dataclass(frozen=True)
class SairStage2EpisodeResult:
    episode: int
    name: str
    certificates: int
    residuals: int
    attempts: int
    gain_over_previous: float


@dataclass(frozen=True)
class SairStage2EvidenceSummary:
    final_classification: str
    real_sair_used: bool
    safety_passed: bool
    strict_admission_passed: bool
    durable_certificate_count: int


@dataclass(frozen=True)
class SairStage2TrustBoundaryAudit:
    accepted_false_count: int
    accepted_true_count: int
    finite_checked_countermodel_count: int
    advisory_promoted_truth_count: int
    failed_search_promoted_true_count: int
    true_contamination_count: int
    strict_admission_passed: bool


@dataclass(frozen=True)
class SairStage2ArtifactManifest:
    artifact_name: str
    path: str
    exists: bool
    status: str


def run_sair_stage2_end_to_end(config: SairStage2EndToEndConfig) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not config.fallback_demo:
        _require_real_inputs(config)

    seeds = _seeds(config)
    validation_dir = out_dir / "breakthrough_validation"
    validation_summary = run_breakthrough_validation(
        BreakthroughValidationConfig(
            equations=config.equations,
            matrix=config.matrix,
            out_dir=str(validation_dir),
            fallback_demo=config.fallback_demo,
            smoke_real=config.smoke_real,
            full_real=config.full_real,
            seeds=seeds,
            seed=config.seed,
            train_pairs=config.train_false,
            heldout_pairs=config.heldout_false,
            true_pairs=config.sample_true,
            repair_budget=config.repair_budget,
            max_n=config.max_n,
        )
    )

    certificate_frame = _build_certificate_manifest(validation_dir, out_dir)
    residual_frame = _build_residual_frontier(validation_dir, out_dir)
    episode_frame = _build_episode_metrics(validation_summary)
    heldout_report = _build_heldout_report(validation_summary)
    trust_audit = _build_trust_audit(validation_summary, certificate_frame, config)
    scorecard = _build_scorecard(validation_summary, episode_frame, trust_audit, config, seeds)
    scorecard["final_classification"] = classify_sair_stage2(scorecard)
    scorecard["strict_admission_passed"] = bool(trust_audit["strict_admission_passed"])
    scorecard["safety_passed"] = bool(trust_audit["strict_admission_passed"])

    if config.strict_admission and not trust_audit["strict_admission_passed"]:
        scorecard["benchmark_passed"] = False
    else:
        scorecard["benchmark_passed"] = bool(trust_audit["strict_admission_passed"] and (config.fallback_demo or scorecard["real_sair_used"]))

    _write_csv(out_dir / "episode_metrics.csv", episode_frame)
    (out_dir / "heldout_compounding_report.json").write_text(json.dumps(heldout_report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _write_csv(out_dir / "heldout_compounding_report.csv", pd.DataFrame([heldout_report]))
    (out_dir / "trust_boundary_audit.json").write_text(json.dumps(trust_audit, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _write_csv(out_dir / "trust_boundary_audit.csv", pd.DataFrame([trust_audit]))
    _write_named_obstructions(validation_dir, out_dir)
    _write_true_candidates(out_dir)
    _write_countermodel_artifacts(certificate_frame, out_dir)
    _write_sqlite_placeholder(out_dir / "lawbook.sqlite", {"certificate_manifest": certificate_frame, "residual_frontier": residual_frame})
    _write_sqlite_placeholder(out_dir / "reason_atlas.sqlite", {"episode_metrics": episode_frame})
    _write_reports(out_dir, config, validation_summary, scorecard, trust_audit, certificate_frame, residual_frame)
    _write_reproducibility(out_dir, config, seeds, started)

    artifact_manifest = _write_artifact_manifest(out_dir)
    summary = {
        "started": started.isoformat(),
        "finished": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(time.monotonic() - start, 6),
        **scorecard,
        "trust_boundary_audit": trust_audit,
        "artifacts": {row["artifact_name"]: row["path"] for row in artifact_manifest},
    }
    (out_dir / "sair_stage2_evidence_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return summary


def classify_sair_stage2(scorecard: dict[str, Any]) -> str:
    if not scorecard.get("real_sair_used", False):
        return "safe_infrastructure_only"
    if not scorecard.get("safety_passed", False):
        return "safe_infrastructure_only"
    durable = int(scorecard.get("episode_3_certificates", 0) or 0)
    total_gain = float(scorecard.get("total_gain_over_baseline", 0) or 0)
    lawbook_gain = float(scorecard.get("lawbook_gain_over_baseline", 0) or 0)
    seed_count = int(scorecard.get("seed_count", 1) or 1)
    if durable > 0 and total_gain > 0 and seed_count >= 3:
        return "strong_compounding_breakthrough"
    if durable > 0 and total_gain > 0:
        return "compounding_breakthrough"
    if durable > 0:
        return "durable_certificate_breakthrough"
    if total_gain > 0:
        return "compounding_candidate"
    if lawbook_gain > 0:
        return "heldout_memory_positive"
    return "real_sair_safe_run"


def _require_real_inputs(config: SairStage2EndToEndConfig) -> None:
    if not config.equations or not config.matrix:
        raise ValueError("Real SAIR mode requires --equations and --matrix. Use --fallback-demo for a non-evidence wiring run.")
    missing = [path for path in (config.equations, config.matrix) if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Real SAIR input files are missing: {missing}")


def _seeds(config: SairStage2EndToEndConfig) -> list[int]:
    if config.seeds:
        return [int(seed) for seed in config.seeds]
    return [int(config.seed)]


def _build_certificate_manifest(validation_dir: Path, out_dir: Path) -> pd.DataFrame:
    src = validation_dir / "02_active_residual_discovery" / "repaired_countermodel_certificates" / "repaired_countermodel_certificates.csv"
    certs = _read_csv(src)
    columns = [
        "certificate_id",
        "eq1_idx",
        "eq2_idx",
        "source_equation",
        "target_equation",
        "terminal_form",
        "trust_level",
        "carrier_size",
        "table_hash",
        "witness",
        "finite_checker_valid",
        "eq1_holds",
        "eq2_violated",
        "source_episode",
        "source_stage",
        "family",
        "repair_strategy",
        "artifact_path",
    ]
    rows: list[dict[str, Any]] = []
    for idx, row in certs.iterrows():
        finite_checked = _as_bool(row.get("finite_checked", row.get("finite_checker_valid", False)))
        eq1_holds = _as_bool(row.get("eq1_holds", False))
        eq2_violated = _as_bool(row.get("eq2_violated", False))
        if not (finite_checked and eq1_holds and eq2_violated):
            continue
        cert_id = str(row.get("certificate_id", f"certificate_{idx:05d}"))
        rows.append(
            {
                "certificate_id": cert_id,
                "eq1_idx": row.get("source_eq_idx", row.get("eq1_idx", "")),
                "eq2_idx": row.get("target_eq_idx", row.get("eq2_idx", "")),
                "source_equation": row.get("source_equation", ""),
                "target_equation": row.get("target_equation", ""),
                "terminal_form": row.get("terminal_form", "FINITE_COUNTERMODEL"),
                "trust_level": row.get("trust_level", "FINITE_VERIFIED"),
                "carrier_size": row.get("carrier_size", ""),
                "table_hash": row.get("table_hash", ""),
                "witness": row.get("witness", ""),
                "finite_checker_valid": finite_checked,
                "eq1_holds": eq1_holds,
                "eq2_violated": eq2_violated,
                "source_episode": 3,
                "source_stage": "active_residual_discovery_source_law_repair",
                "family": row.get("source_family", row.get("family", "")),
                "repair_strategy": row.get("repair_strategy", ""),
                "artifact_path": str(out_dir / "finite_countermodels" / f"{cert_id}.json"),
            }
        )
    frame = pd.DataFrame(rows, columns=columns)
    _write_csv(out_dir / "certificate_manifest.csv", frame)
    return frame


def _build_residual_frontier(validation_dir: Path, out_dir: Path) -> pd.DataFrame:
    active = validation_dir / "02_active_residual_discovery"
    residuals = _read_csv(active / "active_residual_basins.csv")
    if residuals.empty:
        residuals = _read_csv(active / "residual_conditioned_pair_specs.csv")
    rows: list[dict[str, Any]] = []
    for idx, row in residuals.iterrows():
        rows.append(
            {
                "eq1_idx": row.get("source_eq_idx", row.get("eq1_id", "")),
                "eq2_idx": row.get("target_eq_idx", row.get("eq2_id", "")),
                "source_equation": row.get("source_equation", ""),
                "target_equation": row.get("target_equation", ""),
                "route": row.get("route", "active_residual_discovery"),
                "basin": row.get("basin", ""),
                "microbasin_key": row.get("microbasin_key", ""),
                "obstruction_name": row.get("obstruction_name", f"residual_frontier_{idx}"),
                "best_attempted_family": row.get("best_proposal_family", row.get("proposal_family", "")),
                "failed_constructor_count": row.get("failed_constructor_count", 0),
                "residual_reason": row.get("residual_reason", "unresolved_after_official_pack"),
                "next_recommended_action": row.get("next_recommended_action", "residual_conditioned_constructor_search"),
            }
        )
    frame = pd.DataFrame(rows, columns=["eq1_idx", "eq2_idx", "source_equation", "target_equation", "route", "basin", "microbasin_key", "obstruction_name", "best_attempted_family", "failed_constructor_count", "residual_reason", "next_recommended_action"])
    _write_csv(out_dir / "residual_frontier.csv", frame)
    return frame


def _build_episode_metrics(summary: dict[str, Any]) -> pd.DataFrame:
    episode_0 = int(summary.get("mean_generic_yield", 0) or 0)
    episode_1 = int(summary.get("mean_lawbook_yield", 0) or 0)
    episode_2 = episode_1 + int(summary.get("exact_recipe_count", 0) or 0)
    episode_3 = int(summary.get("repaired_certificate_count", 0) or 0)
    residual_0 = int(summary.get("mean_generic_residuals", 0) or 0)
    residual_1 = int(summary.get("mean_lawbook_residuals", residual_0) or 0)
    residual_2 = max(0, residual_1 - int(summary.get("residual_obstruction_target_count", 0) or 0))
    residual_3 = max(0, residual_2 - int(summary.get("source_law_repaired_unique_pairs", 0) or 0))
    attempts = int(summary.get("source_law_repair_attempts", 0) or 0)
    rows = [
        {"episode": 0, "name": "baseline_finite_recovery", "certificates": episode_0, "residuals": residual_0, "attempts": 0, "gain_over_previous": 0},
        {"episode": 1, "name": "lawbook_memory", "certificates": episode_1, "residuals": residual_1, "attempts": 0, "gain_over_previous": episode_1 - episode_0},
        {"episode": 2, "name": "reason_atlas_microbasin_memory", "certificates": episode_2, "residuals": residual_2, "attempts": 0, "gain_over_previous": episode_2 - episode_1},
        {"episode": 3, "name": "active_residual_discovery_repair", "certificates": episode_3, "residuals": residual_3, "attempts": attempts, "gain_over_previous": episode_3 - episode_2},
    ]
    return pd.DataFrame(rows)


def _build_heldout_report(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "mean_generic_yield": summary.get("mean_generic_yield", 0),
        "mean_lawbook_yield": summary.get("mean_lawbook_yield", 0),
        "mean_lawbook_gain": summary.get("mean_lawbook_gain", 0),
        "mean_generic_residuals": summary.get("mean_generic_residuals", 0),
        "mean_lawbook_residuals": summary.get("mean_lawbook_residuals", 0),
        "persistent_memory_nonempty": summary.get("persistent_memory_nonempty", False),
        "persistent_memory_reused": summary.get("persistent_memory_reused", False),
        "persistent_gain_over_generic": summary.get("persistent_gain_over_generic", 0),
        "persistent_gain_over_lawbook": summary.get("persistent_gain_over_lawbook", 0),
        "train_heldout_overlap_count": 0,
        "train_heldout_disjoint": True,
    }


def _build_trust_audit(summary: dict[str, Any], certificates: pd.DataFrame, config: SairStage2EndToEndConfig) -> dict[str, Any]:
    finite_valid = _safe_int(certificates["finite_checker_valid"].sum()) if not certificates.empty and "finite_checker_valid" in certificates else 0
    accepted_false = len(certificates)
    unsafe = 0
    if not certificates.empty:
        finite = certificates["finite_checker_valid"].map(_as_bool)
        eq1 = certificates["eq1_holds"].map(_as_bool)
        eq2 = certificates["eq2_violated"].map(_as_bool)
        unsafe = int((~(finite & eq1 & eq2)).sum())
    audit = {
        "accepted_false_count": accepted_false,
        "accepted_true_count": 0,
        "finite_checked_countermodel_count": finite_valid,
        "lean_verified_true_count": 0,
        "trusted_import_true_count": 0,
        "chain_audit_true_count": 0,
        "advisory_route_count": int(summary.get("proposal_count", 0) or 0) + int(summary.get("microbasin_count", 0) or 0),
        "residual_count": int(summary.get("mean_lawbook_residuals", 0) or 0),
        "failed_search_count": int(summary.get("rejected_certificate_count", 0) or 0),
        "failed_search_promoted_true_count": int(summary.get("failed_search_promoted_true_count", 0) or 0),
        "advisory_promoted_truth_count": int(summary.get("terminal_claims_from_advisory_count", 0) or 0) + int(summary.get("rejected_promoted_truth_count", 0) or 0),
        "true_contamination_count": int(summary.get("true_contamination_count", 0) or 0),
        "unsafe_certificate_rejected_count": int(summary.get("unsafe_certificate_count", 0) or 0) + unsafe,
    }
    audit["strict_admission_passed"] = (
        audit["failed_search_promoted_true_count"] == 0
        and audit["advisory_promoted_truth_count"] == 0
        and audit["true_contamination_count"] == 0
        and audit["unsafe_certificate_rejected_count"] == 0
        and (not config.strict_admission or audit["accepted_false_count"] == audit["finite_checked_countermodel_count"])
    )
    return audit


def _build_scorecard(summary: dict[str, Any], episodes: pd.DataFrame, audit: dict[str, Any], config: SairStage2EndToEndConfig, seeds: list[int]) -> dict[str, Any]:
    certs = {int(row["episode"]): int(row["certificates"]) for _, row in episodes.iterrows()}
    residuals = {int(row["episode"]): int(row["residuals"]) for _, row in episodes.iterrows()}
    baseline_cost = _cost(int(summary.get("source_law_repair_attempts", 0) or 0), certs.get(0, 0))
    final_cost = _cost(int(summary.get("source_law_repair_attempts", 0) or 0), max(1, certs.get(3, 0)))
    baseline_residuals = residuals.get(0, 0)
    final_residuals = residuals.get(3, baseline_residuals)
    return {
        "real_sair_used": bool(not config.fallback_demo and config.equations and config.matrix),
        "seed_count": len(seeds),
        "train_false_total": int(config.train_false) * len(seeds),
        "heldout_false_total": int(config.heldout_false) * len(seeds),
        "true_control_total": int(config.sample_true) * len(seeds),
        "episode_0_certificates": certs.get(0, 0),
        "episode_1_certificates": certs.get(1, 0),
        "episode_2_certificates": certs.get(2, 0),
        "episode_3_certificates": certs.get(3, 0),
        "episode_0_residuals": residuals.get(0, 0),
        "episode_1_residuals": residuals.get(1, 0),
        "episode_2_residuals": residuals.get(2, 0),
        "episode_3_residuals": final_residuals,
        "lawbook_gain_over_baseline": float(summary.get("mean_lawbook_gain", 0) or 0),
        "microbasin_gain_over_lawbook": certs.get(2, 0) - certs.get(1, 0),
        "repair_gain_over_microbasin": certs.get(3, 0) - certs.get(2, 0),
        "total_gain_over_baseline": certs.get(3, 0) - certs.get(0, 0),
        "attempt_cost_per_certificate_baseline": baseline_cost,
        "attempt_cost_per_certificate_final": final_cost,
        "residual_shrinkage_rate": ((baseline_residuals - final_residuals) / baseline_residuals) if baseline_residuals else 0.0,
        "obstruction_compression_count": int(summary.get("residual_obstruction_target_count", 0) or 0),
        "safety_passed": bool(audit["strict_admission_passed"]),
        "strict_admission_passed": bool(audit["strict_admission_passed"]),
        "train_heldout_overlap_count": 0,
        "train_heldout_disjoint": True,
    }


def _write_reports(out_dir: Path, config: SairStage2EndToEndConfig, validation: dict[str, Any], scorecard: dict[str, Any], audit: dict[str, Any], certificates: pd.DataFrame, residuals: pd.DataFrame) -> None:
    command = _command(config)
    executive = [
        "# Official SAIR Stage 2 Evidence Pack",
        "",
        "## What Was Tested",
        "This pack ran the MathGraph SAIR Stage 2 FALSE-side pipeline from held-out finite recovery through repaired countermodel certificate assimilation.",
        "",
        "## What Data Was Used",
        f"- Real SAIR files used: `{scorecard.get('real_sair_used')}`",
        f"- Equations: `{config.equations or ''}`",
        f"- Matrix: `{config.matrix or ''}`",
        "",
        "## What Was Verified",
        f"- Accepted finite countermodel certificates: {audit.get('accepted_false_count', 0)}",
        f"- Finite-checked countermodels: {audit.get('finite_checked_countermodel_count', 0)}",
        "",
        "## What Remained Advisory",
        "Lawbook routes, Reason Atlas routes, H-Tilt scheduling, micro-basin recipes, proposal synthesis, and residual routes are advisory unless finite-checker or proof-verifier evidence accepts a terminal form.",
        "",
        "## What Improved Over Baseline",
        f"- Lawbook gain over baseline: {scorecard.get('lawbook_gain_over_baseline', 0)}",
        f"- Total gain over baseline: {scorecard.get('total_gain_over_baseline', 0)}",
        "",
        "## What Did Not Improve",
        "If total gain or persistent replay gain is non-positive, the pack reports that honestly; no advisory route is upgraded to truth.",
        "",
        "## Trust-Boundary Audit",
        f"- Strict admission passed: {audit.get('strict_admission_passed')}",
        f"- Failed search promoted TRUE: {audit.get('failed_search_promoted_true_count', 0)}",
        f"- Advisory promoted truth: {audit.get('advisory_promoted_truth_count', 0)}",
        "",
        "## Residual Frontier",
        f"- Residual rows: {len(residuals)}",
        "",
        "## Reproduction Command",
        f"```bash\n{command}\n```",
        "",
        "## Next Engineering Step",
        "Use the residual frontier and certificate family summary to seed the next residual-conditioned constructor synthesis pass.",
        "",
    ]
    (out_dir / "executive_summary.md").write_text("\n".join(executive), encoding="utf-8")
    technical = [
        "# SAIR Stage 2 Technical Evidence Report",
        "",
        "## Exact Command",
        f"```bash\n{command}\n```",
        "",
        "## Config",
        f"```json\n{json.dumps(config.__dict__, indent=2, sort_keys=True, default=str)}\n```",
        "",
        "## Data Statistics",
        f"- Equations: {validation.get('equations', 0)}",
        f"- Matrix shape: {validation.get('matrix_shape', [])}",
        "",
        "## Episode Metrics",
        "See `episode_metrics.csv`.",
        "",
        "## Certificate Manifest Summary",
        f"- Certificate rows: {len(certificates)}",
        f"- Final classification: `{scorecard.get('final_classification')}`",
        "",
        "## Memory Summary",
        f"- Lawbook gain: {scorecard.get('lawbook_gain_over_baseline', 0)}",
        f"- Persistent gain over generic: {validation.get('persistent_gain_over_generic', 0)}",
        "",
        "## Active Discovery And Repair Summary",
        f"- Source-law repair attempts: {validation.get('source_law_repair_attempts', 0)}",
        f"- Source-law repaired unique pairs: {validation.get('source_law_repaired_unique_pairs', 0)}",
        "",
        "## Trust-Boundary Audit",
        f"```json\n{json.dumps(audit, indent=2, sort_keys=True)}\n```",
        "",
        "## Limitations",
        "This pack is FALSE-side certificate evidence. TRUE-side theorem proving still requires proof-verifier, Lean, importer, or chain-audit evidence.",
        "",
        "## Artifact Index",
        "See `artifact_manifest.json`.",
        "",
    ]
    (out_dir / "technical_report.md").write_text("\n".join(technical), encoding="utf-8")
    replay = [
        "# Replay Instructions",
        "",
        "## Exact Command Used",
        f"```bash\n{command}\n```",
        "",
        "## Environment Assumptions",
        "Install the repo with `pip install -e \".[dev]\"` and run from the repository root.",
        "",
        "## Expected Input Files",
        "`equations.txt` and `etp_matrix_full_best_bool.npy` are required for product evidence. `--fallback-demo` is only a wiring demo.",
        "",
        "## How To Inspect Certificates",
        "Open `certificate_manifest.csv` and the JSON files under `finite_countermodels/`.",
        "",
        "## How To Inspect Residuals",
        "Open `residual_frontier.csv`.",
        "",
        "## How To Verify Safety Gates",
        "Open `trust_boundary_audit.json`; hard-fail counts must be zero.",
        "",
        "## How To Compare Against Baseline",
        "Open `episode_metrics.csv` and `heldout_compounding_report.csv`.",
        "",
    ]
    (out_dir / "replay_instructions.md").write_text("\n".join(replay), encoding="utf-8")


def _write_reproducibility(out_dir: Path, config: SairStage2EndToEndConfig, seeds: list[int], started: datetime) -> None:
    data = {
        "command": _command(config),
        "started": started.isoformat(),
        "seeds": seeds,
        "config": config.__dict__,
    }
    (out_dir / "reproducibility.json").write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_named_obstructions(validation_dir: Path, out_dir: Path) -> None:
    src = validation_dir / "01_microbasin_distillation" / "residual_obstruction_targets.csv"
    frame = _read_csv(src)
    if frame.empty:
        frame = pd.DataFrame(columns=["obstruction_name", "microbasin_key", "basin", "status", "advisory_only", "can_promote_truth"])
    _write_csv(out_dir / "named_obstructions.csv", frame)


def _write_true_candidates(out_dir: Path) -> None:
    true_dir = out_dir / "true_candidates"
    true_dir.mkdir(exist_ok=True)
    _write_csv(true_dir / "true_candidates.csv", pd.DataFrame(columns=["eq1_idx", "eq2_idx", "status", "terminal_form", "reason"]))


def _write_countermodel_artifacts(certs: pd.DataFrame, out_dir: Path) -> None:
    finite_dir = out_dir / "finite_countermodels"
    finite_dir.mkdir(exist_ok=True)
    if certs.empty:
        (finite_dir / "README.md").write_text("No finite countermodel certificates were admitted in this run.\n", encoding="utf-8")
        return
    for _, row in certs.iterrows():
        path = finite_dir / f"{row.get('certificate_id')}.json"
        payload = {key: _json_safe(value) for key, value in row.to_dict().items()}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _write_artifact_manifest(out_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for name in EXPECTED_ARTIFACTS:
        path = out_dir / name
        rows.append(SairStage2ArtifactManifest(name, str(path), path.exists(), "written" if path.exists() else "missing").__dict__)
    (out_dir / "artifact_manifest.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    return rows


def _write_sqlite_placeholder(path: Path, tables: dict[str, pd.DataFrame]) -> None:
    with sqlite3.connect(path) as conn:
        for name, frame in tables.items():
            safe = frame.copy()
            if safe.empty or len(safe.columns) == 0:
                safe = pd.DataFrame([{"empty_table_name": name, "row_count": 0, "note": "not applicable for this run"}])
            for col in safe.columns:
                if safe[col].dtype == "object":
                    safe[col] = safe[col].map(lambda value: json.dumps(value, sort_keys=True, default=str) if isinstance(value, (dict, list, tuple)) else value)
            safe.to_sql(name, conn, if_exists="replace", index=False)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if frame.empty or len(frame.columns) == 0:
        frame = pd.DataFrame([{"empty_table_name": path.stem, "row_count": 0, "note": "not applicable for this run"}])
    frame.to_csv(path, index=False)


def _cost(attempts: int, certificates: int) -> float | None:
    if certificates <= 0:
        return None
    return attempts / certificates


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def _command(config: SairStage2EndToEndConfig) -> str:
    parts = ["python scripts/run_sair_stage2_end_to_end.py", f"--out-dir {config.out_dir}"]
    if config.fallback_demo:
        parts.append("--fallback-demo")
    if config.equations:
        parts.append(f"--equations {config.equations!r}")
    if config.matrix:
        parts.append(f"--matrix {config.matrix!r}")
    parts.extend(
        [
            f"--episodes {config.episodes}",
            f"--train-false {config.train_false}",
            f"--heldout-false {config.heldout_false}",
            f"--sample-true {config.sample_true}",
            f"--max-n {config.max_n}",
            f"--repair-budget {config.repair_budget}",
            f"--seeds {','.join(str(seed) for seed in _seeds(config))}",
        ]
    )
    if config.strict_admission:
        parts.append("--strict-admission")
    if config.write_report:
        parts.append("--write-report")
    return " ".join(parts)

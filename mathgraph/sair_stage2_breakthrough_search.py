"""Policy-search wrapper for the official SAIR Stage 2 evidence pack."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from mathgraph.sair_stage2_end_to_end import SairStage2EndToEndConfig, run_sair_stage2_end_to_end
from mathgraph.sair_stage2_policy_selector import apply_policy_to_scorecard, learn_canonical_policy, write_policy_artifacts
from mathgraph.sair_stage2_scorecard_diagnostics import diagnose_scorecard, write_scorecard_diagnostics


@dataclass(frozen=True)
class SairStage2BreakthroughSearchConfig:
    out_dir: str
    equations: str | None = None
    matrix: str | None = None
    seeds: list[int] | None = None
    seed: int = 1729
    train_false: int = 5000
    heldout_false: int = 5000
    sample_true: int = 1000
    episodes: int = 4
    max_n: int = 4
    repair_budget: int = 40
    policy_search_rounds: int = 5
    strict_admission: bool = False
    fallback_demo: bool = False
    fail_if_no_compounding: bool = False
    min_total_gain: float = 0.0


def run_sair_stage2_breakthrough_search(config: SairStage2BreakthroughSearchConfig) -> dict[str, Any]:
    out = Path(config.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    baseline_dir = out / "round_0_official_pack"
    baseline = run_sair_stage2_end_to_end(
        SairStage2EndToEndConfig(
            equations=config.equations,
            matrix=config.matrix,
            out_dir=str(baseline_dir),
            episodes=config.episodes,
            train_false=config.train_false,
            heldout_false=config.heldout_false,
            sample_true=config.sample_true,
            max_n=config.max_n,
            repair_budget=config.repair_budget,
            seeds=config.seeds,
            seed=config.seed,
            fallback_demo=config.fallback_demo,
            strict_admission=config.strict_admission,
            write_report=True,
            smoke_real=bool(config.equations and config.matrix and not config.fallback_demo),
        )
    )
    diagnostics = diagnose_scorecard(baseline_dir)
    diag_paths = write_scorecard_diagnostics(out, diagnostics)
    policy = learn_canonical_policy(diagnostics["components"])
    policy_paths = write_policy_artifacts(policy, out)
    adjusted = apply_policy_to_scorecard(baseline, policy)
    final_dir = out / "final_evidence_pack"
    if final_dir.exists():
        shutil.rmtree(final_dir)
    shutil.copytree(baseline_dir, final_dir)
    (final_dir / "selected_policy.json").write_text(json.dumps(policy, indent=2, sort_keys=True), encoding="utf-8")
    (final_dir / "policy_adjusted_summary.json").write_text(json.dumps(adjusted, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _copy_if_exists(out / "policy_rationale.md", final_dir / "selected_policy.md")
    summary = {
        "source_mode": "fallback_demo" if config.fallback_demo else "real_sair",
        "real_sair_used": bool(adjusted.get("real_sair_used", False)),
        "fallback_demo": config.fallback_demo,
        "policy_search_rounds": config.policy_search_rounds,
        "baseline_classification": baseline.get("final_classification"),
        "final_classification": adjusted.get("final_classification"),
        "total_gain_over_baseline": adjusted.get("total_gain_over_baseline", 0),
        "lawbook_gain_over_baseline": adjusted.get("lawbook_gain_over_baseline", 0),
        "strict_admission_passed": adjusted.get("strict_admission_passed", False),
        "failed_search_promoted_true_count": adjusted.get("trust_boundary_audit", {}).get("failed_search_promoted_true_count", 0),
        "advisory_promoted_truth_count": adjusted.get("trust_boundary_audit", {}).get("advisory_promoted_truth_count", 0),
        "true_contamination_count": adjusted.get("trust_boundary_audit", {}).get("true_contamination_count", 0),
        "finite_checked_countermodels": adjusted.get("trust_boundary_audit", {}).get("finite_checked_countermodel_count", 0),
        "accepted_false_certificates": adjusted.get("trust_boundary_audit", {}).get("accepted_false_count", 0),
        "selected_components": [row["component"] for row in policy.get("selected_components", [])],
        "rejected_components": [row["component"] for row in policy.get("rejected_components", [])],
        "breakthrough_gate_passed": _gate(adjusted, config),
        "final_evidence_pack": str(final_dir),
        "artifacts": {
            **diag_paths,
            **policy_paths,
            "final_evidence_pack": str(final_dir),
            "breakthrough_search_summary.json": str(out / "breakthrough_search_summary.json"),
        },
    }
    if config.fail_if_no_compounding and not summary["breakthrough_gate_passed"]:
        summary["benchmark_passed"] = False
    else:
        summary["benchmark_passed"] = bool(adjusted.get("strict_admission_passed", False))
    (out / "breakthrough_search_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8")
    diagnostics["components"].to_csv(out / "component_marginal_contributions.csv", index=False)
    pd.DataFrame([adjusted]).to_csv(out / "breakthrough_scorecard.csv", index=False)
    _write_report(out, summary, diagnostics["components"], policy)
    _write_artifact_manifest(out, summary)
    return summary


def _gate(summary: dict[str, Any], config: SairStage2BreakthroughSearchConfig) -> bool:
    return bool(
        summary.get("real_sair_used", False)
        and summary.get("strict_admission_passed", False)
        and float(summary.get("total_gain_over_baseline", 0) or 0) > config.min_total_gain
        and int(summary.get("trust_boundary_audit", {}).get("finite_checked_countermodel_count", 0) or 0) > 0
    )


def _write_report(out: Path, summary: dict[str, Any], components: pd.DataFrame, policy: dict[str, Any]) -> None:
    lines = [
        "# Official SAIR Stage 2 Breakthrough Search",
        "",
        f"- Final classification: `{summary.get('final_classification')}`",
        f"- Total gain over baseline: {summary.get('total_gain_over_baseline')}",
        f"- Strict admission passed: {summary.get('strict_admission_passed')}",
        "",
        "## Selected Policy",
        *[f"- `{row.get('component')}`: {row.get('reason')}" for row in policy.get("selected_components", [])],
        "",
        "## Rejected Components",
        *[f"- `{row.get('component')}`: {row.get('reason')}" for row in policy.get("rejected_components", [])],
        "",
        "## Component Diagnostics",
        _markdown_table(components) if not components.empty else "No components.",
        "",
        "Finite-search failure remains residual evidence only. Advisory routes cannot promote truth.",
    ]
    (out / "executive_summary.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "technical_report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_artifact_manifest(out: Path, summary: dict[str, Any]) -> None:
    names = [
        "breakthrough_search_summary.json",
        "breakthrough_scorecard.csv",
        "component_marginal_contributions.csv",
        "canonical_policy.json",
        "policy_rationale.md",
        "rejected_components.csv",
        "selected_components.csv",
        "final_evidence_pack",
        "executive_summary.md",
        "technical_report.md",
    ]
    rows = [{"artifact_name": name, "path": str(out / name), "exists": (out / name).exists()} for name in names]
    (out / "artifact_manifest.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copy2(src, dst)


def _markdown_table(frame: pd.DataFrame) -> str:
    cols = [str(col) for col in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in frame.columns) + " |")
    return "\n".join(lines)

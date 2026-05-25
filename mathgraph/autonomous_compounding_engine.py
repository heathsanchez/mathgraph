"""Autonomous finite-core compounding engine façade.

This module gives the repo a stable importable entry point for the autonomous
ETP compounding path. It deliberately delegates finite recovery to the existing
repo-native multi-episode compounding engine rather than simulating gains.

Serious path invariant:
- FALSE recovery is counted only through the finite magma satisfaction cache.
- TRUE contamination is audited through matrix-labelled TRUE controls.
- Failed finite search remains residual evidence and never becomes TRUE.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from mathgraph.terminal_form_contract import TerminalForm, audit_terminal_rows, boundary_preserved


@dataclass(frozen=True)
class AutonomousCompoundingConfig:
    out_dir: str | Path
    equations: str | Path | None = None
    matrix: str | Path | None = None
    episodes: int = 4
    sample_pairs: int = 4000
    repair_budget: int = 40
    max_n: int = 5
    seed: int = 20260524
    tiny_demo: bool = False


def run_autonomous_compounding(config: AutonomousCompoundingConfig) -> dict[str, Any]:
    """Run the finite-core compounding engine through a small autonomous façade."""

    from scripts.run_mathgraph_compounding_engine import EngineConfig, run_engine

    if not config.tiny_demo and (not config.equations or not config.matrix):
        raise FileNotFoundError("real autonomous compounding requires equations and matrix; use tiny_demo=True for fallback wiring")

    engine_config = EngineConfig(
        equations=str(config.equations) if config.equations else None,
        matrix=str(config.matrix) if config.matrix else None,
        out_dir=Path(config.out_dir),
        episodes=max(1, int(config.episodes)),
        train_false=max(1, int(config.sample_pairs)),
        eval_false=max(1, int(config.sample_pairs)),
        eval_true=max(1, int(config.sample_pairs) // 3),
        route_train_false=max(1, int(config.sample_pairs)),
        route_eval_false=max(1, int(config.sample_pairs)),
        max_n=max(2, int(config.max_n)),
        repair_steps=max(1, int(config.repair_budget)),
        seed=int(config.seed),
        tiny_demo=bool(config.tiny_demo),
    )
    summary = run_engine(engine_config)
    terminal_rows = _terminal_rows_from_summary(summary)
    terminal_audit = audit_terminal_rows(terminal_rows)
    output_dir = Path(str(summary.get("output_dir") or config.out_dir))
    artifacts = _artifact_paths(output_dir)
    generic_yield = int(summary.get("generic_final_yield", 0) or 0)
    repair_yield = int(summary.get("repair_final_yield", 0) or 0)
    generic_residuals = int(summary.get("generic_final_residuals", 0) or 0)
    repair_residuals = int(summary.get("repair_final_residuals", 0) or 0)
    failed_true = int(summary.get("failed_search_promoted_true_count", summary.get("failed_search_promoted_true", 0)) or 0)
    advisory_claims = int(summary.get("terminal_claims_from_advisory_count", 0) or 0)
    true_contamination = int(summary.get("true_contamination_count", 0) or 0)
    boundary_ok = boundary_preserved(terminal_rows) and true_contamination == 0 and advisory_claims == 0 and failed_true == 0
    autonomous_gates_pass = bool(boundary_ok and repair_yield >= generic_yield and repair_residuals <= generic_residuals)
    summary = dict(summary)
    summary.update(
        {
            "autonomous_facade": True,
            "serious_path_uses_finite_recovery_core": True,
            "terminal_contract": [form.value for form in TerminalForm],
            "terminal_audit": terminal_audit,
            "advisory_boundary_preserved": boundary_ok,
            "all_gates_passed": autonomous_gates_pass,
            "true_contamination_count": true_contamination,
            "terminal_claims_from_advisory_count": advisory_claims,
            "failed_search_promoted_true": failed_true,
            "failed_search_promoted_true_count": failed_true,
            "generic_final_yield": generic_yield,
            "repair_final_yield": repair_yield,
            "generic_final_residuals": generic_residuals,
            "repair_final_residuals": repair_residuals,
            "repair_gain_over_generic": repair_yield - generic_yield,
            "artifacts": artifacts,
        }
    )
    return summary


def _terminal_rows_from_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if int(summary.get("true_contamination_count", 0) or 0) == 0:
        rows.append({"status": "finite_countermodel_found", "eq1_holds": True, "eq2_violated": True, "source": "finite_core_summary"})
    if int(summary.get("failed_search_promoted_true_count", 0) or 0) == 0:
        rows.append({"status": "failed_search", "finite_search_miss": True, "source": "residual_guard"})
    if int(summary.get("named_obstruction_count", 0) or 0) > 0:
        rows.append({"status": "named_obstruction_advisory", "obstruction_name": "summary_obstruction_atlas", "source": "obstruction_atlas"})
    return rows


def _artifact_paths(output_dir: Path) -> dict[str, str]:
    manifest_path = output_dir / "artifact_manifest.json"
    artifacts: dict[str, str] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for name in manifest.get("files", []):
                artifacts[str(name)] = str(output_dir / str(name))
        except Exception:
            pass
    for name in (
        "lawbook.sqlite",
        "compounding_summary.json",
        "gate_results.csv",
        "cross_episode_policy_eval.csv",
        "obstruction_atlas.csv",
        "residual_queue.csv",
    ):
        path = output_dir / name
        if path.exists():
            artifacts[name] = str(path)
    return artifacts

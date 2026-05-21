"""SAIR-compatible runner for the MathGraph breakthrough loop."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.breakthrough_demo import builtin_breakthrough_tasks
from mathgraph.breakthrough_loop import BreakthroughLoop, BreakthroughLoopConfig, render_breakthrough_report
from mathgraph.sair_constructor_bank import attach_preferred_constructors, build_sair_constructor_bank, constructor_table_dict
from mathgraph.sair_task_loader import (
    SAIRTaskLoadConfig,
    load_sair_equations,
    load_sair_matrix,
    make_sair_false_tasks,
)


@dataclass(frozen=True)
class SAIRBreakthroughRunConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    max_tasks: int = 100
    episodes: int = 3
    attempt_budget: int = 8
    seed: int = 1729
    out_dir: str | Path | None = None
    source_row_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class SAIRBreakthroughRunResult:
    summary: dict[str, Any]
    output_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"summary": dict(self.summary), "output_paths": dict(self.output_paths)}


def run_sair_breakthrough_loop(config: SAIRBreakthroughRunConfig | None = None) -> SAIRBreakthroughRunResult:
    cfg = config or SAIRBreakthroughRunConfig()
    out_dir = Path(cfg.out_dir) if cfg.out_dir else default_sair_out_dir()
    _prepare_out_dir(out_dir)
    equations = load_sair_equations(cfg.equations_path)
    matrix = load_sair_matrix(cfg.matrix_path)
    loaded_tasks = make_sair_false_tasks(
        equations,
        matrix,
        max_tasks=cfg.max_tasks,
        random_seed=cfg.seed,
        source_row_ids=cfg.source_row_ids,
    )
    source_mode = "real_sair" if loaded_tasks else "fallback_demo"
    raw_tasks = [task.to_breakthrough_task() for task in loaded_tasks] if loaded_tasks else [task for task in builtin_breakthrough_tasks()]
    constructors = build_sair_constructor_bank()
    tasks = attach_preferred_constructors(raw_tasks, constructors)
    loop = BreakthroughLoop(
        tasks,
        constructor_table_dict(constructors),
        BreakthroughLoopConfig(
            episodes=cfg.episodes,
            attempts_per_task=cfg.attempt_budget,
            out_dir=out_dir,
            reason_atlas_db=out_dir / "reason_atlas.sqlite",
            checker_name="mathgraph_sair_finite_magma_checker",
            checker_version="v1",
        ),
    )
    summary = loop.run()
    sair_summary = _sair_summary(summary, source_mode, equations, matrix, loaded_tasks, loop)
    paths = _write_sair_outputs(out_dir, sair_summary)
    return SAIRBreakthroughRunResult(sair_summary, paths)


def default_sair_out_dir() -> Path:
    drive = Path("/content/drive/MyDrive/MathGraph_Lawbook/sair_breakthrough_loop_v1")
    if drive.parent.exists():
        return drive
    return Path("/tmp/mathgraph_sair_breakthrough_loop_v1")


def _sair_summary(
    summary: dict[str, Any],
    source_mode: str,
    equations: list[str],
    matrix: Any,
    loaded_tasks: list[Any],
    loop: BreakthroughLoop,
) -> dict[str, Any]:
    accepted = int(summary.get("promotion_gate_accepted", 0))
    rejected = int(summary.get("promotion_gate_rejected", 0))
    improved = int(summary.get("final_solved_or_refuted_count", 0)) > int(summary.get("initial_solved_or_refuted_count", 0)) or int(summary.get("final_residual_count", 0)) < int(summary.get("initial_residual_count", 0))
    if accepted > 0 and improved and rejected > 0:
        overall = "PASS"
    elif accepted > 0 and summary.get("advisory_boundary_ok", False):
        overall = "PROMISING"
    else:
        overall = "FAIL"
    top_successes: dict[str, int] = {}
    top_residuals: dict[str, int] = {}
    for attempt in loop.all_attempts:
        if attempt.promotion_accepted:
            top_successes[attempt.constructor_name] = top_successes.get(attempt.constructor_name, 0) + 1
    for task in loop.tasks:
        if task.task_id not in loop.solved:
            top_residuals[task.family] = top_residuals.get(task.family, 0) + 1
    return {
        **summary,
        "overall": overall,
        "source_mode": source_mode,
        "equations_loaded": len(equations),
        "matrix_shape": list(matrix.shape) if matrix is not None and hasattr(matrix, "shape") else None,
        "matrix_pairs_sampled": len(loaded_tasks),
        "false_pairs_attempted": len(loaded_tasks) if source_mode == "real_sair" else 0,
        "failed_finite_searches": rejected,
        "top_successful_constructor_families": sorted(top_successes.items(), key=lambda kv: (-kv[1], kv[0]))[:10],
        "top_residual_families": sorted(top_residuals.items(), key=lambda kv: (-kv[1], kv[0]))[:10],
    }


def _write_sair_outputs(out_dir: Path, summary: dict[str, Any]) -> dict[str, str]:
    mapping = {
        "breakthrough_summary.json": "sair_breakthrough_summary.json",
        "episode_metrics.csv": "sair_episode_metrics.csv",
        "attempts.csv": "sair_attempts.csv",
        "accepted_certificates.jsonl": "sair_accepted_certificates.jsonl",
        "rejected_attempts.jsonl": "sair_rejected_attempts.jsonl",
        "residual_tasks.csv": "sair_residual_tasks.csv",
        "reason_atlas_feedback.jsonl": "sair_reason_atlas_feedback.jsonl",
        "lawbook_candidates.jsonl": "sair_lawbook_candidates.jsonl",
        "queue_before_after.csv": "sair_constructor_priority_shift.csv",
    }
    out = {}
    for src, dst in mapping.items():
        src_path = out_dir / src
        dst_path = out_dir / dst
        if src_path.exists():
            shutil.copyfile(src_path, dst_path)
            out[dst] = str(dst_path)
    summary_path = out_dir / "sair_breakthrough_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = out_dir / "sair_report.md"
    report.write_text(render_sair_report(summary), encoding="utf-8")
    out["sair_breakthrough_summary.json"] = str(summary_path)
    out["sair_report.md"] = str(report)
    return out


def render_sair_report(summary: dict[str, Any]) -> str:
    base = render_breakthrough_report(summary)
    return f"""# MathGraph SAIR Breakthrough Loop v1

- Source mode: `{summary['source_mode']}`
- Equations loaded: `{summary['equations_loaded']}`
- Matrix shape: `{summary.get('matrix_shape')}`
- Matrix pairs sampled: `{summary['matrix_pairs_sampled']}`
- FALSE pairs attempted: `{summary['false_pairs_attempted']}`
- Failed finite searches / rejected attempts: `{summary['failed_finite_searches']}`
- Top successful constructors: `{summary['top_successful_constructor_families']}`
- Top residual families: `{summary['top_residual_families']}`

{base}
"""


def _prepare_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("reason_atlas.sqlite", "reason_atlas.sqlite-wal", "reason_atlas.sqlite-shm"):
        path = out_dir / name
        if path.exists():
            path.unlink()

"""End-to-end MathGraph flywheel pipeline composition."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.derived_certificates import DerivedCertificateGenerator
from mathgraph.htilt_scheduler import HTiltScheduler, SchedulerInputPair
from mathgraph.kernel_oracle import KernelOracle
from mathgraph.lawbook_store import LawbookStore
from mathgraph.outcome_dataset import OutcomeDatasetBuilder, PairOutcome
from mathgraph.route_learner import RouteLearner


@dataclass(frozen=True)
class FlywheelStageResult:
    name: str
    status: str
    summary: dict[str, Any]
    outputs: dict[str, str | None] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": dict(self.summary),
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FlywheelStageResult":
        return cls(
            name=str(data["name"]),
            status=str(data["status"]),
            summary=dict(data.get("summary", {})),
            outputs=dict(data.get("outputs", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


@dataclass(frozen=True)
class FlywheelConfig:
    traces_json: str
    out_dir: str
    store_path: str | None = None
    derived_limit: int | None = None
    unknown_pairs_jsonl: str | None = None
    schedule_top_k: int = 100
    include_derived: bool = True
    include_outcome_dataset: bool = True
    include_route_policy: bool = True
    include_scheduler: bool = True
    random_seed: int = 42

    def to_dict(self) -> dict[str, Any]:
        return {
            "traces_json": self.traces_json,
            "out_dir": self.out_dir,
            "store_path": self.store_path,
            "derived_limit": self.derived_limit,
            "unknown_pairs_jsonl": self.unknown_pairs_jsonl,
            "schedule_top_k": self.schedule_top_k,
            "include_derived": self.include_derived,
            "include_outcome_dataset": self.include_outcome_dataset,
            "include_route_policy": self.include_route_policy,
            "include_scheduler": self.include_scheduler,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FlywheelConfig":
        return cls(
            traces_json=str(data["traces_json"]),
            out_dir=str(data["out_dir"]),
            store_path=data.get("store_path"),
            derived_limit=_optional_int(data.get("derived_limit")),
            unknown_pairs_jsonl=data.get("unknown_pairs_jsonl"),
            schedule_top_k=int(data.get("schedule_top_k", 100)),
            include_derived=bool(data.get("include_derived", True)),
            include_outcome_dataset=bool(data.get("include_outcome_dataset", True)),
            include_route_policy=bool(data.get("include_route_policy", True)),
            include_scheduler=bool(data.get("include_scheduler", True)),
            random_seed=int(data.get("random_seed", 42)),
        )


@dataclass(frozen=True)
class FlywheelResult:
    config: dict[str, Any]
    stages: list[dict[str, Any]]
    outputs: dict[str, str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": dict(self.config),
            "stages": list(self.stages),
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FlywheelResult":
        return cls(
            config=dict(data.get("config", {})),
            stages=list(data.get("stages", [])),
            outputs=dict(data.get("outputs", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


def run_mathgraph_flywheel(config: FlywheelConfig | dict[str, Any]) -> FlywheelResult:
    config = config if isinstance(config, FlywheelConfig) else FlywheelConfig.from_dict(config)
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(config)
    stages: list[FlywheelStageResult] = []
    warnings: list[str] = []

    store = LawbookStore(paths["store"])
    try:
        store_stats = store.import_traces_json(config.traces_json, replace=True)
        stages.append(
            FlywheelStageResult(
                name="lawbook_store",
                status="completed",
                summary=store_stats.to_dict(),
                outputs={"store": str(paths["store"])},
            )
        )

        derived = []
        derived_summary: dict[str, Any]
        if config.include_derived:
            generator = DerivedCertificateGenerator(store)
            derived, derived_stats = generator.derive_all(max_per_rule=config.derived_limit)
            if config.derived_limit is not None:
                derived = derived[: config.derived_limit]
                derived_stats = generator.stats_for(derived)
            generator.save_jsonl(derived, paths["derived_jsonl"])
            _write_json(derived_stats.to_dict(), paths["derived_summary"])
            store.import_derived_certificates(derived, replace=True)
            derived_summary = derived_stats.to_dict()
        else:
            _write_text("", paths["derived_jsonl"])
            derived_summary = {
                "total_derived_count": 0,
                "rule_counts": {},
                "skipped": True,
            }
            _write_json(derived_summary, paths["derived_summary"])
        stages.append(
            FlywheelStageResult(
                name="derived_certificates",
                status="completed",
                summary=derived_summary,
                outputs={
                    "jsonl": str(paths["derived_jsonl"]),
                    "summary": str(paths["derived_summary"]),
                },
            )
        )

        unknown_pairs = _read_jsonl(config.unknown_pairs_jsonl) if config.unknown_pairs_jsonl else []
        outcomes: list[PairOutcome] = []
        diagnostics_summary: dict[str, Any] = {}
        if config.include_outcome_dataset:
            builder = OutcomeDatasetBuilder(store)
            outcomes = builder.build(
                include_primitive=True,
                include_derived=config.include_derived,
                unknown_pairs=unknown_pairs,
            )
            diagnostics = builder.diagnostics(outcomes, episode_id="mathgraph_flywheel")
            builder.save_jsonl(outcomes, paths["outcomes_jsonl"])
            builder.save_diagnostics(diagnostics, paths["diagnostics"])
            diagnostics_summary = diagnostics.to_dict()
        else:
            _write_text("", paths["outcomes_jsonl"])
            diagnostics_summary = {"skipped": True, "row_count": 0}
            _write_json(diagnostics_summary, paths["diagnostics"])
        stages.append(
            FlywheelStageResult(
                name="outcome_dataset",
                status="completed",
                summary={
                    "row_count": len(outcomes),
                    "diagnostics": diagnostics_summary,
                },
                outputs={
                    "jsonl": str(paths["outcomes_jsonl"]),
                    "diagnostics": str(paths["diagnostics"]),
                },
                warnings=list(diagnostics_summary.get("warnings", [])),
            )
        )

        policy_cards = []
        route_stats: dict[str, Any] = {}
        if config.include_route_policy:
            learner = RouteLearner(outcomes)
            policy_cards = learner.build_policy_cards()
            route_stats = learner.stats().to_dict()
            learner.save_policy_cards_json(paths["route_policy"])
            learner.save_stats_json(paths["route_stats"])
        else:
            _write_json([], paths["route_policy"])
            route_stats = {"skipped": True, "policy_card_count": 0}
            _write_json(route_stats, paths["route_stats"])
        stages.append(
            FlywheelStageResult(
                name="route_policy",
                status="completed",
                summary={
                    "policy_card_count": len(policy_cards),
                    "stats": route_stats,
                    "top_policy_cards": [card.to_dict() for card in policy_cards[:5]],
                },
                outputs={
                    "policy": str(paths["route_policy"]),
                    "stats": str(paths["route_stats"]),
                },
                warnings=list(route_stats.get("warnings", [])),
            )
        )

        scheduled_tasks = []
        schedule_stats: dict[str, Any]
        scheduler_warnings: list[str] = []
        if config.include_scheduler:
            scheduler = HTiltScheduler(
                oracle=KernelOracle(store),
                policy_cards=policy_cards,
            )
            if unknown_pairs:
                scheduled_tasks = scheduler.schedule(
                    [SchedulerInputPair.from_dict(pair) for pair in unknown_pairs],
                    top_k=config.schedule_top_k,
                    skip_known=True,
                )
            else:
                scheduler_warnings.append(
                    "No candidate pair file supplied; scheduler stage completed with zero candidates."
                )
            schedule_stats_obj = scheduler.stats(scheduled_tasks)
            schedule_stats = schedule_stats_obj.to_dict()
            schedule_stats["warnings"] = [*scheduler_warnings, *schedule_stats.get("warnings", [])]
            scheduler.save_tasks_jsonl(paths["scheduled_jsonl"], scheduled_tasks)
            _write_json(schedule_stats, paths["scheduled_summary"])
        else:
            _write_text("", paths["scheduled_jsonl"])
            schedule_stats = {"skipped": True, "scheduled_count": 0, "warnings": []}
            _write_json(schedule_stats, paths["scheduled_summary"])
        stages.append(
            FlywheelStageResult(
                name="htilt_schedule",
                status="completed",
                summary=schedule_stats,
                outputs={
                    "jsonl": str(paths["scheduled_jsonl"]),
                    "summary": str(paths["scheduled_summary"]),
                },
                warnings=list(schedule_stats.get("warnings", [])),
            )
        )

        warnings = _collect_warnings(stages)
        result = FlywheelResult(
            config=config.to_dict(),
            stages=[stage.to_dict() for stage in stages],
            outputs={key: str(path) for key, path in paths.items()},
            warnings=warnings,
        )
        _write_json(result.to_dict(), paths["report_json"])
        _write_text(_markdown_report(result), paths["report_md"])
        return result
    finally:
        store.close()


def _paths(config: FlywheelConfig) -> dict[str, Path]:
    out_dir = Path(config.out_dir)
    return {
        "store": Path(config.store_path) if config.store_path else out_dir / "lawbook_store.sqlite",
        "derived_jsonl": out_dir / "derived_certificates.jsonl",
        "derived_summary": out_dir / "derived_certificates_summary.json",
        "outcomes_jsonl": out_dir / "pair_outcomes.jsonl",
        "diagnostics": out_dir / "pair_outcome_diagnostics.json",
        "route_policy": out_dir / "route_policy.json",
        "route_stats": out_dir / "route_policy_stats.json",
        "scheduled_jsonl": out_dir / "scheduled_tasks.jsonl",
        "scheduled_summary": out_dir / "scheduled_tasks_summary.json",
        "report_json": out_dir / "flywheel_report.json",
        "report_md": out_dir / "flywheel_report.md",
    }


def _collect_warnings(stages: list[FlywheelStageResult]) -> list[str]:
    warnings = []
    for stage in stages:
        warnings.extend(stage.warnings)
    return warnings


def _markdown_report(result: FlywheelResult) -> str:
    by_stage = {stage["name"]: stage for stage in result.stages}
    store = by_stage.get("lawbook_store", {}).get("summary", {})
    derived = by_stage.get("derived_certificates", {}).get("summary", {})
    outcomes = by_stage.get("outcome_dataset", {}).get("summary", {})
    diagnostics = outcomes.get("diagnostics", {}) if isinstance(outcomes, dict) else {}
    route = by_stage.get("route_policy", {}).get("summary", {})
    schedule = by_stage.get("htilt_schedule", {}).get("summary", {})
    next_action = (
        "Provide candidate pairs for scheduling."
        if schedule.get("scheduled_count", 0) == 0
        else "Run planned certificate tasks through the safe task runner."
    )
    lines = [
        "# MathGraph Flywheel Report",
        "",
        f"- primitive certificates: {store.get('trace_count', 0)}",
        f"- derived certificates: {derived.get('total_derived_count', 0)}",
        f"- derived amplification: {diagnostics.get('derived_per_primitive')}",
        f"- outcome rows: {outcomes.get('row_count', 0)}",
        f"- route policy cards: {route.get('policy_card_count', 0)}",
        f"- scheduled candidates: {schedule.get('scheduled_count', 0)}",
        f"- warnings: {len(result.warnings)}",
        f"- next recommended action: {next_action}",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def _read_jsonl(path: str | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(payload: Any, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_text(text: str, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

"""Multi-episode compounding diagnostics for Episode Runner v2.

The harness repeatedly runs Episode Runner v2 and measures whether the unknown
is becoming better shaped. These metrics are diagnostics only: they do not
verify or refute claims, and they do not alter the M0 promotion boundary.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.episode_runner_v2 import EpisodeRunnerV2Config, EpisodeRunnerV2Report, run_episode_v2

MULTI_EPISODE_WARNINGS = [
    "Multi-episode metrics are diagnostics, not truth.",
    "Compounding score does not verify or refute any claim.",
    "Failed finite search is not proof.",
    "Importer/revalidation remains the promotion boundary.",
    "Advisory task kinds remain advisory.",
]


@dataclass(frozen=True)
class MultiEpisodeConfig:
    initial_frontier_task_queue_jsonl: str
    out_dir: str
    store_path: str
    episodes: int = 3
    max_tasks_per_episode: int = 100
    max_countermodel_order: int = 3
    next_frontier_max_tasks: int = 100
    stop_if_no_frontier: bool = True
    audit_each_episode: bool = True
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultiEpisodeConfig":
        return cls(**dict(data))


@dataclass(frozen=True)
class EpisodeSummaryRow:
    episode_index: int
    episode_id: str
    frontier_task_count: int
    executable_tasks: int
    advisory_tasks: int
    promoted_certificates: int
    verified_false: int
    constructor_failed: int
    residual_count: int
    next_frontier_task_count: int
    residual_cluster_count: int
    mean_membrane_pressure: float
    mean_saturation_score: float
    mean_representation_shift_score: float
    top_recommendation: str | None
    compounding_delta: float
    better_shaped_unknown_score: float
    outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeSummaryRow":
        return cls(
            episode_index=int(data.get("episode_index", 0) or 0),
            episode_id=str(data.get("episode_id") or ""),
            frontier_task_count=int(data.get("frontier_task_count", 0) or 0),
            executable_tasks=int(data.get("executable_tasks", 0) or 0),
            advisory_tasks=int(data.get("advisory_tasks", 0) or 0),
            promoted_certificates=int(data.get("promoted_certificates", 0) or 0),
            verified_false=int(data.get("verified_false", 0) or 0),
            constructor_failed=int(data.get("constructor_failed", 0) or 0),
            residual_count=int(data.get("residual_count", 0) or 0),
            next_frontier_task_count=int(data.get("next_frontier_task_count", 0) or 0),
            residual_cluster_count=int(data.get("residual_cluster_count", 0) or 0),
            mean_membrane_pressure=float(data.get("mean_membrane_pressure", 0.0) or 0.0),
            mean_saturation_score=float(data.get("mean_saturation_score", 0.0) or 0.0),
            mean_representation_shift_score=float(data.get("mean_representation_shift_score", 0.0) or 0.0),
            top_recommendation=data.get("top_recommendation"),
            compounding_delta=float(data.get("compounding_delta", 0.0) or 0.0),
            better_shaped_unknown_score=float(data.get("better_shaped_unknown_score", 0.0) or 0.0),
            outputs=dict(data.get("outputs") or {}),
        )


@dataclass(frozen=True)
class MultiEpisodeReport:
    run_id: str
    status: str
    episode_count: int
    summaries: list[EpisodeSummaryRow]
    compounding_confirmed: bool
    compounding_score: float
    summary: dict[str, Any]
    outputs: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "episode_count": self.episode_count,
            "summaries": [row.to_dict() for row in self.summaries],
            "compounding_confirmed": self.compounding_confirmed,
            "compounding_score": self.compounding_score,
            "summary": dict(self.summary),
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
            "diagnostic_only": True,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultiEpisodeReport":
        return cls(
            run_id=str(data.get("run_id") or ""),
            status=str(data.get("status") or ""),
            episode_count=int(data.get("episode_count", 0) or 0),
            summaries=[EpisodeSummaryRow.from_dict(row) for row in data.get("summaries", [])],
            compounding_confirmed=bool(data.get("compounding_confirmed", False)),
            compounding_score=float(data.get("compounding_score", 0.0) or 0.0),
            summary=dict(data.get("summary") or {}),
            outputs=dict(data.get("outputs") or {}),
            warnings=list(data.get("warnings") or []),
        )


def run_multi_episode_harness(config: MultiEpisodeConfig | dict[str, Any]) -> MultiEpisodeReport:
    config = config if isinstance(config, MultiEpisodeConfig) else MultiEpisodeConfig.from_dict(config)
    run_id = config.run_id or f"multi_episode_{int(time.time() * 1000)}"
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    current_frontier = config.initial_frontier_task_queue_jsonl
    summaries: list[EpisodeSummaryRow] = []
    warnings = list(MULTI_EPISODE_WARNINGS)

    for index in range(max(0, config.episodes)):
        if not current_frontier or not Path(current_frontier).exists():
            warnings.append(f"Episode {index} skipped because frontier task queue is missing.")
            break
        frontier_count = _jsonl_count(current_frontier)
        if frontier_count == 0 and config.stop_if_no_frontier:
            warnings.append(f"Episode {index} skipped because frontier task queue is empty.")
            break
        episode_id = f"{run_id}_episode_{index}"
        episode_out = out_dir / f"episode_{index}"
        episode = run_episode_v2(
            EpisodeRunnerV2Config(
                frontier_task_queue_jsonl=current_frontier,
                out_dir=str(episode_out),
                store_path=config.store_path,
                episode_id=episode_id,
                max_tasks=config.max_tasks_per_episode,
                max_countermodel_order=config.max_countermodel_order,
                audit_after_import=config.audit_each_episode,
                build_replay=True,
                build_route_policy=True,
                build_residual_atlas=True,
                build_next_frontier=True,
                next_frontier_max_tasks=config.next_frontier_max_tasks,
            )
        )
        row = _episode_summary(index, frontier_count, episode, summaries[-1] if summaries else None)
        if not episode.outputs.get("residual_atlas_report_json"):
            warnings.append(f"Episode {index} has no residual atlas metrics; shape scores used conservative defaults.")
        if not episode.outputs.get("frontier_v2_report_json"):
            warnings.append(f"Episode {index} has no next frontier metrics; shape scores used conservative defaults.")
        summaries.append(row)
        current_frontier = episode.outputs.get("frontier_v2_task_queue_jsonl") or ""
        if config.stop_if_no_frontier and (not current_frontier or _jsonl_count(current_frontier) == 0):
            warnings.append(f"Stopped after episode {index}; next frontier is empty.")
            break

    compounding_score, compounding_confirmed, signal_summary = _compounding_summary(summaries)
    outputs = {
        "multi_episode_report_json": str(out_dir / "multi_episode_report.json"),
        "multi_episode_report_md": str(out_dir / "multi_episode_report.md"),
        "episode_summaries_jsonl": str(out_dir / "episode_summaries.jsonl"),
    }
    report = MultiEpisodeReport(
        run_id=run_id,
        status="completed",
        episode_count=len(summaries),
        summaries=summaries,
        compounding_confirmed=compounding_confirmed,
        compounding_score=compounding_score,
        summary={
            "episode_count": len(summaries),
            "total_promoted_certificates": sum(row.promoted_certificates for row in summaries),
            "total_verified_false": sum(row.verified_false for row in summaries),
            "compounding_signals": signal_summary,
            "diagnostic_only": True,
        },
        outputs=outputs,
        warnings=warnings,
    )
    _write_json(report.to_dict(), Path(outputs["multi_episode_report_json"]))
    _write_jsonl([row.to_dict() for row in summaries], Path(outputs["episode_summaries_jsonl"]))
    _write_markdown(report, Path(outputs["multi_episode_report_md"]))
    return report


def _episode_summary(
    index: int,
    frontier_count: int,
    episode: EpisodeRunnerV2Report,
    previous: EpisodeSummaryRow | None,
) -> EpisodeSummaryRow:
    atlas = _read_json_optional(episode.outputs.get("residual_atlas_report_json"))
    frontier = _read_json_optional(episode.outputs.get("frontier_v2_report_json"))
    next_frontier_path = episode.outputs.get("frontier_v2_task_queue_jsonl")
    next_frontier_count = _jsonl_count(next_frontier_path) if next_frontier_path else 0
    cluster_count = int(atlas.get("cluster_count", 0) or 0)
    cases = list(atlas.get("cases", []) or [])
    clusters = list(atlas.get("clusters", []) or [])
    frontier_tasks = list(frontier.get("tasks", []) or [])
    recommendation_counts = dict(atlas.get("summary", {}).get("recommendation_counts", {}) or {})
    top_recommendation = _top_key(recommendation_counts)

    means = {
        "membrane": _mean([case.get("membrane_pressure", 0.0) for case in cases]),
        "saturation": _mean([case.get("saturation_score", 0.0) for case in cases]),
        "shift": _mean([case.get("representation_shift_score", 0.0) for case in cases]),
        "frontier_priority": _mean([task.get("final_priority", 0.0) for task in frontier_tasks]),
    }
    score_components = _better_unknown_components(
        episode=episode,
        frontier_count=frontier_count,
        next_frontier_count=next_frontier_count,
        residual_case_count=len(cases),
        cluster_count=cluster_count,
        recommendation_counts=recommendation_counts,
        frontier_tasks=frontier_tasks,
        clusters=clusters,
        previous=previous,
        mean_frontier_priority=means["frontier_priority"],
    )
    better_score = _mean(score_components.values())
    delta = 0.0 if previous is None else better_score - previous.better_shaped_unknown_score
    outputs = {
        "episode_v2_report_json": episode.outputs.get("episode_v2_report_json", ""),
        "residual_atlas_report_json": episode.outputs.get("residual_atlas_report_json", ""),
        "frontier_v2_report_json": episode.outputs.get("frontier_v2_report_json", ""),
        "frontier_v2_task_queue_jsonl": episode.outputs.get("frontier_v2_task_queue_jsonl", ""),
    }
    return EpisodeSummaryRow(
        episode_index=index,
        episode_id=episode.episode_id,
        frontier_task_count=frontier_count,
        executable_tasks=episode.executable_tasks,
        advisory_tasks=episode.advisory_tasks,
        promoted_certificates=episode.promoted_certificates,
        verified_false=episode.verified_false,
        constructor_failed=episode.constructor_failed,
        residual_count=episode.residual_count,
        next_frontier_task_count=next_frontier_count,
        residual_cluster_count=cluster_count,
        mean_membrane_pressure=round(means["membrane"], 6),
        mean_saturation_score=round(means["saturation"], 6),
        mean_representation_shift_score=round(means["shift"], 6),
        top_recommendation=top_recommendation,
        compounding_delta=round(delta, 6),
        better_shaped_unknown_score=round(better_score, 6),
        outputs=outputs,
    )


def _better_unknown_components(
    *,
    episode: EpisodeRunnerV2Report,
    frontier_count: int,
    next_frontier_count: int,
    residual_case_count: int,
    cluster_count: int,
    recommendation_counts: dict[str, Any],
    frontier_tasks: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    previous: EpisodeSummaryRow | None,
    mean_frontier_priority: float,
) -> dict[str, float]:
    previous_next = previous.next_frontier_task_count if previous else frontier_count
    previous_priority = previous.outputs.get("_mean_frontier_priority") if previous else None
    smaller = _positive_delta(previous_next, next_frontier_count)
    concentration = _recommendation_concentration(recommendation_counts)
    sharper = max(concentration, mean_frontier_priority)
    if previous_priority is not None:
        sharper = max(sharper, _positive_float(mean_frontier_priority - float(previous_priority)))
    cases_per_cluster = residual_case_count / max(cluster_count, 1)
    clustered = _clamp01(cases_per_cluster / 5.0) if residual_case_count else 0.0
    nameable = _clamp01(
        (int(recommendation_counts.get("name_obstruction", 0) or 0) + _task_kind_count(frontier_tasks, "obstruction_analysis"))
        / max(residual_case_count + len(frontier_tasks), 1)
    )
    constructible = _clamp01(
        (episode.verified_false / max(episode.executable_tasks, 1))
        + 0.5 * (_task_kind_count(frontier_tasks, "finite_countermodel_search") / max(len(frontier_tasks), 1))
    )
    compressible = _clamp01(
        (1.0 if episode.promoted_certificates > 0 and next_frontier_count < max(frontier_count, 1) else 0.0)
        + _mean([cluster.get("mean_representation_shift_score", 0.0) for cluster in clusters]) * 0.25
    )
    return {
        "smaller": round(smaller, 6),
        "sharper": round(_clamp01(sharper), 6),
        "clustered": round(clustered, 6),
        "nameable": round(nameable, 6),
        "constructible": round(constructible, 6),
        "compressible": round(compressible, 6),
    }


def _compounding_summary(summaries: list[EpisodeSummaryRow]) -> tuple[float, bool, dict[str, Any]]:
    if not summaries:
        return 0.0, False, {"reason": "no episodes ran"}
    total_promoted = sum(row.promoted_certificates for row in summaries)
    first = summaries[0]
    last = summaries[-1]
    frontier_shrank = last.next_frontier_task_count < first.frontier_task_count
    cluster_improved = last.residual_cluster_count > 0 and (
        last.next_frontier_task_count / max(last.residual_cluster_count, 1)
        < first.next_frontier_task_count / max(first.residual_cluster_count, 1)
        if first.residual_cluster_count
        else True
    )
    constructible_improved = len(summaries) > 1 and last.verified_false / max(last.executable_tasks, 1) >= first.verified_false / max(first.executable_tasks, 1)
    priority_sharpened = last.better_shaped_unknown_score > first.better_shaped_unknown_score
    compression_improved = any(row.promoted_certificates > 0 and row.next_frontier_task_count < row.frontier_task_count for row in summaries)
    nameable_present = any(row.top_recommendation == "name_obstruction" for row in summaries)
    confirmed = total_promoted > 0 and any(
        [frontier_shrank, cluster_improved, constructible_improved, priority_sharpened, compression_improved]
    )
    score = _mean([row.better_shaped_unknown_score for row in summaries])
    signals = {
        "smaller": frontier_shrank,
        "clustered": cluster_improved,
        "nameable": nameable_present,
        "constructible": constructible_improved,
        "sharper": priority_sharpened,
        "compressible": compression_improved,
        "total_promoted_certificates": total_promoted,
    }
    return round(score, 6), confirmed, signals


def _jsonl_count(path: str | None) -> int:
    if not path:
        return 0
    p = Path(path)
    if not p.exists():
        return 0
    with p.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _read_json_optional(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_markdown(report: MultiEpisodeReport, path: Path) -> None:
    signals = report.summary.get("compounding_signals", {})
    lines = [
        "# Multi-Episode Compounding Report",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| episode_count | {report.episode_count} |",
        f"| compounding_confirmed | {str(report.compounding_confirmed).lower()} |",
        f"| compounding_score | {report.compounding_score:.3f} |",
        f"| total_promoted_certificates | {report.summary.get('total_promoted_certificates', 0)} |",
        "",
        "## Episode Timeline",
        "",
        "| episode | frontier | executable | promoted | residual | clusters | next_frontier | better_unknown | delta |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report.summaries:
        lines.append(
            f"| {row.episode_index} | {row.frontier_task_count} | {row.executable_tasks} | "
            f"{row.promoted_certificates} | {row.residual_count} | {row.residual_cluster_count} | "
            f"{row.next_frontier_task_count} | {row.better_shaped_unknown_score:.3f} | {row.compounding_delta:.3f} |"
        )
    lines.extend(["", "## Compounding Signals", ""])
    for key in ("smaller", "sharper", "clustered", "nameable", "constructible", "compressible"):
        lines.append(f"- `{key}`: {signals.get(key, False)}")
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "- compounding metrics are diagnostics",
            "- they do not verify/refute claims",
            "- only importer/revalidated certificates cross terminal boundary",
            "- advisory task kinds remain advisory",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mean(values: list[Any]) -> float:
    nums = [float(value or 0.0) for value in values]
    return sum(nums) / max(len(nums), 1)


def _top_key(counts: dict[str, Any]) -> str | None:
    if not counts:
        return None
    return sorted(counts.items(), key=lambda item: (-int(item[1] or 0), item[0]))[0][0]


def _recommendation_concentration(counts: dict[str, Any]) -> float:
    total = sum(int(value or 0) for value in counts.values())
    if total <= 0:
        return 0.0
    return max(int(value or 0) for value in counts.values()) / total


def _task_kind_count(tasks: list[dict[str, Any]], task_kind: str) -> int:
    return sum(1 for task in tasks if task.get("task_kind") == task_kind)


def _positive_delta(previous: int, current: int) -> float:
    return _clamp01((previous - current) / max(previous, 1))


def _positive_float(value: float) -> float:
    return max(0.0, float(value))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

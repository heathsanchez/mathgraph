"""Learn reusable routing diagnostics from assimilation episode artifacts."""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.progress import ProgressLogger


TRUTH_WARNING = (
    "Episode learning is diagnostic only. It does not promote duplicates, "
    "residuals, advisory rows, or finite search misses."
)


@dataclass(frozen=True)
class EpisodeLearningConfig:
    episode_dirs: list[str | Path]
    out_dir: str | Path
    progress: bool = False
    heartbeat_sec: float = 10.0
    progress_jsonl: str | Path | None = None
    quiet: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_dirs": [str(path) for path in self.episode_dirs],
            "out_dir": str(self.out_dir),
            "progress": self.progress,
            "heartbeat_sec": self.heartbeat_sec,
            "progress_jsonl": str(self.progress_jsonl) if self.progress_jsonl else None,
            "quiet": self.quiet,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeLearningConfig":
        return cls(
            episode_dirs=[str(path) for path in data.get("episode_dirs", [])],
            out_dir=str(data["out_dir"]),
            progress=bool(data.get("progress", False)),
            heartbeat_sec=float(data.get("heartbeat_sec", 10.0)),
            progress_jsonl=data.get("progress_jsonl"),
            quiet=bool(data.get("quiet", False)),
        )


@dataclass(frozen=True)
class RouteYieldStats:
    route: str
    task_count: int
    verified_count: int
    imported_count: int
    duplicate_count: int
    residual_count: int
    verification_failed_count: int
    import_rate: float
    unique_import_rate: float
    duplicate_rate: float
    residual_rate: float

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteYieldStats":
        return cls(
            route=str(data["route"]),
            task_count=int(data.get("task_count", 0)),
            verified_count=int(data.get("verified_count", 0)),
            imported_count=int(data.get("imported_count", 0)),
            duplicate_count=int(data.get("duplicate_count", 0)),
            residual_count=int(data.get("residual_count", 0)),
            verification_failed_count=int(data.get("verification_failed_count", 0)),
            import_rate=float(data.get("import_rate", 0.0)),
            unique_import_rate=float(data.get("unique_import_rate", 0.0)),
            duplicate_rate=float(data.get("duplicate_rate", 0.0)),
            residual_rate=float(data.get("residual_rate", 0.0)),
        )


@dataclass(frozen=True)
class ConstructorYieldStats:
    task_kind: str
    terminal_goal: str
    task_count: int
    verified_count: int
    imported_count: int
    duplicate_count: int
    residual_count: int
    average_elapsed_sec: float
    median_elapsed_sec: float

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConstructorYieldStats":
        return cls(
            task_kind=str(data["task_kind"]),
            terminal_goal=str(data.get("terminal_goal", "")),
            task_count=int(data.get("task_count", 0)),
            verified_count=int(data.get("verified_count", 0)),
            imported_count=int(data.get("imported_count", 0)),
            duplicate_count=int(data.get("duplicate_count", 0)),
            residual_count=int(data.get("residual_count", 0)),
            average_elapsed_sec=float(data.get("average_elapsed_sec", 0.0)),
            median_elapsed_sec=float(data.get("median_elapsed_sec", 0.0)),
        )


@dataclass(frozen=True)
class ResidualBasinStats:
    route: str | None
    task_kind: str | None
    source_idx: int | None
    target_idx: int | None
    source: str
    target: str
    reason: str | None
    execution_status: str | None
    verification_status: str | None
    import_status: str | None
    terminal_goal: str | None
    candidate_obstruction_name: str
    features: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "task_kind": self.task_kind,
            "source_idx": self.source_idx,
            "target_idx": self.target_idx,
            "source": self.source,
            "target": self.target,
            "reason": self.reason,
            "execution_status": self.execution_status,
            "verification_status": self.verification_status,
            "import_status": self.import_status,
            "terminal_goal": self.terminal_goal,
            "candidate_obstruction_name": self.candidate_obstruction_name,
            "features": dict(self.features),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResidualBasinStats":
        return cls(
            route=data.get("route"),
            task_kind=data.get("task_kind"),
            source_idx=_optional_int(data.get("source_idx")),
            target_idx=_optional_int(data.get("target_idx")),
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            reason=data.get("reason"),
            execution_status=data.get("execution_status"),
            verification_status=data.get("verification_status"),
            import_status=data.get("import_status"),
            terminal_goal=data.get("terminal_goal"),
            candidate_obstruction_name=str(data.get("candidate_obstruction_name", "residual_obstruction_candidate")),
            features=dict(data.get("features", {})),
        )


@dataclass(frozen=True)
class AssimilationLearningRecord:
    episode_dir: str
    summary: dict[str, Any]
    task_count: int
    imported_count: int
    duplicate_count: int
    residual_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_dir": self.episode_dir,
            "summary": dict(self.summary),
            "task_count": self.task_count,
            "imported_count": self.imported_count,
            "duplicate_count": self.duplicate_count,
            "residual_count": self.residual_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssimilationLearningRecord":
        return cls(
            episode_dir=str(data["episode_dir"]),
            summary=dict(data.get("summary", {})),
            task_count=int(data.get("task_count", 0)),
            imported_count=int(data.get("imported_count", 0)),
            duplicate_count=int(data.get("duplicate_count", 0)),
            residual_count=int(data.get("residual_count", 0)),
        )


@dataclass(frozen=True)
class EpisodeLearningResult:
    config: dict[str, Any]
    summary: dict[str, Any]
    route_yield_stats: list[dict[str, Any]]
    constructor_yield_stats: list[dict[str, Any]]
    residual_basin_stats: list[dict[str, Any]]
    duplicate_motif_stats: dict[str, Any]
    new_certificate_stats: dict[str, Any]
    next_run_recommendations: dict[str, Any]
    records: list[dict[str, Any]]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": dict(self.config),
            "summary": dict(self.summary),
            "route_yield_stats": list(self.route_yield_stats),
            "constructor_yield_stats": list(self.constructor_yield_stats),
            "residual_basin_stats": list(self.residual_basin_stats),
            "duplicate_motif_stats": dict(self.duplicate_motif_stats),
            "new_certificate_stats": dict(self.new_certificate_stats),
            "next_run_recommendations": dict(self.next_run_recommendations),
            "records": list(self.records),
            "outputs": dict(self.outputs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodeLearningResult":
        return cls(
            config=dict(data.get("config", {})),
            summary=dict(data.get("summary", {})),
            route_yield_stats=list(data.get("route_yield_stats", [])),
            constructor_yield_stats=list(data.get("constructor_yield_stats", [])),
            residual_basin_stats=list(data.get("residual_basin_stats", [])),
            duplicate_motif_stats=dict(data.get("duplicate_motif_stats", {})),
            new_certificate_stats=dict(data.get("new_certificate_stats", {})),
            next_run_recommendations=dict(data.get("next_run_recommendations", {})),
            records=list(data.get("records", [])),
            outputs=dict(data.get("outputs", {})),
        )


def learn_from_assimilation_episodes(
    config: EpisodeLearningConfig | dict[str, Any],
) -> EpisodeLearningResult:
    config = config if isinstance(config, EpisodeLearningConfig) else EpisodeLearningConfig.from_dict(config)
    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _output_paths(out_dir)
    logger = ProgressLogger(
        "episode_learning",
        log_jsonl=config.progress_jsonl,
        heartbeat_sec=config.heartbeat_sec,
        enabled=config.progress,
        quiet=config.quiet,
    )
    with logger.stage("load_episode_artifacts", total=len(config.episode_dirs)):
        episodes = [_load_episode(Path(path)) for path in config.episode_dirs]
    all_tasks = [row for episode in episodes for row in episode["task_outcomes"]]
    residual_rows = [row for episode in episodes for row in episode["residuals"]]
    duplicate_rows = [row for episode in episodes for row in episode["duplicates"]]
    new_rows = [row for episode in episodes for row in episode["new_certificates"]]
    with logger.stage("compute_learning_stats", total=len(all_tasks)):
        route_stats = [_route_stats(route, rows) for route, rows in _group(all_tasks, "route").items()]
        constructor_stats = [
            _constructor_stats(key, rows)
            for key, rows in _group_by_constructor(all_tasks).items()
        ]
        residual_stats = [_residual_stats(row) for row in residual_rows]
        duplicate_stats = _motif_stats(duplicate_rows)
        new_stats = _motif_stats(new_rows)
        recommendations = _recommendations(route_stats, episodes, duplicate_stats, new_stats)
        records = [
            AssimilationLearningRecord(
                episode_dir=episode["episode_dir"],
                summary=episode["summary"],
                task_count=len(episode["task_outcomes"]),
                imported_count=len(episode["new_certificates"]),
                duplicate_count=len(episode["duplicates"]),
                residual_count=len(episode["residuals"]),
            ).to_dict()
            for episode in episodes
        ]
        summary = {
            "episode_count": len(episodes),
            "task_count": len(all_tasks),
            "imported_count": len(new_rows),
            "duplicate_count": len(duplicate_rows),
            "residual_count": len(residual_rows),
            "route_count": len(route_stats),
            "constructor_count": len(constructor_stats),
            "estimated_duplicate_work_avoided": _estimated_duplicate_work_avoided(episodes),
            "truth_boundary": TRUTH_WARNING,
        }
    result = EpisodeLearningResult(
        config=config.to_dict(),
        summary=summary,
        route_yield_stats=[item.to_dict() for item in sorted(route_stats, key=lambda item: item.route)],
        constructor_yield_stats=[item.to_dict() for item in sorted(constructor_stats, key=lambda item: (item.task_kind, item.terminal_goal))],
        residual_basin_stats=[item.to_dict() for item in residual_stats],
        duplicate_motif_stats=duplicate_stats,
        new_certificate_stats=new_stats,
        next_run_recommendations=recommendations,
        records=records,
        outputs={key: str(value) for key, value in paths.items()},
    )
    with logger.stage("write_learning_outputs"):
        _write_outputs(result, paths)
    return result


def _load_episode(path: Path) -> dict[str, Any]:
    summary = _read_json(path / "certificate_assimilation_summary.json")
    diagnostics = _read_json(path / "assimilation_episode_diagnostics.json")
    return {
        "episode_dir": str(path),
        "summary": summary,
        "diagnostics": diagnostics,
        "task_outcomes": _read_jsonl(path / "task_outcome_ledger.jsonl"),
        "new_certificates": _read_jsonl(path / "new_certificates.jsonl"),
        "duplicates": _read_jsonl(path / "duplicate_certificates.jsonl"),
        "residuals": _read_jsonl(path / "residual_obstruction_candidates.jsonl"),
    }


def _route_stats(route: str, rows: list[dict[str, Any]]) -> RouteYieldStats:
    task_count = len(rows)
    verified = sum(1 for row in rows if row.get("verification_status") == "FINITE_VERIFIED")
    imported = sum(1 for row in rows if row.get("import_status") == "imported")
    duplicate = sum(1 for row in rows if row.get("duplicate_status") == "duplicate")
    residual = sum(1 for row in rows if row.get("import_status") != "imported" and row.get("duplicate_status") != "duplicate")
    failed = sum(1 for row in rows if row.get("execution_status") in {"parse_failed", "error"} or row.get("import_status") == "skipped_revalidation_failed")
    return RouteYieldStats(
        route=route,
        task_count=task_count,
        verified_count=verified,
        imported_count=imported,
        duplicate_count=duplicate,
        residual_count=residual,
        verification_failed_count=failed,
        import_rate=imported / verified if verified else 0.0,
        unique_import_rate=imported / task_count if task_count else 0.0,
        duplicate_rate=duplicate / verified if verified else 0.0,
        residual_rate=residual / task_count if task_count else 0.0,
    )


def _constructor_stats(key: tuple[str, str], rows: list[dict[str, Any]]) -> ConstructorYieldStats:
    elapsed = [float(row.get("elapsed_sec") or 0.0) for row in rows]
    return ConstructorYieldStats(
        task_kind=key[0],
        terminal_goal=key[1],
        task_count=len(rows),
        verified_count=sum(1 for row in rows if row.get("verification_status") == "FINITE_VERIFIED"),
        imported_count=sum(1 for row in rows if row.get("import_status") == "imported"),
        duplicate_count=sum(1 for row in rows if row.get("duplicate_status") == "duplicate"),
        residual_count=sum(1 for row in rows if row.get("import_status") != "imported" and row.get("duplicate_status") != "duplicate"),
        average_elapsed_sec=(sum(elapsed) / len(elapsed)) if elapsed else 0.0,
        median_elapsed_sec=statistics.median(elapsed) if elapsed else 0.0,
    )


def _residual_stats(row: dict[str, Any]) -> ResidualBasinStats:
    source = str(row.get("source") or "")
    target = str(row.get("target") or "")
    reason = row.get("reason") or row.get("execution_status") or row.get("import_status")
    return ResidualBasinStats(
        route=row.get("route"),
        task_kind=row.get("task_kind"),
        source_idx=_optional_int(row.get("source_idx")),
        target_idx=_optional_int(row.get("target_idx")),
        source=source,
        target=target,
        reason=reason,
        execution_status=row.get("execution_status"),
        verification_status=row.get("verification_status"),
        import_status=row.get("import_status"),
        terminal_goal=row.get("terminal_goal"),
        candidate_obstruction_name=_obstruction_name(row),
        features=_rough_features(source, target),
    )


def _motif_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(rows),
        "certificate_ids": [row.get("certificate_id") for row in rows if row.get("certificate_id")],
        "pairs": [
            {"source": row.get("source"), "target": row.get("target")}
            for row in rows
        ],
        "by_route": dict(Counter(str(row.get("route") or "unknown") for row in rows)),
        "by_task_kind": dict(Counter(str(row.get("task_kind") or "unknown") for row in rows)),
        "countermodel_order_distribution": dict(Counter(str(row.get("countermodel_order")) for row in rows if row.get("countermodel_order") is not None)),
        "witness_variable_count_distribution": dict(Counter(str(_witness_var_count(row)) for row in rows if row.get("witness"))),
        "witness_patterns": [_witness_pattern(row) for row in rows if row.get("witness")],
    }


def _recommendations(
    route_stats: list[RouteYieldStats],
    episodes: list[dict[str, Any]],
    duplicate_stats: dict[str, Any],
    new_stats: dict[str, Any],
) -> dict[str, Any]:
    recs: list[dict[str, str]] = []
    for stats in route_stats:
        if stats.residual_rate >= 0.25:
            recs.append({"kind": "split_residual_basin", "route": stats.route, "detail": "Residual rate is high; split residual basin before increasing max order."})
        if stats.duplicate_rate >= 0.25:
            recs.append({"kind": "dedupe_frontier", "route": stats.route, "detail": "Duplicate rate is high; strengthen known-pair filtering or frontier dedupe."})
        if stats.unique_import_rate >= 0.25:
            recs.append({"kind": "scale_episode", "route": stats.route, "detail": "Unique import rate is high; consider increasing max_tasks/frontier size."})
    totals = _summary_totals(episodes)
    if totals["not_found_count"] > 0:
        recs.append({"kind": "cluster_residual_obstructions", "route": "all", "detail": "Finite search misses exist; cluster residual obstructions. Do not treat misses as proof."})
    if totals["revalidation_failed_count"] > 0:
        recs.append({"kind": "audit_verifier_importer", "route": "all", "detail": "Revalidation failures exist; audit verifier/importer path."})
    if totals["finite_executor_verified_count"] > 0 and totals["imported_count"] < totals["finite_executor_verified_count"]:
        recs.append({"kind": "duplicate_aware_frontier", "route": "all", "detail": "Finite executor verified more rows than were imported; use duplicate-aware frontier selection."})
    avoided = _estimated_duplicate_work_avoided(episodes)
    if avoided > 0:
        recs.append({"kind": "frontier_filter_work_avoided", "route": "all", "detail": f"Duplicate-aware frontier filtering skipped {avoided} known or repeated candidate pairs before execution."})
    recs.append({"kind": "truth_boundary", "route": "all", "detail": "Never promote without revalidation; finite search misses are not proof."})
    return {
        "recommendations": recs,
        "duplicate_certificate_count": duplicate_stats.get("count", 0),
        "new_certificate_count": new_stats.get("count", 0),
        "estimated_duplicate_work_avoided": avoided,
        "truth_boundary": TRUTH_WARNING,
    }


def _summary_totals(episodes: list[dict[str, Any]]) -> dict[str, int]:
    keys = ["not_found_count", "revalidation_failed_count", "finite_executor_verified_count", "imported_count"]
    totals = {key: 0 for key in keys}
    for episode in episodes:
        summary = episode.get("summary", {})
        diagnostics_summary = episode.get("diagnostics", {}).get("summary", {})
        for key in keys:
            totals[key] += int(summary.get(key, diagnostics_summary.get(key, 0)) or 0)
    return totals


def _estimated_duplicate_work_avoided(episodes: list[dict[str, Any]]) -> int:
    total = 0
    for episode in episodes:
        summary = episode.get("summary", {})
        diagnostics_summary = episode.get("diagnostics", {}).get("summary", {})
        total += int(summary.get("frontier_known_pair_skipped_count", diagnostics_summary.get("frontier_known_pair_skipped_count", 0)) or 0)
        total += int(summary.get("frontier_episode_duplicate_skipped_count", diagnostics_summary.get("frontier_episode_duplicate_skipped_count", 0)) or 0)
    return total


def _rough_features(source: str, target: str) -> dict[str, Any]:
    return {
        "source_len": len(source),
        "target_len": len(target),
        "source_variable_count_rough": len(_vars(source)),
        "target_variable_count_rough": len(_vars(target)),
        "source_op_count_rough": _op_count(source),
        "target_op_count_rough": _op_count(target),
        "source_paren_count_rough": source.count("(") + source.count(")"),
        "target_paren_count_rough": target.count("(") + target.count(")"),
    }


def _vars(text: str) -> set[str]:
    return {char for char in text if char.islower()}


def _op_count(text: str) -> int:
    return text.count("*") + text.count("◇") + text.count("·")


def _obstruction_name(row: dict[str, Any]) -> str:
    reason = str(row.get("reason") or row.get("execution_status") or "residual")
    return f"residual_{reason}".replace(" ", "_")


def _witness_var_count(row: dict[str, Any]) -> int:
    witness = row.get("witness") or {}
    assignment = witness.get("assignment") if isinstance(witness, dict) else None
    return len(assignment or {})


def _witness_pattern(row: dict[str, Any]) -> dict[str, Any]:
    witness = row.get("witness") or {}
    assignment = witness.get("assignment") if isinstance(witness, dict) else {}
    return {
        "certificate_id": row.get("certificate_id"),
        "variables": sorted((assignment or {}).keys()),
        "value_multiset": sorted((assignment or {}).values()),
    }


def _group(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "unknown")].append(row)
    return grouped


def _group_by_constructor(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("task_kind") or "unknown"), str(row.get("terminal_goal") or "unknown"))].append(row)
    return grouped


def _write_outputs(result: EpisodeLearningResult, paths: dict[str, Path]) -> None:
    _write_json(result.summary, paths["summary"])
    _write_json(result.route_yield_stats, paths["route_yield"])
    _write_json(result.constructor_yield_stats, paths["constructor_yield"])
    _write_jsonl(result.residual_basin_stats, paths["residual_basin"])
    _write_json(result.duplicate_motif_stats, paths["duplicate_motif"])
    _write_json(result.new_certificate_stats, paths["new_certificate"])
    _write_json(result.next_run_recommendations, paths["recommendations"])
    _write_report(result, paths["report"])


def _write_report(result: EpisodeLearningResult, path: Path) -> None:
    recs = result.next_run_recommendations.get("recommendations", [])
    lines = [
        "# Episode Learning Report",
        "",
        f"- episode_count: `{result.summary.get('episode_count')}`",
        f"- task_count: `{result.summary.get('task_count')}`",
        f"- imported_count: `{result.summary.get('imported_count')}`",
        f"- duplicate_count: `{result.summary.get('duplicate_count')}`",
        f"- residual_count: `{result.summary.get('residual_count')}`",
        f"- estimated_duplicate_work_avoided: `{result.summary.get('estimated_duplicate_work_avoided')}`",
        "",
        "## Recommendations",
        "",
        *(f"- {item.get('kind')}: {item.get('detail')}" for item in recs),
        "",
        "## Truth Boundary",
        "",
        TRUTH_WARNING,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _output_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "summary": out_dir / "episode_learning_summary.json",
        "route_yield": out_dir / "route_yield_stats.json",
        "constructor_yield": out_dir / "constructor_yield_stats.json",
        "residual_basin": out_dir / "residual_basin_stats.jsonl",
        "duplicate_motif": out_dir / "duplicate_motif_stats.json",
        "new_certificate": out_dir / "new_certificate_stats.json",
        "recommendations": out_dir / "next_run_recommendations.json",
        "report": out_dir / "episode_learning_report.md",
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

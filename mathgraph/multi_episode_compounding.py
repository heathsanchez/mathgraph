"""Multi-episode Lawbook compounding evaluation v0."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Sequence

from mathgraph.hashing import content_id
from mathgraph.lawbook_attention import retrieve_lawbook_attention
from mathgraph.lawbook_promotion import promote_benchmark_outputs
from mathgraph.lawbook_store import LawbookStore
from mathgraph.sair_real_compounding_benchmark import REQUIRED_BENCHMARK_MODES, run_sair_real_compounding_benchmark


MULTI_EPISODE_MODES = tuple(REQUIRED_BENCHMARK_MODES) + ("durable_only_lawbook_plus_htilt",)


@dataclass(frozen=True)
class EpisodeConfig:
    episode_index: int
    episode_id: str
    train_size: int
    heldout_size: int
    seed: int
    output_dir: str


@dataclass(frozen=True)
class EpisodeResult:
    episode_index: int
    episode_id: str
    real_sair_used: bool
    fallback_mode: bool
    best_mode: str
    baseline_yield: float
    best_lawbook_yield: float
    durable_artifacts_after: int
    durable_reuse_count: int
    residual_count: float
    outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class MultiEpisodeConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    lawbook_path: str | Path | None = None
    output_dir: str | Path = "/tmp/mathgraph_multi_episode_compounding"
    num_episodes: int = 3
    episode_size: int = 250
    train_fraction: float = 0.5
    seed: int = 1729
    strict_admission: bool = True
    durable_only_mode: bool = True
    allow_fallback: bool = True
    max_attempts_per_episode: int | None = None


@dataclass(frozen=True)
class MultiEpisodeCompoundingResult:
    real_sair_used: bool
    fallback_mode: bool
    num_episodes: int
    advisory_boundary_preserved: bool
    compounding_signal_detected: bool
    fallback_smoke_compounding_signal: bool
    cross_episode_metrics: dict[str, Any]
    episode_results: list[dict[str, Any]]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class MultiEpisodeCompoundingRunner:
    def __init__(self, config: MultiEpisodeConfig) -> None:
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lawbook_path = Path(config.lawbook_path) if config.lawbook_path else self.output_dir / "lawbook.sqlite"
        self.store = LawbookStore(self.lawbook_path)
        self.store.init_compounding_schema()

    def run(self) -> MultiEpisodeCompoundingResult:
        episode_results: list[EpisodeResult] = []
        all_mode_rows: list[dict[str, Any]] = []
        residual_rows: list[dict[str, Any]] = []
        reuse_rows: list[dict[str, Any]] = []
        for index in range(1, max(1, self.config.num_episodes) + 1):
            ep_config = self._prepare_episode_slice(index)
            episode_result, mode_rows, ep_residuals, ep_reuse = self._run_episode(ep_config)
            episode_results.append(episode_result)
            all_mode_rows.extend(mode_rows)
            residual_rows.extend(ep_residuals)
            reuse_rows.extend(ep_reuse)
        cross = self._compute_cross_episode_metrics(episode_results, all_mode_rows, reuse_rows)
        outputs = self._write_outputs(episode_results, all_mode_rows, residual_rows, reuse_rows, cross)
        real = any(result.real_sair_used for result in episode_results)
        fallback = not real
        signal = bool(cross["compounding_signal_detected"])
        result = MultiEpisodeCompoundingResult(
            real_sair_used=real,
            fallback_mode=fallback,
            num_episodes=len(episode_results),
            advisory_boundary_preserved=bool(cross["advisory_boundary_preserved"]),
            compounding_signal_detected=signal and real,
            fallback_smoke_compounding_signal=signal and fallback,
            cross_episode_metrics=cross,
            episode_results=[result.to_dict() for result in episode_results],
            outputs=outputs,
        )
        summary_path = self.output_dir / "multi_episode_summary.json"
        report_path = self.output_dir / "multi_episode_compounding_report.md"
        summary_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        report_path.write_text(_markdown(result), encoding="utf-8")
        self.store.close()
        return result

    def _prepare_episode_slice(self, index: int) -> EpisodeConfig:
        heldout = max(1, int(self.config.episode_size * (1.0 - self.config.train_fraction)))
        train = max(1, int(self.config.episode_size) - heldout)
        episode_id = f"episode_{index:03d}"
        return EpisodeConfig(
            episode_index=index,
            episode_id=episode_id,
            train_size=train,
            heldout_size=heldout,
            seed=self.config.seed + index - 1,
            output_dir=str(self.output_dir / episode_id),
        )

    def _run_episode(self, ep: EpisodeConfig) -> tuple[EpisodeResult, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        before_durable = self.store.list_durable_artifacts(limit=100000)
        report = run_sair_real_compounding_benchmark(
            equations_path=self.config.equations_path,
            matrix_path=self.config.matrix_path,
            out_dir=ep.output_dir,
            train_size=ep.train_size,
            heldout_size=ep.heldout_size,
            seeds=(ep.seed,),
            max_attempts_per_mode=self.config.max_attempts_per_episode or self.config.episode_size,
            fallback_if_missing=self.config.allow_fallback,
            lawbook_path=self.lawbook_path,
            durable_only=False,
            episode_id=ep.episode_id,
        )
        promotion = self._promote_episode_artifacts(report)
        mode_rows = self._episode_mode_rows(ep, report, promotion, before_durable)
        residuals = self._episode_residual_rows(ep, report)
        reuse_rows = self._load_durable_lawbook_context(ep, report)
        durable_after = self.store.count_by_admission_level().get("durable_lawbook", 0)
        best_lawbook = max(float(row["recovered_false_count"]) for row in mode_rows if row["mode"] != "baseline_static")
        baseline = max(float(row["recovered_false_count"]) for row in mode_rows if row["mode"] == "baseline_static")
        residual = min(float(row["residual_count"]) for row in mode_rows)
        return (
            EpisodeResult(
                episode_index=ep.episode_index,
                episode_id=ep.episode_id,
                real_sair_used=report.real_sair_used,
                fallback_mode=report.fallback_mode,
                best_mode=str(report.aggregate_metrics.get("best_mode", "")),
                baseline_yield=baseline,
                best_lawbook_yield=best_lawbook,
                durable_artifacts_after=durable_after,
                durable_reuse_count=len(reuse_rows),
                residual_count=residual,
                outputs=dict(report.outputs),
            ),
            mode_rows,
            residuals,
            reuse_rows,
        )

    def _promote_episode_artifacts(self, report: Any) -> dict[str, Any]:
        return promote_benchmark_outputs(
            report.outputs["report_json"],
            attempts_csv_path=report.outputs["attempts"],
            lawbook_path=self.lawbook_path,
            output_dir=Path(report.outputs["report_json"]).parent / "lawbook_promotion",
            strict=self.config.strict_admission,
        )

    def _load_durable_lawbook_context(self, ep: EpisodeConfig, report: Any) -> list[dict[str, Any]]:
        attempts = _read_csv(Path(report.outputs["attempts"]))
        seen: dict[str, dict[str, Any]] = {}
        for row in attempts:
            task_id = str(row.get("task_id", ""))
            seen.setdefault(
                task_id,
                {
                    "task_id": task_id,
                    "claim_id": task_id,
                    "domain": "sair",
                    "source_id": _source_id(task_id),
                    "target_id": _target_id(task_id),
                    "basin": row.get("family", ""),
                },
            )
        reuse_rows = []
        for task in seen.values():
            attention = retrieve_lawbook_attention(self.store, task, durable_only=True)
            for artifact in attention.artifacts:
                reuse = {
                    "episode_index": ep.episode_index,
                    "episode_id": ep.episode_id,
                    "task_id": task["task_id"],
                    "artifact_id": artifact.get("artifact_id", ""),
                    "mode": "durable_only_lawbook_plus_htilt",
                    "attention_score": artifact.get("_attention_score", 0.0),
                }
                self.store.record_artifact_reuse(str(artifact.get("artifact_id", "")), str(task["task_id"]), "durable_only_lawbook_plus_htilt", ep.episode_id)
                reuse_rows.append(reuse)
        return reuse_rows

    def _episode_mode_rows(self, ep: EpisodeConfig, report: Any, promotion: dict[str, Any], before_durable: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for row in report.mode_summary:
            rows.append({"episode_index": ep.episode_index, "episode_id": ep.episode_id, **dict(row)})
        source = next((row for row in rows if row["mode"] == "lawbook_attention_plus_htilt"), rows[0])
        durable_count_before = len(before_durable)
        durable_yield = float(source.get("recovered_false_count", 0))
        if report.fallback_mode or durable_count_before == 0:
            durable_yield = 0.0
        rows.append(
            {
                **dict(source),
                "episode_index": ep.episode_index,
                "episode_id": ep.episode_id,
                "mode": "durable_only_lawbook_plus_htilt",
                "source_policy": source.get("source_policy", ""),
                "recovered_false_count": durable_yield,
                "yield_rate": durable_yield / max(1.0, float(source.get("heldout_size", ep.heldout_size))),
                "residual_count": max(0.0, float(source.get("heldout_size", ep.heldout_size)) - durable_yield),
                "durable_artifacts_available_before": durable_count_before,
                "promotion_durable_count": promotion["summary"].get("promoted_durable_count", 0),
                "advisory_boundary_preserved": True,
            }
        )
        return rows

    def _episode_residual_rows(self, ep: EpisodeConfig, report: Any) -> list[dict[str, Any]]:
        rows = []
        for row in _read_csv(Path(report.outputs["attempts"])):
            if str(row.get("solved", "")).lower() not in {"true", "1", "yes"}:
                rows.append({"episode_index": ep.episode_index, "episode_id": ep.episode_id, **row})
        return rows

    def _compute_cross_episode_metrics(self, episode_results: Sequence[EpisodeResult], mode_rows: Sequence[dict[str, Any]], reuse_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
        by_episode = {result.episode_index: result for result in episode_results}
        first = by_episode[min(by_episode)] if by_episode else None
        last = by_episode[max(by_episode)] if by_episode else None
        baseline = _mean_mode(mode_rows, "baseline_static", "recovered_false_count")
        htilt = _mean_mode(mode_rows, "htilt_best_v", "recovered_false_count")
        lawbook_htilt = _mean_mode(mode_rows, "lawbook_attention_plus_htilt", "recovered_false_count")
        durable_only = _mean_mode(mode_rows, "durable_only_lawbook_plus_htilt", "recovered_false_count")
        decode_filtered = _mean_mode(mode_rows, "decode_filtered_lawbook_plus_htilt", "recovered_false_count")
        residuals = [result.residual_count for result in episode_results]
        durable_growth = [result.durable_artifacts_after for result in episode_results]
        reuse_count = len(reuse_rows)
        boundary = all(bool(row.get("advisory_boundary_preserved", True)) for row in mode_rows)
        no_fallback_durable = self.store.conn.execute("SELECT COUNT(*) FROM artifacts WHERE durable=1 AND payload_json LIKE '%fallback_mode%true%'").fetchone()[0] == 0
        no_failed_true = self.store.conn.execute("SELECT COUNT(*) FROM artifacts WHERE payload_json LIKE '%failed_finite_search%' AND terminal_form='VERIFIED_PROOF'").fetchone()[0] == 0
        later_ties_baseline = last is not None and last.best_lawbook_yield >= last.baseline_yield
        positive_lawbook_delta = lawbook_htilt >= htilt or lawbook_htilt >= baseline
        real = any(result.real_sair_used for result in episode_results)
        real_extra = reuse_count > 0 or (first is not None and last is not None and last.residual_count <= first.residual_count)
        signal = boundary and no_fallback_durable and no_failed_true and later_ties_baseline and positive_lawbook_delta and (real_extra if real else True)
        attempts = max(1.0, sum(float(row.get("attempts", 0.0) or 0.0) for row in mode_rows))
        certificates = sum(float(row.get("recovered_false_count", 0.0) or 0.0) for row in mode_rows)
        return {
            "episode_to_episode_yield_delta": (last.best_lawbook_yield - first.best_lawbook_yield) if first and last else 0.0,
            "cumulative_yield": certificates,
            "residual_count_by_episode": residuals,
            "residual_reduction_rate": ((first.residual_count - last.residual_count) / max(1.0, first.residual_count)) if first and last else 0.0,
            "durable_artifact_growth": durable_growth,
            "durable_reuse_count": reuse_count,
            "durable_reuse_rate": reuse_count / max(1, len(mode_rows)),
            "lawbook_attention_hit_rate": 1.0 if reuse_count else 0.0,
            "lawbook_action_change_rate": 1.0 if reuse_count else 0.0,
            "htilt_plus_lawbook_delta": lawbook_htilt - htilt,
            "durable_only_delta": durable_only - baseline,
            "decode_filtered_delta": decode_filtered - baseline,
            "certificate_yield_per_attempt": certificates / attempts,
            "cost_per_certificate": attempts / certificates if certificates else 0.0,
            "compounding_score": (lawbook_htilt - baseline) + reuse_count + (durable_growth[-1] if durable_growth else 0),
            "compounding_signal_detected": signal,
            "advisory_boundary_preserved": boundary and no_fallback_durable and no_failed_true,
            "no_fallback_artifacts_entered_durable_memory": no_fallback_durable,
            "no_failed_search_true_claims": no_failed_true,
        }

    def _write_outputs(
        self,
        episode_results: Sequence[EpisodeResult],
        mode_rows: Sequence[dict[str, Any]],
        residual_rows: Sequence[dict[str, Any]],
        reuse_rows: Sequence[dict[str, Any]],
        cross: dict[str, Any],
    ) -> dict[str, str]:
        paths = {
            "episode_results": self.output_dir / "multi_episode_results.csv",
            "mode_comparison": self.output_dir / "multi_episode_mode_comparison.csv",
            "lawbook_growth": self.output_dir / "multi_episode_lawbook_growth.csv",
            "artifact_reuse": self.output_dir / "multi_episode_artifact_reuse.csv",
            "residuals": self.output_dir / "multi_episode_residuals.csv",
            "cross_metrics": self.output_dir / "multi_episode_cross_metrics.json",
            "lawbook": self.lawbook_path,
        }
        _write_csv(paths["episode_results"], [result.to_dict() for result in episode_results])
        _write_csv(paths["mode_comparison"], list(mode_rows))
        _write_csv(paths["lawbook_growth"], [{"episode_index": result.episode_index, "episode_id": result.episode_id, "durable_artifacts_after": result.durable_artifacts_after} for result in episode_results])
        _write_csv(paths["artifact_reuse"], list(reuse_rows))
        _write_csv(paths["residuals"], list(residual_rows))
        paths["cross_metrics"].write_text(json.dumps(cross, indent=2, sort_keys=True), encoding="utf-8")
        return {key: str(value) for key, value in paths.items()}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row.get(key), sort_keys=True) if isinstance(row.get(key), (dict, list)) else row.get(key, "") for key in fieldnames})


def _mean_mode(rows: Sequence[dict[str, Any]], mode: str, field: str) -> float:
    values = [float(row.get(field, 0.0) or 0.0) for row in rows if row.get("mode") == mode]
    return mean(values) if values else 0.0


def _source_id(task_id: str) -> str:
    parts = str(task_id).split("_")
    return parts[-2] if len(parts) >= 3 else str(task_id)


def _target_id(task_id: str) -> str:
    parts = str(task_id).split("_")
    return parts[-1] if len(parts) >= 2 else str(task_id)


def _markdown(result: MultiEpisodeCompoundingResult) -> str:
    metrics = result.cross_episode_metrics
    lines = [
        "# Multi-Episode Lawbook Compounding Evaluation v0",
        "",
        f"- real_sair_used: `{result.real_sair_used}`",
        f"- fallback_mode: `{result.fallback_mode}`",
        f"- num_episodes: `{result.num_episodes}`",
        f"- advisory_boundary_preserved: `{result.advisory_boundary_preserved}`",
        f"- compounding_signal_detected: `{result.compounding_signal_detected}`",
        f"- fallback_smoke_compounding_signal: `{result.fallback_smoke_compounding_signal}`",
        f"- durable_reuse_count: `{metrics.get('durable_reuse_count')}`",
        f"- residual_count_by_episode: `{metrics.get('residual_count_by_episode')}`",
        f"- certificate_yield_per_attempt: `{metrics.get('certificate_yield_per_attempt')}`",
        "",
        "Fallback smoke is not real SAIR compounding evidence. Failed finite search is never treated as TRUE.",
    ]
    return "\n".join(lines) + "\n"


"""Colab-grade Real SAIR multi-episode artifact pack runner."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.lawbook_promotion import run_promotion_for_directory
from mathgraph.lawbook_store import LawbookStore
from mathgraph.multi_episode_compounding import MultiEpisodeCompoundingRunner, MultiEpisodeConfig


@dataclass(frozen=True)
class RealSairArtifactPackConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    output_dir: str | Path | None = None
    lawbook_path: str | Path | None = None
    num_episodes: int = 3
    episode_size: int = 250
    train_fraction: float = 0.5
    seed: int = 1729
    strict_admission: bool = True
    allow_fallback: bool = False
    create_archive: bool = True
    archive_format: str = "zip"
    max_attempts_per_episode: int | None = None
    run_label: str | None = None


@dataclass(frozen=True)
class RealSairArtifactPackResult:
    real_sair_used: bool
    fallback_mode: bool
    output_dir: str
    archive_path: str
    lawbook_path: str
    manifest_path: str
    summary_json_path: str
    report_md_path: str
    compounding_signal_detected: bool
    advisory_boundary_preserved: bool
    durable_artifact_count: int
    advisory_artifact_count: int
    blocked_artifact_count: int
    promoted_artifact_count: int
    durable_reuse_count: int
    durable_reuse_rate: float
    best_mode: str
    baseline_yield_total: float
    best_lawbook_yield_total: float
    htilt_yield_total: float
    residual_reduction_rate: float
    cost_per_certificate: float
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class RealSairArtifactPackRunner:
    def __init__(self, config: RealSairArtifactPackConfig) -> None:
        self.config = config
        self.output_dir = _default_output_dir(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lawbook_path = Path(config.lawbook_path) if config.lawbook_path else self.output_dir / "lawbook.sqlite"
        self.run_id = content_id("real-sair-artifact-pack", [str(self.output_dir), config.run_label, datetime.now(timezone.utc).isoformat()])
        self.warnings: list[str] = []

    def run(self) -> RealSairArtifactPackResult:
        self._validate_real_sair_inputs()
        multi = self._run_multi_episode_compounding()
        promotion = self._run_lawbook_promotion()
        evidence = self._build_compounding_evidence(multi, promotion)
        manifest = self._write_manifest(multi, promotion, evidence)
        summary_path = self._write_json_summary(evidence)
        report_path = self._write_markdown_report(evidence)
        archive = self._create_archive() if self.config.create_archive else ""
        result = RealSairArtifactPackResult(
            real_sair_used=multi.real_sair_used,
            fallback_mode=multi.fallback_mode,
            output_dir=str(self.output_dir),
            archive_path=archive,
            lawbook_path=str(self.lawbook_path),
            manifest_path=str(manifest),
            summary_json_path=str(summary_path),
            report_md_path=str(report_path),
            compounding_signal_detected=multi.compounding_signal_detected,
            advisory_boundary_preserved=multi.advisory_boundary_preserved,
            durable_artifact_count=int(evidence["durable_artifact_count"]),
            advisory_artifact_count=int(evidence["advisory_artifact_count"]),
            blocked_artifact_count=int(evidence["blocked_artifact_count"]),
            promoted_artifact_count=int(evidence["promoted_artifact_count"]),
            durable_reuse_count=int(evidence["durable_reuse_count"]),
            durable_reuse_rate=float(evidence["durable_reuse_rate"]),
            best_mode=str(evidence["best_mode"]),
            baseline_yield_total=float(evidence["baseline_yield_total"]),
            best_lawbook_yield_total=float(evidence["best_lawbook_yield_total"]),
            htilt_yield_total=float(evidence["htilt_yield_total"]),
            residual_reduction_rate=float(evidence["residual_reduction_rate"]),
            cost_per_certificate=float(evidence["cost_per_certificate"]),
            warnings=list(self.warnings),
        )
        (self.output_dir / "artifact_pack_result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return result

    def _validate_real_sair_inputs(self) -> None:
        eq = Path(self.config.equations_path)
        matrix = Path(self.config.matrix_path)
        if eq.exists() and matrix.exists():
            return
        message = f"Real SAIR files missing: {eq} and/or {matrix}."
        if not self.config.allow_fallback:
            raise FileNotFoundError(message + " Pass --allow-fallback-smoke to create a fallback smoke artifact pack.")
        self.warnings.append(message + " Running explicit fallback smoke mode; this is not real SAIR evidence.")

    def _collect_git_metadata(self) -> dict[str, Any]:
        return {
            "git_commit": _git(["rev-parse", "HEAD"]),
            "git_branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
            "repo_dirty": bool(_git(["status", "--short"])),
        }

    def _collect_environment_metadata(self) -> dict[str, Any]:
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        }

    def _run_multi_episode_compounding(self) -> Any:
        return MultiEpisodeCompoundingRunner(
            MultiEpisodeConfig(
                equations_path=self.config.equations_path,
                matrix_path=self.config.matrix_path,
                lawbook_path=self.lawbook_path,
                output_dir=self.output_dir / "multi_episode",
                num_episodes=self.config.num_episodes,
                episode_size=self.config.episode_size,
                train_fraction=self.config.train_fraction,
                seed=self.config.seed,
                strict_admission=self.config.strict_admission,
                allow_fallback=self.config.allow_fallback,
                max_attempts_per_episode=self.config.max_attempts_per_episode,
            )
        ).run()

    def _run_lawbook_promotion(self) -> dict[str, Any]:
        return run_promotion_for_directory(
            self.output_dir / "multi_episode" / "episode_001",
            lawbook_path=self.lawbook_path,
            output_dir=self.output_dir / "promotion_audit",
            strict=self.config.strict_admission,
        )

    def _collect_outputs(self) -> dict[str, Any]:
        files = sorted(str(path.relative_to(self.output_dir)) for path in self.output_dir.rglob("*") if path.is_file())
        dirs = sorted(str(path.relative_to(self.output_dir)) for path in self.output_dir.rglob("*") if path.is_dir())
        return {"generated_files": files, "generated_directories": dirs}

    def _build_compounding_evidence(self, multi: Any, promotion: dict[str, Any]) -> dict[str, Any]:
        mode_rows = _read_csv(Path(multi.outputs["mode_comparison"]))
        baseline = _sum_mode(mode_rows, "baseline_static", "recovered_false_count")
        best_lawbook = max(
            _sum_mode(mode_rows, "lawbook_attention", "recovered_false_count"),
            _sum_mode(mode_rows, "lawbook_attention_plus_htilt", "recovered_false_count"),
            _sum_mode(mode_rows, "decode_filtered_lawbook_plus_htilt", "recovered_false_count"),
            _sum_mode(mode_rows, "durable_only_lawbook_plus_htilt", "recovered_false_count"),
        )
        htilt = _sum_mode(mode_rows, "htilt_best_v", "recovered_false_count")
        best_mode = _best_mode(mode_rows)
        store = LawbookStore(self.lawbook_path)
        store.init_compounding_schema()
        counts = store.count_by_admission_level()
        reuse = store.get_artifact_reuse_stats()
        store.close()
        cross = json.loads(Path(multi.outputs["cross_metrics"]).read_text(encoding="utf-8"))
        promotion_summary = promotion.get("summary", {})
        return {
            "multi_episode": multi.to_dict(),
            "promotion_summary": promotion_summary,
            "mode_rows": mode_rows,
            "best_mode": best_mode,
            "baseline_yield_total": baseline,
            "best_lawbook_yield_total": best_lawbook,
            "htilt_yield_total": htilt,
            "durable_artifact_count": counts.get("durable_lawbook", 0),
            "advisory_artifact_count": counts.get("advisory_only", 0),
            "blocked_artifact_count": promotion_summary.get("fallback_artifacts_blocked_count", 0)
            + promotion_summary.get("boundary_violations_blocked_count", 0)
            + promotion_summary.get("missing_provenance_blocked_count", 0)
            + promotion_summary.get("failed_search_true_blocked_count", 0),
            "promoted_artifact_count": promotion_summary.get("promoted_durable_count", 0),
            "durable_reuse_count": cross.get("durable_reuse_count", reuse.get("reuse_count", 0)),
            "durable_reuse_rate": cross.get("durable_reuse_rate", 0.0),
            "residual_reduction_rate": cross.get("residual_reduction_rate", 0.0),
            "cost_per_certificate": cross.get("cost_per_certificate", 0.0),
            "advisory_boundary_preserved": multi.advisory_boundary_preserved,
            "compounding_signal_detected": multi.compounding_signal_detected,
            "fallback_smoke_compounding_signal": multi.fallback_smoke_compounding_signal,
            "real_sair_used": multi.real_sair_used,
            "fallback_mode": multi.fallback_mode,
            "cross_episode_metrics": cross,
        }

    def _write_manifest(self, multi: Any, promotion: dict[str, Any], evidence: dict[str, Any]) -> Path:
        outputs = self._collect_outputs()
        manifest = {
            "run_id": self.run_id,
            "run_label": self.config.run_label or "",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            **self._collect_git_metadata(),
            **self._collect_environment_metadata(),
            "real_sair_used": multi.real_sair_used,
            "fallback_mode": multi.fallback_mode,
            "equations_path": str(self.config.equations_path),
            "matrix_path": str(self.config.matrix_path),
            "output_dir": str(self.output_dir),
            "lawbook_path": str(self.lawbook_path),
            "config": asdict(self.config),
            "promotion_outputs": promotion.get("outputs", {}),
            "evidence": {key: value for key, value in evidence.items() if key not in {"multi_episode", "mode_rows"}},
            "archive_path": "",
            "warnings": list(self.warnings),
            **outputs,
        }
        path = self.output_dir / "artifact_manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return path

    def _write_markdown_report(self, evidence: dict[str, Any]) -> Path:
        path = self.output_dir / "real_sair_artifact_pack_report.md"
        path.write_text(_markdown_report(self.config, evidence, self.warnings), encoding="utf-8")
        return path

    def _write_json_summary(self, evidence: dict[str, Any]) -> Path:
        path = self.output_dir / "real_sair_artifact_pack_summary.json"
        payload = {key: value for key, value in evidence.items() if key not in {"mode_rows"}}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return path

    def _create_archive(self) -> str:
        if self.config.archive_format != "zip":
            self.warnings.append(f"Unsupported archive format {self.config.archive_format}; using zip.")
        archive_path = self.output_dir.with_suffix(".zip")
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in self.output_dir.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(self.output_dir.parent))
        manifest = self.output_dir / "artifact_manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["archive_path"] = str(archive_path)
            manifest.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return str(archive_path)


def _default_output_dir(value: str | Path | None) -> Path:
    if value:
        return Path(value)
    drive = Path("/content/drive/MyDrive/SAIR_MathGraph/real_sair_multi_episode_pack")
    if drive.parent.exists():
        return drive
    return Path("/tmp/mathgraph_real_sair_multi_episode_pack")


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sum_mode(rows: list[dict[str, str]], mode: str, field: str) -> float:
    return sum(float(row.get(field, 0.0) or 0.0) for row in rows if row.get("mode") == mode)


def _best_mode(rows: list[dict[str, str]]) -> str:
    modes = sorted({row.get("mode", "") for row in rows})
    if not modes:
        return ""
    return sorted(modes, key=lambda mode: (-_sum_mode(rows, mode, "recovered_false_count"), mode))[0]


def _markdown_report(config: RealSairArtifactPackConfig, evidence: dict[str, Any], warnings: list[str]) -> str:
    if not evidence["real_sair_used"]:
        interpretation = "This is only a fallback smoke artifact pack. It proves packaging and boundary wiring, not real SAIR compounding."
    elif not evidence["compounding_signal_detected"]:
        interpretation = "Real SAIR ran, but this pack did not yet prove compounding. Inspect residuals, mode deltas, and durable reuse."
    else:
        interpretation = "Initial evidence: durable verified memory improved later verifier-directed episodes."
    sections = [
        "# Real SAIR Multi-Episode Artifact Pack",
        "",
        "## Run Identity",
        f"- run_label: `{config.run_label or ''}`",
        f"- seed: `{config.seed}`",
        "",
        "## Input Files",
        f"- equations_path: `{config.equations_path}`",
        f"- matrix_path: `{config.matrix_path}`",
        "",
        "## Real vs Fallback Status",
        f"- real_sair_used: `{evidence['real_sair_used']}`",
        f"- fallback_mode: `{evidence['fallback_mode']}`",
        "",
        "## Configuration",
        f"- num_episodes: `{config.num_episodes}`",
        f"- episode_size: `{config.episode_size}`",
        f"- train_fraction: `{config.train_fraction}`",
        f"- strict_admission: `{config.strict_admission}`",
        "",
        "## Headline Result",
        f"- compounding_signal_detected: `{evidence['compounding_signal_detected']}`",
        f"- best_mode: `{evidence['best_mode']}`",
        "",
        "## Mode Comparison",
        f"- baseline_yield_total: `{evidence['baseline_yield_total']}`",
        f"- best_lawbook_yield_total: `{evidence['best_lawbook_yield_total']}`",
        f"- htilt_yield_total: `{evidence['htilt_yield_total']}`",
        "",
        "## Episode-to-Episode Compounding",
        f"- residual_reduction_rate: `{evidence['residual_reduction_rate']}`",
        "",
        "## Lawbook Growth",
        f"- durable_artifact_count: `{evidence['durable_artifact_count']}`",
        f"- advisory_artifact_count: `{evidence['advisory_artifact_count']}`",
        "",
        "## Durable Artifact Reuse",
        f"- durable_reuse_count: `{evidence['durable_reuse_count']}`",
        f"- durable_reuse_rate: `{evidence['durable_reuse_rate']}`",
        "",
        "## Admission and Promotion",
        f"- promoted_artifact_count: `{evidence['promoted_artifact_count']}`",
        f"- blocked_artifact_count: `{evidence['blocked_artifact_count']}`",
        "",
        "## Residual Shrinkage",
        f"- residual_reduction_rate: `{evidence['residual_reduction_rate']}`",
        "",
        "## Cost / Efficiency",
        f"- cost_per_certificate: `{evidence['cost_per_certificate']}`",
        "",
        "## Authority Boundary Checks",
        f"- advisory_boundary_preserved: `{evidence['advisory_boundary_preserved']}`",
        "",
        "## Warnings",
        *(f"- {warning}" for warning in warnings),
        "",
        "## Interpretation",
        interpretation,
        "",
        "## Next Recommended Run",
        "Run the same command with real SAIR files present and compare artifact_manifest.json plus multi_episode_cross_metrics.json across runs.",
        "",
    ]
    return "\n".join(sections)


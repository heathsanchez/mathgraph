"""Materialize external MathGraph assets into a stable local bundle."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.asset_discovery import (
    validate_equations_file,
    validate_matrix_file,
    validate_traces_json,
)


SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".lake",
    "lake-packages",
    "build",
    "dist",
}

ASSETS = {
    "traces_json": {
        "filename": "traces.json",
        "target": "traces.json",
    },
    "equations_path": {
        "filename": "equations.txt",
        "target": "equations.txt",
    },
    "matrix_path": {
        "filename": "etp_matrix_full_best_bool.npy",
        "target": "etp_matrix_full_best_bool.npy",
    },
}

RELATED_FILENAMES = {"routelean_results_v19_1.parquet"}


@dataclass(frozen=True)
class AssetMaterializationConfig:
    out_dir: str
    traces_json: str | None = None
    equations_path: str | None = None
    matrix_path: str | None = None
    mode: str = "copy"
    search_roots: list[str] = field(default_factory=list)
    max_depth: int = 6
    max_files: int = 20000
    hash_limit_bytes: int = 256 * 1024 * 1024

    def to_dict(self) -> dict[str, Any]:
        return {
            "out_dir": self.out_dir,
            "traces_json": self.traces_json,
            "equations_path": self.equations_path,
            "matrix_path": self.matrix_path,
            "mode": self.mode,
            "search_roots": list(self.search_roots),
            "max_depth": self.max_depth,
            "max_files": self.max_files,
            "hash_limit_bytes": self.hash_limit_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetMaterializationConfig":
        return cls(
            out_dir=str(data["out_dir"]),
            traces_json=data.get("traces_json"),
            equations_path=data.get("equations_path"),
            matrix_path=data.get("matrix_path"),
            mode=str(data.get("mode", "copy")),
            search_roots=[str(item) for item in data.get("search_roots", [])],
            max_depth=int(data.get("max_depth", 6)),
            max_files=int(data.get("max_files", 20000)),
            hash_limit_bytes=int(data.get("hash_limit_bytes", 256 * 1024 * 1024)),
        )


@dataclass(frozen=True)
class AssetMaterializationResult:
    ok: bool
    complete: bool
    missing_assets: list[str]
    selected_assets: dict[str, dict[str, Any] | None]
    materialized_assets: dict[str, str | None]
    candidates: dict[str, list[dict[str, Any]]]
    related_artifacts: list[dict[str, Any]]
    warnings: list[str]
    outputs: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "complete": self.complete,
            "missing_assets": list(self.missing_assets),
            "selected_assets": dict(self.selected_assets),
            "materialized_assets": dict(self.materialized_assets),
            "candidates": {key: list(value) for key, value in self.candidates.items()},
            "related_artifacts": list(self.related_artifacts),
            "warnings": list(self.warnings),
            "outputs": dict(self.outputs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetMaterializationResult":
        return cls(
            ok=bool(data.get("ok", False)),
            complete=bool(data.get("complete", False)),
            missing_assets=[str(item) for item in data.get("missing_assets", [])],
            selected_assets=dict(data.get("selected_assets", {})),
            materialized_assets=dict(data.get("materialized_assets", {})),
            candidates={str(key): list(value) for key, value in dict(data.get("candidates", {})).items()},
            related_artifacts=list(data.get("related_artifacts", [])),
            warnings=[str(item) for item in data.get("warnings", [])],
            outputs=dict(data.get("outputs", {})),
        )


def materialize_mathgraph_assets(
    config: AssetMaterializationConfig | dict[str, Any],
) -> AssetMaterializationResult:
    config = config if isinstance(config, AssetMaterializationConfig) else AssetMaterializationConfig.from_dict(config)
    if config.mode not in {"copy", "symlink", "manifest-only"}:
        raise ValueError("mode must be one of: copy, symlink, manifest-only")

    out_dir = Path(config.out_dir)
    assets_dir = out_dir / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    if config.mode != "manifest-only":
        assets_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    candidates = _collect_candidates(config, warnings)
    selected = {kind: _select_candidate(kind, rows) for kind, rows in candidates.items()}
    related = _discover_related_artifacts(config, warnings)
    materialized: dict[str, str | None] = {}

    for kind, row in selected.items():
        if row is None:
            materialized[kind] = None
            continue
        if config.mode == "manifest-only":
            materialized[kind] = None
            continue
        target = assets_dir / ASSETS[kind]["target"]
        materialized[kind] = _materialize_one(Path(row["path"]), target, config.mode, warnings)

    missing = [kind for kind, row in selected.items() if row is None]
    complete = not missing
    outputs = {
        "summary_json": str(out_dir / "asset_materialization_summary.json"),
        "report_md": str(out_dir / "asset_materialization_report.md"),
    }
    result = AssetMaterializationResult(
        ok=True,
        complete=complete,
        missing_assets=missing,
        selected_assets=selected,
        materialized_assets=materialized,
        candidates=candidates,
        related_artifacts=related,
        warnings=warnings,
        outputs=outputs,
    )
    _write_json(result.to_dict(), outputs["summary_json"])
    _write_report(result, outputs["report_md"])
    return result


def _collect_candidates(
    config: AssetMaterializationConfig, warnings: list[str]
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {kind: [] for kind in ASSETS}
    explicit = {
        "traces_json": config.traces_json,
        "equations_path": config.equations_path,
        "matrix_path": config.matrix_path,
    }
    for kind, value in explicit.items():
        if value:
            rows[kind].append(_candidate(kind, Path(value), source="explicit", config=config))

    scanned = 0
    for root in _search_roots(config):
        if not root.exists():
            continue
        for current, dirs, files in os.walk(root):
            dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
            current_path = Path(current)
            try:
                depth = len(current_path.relative_to(root).parts)
            except ValueError:
                depth = 0
            if depth >= config.max_depth:
                dirs[:] = []
            for filename in files:
                scanned += 1
                if scanned > config.max_files:
                    warnings.append(f"Stopped asset scan after max_files={config.max_files}.")
                    return _dedupe_candidates(rows)
                for kind, meta in ASSETS.items():
                    if filename == meta["filename"]:
                        rows[kind].append(_candidate(kind, current_path / filename, source="search", config=config))
    return _dedupe_candidates(rows)


def _discover_related_artifacts(
    config: AssetMaterializationConfig, warnings: list[str]
) -> list[dict[str, Any]]:
    related: list[dict[str, Any]] = []
    scanned = 0
    for root in _search_roots(config):
        if not root.exists():
            continue
        for current, dirs, files in os.walk(root):
            dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
            current_path = Path(current)
            try:
                depth = len(current_path.relative_to(root).parts)
            except ValueError:
                depth = 0
            if depth >= config.max_depth:
                dirs[:] = []
            for filename in files:
                scanned += 1
                if scanned > config.max_files:
                    warnings.append(f"Stopped related artifact scan after max_files={config.max_files}.")
                    return related
                if filename in RELATED_FILENAMES or (filename.endswith(".parquet") and "routelean" in filename):
                    related.append(
                        _file_record(
                            path=current_path / filename,
                            kind="related_routelean_results",
                            reason="related parquet result artifact; not a traces.json",
                            config=config,
                        )
                    )
    return related


def _candidate(kind: str, path: Path, source: str, config: AssetMaterializationConfig) -> dict[str, Any]:
    record = _file_record(path, kind=kind, reason=source, config=config)
    validation = _validate(kind, path)
    record["validation"] = validation
    record["priority_score"] = _priority(kind, source, validation)
    record["selected_filename"] = ASSETS[kind]["target"]
    return record


def _file_record(path: Path, kind: str, reason: str, config: AssetMaterializationConfig) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    sha_prefix = None
    hash_skipped = False
    if exists and path.is_file() and size <= config.hash_limit_bytes:
        sha_prefix = _sha256_prefix(path)
    elif exists and path.is_file():
        hash_skipped = True
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": size,
        "sha256_prefix": sha_prefix,
        "hash_skipped": hash_skipped,
        "kind": kind,
        "reason": reason,
    }


def _validate(kind: str, path: Path) -> dict[str, Any]:
    if kind == "traces_json":
        return validate_traces_json(path)
    if kind == "equations_path":
        return validate_equations_file(path)
    if kind == "matrix_path":
        return validate_matrix_file(path)
    return {}


def _priority(kind: str, source: str, validation: dict[str, Any]) -> float:
    score = 1000.0 if source == "explicit" else 0.0
    if validation.get("exists"):
        score += 10.0
    if validation.get("readable"):
        score += 5.0
    if validation.get("valid"):
        score += 20.0
    if kind == "traces_json":
        score += min(float(validation.get("trace_count", 0)), 10000.0) / 100.0
    elif kind == "equations_path":
        count = int(validation.get("equation_count", 0))
        score += max(0.0, 20.0 - abs(count - 4694) / 234.7) if count else 0.0
    elif kind == "matrix_path":
        shape = validation.get("shape") or []
        if len(shape) == 2:
            score += max(0.0, 20.0 - (abs(shape[0] - 4694) + abs(shape[1] - 4694)) / 234.7)
    return score


def _select_candidate(kind: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    usable = [row for row in rows if row.get("exists") and row.get("validation", {}).get("valid")]
    if not usable:
        return None
    return sorted(usable, key=lambda row: (-float(row["priority_score"]), row["path"]))[0]


def _materialize_one(source: Path, target: Path, mode: str, warnings: list[str]) -> str:
    if target.exists() or target.is_symlink():
        target.unlink()
    if mode == "symlink":
        try:
            target.symlink_to(source)
            return str(target)
        except OSError as exc:
            warnings.append(f"Symlink failed for {source}; fell back to copy: {exc}")
    shutil.copy2(source, target)
    return str(target)


def _search_roots(config: AssetMaterializationConfig) -> list[Path]:
    roots = [Path(path).resolve() for path in config.search_roots]
    seen = set()
    unique = []
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def default_search_roots(repo_root: str | Path | None = None) -> list[str]:
    roots = [
        Path("/content"),
        Path("/content/drive/MyDrive"),
        Path("/mnt/data"),
        Path.cwd(),
    ]
    if repo_root is not None:
        roots.append(Path(repo_root))
    return [str(root) for root in roots if root.exists()]


def _dedupe_candidates(rows: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    deduped: dict[str, list[dict[str, Any]]] = {}
    for kind, candidates in rows.items():
        seen = set()
        deduped[kind] = []
        for row in candidates:
            path = row["path"]
            if path in seen:
                continue
            seen.add(path)
            deduped[kind].append(row)
    return deduped


def _sha256_prefix(path: Path, n: int = 16) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:n]


def _write_json(payload: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_report(result: AssetMaterializationResult, path: str | Path) -> None:
    lines = [
        "# MathGraph Asset Materialization Report",
        "",
        f"- ok: `{result.ok}`",
        f"- complete: `{result.complete}`",
        f"- missing_assets: `{result.missing_assets}`",
        "",
        "## Selected Assets",
    ]
    for kind, row in result.selected_assets.items():
        lines.append(f"- {kind}: `{row.get('path') if row else None}`")
    lines.extend(["", "## Materialized Assets"])
    for kind, path_text in result.materialized_assets.items():
        lines.append(f"- {kind}: `{path_text}`")
    lines.extend(["", "Related routelean parquet artifacts are reported as related artifacts, not selected traces."])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")

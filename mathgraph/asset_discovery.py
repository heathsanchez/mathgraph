"""Discovery and validation helpers for external MathGraph assets."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_TRACES_CANDIDATES = [
    "/content/drive/MyDrive/MathGraphKernel/github_imports/repo_cli_v19_1_artifact_provenance_fixed/traces.json",
    "/content/drive/MyDrive/MathGraphKernel/github_imports/repo_cli_v19_1_artifact_backed/traces.json",
    "/content/drive/MyDrive/MathGraphKernel/github_imports/repo_cli_v19_1_lawbook/traces.json",
    "/content/drive/MyDrive/MathGraphKernel/lean_kernel_v19_1/latest/traces.json",
]

DEFAULT_EQUATIONS_CANDIDATES = [
    "/content/equations.txt",
    "/content/drive/MyDrive/MathGraphKernel/core/equations.txt",
    "/content/drive/MyDrive/SAIR_MathGraph/equations.txt",
]

DEFAULT_MATRIX_CANDIDATES = [
    "/content/etp_matrix_full_best_bool.npy",
    "/content/drive/MyDrive/MathGraphKernel/core/etp_matrix_full_best_bool.npy",
    "/content/drive/MyDrive/SAIR_MathGraph/etp_matrix_full_best_bool.npy",
]

DEFAULT_SEARCH_ROOTS = [
    "/content/drive/MyDrive/MathGraphKernel",
    "/content/drive/MyDrive/SAIR_MathGraph",
    "/content",
]


@dataclass(frozen=True)
class AssetCandidate:
    asset_type: str
    path: str
    source: str
    exists: bool
    readable: bool
    validation: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_type": self.asset_type,
            "path": self.path,
            "source": self.source,
            "exists": self.exists,
            "readable": self.readable,
            "validation": dict(self.validation),
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetCandidate":
        return cls(
            asset_type=str(data["asset_type"]),
            path=str(data["path"]),
            source=str(data.get("source", "")),
            exists=bool(data.get("exists", False)),
            readable=bool(data.get("readable", False)),
            validation=dict(data.get("validation", {})),
            score=float(data.get("score", 0.0)),
        )


@dataclass(frozen=True)
class AssetDiscoveryConfig:
    traces_candidates: list[str] = field(default_factory=lambda: list(DEFAULT_TRACES_CANDIDATES))
    equations_candidates: list[str] = field(default_factory=lambda: list(DEFAULT_EQUATIONS_CANDIDATES))
    matrix_candidates: list[str] = field(default_factory=lambda: list(DEFAULT_MATRIX_CANDIDATES))
    search_roots: list[str] = field(default_factory=lambda: list(DEFAULT_SEARCH_ROOTS))
    max_depth: int = 4
    max_files: int = 5000

    def to_dict(self) -> dict[str, Any]:
        return {
            "traces_candidates": list(self.traces_candidates),
            "equations_candidates": list(self.equations_candidates),
            "matrix_candidates": list(self.matrix_candidates),
            "search_roots": list(self.search_roots),
            "max_depth": self.max_depth,
            "max_files": self.max_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetDiscoveryConfig":
        return cls(
            traces_candidates=[str(item) for item in data.get("traces_candidates", DEFAULT_TRACES_CANDIDATES)],
            equations_candidates=[str(item) for item in data.get("equations_candidates", DEFAULT_EQUATIONS_CANDIDATES)],
            matrix_candidates=[str(item) for item in data.get("matrix_candidates", DEFAULT_MATRIX_CANDIDATES)],
            search_roots=[str(item) for item in data.get("search_roots", DEFAULT_SEARCH_ROOTS)],
            max_depth=int(data.get("max_depth", 4)),
            max_files=int(data.get("max_files", 5000)),
        )


@dataclass(frozen=True)
class AssetDiscoveryResult:
    candidates: dict[str, list[dict[str, Any]]]
    selected: dict[str, dict[str, Any] | None]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": {key: list(value) for key, value in self.candidates.items()},
            "selected": dict(self.selected),
            "summary": dict(self.summary),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetDiscoveryResult":
        return cls(
            candidates={str(key): list(value) for key, value in dict(data.get("candidates", {})).items()},
            selected=dict(data.get("selected", {})),
            summary=dict(data.get("summary", {})),
            warnings=[str(item) for item in data.get("warnings", [])],
        )


def discover_mathgraph_assets(
    config: AssetDiscoveryConfig | dict[str, Any] | None = None,
) -> AssetDiscoveryResult:
    config = _coerce_config(config)
    warnings: list[str] = []
    paths = {
        "traces_json": _ordered_paths(config.traces_candidates),
        "equations": _ordered_paths(config.equations_candidates),
        "matrix": _ordered_paths(config.matrix_candidates),
    }
    found = _shallow_search(config, warnings)
    for key, values in found.items():
        paths[key].extend(path for path in values if path not in paths[key])

    candidates = {
        "traces_json": [_candidate("traces_json", path, "candidate_or_search") for path in paths["traces_json"]],
        "equations": [_candidate("equations", path, "candidate_or_search") for path in paths["equations"]],
        "matrix": [_candidate("matrix", path, "candidate_or_search") for path in paths["matrix"]],
    }
    selected = {key: _select_best(items) for key, items in candidates.items()}
    summary = {
        "traces_json_found": selected["traces_json"] is not None,
        "equations_found": selected["equations"] is not None,
        "matrix_found": selected["matrix"] is not None,
        "candidate_counts": {key: len(value) for key, value in candidates.items()},
        "selected_paths": {
            key: (value.path if value is not None else None) for key, value in selected.items()
        },
    }
    return AssetDiscoveryResult(
        candidates={key: [item.to_dict() for item in value] for key, value in candidates.items()},
        selected={key: (value.to_dict() if value is not None else None) for key, value in selected.items()},
        summary=summary,
        warnings=warnings,
    )


def validate_traces_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    base = _base_validation(path)
    if not base["exists"] or not base["readable"]:
        return {**base, "valid": False, "validation_status": "missing_or_unreadable"}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        rows = _trace_rows(data)
        terminal_counts = Counter(_terminal_form(row) for row in rows if _terminal_form(row))
        return {
            **base,
            "valid": bool(rows),
            "validation_status": "ok" if rows else "no_trace_rows",
            "trace_count": len(rows),
            "terminal_form_counts": dict(terminal_counts),
            "container_type": type(data).__name__,
        }
    except Exception as exc:
        return {**base, "valid": False, "validation_status": "error", "error": str(exc)}


def validate_equations_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    base = _base_validation(path)
    if not base["exists"] or not base["readable"]:
        return {**base, "valid": False, "validation_status": "missing_or_unreadable"}
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return {
            **base,
            "valid": bool(lines),
            "validation_status": "ok" if lines else "empty",
            "equation_count": len(lines),
            "sample": lines[:3],
        }
    except Exception as exc:
        return {**base, "valid": False, "validation_status": "error", "error": str(exc)}


def validate_matrix_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    base = _base_validation(path)
    if not base["exists"] or not base["readable"]:
        return {
            **base,
            "valid": False,
            "matrix_exists": base["exists"],
            "matrix_validation_status": "missing_or_unreadable",
        }
    try:
        import numpy as np  # type: ignore

        matrix = np.load(path, mmap_mode="r")
        shape = tuple(int(value) for value in getattr(matrix, "shape", ()))
        dtype = str(getattr(matrix, "dtype", "unknown"))
        mean = None
        if shape and len(shape) == 2 and shape[0] * shape[1] <= 1_000_000:
            mean = float(np.asarray(matrix).mean())
        return {
            **base,
            "valid": len(shape) == 2,
            "matrix_exists": True,
            "matrix_validation_status": "ok",
            "shape": list(shape),
            "dtype": dtype,
            "mean": mean,
        }
    except ImportError:
        return {
            **base,
            "valid": True,
            "matrix_exists": True,
            "matrix_validation_status": "numpy_unavailable",
        }
    except Exception as exc:
        return {
            **base,
            "valid": False,
            "matrix_exists": True,
            "matrix_validation_status": "error",
            "error": str(exc),
        }


def materialize_assets(
    result: AssetDiscoveryResult | dict[str, Any],
    out_dir: str | Path,
    copy: bool = False,
    symlink: bool = False,
) -> dict[str, Any]:
    result = result if isinstance(result, AssetDiscoveryResult) else AssetDiscoveryResult.from_dict(result)
    out = Path(out_dir) / "assets"
    out.mkdir(parents=True, exist_ok=True)
    materialized: dict[str, Any] = {}
    if not copy and not symlink:
        return {
            key: (value["path"] if value else None) for key, value in result.selected.items()
        }
    for key, selected in result.selected.items():
        if not selected:
            materialized[key] = None
            continue
        source = Path(str(selected["path"]))
        target = out / _asset_filename(key)
        if target.exists() or target.is_symlink():
            target.unlink()
        if symlink:
            target.symlink_to(source)
        elif copy:
            shutil.copy2(source, target)
        materialized[key] = str(target)
    return materialized


def _candidate(asset_type: str, path: str, source: str) -> AssetCandidate:
    if asset_type == "traces_json":
        validation = validate_traces_json(path)
    elif asset_type == "equations":
        validation = validate_equations_file(path)
    else:
        validation = validate_matrix_file(path)
    return AssetCandidate(
        asset_type=asset_type,
        path=str(path),
        source=source,
        exists=bool(validation.get("exists")),
        readable=bool(validation.get("readable")),
        validation=validation,
        score=_score(asset_type, validation),
    )


def _score(asset_type: str, validation: dict[str, Any]) -> float:
    score = 0.0
    if validation.get("exists"):
        score += 10.0
    if validation.get("readable"):
        score += 5.0
    if validation.get("valid"):
        score += 20.0
    if asset_type == "traces_json":
        score += min(float(validation.get("trace_count", 0)) / 1000.0, 10.0)
    elif asset_type == "equations":
        count = int(validation.get("equation_count", 0))
        score += max(0.0, 10.0 - abs(count - 4694) / 469.4) if count else 0.0
    elif asset_type == "matrix":
        shape = validation.get("shape") or []
        if len(shape) == 2:
            score += max(0.0, 10.0 - (abs(shape[0] - 4694) + abs(shape[1] - 4694)) / 469.4)
    return score


def _select_best(candidates: list[AssetCandidate]) -> AssetCandidate | None:
    valid = [item for item in candidates if item.exists and item.readable and item.validation.get("valid")]
    if not valid:
        return None
    return sorted(valid, key=lambda item: (-item.score, item.path))[0]


def _base_validation(path: Path) -> dict[str, Any]:
    exists = path.exists()
    readable = exists and os.access(path, os.R_OK)
    return {
        "path": str(path),
        "exists": exists,
        "readable": readable,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": _sha256_file(path) if exists and readable and path.is_file() else None,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _trace_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("traces", "records", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "trace" in data and isinstance(data["trace"], dict):
            return [data["trace"]]
    return []


def _terminal_form(row: dict[str, Any]) -> str | None:
    value = row.get("terminal_form")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("value") or value.get("name")
    return None


def _ordered_paths(paths: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _shallow_search(config: AssetDiscoveryConfig, warnings: list[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {"traces_json": [], "equations": [], "matrix": []}
    scanned = 0
    targets = {
        "traces.json": "traces_json",
        "equations.txt": "equations",
        "etp_matrix_full_best_bool.npy": "matrix",
    }
    for root_text in config.search_roots:
        root = Path(root_text)
        if not root.exists():
            continue
        try:
            for current, dirs, files in os.walk(root):
                current_path = Path(current)
                depth = len(current_path.relative_to(root).parts)
                if depth >= config.max_depth:
                    dirs[:] = []
                for filename in files:
                    scanned += 1
                    if scanned > config.max_files:
                        warnings.append(f"Stopped asset search after max_files={config.max_files}.")
                        return found
                    asset_type = targets.get(filename)
                    if asset_type:
                        found[asset_type].append(str(current_path / filename))
        except Exception as exc:
            warnings.append(f"Could not search {root}: {exc}")
    return found


def _asset_filename(asset_type: str) -> str:
    return {
        "traces_json": "traces.json",
        "equations": "equations.txt",
        "matrix": "etp_matrix_full_best_bool.npy",
    }.get(asset_type, asset_type)


def _coerce_config(config: AssetDiscoveryConfig | dict[str, Any] | None) -> AssetDiscoveryConfig:
    if config is None:
        return AssetDiscoveryConfig()
    return config if isinstance(config, AssetDiscoveryConfig) else AssetDiscoveryConfig.from_dict(config)

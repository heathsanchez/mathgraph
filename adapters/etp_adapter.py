"""Lightweight ETP asset helpers.

The adapter loads local equation/matrix assets when the caller supplies paths.
Generated ETP data stays outside git; this module contains source code only.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from mathgraph.certificates import Certificate, named_obstruction


def _require_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "ETP matrix loading requires numpy. Install numpy in your local environment "
            "or call only equation/text helpers."
        ) from exc
    return np


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_equations(path: str | Path) -> list[str]:
    """Load non-empty ETP equation lines from a local text file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def load_matrix(path: str | Path) -> Any:
    """Load an ETP matrix with numpy from a local path."""

    np = _require_numpy()
    return np.load(Path(path), allow_pickle=False)


def summarize_assets(equations_path: str | Path, matrix_path: str | Path) -> dict[str, Any]:
    """Summarize local ETP equation and matrix assets without storing outputs."""

    np = _require_numpy()
    equations = load_equations(equations_path)
    matrix = load_matrix(matrix_path)
    bool_matrix = matrix.astype(bool, copy=False)
    true_total = int(np.count_nonzero(bool_matrix))
    false_total = int(bool_matrix.size - true_total)
    true_rate = true_total / bool_matrix.size if bool_matrix.size else 0.0

    return {
        "n_equations": len(equations),
        "matrix_shape": tuple(int(dim) for dim in matrix.shape),
        "true_total": true_total,
        "false_total": false_total,
        "true_rate": true_rate,
        "sha256": {
            "equations": sha256_file(equations_path),
            "matrix": sha256_file(matrix_path),
        },
    }


def sample_false_pairs(matrix: Any, limit: int = 10, seed: int | None = 0) -> list[tuple[int, int]]:
    """Return source/target index pairs where the ETP matrix is false."""

    if limit < 0:
        raise ValueError("limit must be non-negative")

    np = _require_numpy()
    bool_matrix = matrix.astype(bool, copy=False)
    false_indices = np.argwhere(~bool_matrix)
    rng = np.random.default_rng(seed)
    if len(false_indices) > 0:
        rng.shuffle(false_indices)
    return [tuple(int(value) for value in pair) for pair in false_indices[:limit]]


def unavailable(claim: str) -> Certificate:
    return named_obstruction(claim, "ETP_ADAPTER_NOT_CONFIGURED")

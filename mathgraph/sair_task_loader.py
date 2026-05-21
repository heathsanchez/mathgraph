"""Load SAIR-style equation implication tasks for the breakthrough loop."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from mathgraph.breakthrough_loop import BreakthroughTask
from mathgraph.finite_magma_world import parse_equation


@dataclass(frozen=True)
class SAIRTaskLoadConfig:
    equations_path: str | Path = "/content/equations.txt"
    matrix_path: str | Path = "/content/etp_matrix_full_best_bool.npy"
    max_tasks: int = 100
    random_seed: int = 1729
    source_row_ids: tuple[int, ...] = ()
    false_only: bool = True
    include_true_controls: bool = False


@dataclass(frozen=True)
class LoadedSAIRTask:
    task_id: str
    eq1_id: int
    eq2_id: int
    equation1: str
    equation2: str
    normalized_equation1: str
    normalized_equation2: str
    expected_matrix_label: bool
    family: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_breakthrough_task(self) -> BreakthroughTask:
        return BreakthroughTask(
            task_id=self.task_id,
            source_equation=self.normalized_equation1,
            target_equation=self.normalized_equation2,
            family=self.family,
            metadata={
                "eq1_id": self.eq1_id,
                "eq2_id": self.eq2_id,
                "equation1": self.equation1,
                "equation2": self.equation2,
                "expected_matrix_label": self.expected_matrix_label,
                **dict(self.metadata),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "eq1_id": self.eq1_id,
            "eq2_id": self.eq2_id,
            "equation1": self.equation1,
            "equation2": self.equation2,
            "normalized_equation1": self.normalized_equation1,
            "normalized_equation2": self.normalized_equation2,
            "expected_matrix_label": self.expected_matrix_label,
            "family": self.family,
            "metadata": dict(self.metadata),
        }


def normalize_sair_equation(text: str) -> str:
    s = text.strip()
    s = s.replace("◇", "*").replace("⋄", "*").replace("·", "*").replace("∙", "*")
    s = s.replace("=", " = ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_sair_equations(path: str | Path) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        normalized = normalize_sair_equation(line)
        try:
            parse_equation(normalized)
        except Exception:
            continue
        out.append(normalized)
    return out


def load_sair_matrix(path: str | Path) -> Any | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        import numpy as np  # type: ignore

        return np.load(p, mmap_mode="r")
    except Exception:
        return None


def make_sair_false_tasks(
    equations: Sequence[str],
    matrix: Any,
    *,
    max_tasks: int = 100,
    random_seed: int = 1729,
    source_row_ids: Sequence[int] = (),
    include_true_controls: bool = False,
) -> list[LoadedSAIRTask]:
    if not equations or matrix is None:
        return []
    n = min(len(equations), int(matrix.shape[0]), int(matrix.shape[1]))
    rows = [int(i) for i in source_row_ids if 0 <= int(i) < n] or list(range(n))
    pairs: list[tuple[int, int, bool]] = []
    for i in rows:
        row_limit = n
        for j in range(row_limit):
            if i == j:
                continue
            label = bool(matrix[i, j])
            if not label:
                pairs.append((i, j, False))
            elif include_true_controls and len(pairs) < max_tasks:
                pairs.append((i, j, True))
    rng = random.Random(random_seed)
    rng.shuffle(pairs)
    selected = pairs[: max(0, int(max_tasks))]
    return [_loaded_task(i, j, label, equations[i], equations[j]) for i, j, label in selected]


def make_sair_eval_sample(config: SAIRTaskLoadConfig) -> list[BreakthroughTask]:
    equations = load_sair_equations(config.equations_path)
    matrix = load_sair_matrix(config.matrix_path)
    loaded = make_sair_false_tasks(
        equations,
        matrix,
        max_tasks=config.max_tasks,
        random_seed=config.random_seed,
        source_row_ids=config.source_row_ids,
        include_true_controls=config.include_true_controls,
    )
    return [task.to_breakthrough_task() for task in loaded]


def _loaded_task(i: int, j: int, label: bool, eq1: str, eq2: str) -> LoadedSAIRTask:
    family = infer_sair_family(eq1, eq2)
    return LoadedSAIRTask(
        task_id=f"sair_{i}_{j}",
        eq1_id=i,
        eq2_id=j,
        equation1=eq1,
        equation2=eq2,
        normalized_equation1=normalize_sair_equation(eq1),
        normalized_equation2=normalize_sair_equation(eq2),
        expected_matrix_label=label,
        family=family,
        metadata={"source": "sair_matrix", "false_pair": not label},
    )


def infer_sair_family(eq1: str, eq2: str) -> str:
    lhs2, rhs2 = [part.strip() for part in normalize_sair_equation(eq2).split("=", 1)]
    joined = f"{eq1} {eq2}"
    if lhs2 in {"x", "y", "z"} or rhs2 in {"x", "y", "z"}:
        return "projection_pressure"
    if "x = y" in normalize_sair_equation(eq2) or "y = z" in normalize_sair_equation(eq2):
        return "collapse_or_constant_pressure"
    if _is_commutative_shape(eq2):
        return "commutativity_pressure"
    if "(x * x)" in joined or "(y * y)" in joined:
        return "idempotent_band_pressure"
    if joined.count("*") >= 4:
        return "associative_or_deep_term_pressure"
    return "mixed_sair_false_pair"


def _is_commutative_shape(eq: str) -> bool:
    s = normalize_sair_equation(eq)
    return "(x * y)" in s and "(y * x)" in s
